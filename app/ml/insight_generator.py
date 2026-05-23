import logging
from app.database.models import PriceHistory, ProductPrediction
import numpy as np

logger = logging.getLogger(__name__)

class AIInsightGenerator:
    @staticmethod
    def generate_insights(product_id, current_price):
        """
        Generates dynamic, human-readable AI insights for a product.
        Returns a list of dictionaries with text, icon, and type keys.
        """
        insights = []
        
        # 1. Fetch History
        history = PriceHistory.query.filter_by(product_id=product_id).all()
        if not history:
            return [{
                "text": "Initializing price history collection. Check back shortly for insights.",
                "icon": "⏳",
                "type": "info"
            }]
            
        prices = [h.price for h in history]
        avg_price = np.mean(prices) if prices else current_price
        min_price = min(prices) if prices else current_price
        
        # Current price vs average price
        if current_price < avg_price:
            diff_pct = round(((avg_price - current_price) / avg_price) * 100, 1)
            insights.append({
                "text": f"This product is currently {diff_pct}% below average market price.",
                "icon": "💰",
                "type": "positive"
            })
        elif current_price > avg_price:
            diff_pct = round(((current_price - avg_price) / avg_price) * 100, 1)
            insights.append({
                "text": f"This product is trading {diff_pct}% above average market price.",
                "icon": "📈",
                "type": "warning"
            })
            
        # Volatility
        if len(prices) >= 3:
            volatility = np.std(prices) / avg_price if avg_price > 0 else 0
            if volatility > 0.10:
                insights.append({
                    "text": "Price volatility is high this week. Rapid price shifts detected.",
                    "icon": "⚡",
                    "type": "warning"
                })
            elif volatility < 0.03:
                insights.append({
                    "text": "Price is highly stable with low fluctuation over recent checks.",
                    "icon": "🛡️",
                    "type": "neutral"
                })
                
        # All time low check
        if current_price <= min_price and len(prices) > 1:
            insights.append({
                "text": "Historical low detected! This matches or beats the lowest recorded price.",
                "icon": "🏆",
                "type": "positive"
            })
            
        # 2. Fetch Prediction
        prediction = ProductPrediction.query.filter_by(product_id=product_id)\
            .order_by(ProductPrediction.timestamp.desc()).first()
            
        if prediction:
            if prediction.buy_recommendation == 'WAIT':
                insights.append({
                    "text": f"AI predicts a likely drop of {prediction.expected_drop_percentage}% within {prediction.prediction_window_days} days.",
                    "icon": "🔮",
                    "type": "info"
                })
            elif prediction.buy_recommendation == 'BUY NOW':
                insights.append({
                    "text": "AI models suggest buying now as prices are projected to rise soon.",
                    "icon": "🚀",
                    "type": "positive"
                })
                
        # Default fallback
        if not insights:
            insights.append({
                "text": "Product is trading within a normal range. Keep watching for automated price updates.",
                "icon": "🔔",
                "type": "neutral"
            })
            
        return insights
