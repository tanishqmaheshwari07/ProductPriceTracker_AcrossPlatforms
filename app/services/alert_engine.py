import logging
import datetime
from app.database.models import db, PriceAlert, PriceHistory, Product, User
from app.services.notification_service import NotificationService
from app.analytics.trend_analysis import TrendAnalyzer

logger = logging.getLogger(__name__)

class AlertEngine:
    @staticmethod
    def check_all_alerts(app):
        """
        Runs alert scan across all active price alert subscriptions.
        """
        with app.app_context():
            logger.info("Starting alert verification scan...")
            active_alerts = PriceAlert.query.filter_by(is_active=True).all()
            
            for alert in active_alerts:
                try:
                    product = alert.product
                    user = User.query.get(alert.user_id)
                    if not product or not user:
                        continue
                        
                    # Find cheapest current price for this product
                    latest_history = PriceHistory.query.filter_by(product_id=product.id)\
                        .order_by(PriceHistory.timestamp.desc()).limit(15).all()
                    
                    if not latest_history:
                        continue
                        
                    # Get cheapest platform currently
                    cheapest_record = min(latest_history, key=lambda x: x.price)
                    current_price = cheapest_record.price
                    website = cheapest_record.website
                    buy_url = cheapest_record.buy_url
                    
                    # 1. Price Threshold Check
                    if alert.alert_type == 'price_drop' and alert.price_threshold:
                        if current_price <= alert.price_threshold:
                            title = f"Price Alert: {product.title} dropped!"
                            message = f"{product.title} has reached your target price of ₹{current_price} (Target: ₹{alert.price_threshold}) on {website}!"
                            NotificationService.send_notification(
                                user=user,
                                title=title,
                                message=message,
                                type='positive',
                                icon='📉',
                                action='Buy Now',
                                buy_url=buy_url
                            )
                            # Deactivate or set cooldown to prevent duplicate spamming
                            alert.is_active = False 
                            db.session.commit()
                            continue
                            
                    # 2. Historical Low Check
                    trend_data = TrendAnalyzer.analyze_product_trend(product.id)
                    if alert.alert_type == 'historical_low' and trend_data and trend_data.get('is_historical_low'):
                        # Check if current price is actually close to historical low
                        historical_min = trend_data.get('historical_low')
                        if historical_min and current_price <= historical_min:
                            title = f"Historical Low Detected: {product.title}"
                            message = f"{product.title} is at an all-time low price of ₹{current_price} on {website}!"
                            NotificationService.send_notification(
                                user=user,
                                title=title,
                                message=message,
                                type='positive',
                                icon='🏆',
                                action='View Deal',
                                buy_url=buy_url
                            )
                            alert.is_active = False 
                            db.session.commit()
                            continue
                        
                    # 3. Volatility Spike Check
                    if alert.alert_type == 'volatility_spike':
                        prices = [h.price for h in latest_history]
                        if len(prices) >= 3:
                            # Volatility is calculated standard deviation over mean
                            import numpy as np
                            std_dev = np.std(prices)
                            mean_price = np.mean(prices)
                            volatility = std_dev / mean_price if mean_price > 0 else 0
                            if volatility > 0.08: # >8% standard deviation
                                title = f"Price Volatility Spike: {product.title}"
                                message = f"{product.title} is experiencing high price fluctuations this week! Volatility is at {round(volatility*100, 1)}%."
                                NotificationService.send_notification(
                                    user=user,
                                    title=title,
                                    message=message,
                                    type='warning',
                                    icon='⚡',
                                    action='Compare Prices',
                                    buy_url=buy_url
                                )
                                alert.is_active = False
                                db.session.commit()
                                continue
                                
                    # 4. Trend changes
                    if alert.alert_type == 'trend_change' and trend_data:
                        current_trend = trend_data.get('trend_status')
                        if current_trend == 'Falling':
                            title = f"Price Trend Drop: {product.title}"
                            message = f"AI analysis shows price is dropping for {product.title}. Good time to buy might be close!"
                            NotificationService.send_notification(
                                user=user,
                                title=title,
                                message=message,
                                type='info',
                                icon='🎯',
                                action='View Forecast',
                                buy_url=buy_url
                            )
                            alert.is_active = False
                            db.session.commit()
                            continue

                except Exception as e:
                    logger.error(f"Error checking alert id {alert.id}: {e}")
                    db.session.rollback()
