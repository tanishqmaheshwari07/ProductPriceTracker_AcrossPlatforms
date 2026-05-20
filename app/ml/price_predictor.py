import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import datetime
import json
import logging

logger = logging.getLogger(__name__)

class PricePredictor:
    def __init__(self):
        self.rf_model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
        self.lr_model = LinearRegression()

    def predict(self, price_history):
        """
        Takes a list of PriceHistory dicts and returns a prediction dict.
        """
        if not price_history or len(price_history) < 3:
            return self._not_enough_data()

        # 1. Preprocess Data
        df = pd.DataFrame(price_history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate base features
        min_time = df['timestamp'].min()
        df['days'] = (df['timestamp'] - min_time).dt.total_seconds() / (24 * 3600)
        
        # Only use days and average prices per day
        daily_df = df.groupby('days')['price'].min().reset_index()
        
        if len(daily_df) < 3:
            return self._not_enough_data()

        X = daily_df[['days']].values
        y = daily_df['price'].values
        
        # 2. Train Lightweight Models
        # Linear Regression for trend
        self.lr_model.fit(X, y)
        trend_slope = self.lr_model.coef_[0]
        
        # If the data spans less than 1 day (e.g. mock data or rapid inserts), 
        # the slope will be artificially massive. Cap the slope to avoid billions in predictions.
        days_span = X[-1][0] - X[0][0]
        if days_span < 1.0:
            trend_slope = 0 # Assume flat trend if we don't have even 1 day of data
            
        # Random Forest for non-linear patterns
        self.rf_model.fit(X, y)
        
        # 3. Generate Future Timeline (7, 14, 21, 30 days)
        last_day = daily_df['days'].max()
        future_days_offsets = [7, 14, 21, 30]
        future_days = np.array([last_day + d for d in future_days_offsets]).reshape(-1, 1)
        
        # Blend Random Forest and Linear Regression
        # If trend_slope was zeroed out, lr_preds would just be the mean or wildly off intercept.
        # It's safer to rely mostly on Random Forest if we have no real time span.
        if days_span < 1.0:
            future_preds = rf_preds
        else:
            future_preds = (rf_preds * 0.7) + (lr_preds * 0.3)
            
        # Ensure predictions don't drop below 0 or go insanely high
        max_reasonable_price = y[-1] * 2
        future_preds = np.clip(future_preds, 0, max_reasonable_price)
        
        # 4. Generate Future Dates
        last_date = df['timestamp'].max()
        future_dates_str = [(last_date + datetime.timedelta(days=int(d))).strftime('%Y-%m-%d') for d in future_days_offsets]
        
        # 5. Extract Metrics
        current_price = y[-1]
        min_predicted_price = min(future_preds)
        max_predicted_price = max(future_preds)
        predicted_price = int(min_predicted_price)
        
        # Calculate Volatility
        volatility = np.std(y) / np.mean(y) if np.mean(y) > 0 else 0
        
        # 6. Recommendation Logic
        expected_drop_percentage = 0.0
        if min_predicted_price < current_price:
            expected_drop_percentage = ((current_price - min_predicted_price) / current_price) * 100
            
        trend = self._classify_trend(trend_slope)
        buy_recommendation, window = self._get_recommendation(trend, expected_drop_percentage, volatility)
        
        # 7. Confidence Score
        confidence = self._calculate_confidence(len(daily_df), volatility, rf_preds, lr_preds)
        
        return {
            'predicted_price': int(predicted_price),
            'confidence': round(confidence, 1),
            'trend': trend,
            'buy_recommendation': buy_recommendation,
            'expected_drop_percentage': round(expected_drop_percentage, 1),
            'prediction_window_days': window,
            'future_dates': future_dates_str,
            'future_prices': [int(p) for p in future_preds],
            'current_price': int(current_price)
        }

    def _not_enough_data(self):
        return {
            'predicted_price': 0,
            'confidence': 0.0,
            'trend': 'Stable',
            'buy_recommendation': 'NOT ENOUGH DATA',
            'expected_drop_percentage': 0.0,
            'prediction_window_days': 0,
            'future_dates': [],
            'future_prices': [],
            'current_price': 0
        }

    def _classify_trend(self, slope):
        if slope > 5:
            return "Rising"
        elif slope < -5:
            return "Falling"
        return "Stable"

    def _get_recommendation(self, trend, drop_pct, volatility):
        if drop_pct > 5.0:
            return "WAIT", 14 # Wait for price drop
        elif trend == "Rising" and drop_pct <= 0:
            return "BUY NOW", 0 # Price might go up
        elif volatility > 0.15:
            return "WAIT", 7 # Highly volatile, wait a bit
        else:
            return "BUY NOW", 0 # Stable, good to buy

    def _calculate_confidence(self, data_points, volatility, rf_preds, lr_preds):
        # Base confidence from data size (max 50 points)
        conf = min((data_points / 50.0) * 40.0, 40.0)
        
        # Penalty for high volatility (max 30 points)
        vol_penalty = min(volatility * 100, 30)
        conf += (30 - vol_penalty)
        
        # Model agreement (max 30 points)
        agreement_error = np.mean(np.abs(rf_preds - lr_preds) / rf_preds)
        agr_penalty = min(agreement_error * 100, 30)
        conf += (30 - agr_penalty)
        
        # Boost confidence for robust cases
        return min(max(conf, 10.0), 98.5)
