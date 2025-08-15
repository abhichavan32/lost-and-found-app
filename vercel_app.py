from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "vercel-secret-key")

# Database configuration for Vercel (using SQLite in memory for demo)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Import and initialize database
from models import db
db.init_app(app)

# Import models
from models import User, Item, Notification, MarketItem, Order, Payment, Review

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Categories for filtering
CATEGORIES = [
    'Electronics', 'Clothing', 'Jewelry', 'Keys', 'Documents', 
    'Bags', 'Books', 'Pets', 'Vehicles', 'Sports Equipment', 'Other'
]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_item_id():
    return str(uuid.uuid4())[:8]

# Initialize database and create sample data
def init_vercel_db():
    with app.app_context():
        db.create_all()
        
        # Create sample users if none exist
        if not User.query.first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                first_name='Admin',
                last_name='User',
                phone='123-456-7890',
                email_verified=True,
                active=True
            )
            db.session.add(admin_user)
            
            # Create sample items
            sample_items = [
                Item(
                    id=generate_item_id(),
                    type='lost',
                    title='iPhone 13',
                    description='Lost my iPhone at the mall yesterday. It has a blue case and a cracked screen protector.',
                    category='Electronics',
                    location='Shopping Mall',
                    date_posted=datetime.utcnow(),
                    user_id=1
                ),
                Item(
                    id=generate_item_id(),
                    type='found',
                    title='Car Keys',
                    description='Found a set of car keys with a red keychain in the parking lot.',
                    category='Keys',
                    location='Parking Lot',
                    date_posted=datetime.utcnow(),
                    user_id=1
                ),
                Item(
                    id=generate_item_id(),
                    type='lost',
                    title='Student ID Card',
                    description='Lost my student ID card. Name: John Doe, Student ID: 12345',
                    category='Documents',
                    location='University Library',
                    date_posted=datetime.utcnow(),
                    user_id=1
                )
            ]
            
            for item in sample_items:
                db.session.add(item)
            
            db.session.commit()

# Initialize database
init_vercel_db()

@app.route("/")
def home():
    items = Item.query.filter_by(status='active').order_by(Item.date_posted.desc()).limit(6).all()
    return render_template('vercel_home.html', items=items, categories=CATEGORIES)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    
    return render_template('auth/login.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('auth/register.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            email_verified=True,
            active=True
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/api/items")
def get_items():
    items = Item.query.filter_by(status='active').order_by(Item.date_posted.desc()).all()
    return jsonify([{
        'id': item.id,
        'type': item.type,
        'title': item.title,
        'description': item.description,
        'location': item.location,
        'category': item.category,
        'date_posted': item.date_posted.isoformat()
    } for item in items])

@app.route("/api/items", methods=['POST'])
def add_item():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    new_item = Item(
        id=generate_item_id(),
        type=data.get('type', 'lost'),
        title=data.get('title', ''),
        description=data.get('description', ''),
        location=data.get('location', ''),
        category=data.get('category', 'Other'),
        date_posted=datetime.utcnow(),
        user_id=current_user.id
    )
    
    db.session.add(new_item)
    db.session.commit()
    
    return jsonify({
        'id': new_item.id,
        'type': new_item.type,
        'title': new_item.title,
        'description': new_item.description,
        'location': new_item.location,
        'category': new_item.category,
        'date_posted': new_item.date_posted.isoformat()
    }), 201

@app.route("/health")
def health():
    return {"status": "healthy", "message": "Lost & Found API is running!"}

if __name__ == "__main__":
    app.run(debug=True)
