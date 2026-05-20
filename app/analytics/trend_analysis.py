import pandas as pd
from app.database.models import PriceHistory, db

class TrendAnalyzer:
    @staticmethod
    def analyze_product_trend(product_id):
        """
        Analyzes the price history for a given product_id.
        Returns a dictionary with trend information:
        {
            'trend_status': 'Rising' | 'Falling' | 'Stable' | 'Not Enough Data',
            'historical_low': int,
            'is_historical_low': bool,
            'average_price': float
        }
        """
        # Fetch history from DB
        records = PriceHistory.query.filter_by(product_id=product_id).order_by(PriceHistory.timestamp.asc()).all()
        
        if not records or len(records) < 2:
            return {
                'trend_status': 'Not Enough Data',
                'historical_low': records[0].price if records else None,
                'is_historical_low': False,
                'average_price': records[0].price if records else None
            }
            
        # Convert to pandas DataFrame
        df = pd.DataFrame([r.to_dict() for r in records])
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Convert timestamps to numerical values for linear regression (days since first record)
        min_time = df['timestamp'].min()
        df['days'] = (df['timestamp'] - min_time).dt.total_seconds() / (24 * 3600)
        
        # Calculate basic stats
        historical_low = int(df['price'].min())
        latest_price = int(df.iloc[-1]['price'])
        avg_price = float(df['price'].mean())
        
        # Determine if current price is at or near historical low (within 2%)
        is_historical_low = latest_price <= (historical_low * 1.02)
        
        # Calculate slope (linear regression) to find trend
        # y = mx + c
        if len(df['days'].unique()) > 1: # We need variation in x to calculate slope
            x = df['days']
            y = df['price']
            
            x_mean = x.mean()
            y_mean = y.mean()
            
            numerator = sum((x - x_mean) * (y - y_mean))
            denominator = sum((x - x_mean)**2)
            
            slope = numerator / denominator if denominator != 0 else 0
            
            # Classify slope
            if slope > 10:  # Price increasing by more than 10 per day on average
                trend_status = 'Rising'
            elif slope < -10:
                trend_status = 'Falling'
            else:
                trend_status = 'Stable'
        else:
            # Not enough time variation, just compare first and last
            first_price = df.iloc[0]['price']
            if latest_price > first_price * 1.05:
                trend_status = 'Rising'
            elif latest_price < first_price * 0.95:
                trend_status = 'Falling'
            else:
                trend_status = 'Stable'
                
        return {
            'trend_status': trend_status,
            'historical_low': historical_low,
            'is_historical_low': is_historical_low,
            'average_price': avg_price
        }
