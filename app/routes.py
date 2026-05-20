from flask import Blueprint, request, jsonify, render_template
from app.mock_data import ALERTS_DATA
from app.scraper.manager import ScraperManager
from app.analytics.price_logic import process_scraped_data
from app.database.models import db, Product, PriceHistory

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Serve the webpage"""
    return render_template('index.html')

@main_bp.route('/api/products', methods=['GET'])
def get_products():
    """
    Return the list of products for the comparison dashboard.
    Accepts an optional '?q=' search parameter.
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        # Default behavior or empty
        from app.mock_data import PRODUCT_DATA
        return jsonify(PRODUCT_DATA)
        
    # 1. Scrape data
    raw_results = ScraperManager.search_all(query)
    
    # 2. Get or create product and calculate trend
    norm_title = query.lower() # simplify normalization for DB
    prod = Product.query.filter_by(normalized_title=norm_title).first()
    
    trend_data = None
    if prod:
        from app.analytics.trend_analysis import TrendAnalyzer
        trend_data = TrendAnalyzer.analyze_product_trend(prod.id)
    
    # 3. Process scraped data with trend context
    final_results = process_scraped_data(raw_results, query, trend_data)
    
    # 4. Store new snapshot in DB
    try:
        if not prod:
            prod = Product(title=query, normalized_title=norm_title)
            db.session.add(prod)
            db.session.commit()
            
        # Add history
        for variant in final_results:
            for store, store_data in variant['platforms'].items():
                hist = PriceHistory(
                    product_id=prod.id,
                    website=store,
                    seller_name=store_data['cheapest_seller_name'],
                    price=store_data['lowest_price'],
                    original_price=store_data['lowest_price'], # Simplification for now
                    discount=0,
                    rating=4.5,
                    review_count=1000,
                    availability="In Stock",
                    buy_url=store_data['direct_seller_link']
                )
                db.session.add(hist)
        db.session.commit()
    except Exception as e:
        print("DB Error:", e)
        db.session.rollback()

    return jsonify({
        "search_query": query,
        "results": final_results
    })

@main_bp.route('/api/history', methods=['GET'])
def get_history():
    """
    Returns price history for a specific product query.
    """
    query = request.args.get('q', '').strip().lower()
    prod = Product.query.filter_by(normalized_title=query).first()
    
    if not prod:
        return jsonify([])
        
    history = PriceHistory.query.filter_by(product_id=prod.id).order_by(PriceHistory.timestamp.asc()).all()
    return jsonify([h.to_dict() for h in history])

@main_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
    """
    Return the list of active price alerts.
    """
    return jsonify(ALERTS_DATA)
