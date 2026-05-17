from flask_sqlalchemy import SQLAlchemy
import datetime

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
