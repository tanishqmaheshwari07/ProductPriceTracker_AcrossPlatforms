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
