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
    
    # 2. Filter lowest price per store
    final_results = process_scraped_data(raw_results)
    
    # 3. Store in DB
    try:
        # Get or create product
        norm_title = query.lower() # simplify normalization for DB
        prod = Product.query.filter_by(normalized_title=norm_title).first()
        if not prod:
            prod = Product(title=query, normalized_title=norm_title)
            db.session.add(prod)
            db.session.commit()
            
        # Add history
        for item in final_results:
            hist = PriceHistory(
                product_id=prod.id,
                website=item['store'],
                seller_name=item.get('seller_name', ''),
                price=item['price'],
                original_price=item.get('originalPrice'),
                discount=item.get('discount', 0),
                rating=item.get('rating'),
                review_count=item.get('reviewCount', 0),
                availability=item.get('availability'),
                buy_url=item.get('buyUrl', '#')
            )
            db.session.add(hist)
        db.session.commit()
    except Exception as e:
        print("DB Error:", e)
        db.session.rollback()

    return jsonify(final_results)

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
