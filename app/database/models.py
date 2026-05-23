from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import datetime
import json

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    normalized_title = db.Column(db.String(255), nullable=False, unique=True, index=True)
    brand = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    
    # Relationships
    history = db.relationship('PriceHistory', backref='product', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'brand': self.brand,
            'category': self.category
        }

class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    website = db.Column(db.String(50), nullable=False) # e.g. "Amazon"
    seller_name = db.Column(db.String(100), nullable=True)
    
    price = db.Column(db.Integer, nullable=False)
    original_price = db.Column(db.Integer, nullable=True)
    discount = db.Column(db.Integer, default=0)
    
    rating = db.Column(db.Float, nullable=True)
    review_count = db.Column(db.Integer, default=0)
    
    availability = db.Column(db.String(50), nullable=True)
    delivery = db.Column(db.String(100), nullable=True)
    buy_url = db.Column(db.Text, nullable=False)
    
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'website': self.website,
            'seller_name': self.seller_name,
            'price': self.price,
            'original_price': self.original_price,
            'discount': self.discount,
            'rating': self.rating,
            'reviewCount': self.review_count,
            'availability': self.availability,
            'delivery': self.delivery,
            'buyUrl': self.buy_url,
            'timestamp': self.timestamp.isoformat()
        }

class ProductPrediction(db.Model):
    __tablename__ = 'product_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    
    predicted_price = db.Column(db.Integer, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    trend = db.Column(db.String(50), nullable=False)
    buy_recommendation = db.Column(db.String(100), nullable=False)
    expected_drop_percentage = db.Column(db.Float, nullable=False)
    prediction_window_days = db.Column(db.Integer, nullable=False)
    
    # Store future dates and prices as JSON for charts
    future_dates = db.Column(db.Text, nullable=True) # JSON list
    future_prices = db.Column(db.Text, nullable=True) # JSON list
    
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'product_id': self.product_id,
            'predicted_price': self.predicted_price,
            'confidence': self.confidence,
            'trend': self.trend,
            'buy_recommendation': self.buy_recommendation,
            'expected_drop_percentage': self.expected_drop_percentage,
            'prediction_window_days': self.prediction_window_days,
            'future_dates': json.loads(self.future_dates) if self.future_dates else [],
            'future_prices': json.loads(self.future_prices) if self.future_prices else [],
            'timestamp': self.timestamp.isoformat()
        }

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    plan = db.Column(db.String(50), default='Free Plan')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    preferences = db.relationship('UserPreferences', backref='user', uselist=False, cascade="all, delete-orphan")
    activities = db.relationship('UserActivity', backref='user', lazy=True, cascade="all, delete-orphan")
    watchlist = db.relationship('Watchlist', backref='user', lazy=True, cascade="all, delete-orphan")
    alerts = db.relationship('PriceAlert', backref='user', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'plan': self.plan,
            'created_at': self.created_at.isoformat()
        }

class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    category_preferences = db.Column(db.Text, default='[]') # JSON string list
    brand_preferences = db.Column(db.Text, default='[]') # JSON string list
    budget_min = db.Column(db.Integer, nullable=True)
    budget_max = db.Column(db.Integer, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category_preferences': json.loads(self.category_preferences) if self.category_preferences else [],
            'brand_preferences': json.loads(self.brand_preferences) if self.brand_preferences else [],
            'budget_min': self.budget_min,
            'budget_max': self.budget_max
        }

class UserActivity(db.Model):
    __tablename__ = 'user_activity'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # nullable for guest search
    
    activity_type = db.Column(db.String(50), nullable=False) # search, view_deal, add_watchlist
    details = db.Column(db.Text, nullable=True) # text details / json
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

class Watchlist(db.Model):
    __tablename__ = 'watchlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    target_price = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='watchlist_entries')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'target_price': self.target_price,
            'product': self.product.to_dict() if self.product else None,
            'created_at': self.created_at.isoformat()
        }

class PriceAlert(db.Model):
    __tablename__ = 'price_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    alert_type = db.Column(db.String(50), nullable=False, default='price_drop') # price_drop, historical_low, trend_change, volatility_spike
    price_threshold = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='alerts')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'alert_type': self.alert_type,
            'price_threshold': self.price_threshold,
            'is_active': self.is_active,
            'product_title': self.product.title if self.product else '',
            'created_at': self.created_at.isoformat()
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    type = db.Column(db.String(50), default='info') # positive, warning, info, neutral, urgent
    icon = db.Column(db.String(10), default='🔔')
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    action = db.Column(db.String(100), default='View')
    buy_url = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'icon': self.icon,
            'title': self.title,
            'message': self.message,
            'action': self.action,
            'buy_url': self.buy_url,
            'is_read': self.is_read,
            'timestamp': self.timestamp.isoformat()
        }
