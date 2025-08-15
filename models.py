from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    profile_image = db.Column(db.String(200))
    bio = db.Column(db.Text)
    school = db.Column(db.String(100))
    major = db.Column(db.String(100))
    graduation_year = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    phone_verified = db.Column(db.Boolean, default=False, nullable=False)
    wallet_balance = db.Column(db.Float, default=0.0, nullable=False)
    rating = db.Column(db.Float, default=0.0)
    total_ratings = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('Item', foreign_keys='Item.user_id', back_populates='owner', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    market_items = db.relationship('MarketItem', backref='seller', lazy=True, cascade='all, delete-orphan')
    purchases = db.relationship('Order', backref='buyer', lazy=True, foreign_keys='Order.buyer_id')
    sales = db.relationship('Order', backref='seller', lazy=True, foreign_keys='Order.seller_id')
    reviews_given = db.relationship('Review', backref='reviewer', lazy=True, foreign_keys='Review.reviewer_id')
    reviews_received = db.relationship('Review', backref='reviewed', lazy=True, foreign_keys='Review.reviewed_id')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.String(8), primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'lost' or 'found'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50))
    brand = db.Column(db.String(100))
    color = db.Column(db.String(50))
    size = db.Column(db.String(50))
    value = db.Column(db.Float)  # estimated value
    location = db.Column(db.String(200), nullable=False)
    location_details = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_lost_found = db.Column(db.DateTime)
    time_lost_found = db.Column(db.String(20))  # approximate time
    image = db.Column(db.String(200))
    additional_images = db.Column(db.JSON)  # array of image paths
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active', 'resolved', 'expired'
    resolution_type = db.Column(db.String(20))  # 'claimed', 'returned', 'donated'
    resolution_date = db.Column(db.DateTime)
    views = db.Column(db.Integer, default=0)
    reward_amount = db.Column(db.Float, default=0.0)
    tags = db.Column(db.JSON)  # array of searchable tags
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resolver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    owner = db.relationship('User', foreign_keys=[user_id], back_populates='items')
    resolver = db.relationship('User', foreign_keys=[resolver_id])
    
    def __repr__(self):
        return f'<Item {self.title}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'lost_item', 'found_item', 'match', etc.
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.String(8), db.ForeignKey('items.id'))
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class MarketItem(db.Model):
    __tablename__ = 'market_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(50), nullable=False)  # 'new', 'like_new', 'good', 'fair'
    category = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200))
    additional_images = db.Column(db.JSON)  # array of image paths
    status = db.Column(db.String(20), nullable=False, default='available')  # 'available', 'sold', 'reserved'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<MarketItem {self.title}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'completed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('market_items.id'), nullable=False)
    
    def __repr__(self):
        return f'<Order {self.id}>'

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Foreign keys
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    def __repr__(self):
        return f'<Review {self.id}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # 'wallet', 'credit_card', 'paypal'
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'completed', 'failed'
    transaction_id = db.Column(db.String(100))
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Foreign keys
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    def __repr__(self):
        return f'<Payment {self.id}>'
