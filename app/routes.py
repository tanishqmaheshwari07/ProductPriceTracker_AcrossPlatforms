from flask import Blueprint, request, jsonify, render_template
from app.mock_data import ALERTS_DATA
from app.scraper.manager import ScraperManager
from app.analytics.price_logic import process_scraped_data
from app.database.models import db, Product, PriceHistory, ProductPrediction
import datetime
import json

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
        mock_results = []
        for item in PRODUCT_DATA:
            new_item = dict(item)
            new_item['title'] = "iPhone 16 Pro 256GB"
            mock_results.append(new_item)
        final_results = process_scraped_data(mock_results, "iPhone 16 Pro")
        return jsonify({
            "search_query": "iPhone 16 Pro",
            "results": final_results
        })
        
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

@main_bp.route('/api/predict', methods=['GET'])
def get_prediction():
    """
    Returns AI prediction for a specific product query.
    Uses ML models to forecast prices and generate smart buying recommendations.
    """
    query = request.args.get('q', '').strip().lower()
    prod = Product.query.filter_by(normalized_title=query).first()
    
    if not prod:
        return jsonify({"error": "Product not found"}), 404
        
    # Check if a recent prediction exists (within the last hour)
    one_hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    cached_prediction = ProductPrediction.query.filter(
        ProductPrediction.product_id == prod.id,
        ProductPrediction.timestamp >= one_hour_ago
    ).order_by(ProductPrediction.timestamp.desc()).first()
    
    if cached_prediction:
        return jsonify(cached_prediction.to_dict())
        
    # Fetch historical data
    history = PriceHistory.query.filter_by(product_id=prod.id).order_by(PriceHistory.timestamp.asc()).all()
    history_dicts = [h.to_dict() for h in history]
    
    # Run Prediction
    from app.ml.price_predictor import PricePredictor
    predictor = PricePredictor()
    prediction_result = predictor.predict(history_dicts)
    
    # Save Prediction to DB
    try:
        new_prediction = ProductPrediction(
            product_id=prod.id,
            predicted_price=prediction_result['predicted_price'],
            confidence=prediction_result['confidence'],
            trend=prediction_result['trend'],
            buy_recommendation=prediction_result['buy_recommendation'],
            expected_drop_percentage=prediction_result['expected_drop_percentage'],
            prediction_window_days=prediction_result['prediction_window_days'],
            future_dates=json.dumps(prediction_result['future_dates']),
            future_prices=json.dumps(prediction_result['future_prices'])
        )
        db.session.add(new_prediction)
        db.session.commit()
        return jsonify(new_prediction.to_dict())
    except Exception as e:
        print("Prediction DB Error:", e)
        db.session.rollback()
        # Still return the result even if caching failed
        prediction_result['product_id'] = prod.id
        return jsonify(prediction_result)
