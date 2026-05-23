import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationEngine:
    @staticmethod
    def rank_platforms(platforms_data, trend_data=None):
        """
        Analyzes all compared platforms for a product variant and computes intelligent deal scores.
        
        platforms_data: dictionary of platform objects.
        trend_data: optional dictionary of trend context from TrendAnalyzer.
        """
        ranked = []
        
        # 1. Find absolute lowest price across platforms for baseline
        valid_prices = [p.get('lowest_price') for p in platforms_data.values() if p.get('lowest_price')]
        lowest_overall_price = min(valid_prices) if valid_prices else 1
        
        for platform_name, data in platforms_data.items():
            score = 0
            reasons = []
            
            # --- A. Current Price (40 points max) ---
            price = data.get('lowest_price', 0)
            if price > 0:
                # If it's the absolute lowest, give max points. Otherwise scale down.
                price_ratio = lowest_overall_price / price
                price_score = price_ratio * 40
                score += price_score
                
                if price == lowest_overall_price:
                    reasons.append("Lowest current price")
            
            # --- B. Historical Price Context (30 points max) ---
            if trend_data and trend_data.get('trend_status') != 'Not Enough Data':
                if trend_data['is_historical_low'] and price <= trend_data['historical_low']:
                    score += 30
                    reasons.append("Historical low detected 📉")
                elif trend_data['trend_status'] == 'Falling':
                    score += 20
                    reasons.append("Price is dropping")
                elif trend_data['trend_status'] == 'Stable':
                    score += 10
                elif trend_data['trend_status'] == 'Rising':
                    score += 0
                    reasons.append("Price is unusually high right now")
            else:
                # Without trend data, we give a baseline score
                score += 15
            
            # --- C. Discount Percentage (10 points max) ---
            discount = 0
            if 'original_price' in data and data['original_price'] > price:
                discount = ((data['original_price'] - price) / data['original_price']) * 100
            
            discount_score = min(discount / 5, 10) # 50% discount gives max 10 points
            score += discount_score
            if discount > 20:
                reasons.append(f"High discount ({int(discount)}% off)")
                
            # --- D. Match Confidence (10 points max) ---
            confidence = data.get('match_confidence', 0)
            if confidence > 85:
                score += 10
                reasons.append("AI highly confident in product match ✨")
            elif confidence > 70:
                score += 5
                
            # --- E. Seller Quality / Delivery (10 points max) ---
            # Using mock markers for now
            seller = data.get('cheapest_seller_name', '')
            if "Official" in seller or "Assured" in seller or "Prime" in seller:
                score += 10
                reasons.append("Highly trusted seller 🛡️")
            else:
                score += 5
                
            # Cap score at 100
            final_score = round(min(score, 100), 1)
            
            # Determine Badge/Category
            badge = "AI Recommended"
            if final_score > 90 and trend_data and trend_data.get('is_historical_low'):
                badge = "🔥 Best Deal & Historical Low"
            elif final_score > 85:
                badge = "🔥 Best Deal"
            elif price == lowest_overall_price:
                badge = "💰 Cheapest Price"
            
            # Save results back to the data dictionary
            data['recommendation'] = {
                'deal_score': final_score,
                'badge': badge,
                'reasons': reasons
            }
            
            ranked.append({
                'platform': platform_name,
                'score': final_score,
                'data': data
            })
            
            logger.info(f"Recommendation Engine: {platform_name} scored {final_score} (Price: {price})")

        # Sort platforms by score descending
        ranked.sort(key=lambda x: x['score'], reverse=True)
        
        # Return the winning platform name
        best_platform = ranked[0]['platform'] if ranked else None
        return best_platform

    @staticmethod
    def get_personalized_recommendations(user_id):
        """
        Generates personalized recommendations based on user activities, 
        watchlist, preferences, and deal scores.
        """
        from app.database.models import User, UserPreferences, UserActivity, Product, PriceHistory
        import json
        
        user = User.query.get(user_id)
        if not user:
            return RecommendationEngine.get_trending_deals()
            
        # Try to load user preferences
        pref_categories = []
        pref_brands = []
        budget_max = None
        
        if user.preferences:
            pref_categories = json.loads(user.preferences.category_preferences) if user.preferences.category_preferences else []
            pref_brands = json.loads(user.preferences.brand_preferences) if user.preferences.brand_preferences else []
            budget_max = user.preferences.budget_max
            
        # Get user's recent search/view activity to extract brand/category hints
        recent_activities = UserActivity.query.filter_by(user_id=user_id)\
            .order_by(UserActivity.timestamp.desc()).limit(10).all()
            
        for act in recent_activities:
            if act.activity_type == 'search' and act.details:
                query = act.details.lower()
                if 'iphone' in query or 'apple' in query:
                    pref_brands.append('apple')
                if 'samsung' in query:
                    pref_brands.append('samsung')
                if 'sony' in query:
                    pref_brands.append('sony')
                if 'tv' in query or 'television' in query:
                    pref_categories.append('tv')
                if 'phone' in query or 'mobile' in query:
                    pref_categories.append('smartphones')
                    
        # Make lists unique and lowercase
        pref_categories = list(set([c.lower() for c in pref_categories]))
        pref_brands = list(set([b.lower() for b in pref_brands]))
        
        # Query products
        query = Product.query
        
        # Build filters
        if pref_brands and pref_categories:
            query = query.filter((Product.brand.in_(pref_brands)) | (Product.category.in_(pref_categories)))
        elif pref_brands:
            query = query.filter(Product.brand.in_(pref_brands))
        elif pref_categories:
            query = query.filter(Product.category.in_(pref_categories))
            
        products = query.limit(20).all()
        
        # If no preferred products, fall back to all products
        if not products:
            products = Product.query.limit(20).all()
            
        # Calculate scores and sort
        recommendations = []
        for prod in products:
            # Get latest price histories
            histories = PriceHistory.query.filter_by(product_id=prod.id)\
                .order_by(PriceHistory.timestamp.desc()).all()
                
            if not histories:
                continue
                
            # Keep only the latest entry per website
            latest_by_website = {}
            for h in histories:
                if h.website not in latest_by_website or h.timestamp > latest_by_website[h.website].timestamp:
                    latest_by_website[h.website] = h
                    
            if not latest_by_website:
                continue
                
            # Build platforms_data structure
            platforms_data = {}
            for web, h in latest_by_website.items():
                platforms_data[web] = {
                    'lowest_price': h.price,
                    'original_price': h.original_price or h.price,
                    'cheapest_seller_name': h.seller_name or 'Seller',
                    'direct_seller_link': h.buy_url,
                    'match_confidence': 90, 
                }
                
            # Run ranking
            from app.analytics.trend_analysis import TrendAnalyzer
            trend_data = TrendAnalyzer.analyze_product_trend(prod.id)
            
            best_platform = RecommendationEngine.rank_platforms(platforms_data, trend_data)
            if best_platform and best_platform in platforms_data:
                best_data = platforms_data[best_platform]
                
                # Check budget constraints
                if budget_max and best_data['lowest_price'] > budget_max:
                    continue
                    
                recommendations.append({
                    'product_id': prod.id,
                    'title': prod.title,
                    'brand': prod.brand or 'Generic',
                    'category': prod.category or 'Electronics',
                    'price': best_data['lowest_price'],
                    'original_price': best_data['original_price'],
                    'store': best_platform,
                    'buy_url': best_data['direct_seller_link'],
                    'deal_score': best_data['recommendation']['deal_score'],
                    'badge': best_data['recommendation']['badge'],
                    'reasons': best_data['recommendation']['reasons']
                })
                
        # Sort by deal_score descending
        recommendations.sort(key=lambda x: x['deal_score'], reverse=True)
        return recommendations[:4]

    @staticmethod
    def get_trending_deals():
        """
        Returns highest-scoring deals globally from the system.
        """
        from app.database.models import Product, PriceHistory
        products = Product.query.limit(10).all()
        deals = []
        for prod in products:
            histories = PriceHistory.query.filter_by(product_id=prod.id)\
                .order_by(PriceHistory.timestamp.desc()).all()
            if not histories:
                continue
            latest_by_website = {}
            for h in histories:
                if h.website not in latest_by_website or h.timestamp > latest_by_website[h.website].timestamp:
                    latest_by_website[h.website] = h
            platforms_data = {}
            for web, h in latest_by_website.items():
                platforms_data[web] = {
                    'lowest_price': h.price,
                    'original_price': h.original_price or h.price,
                    'cheapest_seller_name': h.seller_name or 'Seller',
                    'direct_seller_link': h.buy_url,
                    'match_confidence': 90,
                }
            best_platform = RecommendationEngine.rank_platforms(platforms_data, None)
            if best_platform and best_platform in platforms_data:
                best_data = platforms_data[best_platform]
                deals.append({
                    'product_id': prod.id,
                    'title': prod.title,
                    'brand': prod.brand or 'Generic',
                    'category': prod.category or 'Electronics',
                    'price': best_data['lowest_price'],
                    'original_price': best_data['original_price'],
                    'store': best_platform,
                    'buy_url': best_data['direct_seller_link'],
                    'deal_score': best_data['recommendation']['deal_score'],
                    'badge': best_data['recommendation']['badge'],
                    'reasons': best_data['recommendation']['reasons']
                })
        deals.sort(key=lambda x: x['deal_score'], reverse=True)
        return deals[:4]

