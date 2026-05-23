from flask import Blueprint, request, jsonify, render_template
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.mock_data import ALERTS_DATA
from app.scraper.manager import ScraperManager
from app.analytics.price_logic import process_scraped_data
from app.database.models import db, Product, PriceHistory, ProductPrediction, User, UserPreferences, UserActivity, Watchlist, PriceAlert, Notification
from app.utils.rate_limiter import rate_limit
from app.ml.insight_generator import AIInsightGenerator
from app.ml.recommendation_engine import RecommendationEngine
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

    BUG FIX (no-query path):
    The original code returned mock PRODUCT_DATA but forcibly overwrote
    every item's title with "iPhone 16 Pro 256GB" regardless of what was
    in PRODUCT_DATA, and the buyUrl for every mock item was "#" (a dead link).

    The landing page now shows a helpful empty-state message instead of fake
    data. When the user actually types a query the real scraping path runs.
    This also means mock_data.py stays as demo data for the Alerts section
    only (which is its intended purpose) and never pollutes the product grid.
    """
    query = request.args.get('q', '').strip()

    if not query:
        # Return an empty results list — the frontend will show the
        # "Type something to search" empty-state UI.
        return jsonify({
            "search_query": "",
            "results": []
        })

    # 1. Scrape live data
    raw_results = ScraperManager.search_all(query)

    # 2. Get or create product record and calculate trend
    norm_title = query.lower()
    prod = Product.query.filter_by(normalized_title=norm_title).first()

    trend_data = None
    if prod:
        from app.analytics.trend_analysis import TrendAnalyzer
        trend_data = TrendAnalyzer.analyze_product_trend(prod.id)

    # 3. Process scraped data — group by variant, rank, sort cheapest first
    final_results = process_scraped_data(raw_results, query, trend_data)

    # 4. Store snapshot in DB
    try:
        if not prod:
            prod = Product(title=query, normalized_title=norm_title)
            db.session.add(prod)
            db.session.commit()

        # Log User Activity
        if current_user.is_authenticated:
            recent_act = UserActivity.query.filter_by(user_id=current_user.id, activity_type='search', details=query).first()
            if not recent_act:
                act = UserActivity(user_id=current_user.id, activity_type='search', details=query)
                db.session.add(act)
        else:
            act = UserActivity(user_id=None, activity_type='search', details=query)
            db.session.add(act)

        for variant in final_results:
            for store, store_data in variant['platforms'].items():
                hist = PriceHistory(
                    product_id=prod.id,
                    website=store,
                    seller_name=store_data['cheapest_seller_name'],
                    price=store_data['lowest_price'],
                    original_price=store_data['lowest_price'],
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
    if current_user.is_authenticated:
        notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
        if not notifs:
            return jsonify(ALERTS_DATA)
        return jsonify([
            {
                "id": n.id,
                "type": n.type,
                "icon": n.icon,
                "product": n.title.replace("Price Alert: ", "").replace("Historical Low Detected: ", ""),
                "title": n.title,
                "message": n.message,
                "store": n.action,
                "time": n.timestamp.strftime("%d %b, %H:%M"),
                "action": n.action,
                "buy_url": n.buy_url or '#'
            } for n in notifs
        ])
    return jsonify(ALERTS_DATA)



@main_bp.route('/api/predict', methods=['GET'])
def get_prediction():
    """
    Returns AI prediction for a specific product query.
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
        prediction_result['product_id'] = prod.id
        return jsonify(prediction_result)


# --- User Authentication Endpoints ---

@main_bp.route('/api/auth/register', methods=['POST'])
@rate_limit(limit=10, period=60)
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    name = data.get('name', '').strip()
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 400
        
    try:
        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            password_hash=hashed_password,
            name=name
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Create default preferences
        prefs = UserPreferences(user_id=new_user.id)
        db.session.add(prefs)
        db.session.commit()
        
        return jsonify({"message": "User registered successfully", "user": new_user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to register user: {e}"}), 500

@main_bp.route('/api/auth/login', methods=['POST'])
@rate_limit(limit=10, period=60)
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401
        
    login_user(user, remember=True)
    
    try:
        activity = UserActivity(user_id=user.id, activity_type='login', details=f"Logged in from {request.remote_addr}")
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        
    return jsonify({"message": "Logged in successfully", "user": user.to_dict()})

@main_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    if current_user.is_authenticated:
        logout_user()
    return jsonify({"message": "Logged out successfully"})

@main_bp.route('/api/auth/status', methods=['GET'])
def auth_status():
    if current_user.is_authenticated:
        return jsonify({
            "authenticated": True,
            "user": current_user.to_dict()
        })
    return jsonify({
        "authenticated": False
    })

@main_bp.route('/api/auth/preferences', methods=['GET', 'POST'])
@login_required
def user_preferences():
    prefs = UserPreferences.query.filter_by(user_id=current_user.id).first()
    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.session.add(prefs)
        db.session.commit()
        
    if request.method == 'POST':
        data = request.get_json() or {}
        categories = data.get('category_preferences', [])
        brands = data.get('brand_preferences', [])
        budget_min = data.get('budget_min')
        budget_max = data.get('budget_max')
        
        prefs.category_preferences = json.dumps(categories)
        prefs.brand_preferences = json.dumps(brands)
        if budget_min is not None:
            prefs.budget_min = int(budget_min)
        if budget_max is not None:
            prefs.budget_max = int(budget_max)
            
        try:
            db.session.commit()
            return jsonify({"message": "Preferences updated successfully", "preferences": prefs.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update preferences: {e}"}), 500
            
    return jsonify(prefs.to_dict())

# --- Watchlist System ---

@main_bp.route('/api/watchlist', methods=['GET'])
@login_required
def get_watchlist():
    watchlist_items = Watchlist.query.filter_by(user_id=current_user.id).all()
    result = []
    for item in watchlist_items:
        prod = item.product
        if not prod:
            continue
            
        latest_hist = PriceHistory.query.filter_by(product_id=prod.id)\
            .order_by(PriceHistory.timestamp.desc()).first()
            
        current_price = latest_hist.price if latest_hist else 0
        website = latest_hist.website if latest_hist else 'N/A'
        
        pred = ProductPrediction.query.filter_by(product_id=prod.id)\
            .order_by(ProductPrediction.timestamp.desc()).first()
        
        item_dict = item.to_dict()
        item_dict['current_price'] = current_price
        item_dict['website'] = website
        item_dict['prediction'] = pred.to_dict() if pred else None
        result.append(item_dict)
        
    return jsonify(result)

@main_bp.route('/api/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    product_title = data.get('product_title', '').strip()
    target_price = data.get('target_price')
    
    prod = None
    if product_id:
        prod = Product.query.get(product_id)
    elif product_title:
        norm_title = product_title.lower()
        prod = Product.query.filter_by(normalized_title=norm_title).first()
        if not prod:
            prod = Product(title=product_title, normalized_title=norm_title)
            db.session.add(prod)
            db.session.commit()
            
            try:
                raw_results = ScraperManager.search_all(product_title)
                from app.analytics.price_logic import process_scraped_data
                final_results = process_scraped_data(raw_results, product_title, None)
                for variant in final_results:
                    for store, store_data in variant['platforms'].items():
                        hist = PriceHistory(
                            product_id=prod.id,
                            website=store,
                            seller_name=store_data['cheapest_seller_name'],
                            price=store_data['lowest_price'],
                            original_price=store_data['lowest_price'],
                            discount=0,
                            rating=4.5,
                            review_count=1000,
                            availability="In Stock",
                            buy_url=store_data['direct_seller_link']
                        )
                        db.session.add(hist)
                db.session.commit()
            except Exception as e:
                print("Watchlist bootstrap scraping failed:", e)
                
    if not prod:
        return jsonify({"error": "Product not found and could not be initialized"}), 404
        
    existing = Watchlist.query.filter_by(user_id=current_user.id, product_id=prod.id).first()
    if existing:
        if target_price is not None:
            existing.target_price = int(target_price)
            db.session.commit()
            return jsonify({"message": "Watchlist target price updated", "watchlist_item": existing.to_dict()})
        return jsonify({"message": "Product is already in watchlist", "watchlist_item": existing.to_dict()})
        
    try:
        new_item = Watchlist(
            user_id=current_user.id,
            product_id=prod.id,
            target_price=int(target_price) if target_price is not None else None
        )
        db.session.add(new_item)
        
        activity = UserActivity(user_id=current_user.id, activity_type='add_watchlist', details=f"Added {prod.title} to watchlist")
        db.session.add(activity)
        
        new_alert = PriceAlert(
            user_id=current_user.id,
            product_id=prod.id,
            alert_type='price_drop',
            price_threshold=int(target_price) if target_price is not None else None
        )
        db.session.add(new_alert)
        
        db.session.commit()
        return jsonify({"message": "Product added to watchlist", "watchlist_item": new_item.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add to watchlist: {e}"}), 500

@main_bp.route('/api/watchlist/remove/<int:id>', methods=['DELETE'])
@login_required
def remove_from_watchlist(id):
    item = Watchlist.query.filter_by(id=id, user_id=current_user.id).first()
    if not item:
        return jsonify({"error": "Watchlist item not found"}), 404
        
    try:
        PriceAlert.query.filter_by(user_id=current_user.id, product_id=item.product_id).delete()
        
        activity = UserActivity(user_id=current_user.id, activity_type='remove_watchlist', details=f"Removed product ID {item.product_id} from watchlist")
        db.session.add(activity)
        
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Product removed from watchlist successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to remove from watchlist: {e}"}), 500

# --- Price Alert System ---

@main_bp.route('/api/alerts/create', methods=['POST'])
@login_required
def create_custom_alert():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    alert_type = data.get('alert_type', 'price_drop')
    price_threshold = data.get('price_threshold')
    
    if not product_id:
        return jsonify({"error": "Product ID is required"}), 400
        
    prod = Product.query.get(product_id)
    if not prod:
        return jsonify({"error": "Product not found"}), 404
        
    try:
        new_alert = PriceAlert(
            user_id=current_user.id,
            product_id=prod.id,
            alert_type=alert_type,
            price_threshold=int(price_threshold) if price_threshold is not None else None
        )
        db.session.add(new_alert)
        db.session.commit()
        return jsonify({"message": "Custom price alert created", "alert": new_alert.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create alert: {e}"}), 500

@main_bp.route('/api/alerts/read/<int:id>', methods=['POST'])
@login_required
def mark_notification_read(id):
    notif = Notification.query.filter_by(id=id, user_id=current_user.id).first()
    if not notif:
        return jsonify({"error": "Notification not found"}), 404
    try:
        notif.is_read = True
        db.session.commit()
        return jsonify({"message": "Notification marked as read"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed: {e}"}), 500

# --- Recommendation System ---

@main_bp.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    if current_user.is_authenticated:
        recs = RecommendationEngine.get_personalized_recommendations(current_user.id)
    else:
        recs = RecommendationEngine.get_trending_deals()
    return jsonify(recs)

# --- AI Insight Engine ---

@main_bp.route('/api/insights', methods=['GET'])
def get_insights():
    query = request.args.get('q', '').strip().lower()
    prod = Product.query.filter_by(normalized_title=query).first()
    if not prod:
        return jsonify([])
        
    latest_hist = PriceHistory.query.filter_by(product_id=prod.id)\
        .order_by(PriceHistory.timestamp.desc()).first()
    latest_price = latest_hist.price if latest_hist else 0
    
    insights = AIInsightGenerator.generate_insights(prod.id, latest_price)
    return jsonify(insights)

# --- Advanced Analytics Summary ---

@main_bp.route('/api/analytics/dashboard', methods=['GET'])
@login_required
def get_analytics_dashboard():
    watchlist_items = Watchlist.query.filter_by(user_id=current_user.id).all()
    count_watchlist = len(watchlist_items)
    
    active_alerts = PriceAlert.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    potential_savings = 0
    category_counts = {}
    
    for item in watchlist_items:
        prod = item.product
        if not prod:
            continue
            
        cat = prod.category or 'Other'
        category_counts[cat] = category_counts.get(cat, 0) + 1
        
        latest_hist = PriceHistory.query.filter_by(product_id=prod.id)\
            .order_by(PriceHistory.timestamp.desc()).first()
        if latest_hist and item.target_price:
            diff = latest_hist.price - item.target_price
            if diff > 0:
                potential_savings += diff
                
    recent_searches = UserActivity.query.filter_by(user_id=current_user.id, activity_type='search').count()
    
    return jsonify({
        "watchlist_count": count_watchlist,
        "active_alerts_count": active_alerts,
        "potential_savings": potential_savings,
        "category_distribution": category_counts,
        "search_count": recent_searches
    })

