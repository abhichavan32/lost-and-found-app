import os
import logging
import uuid
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from sqlalchemy import or_

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------
from models import db, User, Item, Notification, MarketItem, Order, Payment

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    db_url = "sqlite:///lost_and_found.db"  # fallback for local dev
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 300, "pool_pre_ping": True}

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")

# ---------------------------------------------------------------------------
# Flask-Login
# ---------------------------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------------------------------------------------------
# File uploads
# ---------------------------------------------------------------------------
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------------------------------------------------------
# Constants / helpers
# ---------------------------------------------------------------------------
CATEGORIES = [
    "Electronics", "Clothing", "Jewelry", "Keys", "Documents",
    "Bags", "Books", "Pets", "Vehicles", "Sports Equipment", "Other",
]

def generate_item_id() -> str:
    return str(uuid.uuid4())[:8]

def create_notification_for_lost_item(item: Item) -> None:
    try:
        users = User.query.filter(User.id != item.user_id).all()
        for user in users:
            notification = Notification(
                title=f"New Lost Item Posted: {item.title}",
                message=f"A new lost item '{item.title}' was posted in {item.location}. Check if you've found something similar!",
                type="lost_item",
                user_id=user.id,
                item_id=item.id,
            )
            db.session.add(notification)
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Error creating notifications: {e}")

# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        phone = request.form.get("phone")

        if not all([username, email, password, first_name, last_name]):
            flash("Please fill in all required fields.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html")

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )
        try:
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {e}")
            flash("Registration failed. Please try again.", "error")

    return render_template("auth/register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template("auth/login.html")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("auth/login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("index"))

# ---------------------------------------------------------------------------
# Dashboard & notifications
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user_items = Item.query.filter_by(user_id=current_user.id).order_by(Item.date_posted.desc()).all()
    lost_items = Item.query.filter_by(user_id=current_user.id, type="lost").all()
    found_items = Item.query.filter_by(user_id=current_user.id, type="found").all()
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    recent_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    return render_template(
        "dashboard.html",
        user_items=user_items,
        lost_items=lost_items,
        found_items=found_items,
        unread_notifications=unread_notifications,
        recent_notifications=recent_notifications,
    )

@app.route("/notifications")
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template("notifications.html", notifications=notifications)

@app.route("/notifications/<int:notification_id>/mark_read")
@login_required
def mark_notification_read(notification_id: int):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return redirect(url_for("notifications"))

# ---------------------------------------------------------------------------
# Main / Item routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    recent_lost = Item.query.filter_by(type="lost", status="active").order_by(Item.date_posted.desc()).limit(6).all()
    recent_found = Item.query.filter_by(type="found", status="active").order_by(Item.date_posted.desc()).limit(6).all()
    return render_template("index.html", recent_lost=recent_lost, recent_found=recent_found)

@app.route("/item/new", methods=["GET", "POST"])
@login_required
def new_item():
    if request.method == "POST":
        title = request.form.get("title")
        type_ = request.form.get("type")
        location = request.form.get("location")
        description = request.form.get("description")
        category = request.form.get("category")
        file = request.files.get("image")

        if not title or not type_ or not location:
            flash("Title, type, and location are required.", "error")
            return redirect(request.url)

        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        item = Item(
            title=title,
            type=type_,
            location=location,
            description=description,
            category=category,
            image_filename=filename,
            user_id=current_user.id,
            item_id=generate_item_id(),
            status="active",
            date_posted=datetime.utcnow(),
        )

        try:
            db.session.add(item)
            db.session.commit()
            if type_ == "lost":
                create_notification_for_lost_item(item)
            flash("Item posted successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error posting item: {e}")
            flash("Failed to post item. Try again.", "error")

    return render_template("item_form.html", categories=CATEGORIES)

@app.route("/item/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("You cannot edit this item.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        item.title = request.form.get("title")
        item.type = request.form.get("type")
        item.location = request.form.get("location")
        item.description = request.form.get("description")
        item.category = request.form.get("category")
        file = request.files.get("image")

        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            item.image_filename = filename

        try:
            db.session.commit()
            flash("Item updated successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating item: {e}")
            flash("Failed to update item. Try again.", "error")

    return render_template("item_form.html", item=item, categories=CATEGORIES)

@app.route("/item/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("You cannot delete this item.", "error")
        return redirect(url_for("dashboard"))
    try:
        db.session.delete(item)
        db.session.commit()
        flash("Item deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting item: {e}")
        flash("Failed to delete item.", "error")
    return redirect(url_for("dashboard"))

# ---------------------------------------------------------------------------
# Marketplace routes
# ---------------------------------------------------------------------------
@app.route("/marketplace")
def marketplace():
    items = MarketItem.query.filter_by(status="active").order_by(MarketItem.date_posted.desc()).all()
    return render_template("marketplace.html", items=items)

@app.route("/marketplace/new", methods=["GET", "POST"])
@login_required
def new_market_item():
    if request.method == "POST":
        title = request.form.get("title")
        price = float(request.form.get("price") or 0)
        description = request.form.get("description")
        file = request.files.get("image")

        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        item = MarketItem(
            title=title,
            description=description,
            price=price,
            image_filename=filename,
            user_id=current_user.id,
            status="active",
            date_posted=datetime.utcnow(),
        )
        try:
            db.session.add(item)
            db.session.commit()
            flash("Marketplace item posted!", "success")
            return redirect(url_for("marketplace"))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error posting market item: {e}")
            flash("Failed to post item.", "error")
    return render_template("market_item_form.html")

@app.route("/marketplace/<int:item_id>/buy", methods=["POST"])
@login_required
def buy_market_item(item_id):
    item = MarketItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        flash("You cannot buy your own item.", "error")
        return redirect(url_for("marketplace"))
    try:
        order = Order(
            item_id=item.id,
            buyer_id=current_user.id,
            seller_id=item.user_id,
            amount=item.price,
            date_ordered=datetime.utcnow(),
        )
        db.session.add(order)
        item.status = "sold"
        db.session.commit()
        flash("Purchase successful!", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error buying item: {e}")
        flash("Purchase failed. Try again.", "error")
    return redirect(url_for("marketplace"))

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
