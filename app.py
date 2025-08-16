import os
import logging
import uuid
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from sqlalchemy import or_

# -----------------------------------------------------------------------------
# App & Logging
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# -----------------------------------------------------------------------------
# Database configuration (Render-friendly, supports Postgres and MySQL)
# -----------------------------------------------------------------------------
db_url = os.environ.get("DATABASE_URL", "sqlite:///lost_and_found.db")

# Render gives postgres://... but SQLAlchemy expects postgresql://...
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# If user provided a MySQL URL, switch to PyMySQL to avoid MySQLdb build issues
if db_url.startswith("mysql://") or db_url.startswith("mysql+pymysql://"):
    try:
        import pymysql  # pure-Python MySQL driver
        pymysql.install_as_MySQLdb()
        # normalize to mysql:// so the above shim is used
        if db_url.startswith("mysql+pymysql://"):
            db_url = db_url.replace("mysql+pymysql://", "mysql://", 1)
        app.logger.info("Configured PyMySQL shim for MySQL.")
    except Exception as e:
        app.logger.warning(f"PyMySQL not available; MySQL may fail: {e}")


from flask_sqlalchemy import SQLAlchemy
import os
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
db = SQLAlchemy(app)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# -----------------------------------------------------------------------------
# Models & DB (import your existing `db` and models)
# -----------------------------------------------------------------------------
from models import db  # db = SQLAlchemy() should be defined inside models.py
db.init_app(app)

from models import User, Item, Notification, MarketItem, Order, Payment

# -----------------------------------------------------------------------------
# Migrations
# -----------------------------------------------------------------------------
migrate = Migrate(app, db)

# -----------------------------------------------------------------------------
# Auth (Flask-Login)
# -----------------------------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------------------------------------------------------
# File uploads
# -----------------------------------------------------------------------------
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
CATEGORIES = [
    "Electronics", "Clothing", "Jewelry", "Keys", "Documents",
    "Bags", "Books", "Pets", "Vehicles", "Sports Equipment", "Other",
]

def generate_item_id() -> str:
    return str(uuid.uuid4())[:8]

def create_notification_for_lost_item(item: Item) -> None:
    """Create notifications for all users when a lost item is posted."""
    try:
        users = User.query.filter(User.id != item.user_id).all()
        for user in users:
            notification = Notification(
                title=f"New Lost Item Posted: {item.title}",
                message=(
                    f"A new lost item '{item.title}' was posted in {item.location}. "
                    "Check if you've found something similar!"
                ),
                type="lost_item",
                user_id=user.id,
                item_id=item.id,
            )
            db.session.add(notification)
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Error creating notifications: {e}")

# -----------------------------------------------------------------------------
# Auth routes
# -----------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        phone = request.form.get("phone")

        # Validation
        if not all([username, email, password, first_name, last_name]):
            flash("Please fill in all required fields.", "error")
            return render_template("auth/register.html")

        # Check dupes
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

# -----------------------------------------------------------------------------
# Dashboard / Notifications
# -----------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user_items = Item.query.filter_by(user_id=current_user.id).order_by(Item.date_posted.desc()).all()
    lost_items = Item.query.filter_by(user_id=current_user.id, type="lost").all()
    found_items = Item.query.filter_by(user_id=current_user.id, type="found").all()
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    recent_notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(5).all()
    )
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
    notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc()).all()
    )
    return render_template("notifications.html", notifications=notifications)

@app.route("/notifications/<int:notification_id>/mark_read")
@login_required
def mark_notification_read(notification_id: int):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return redirect(url_for("notifications"))

# -----------------------------------------------------------------------------
# Main / Item routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    recent_lost = (
        Item.query.filter_by(type="lost", status="active")
        .order_by(Item.date_posted.desc()).limit(6).all()
    )
    recent_found = (
        Item.query.filter_by(type="found", status="active")
        .order_by(Item.date_posted.desc()).limit(6).all()
    )
    return render_template("index.html", recent_lost=recent_lost, recent_found=recent_found)

@app.route("/post/<item_type>")
@login_required
def post_item_form(item_type: str):
    if item_type not in ["lost", "found"]:
        flash("Invalid item type", "error")
        return redirect(url_for("index"))
    return render_template("post_item.html", item_type=item_type, categories=CATEGORIES)

@app.route("/post/<item_type>", methods=["POST"])
@login_required
def post_item(item_type: str):
    if item_type not in ["lost", "found"]:
        flash("Invalid item type", "error")
        return redirect(url_for("index"))

    try:
        # Required fields
        required_fields = ["title", "description", "category", "location"]
        for field in required_fields:
            if not request.form.get(field):
                flash(f"{field.replace('_', ' ').title()} is required", "error")
                return redirect(url_for("post_item_form", item_type=item_type))

        # Upload
        image_filename = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_filename = filename

        # Create item
        item = Item(
            id=generate_item_id(),
            type=item_type,
            title=request.form["title"].strip(),
            description=request.form["description"].strip(),
            category=request.form["category"],
            location=request.form["location"].strip(),
            date_lost_found=request.form.get("date_lost_found", ""),
            image=image_filename,
            user_id=current_user.id,
        )

        db.session.add(item)
        db.session.commit()

        if item_type == "lost":
            create_notification_for_lost_item(item)

        flash(f"{item_type.title()} item posted successfully!", "success")
        return redirect(url_for("item_detail", item_id=item.id))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error posting item: {e}")
        flash("An error occurred while posting the item. Please try again.", "error")
        return redirect(url_for("post_item_form", item_type=item_type))

@app.route("/browse/<item_type>")
def browse_items(item_type: str):
    if item_type not in ["lost", "found"]:
        flash("Invalid item type", "error")
        return redirect(url_for("index"))

    category = request.args.get("category", "")
    location = request.args.get("location", "")
    search = request.args.get("search", "")

    query = Item.query.filter_by(type=item_type, status="active")

    if category:
        query = query.filter(Item.category == category)
    if location:
        query = query.filter(Item.location.ilike(f"%{location}%"))
    if search:
        query = query.filter(
            or_(
                Item.title.ilike(f"%{search}%"),
                Item.description.ilike(f"%{search}%"),
                Item.location.ilike(f"%{search}%"),
            )
        )

    items = query.order_by(Item.date_posted.desc()).all()
    return render_template(
        "browse.html",
        items=items,
        item_type=item_type,
        categories=CATEGORIES,
        current_category=category,
        current_location=location,
        current_search=search,
    )

@app.route("/item/<item_id>")
def item_detail(item_id: str):
    item = Item.query.get_or_404(item_id)
    return render_template("item_detail.html", item=item)

@app.route("/item/<item_id>/edit")
@login_required
def edit_item_form(item_id: str):
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    return render_template("post_item.html", item=item, categories=CATEGORIES, editing=True)

@app.route("/item/<item_id>/edit", methods=["POST"])
@login_required
def edit_item(item_id: str):
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    try:
        required_fields = ["title", "description", "category", "location"]
        for field in required_fields:
            if not request.form.get(field):
                flash(f"{field.replace('_', ' ').title()} is required", "error")
                return redirect(url_for("edit_item_form", item_id=item_id))

        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                item.image = filename

        item.title = request.form["title"].strip()
        item.description = request.form["description"].strip()
        item.category = request.form["category"]
        item.location = request.form["location"].strip()
        item.date_lost_found = request.form.get("date_lost_found", "")

        db.session.commit()
        flash("Item updated successfully!", "success")
        return redirect(url_for("item_detail", item_id=item_id))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating item: {e}")
        flash("An error occurred while updating the item. Please try again.", "error")
        return redirect(url_for("edit_item_form", item_id=item_id))

@app.route("/item/<item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id: str):
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    try:
        db.session.delete(item)
        db.session.commit()
        flash("Item deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting item: {e}")
        flash("Error deleting item", "error")
    return redirect(url_for("dashboard"))

# -----------------------------------------------------------------------------
# Marketplace
# -----------------------------------------------------------------------------
@app.route("/marketplace")
def marketplace():
    items = (
        MarketItem.query.filter_by(status="available")
        .order_by(MarketItem.created_at.desc()).all()
    )
    return render_template("marketplace/index.html", items=items)

@app.route("/marketplace/sell", methods=["GET", "POST"])
@login_required
def sell_item():
    if request.method == "POST":
        try:
            image_filename = None
            if "image" in request.files:
                file = request.files["image"]
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                    filename = timestamp + filename
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                    image_filename = filename

            item = MarketItem(
                title=request.form["title"].strip(),
                description=request.form["description"].strip(),
                price=float(request.form["price"]),
                type=request.form["type"],  # 'book' or 'notes'
                condition=request.form.get("condition"),
                subject=request.form.get("subject"),
                author=request.form.get("author"),
                image=image_filename,
                seller_id=current_user.id,
            )

            db.session.add(item)
            db.session.commit()

            flash("Item listed successfully!", "success")
            return redirect(url_for("marketplace_item", item_id=item.id))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error listing item: {e}")
            flash("An error occurred while listing the item. Please try again.", "error")

    return render_template("marketplace/sell.html")

@app.route("/marketplace/item/<int:item_id>")
def marketplace_item(item_id: int):
    item = MarketItem.query.get_or_404(item_id)
    return render_template("marketplace/item_detail.html", item=item)

@app.route("/marketplace/buy/<int:item_id>", methods=["POST"])
@login_required
def buy_item(item_id: int):
    item = MarketItem.query.get_or_404(item_id)

    if item.status != "available":
        flash("This item is no longer available.", "error")
        return redirect(url_for("marketplace_item", item_id=item_id))

    if item.seller_id == current_user.id:
        flash("You cannot buy your own item.", "error")
        return redirect(url_for("marketplace_item", item_id=item_id))

    if current_user.wallet_balance < item.price:
        flash("Insufficient wallet balance.", "error")
        return redirect(url_for("marketplace_item", item_id=item_id))

    try:
        order = Order(
            item_id=item.id,
            buyer_id=current_user.id,
            seller_id=item.seller_id,
            amount=item.price,
            status="completed",
        )

        payment = Payment(
            order=order,
            amount=item.price,
            payment_method="wallet",
            status="completed",
            completed_at=datetime.utcnow(),
        )

        current_user.wallet_balance -= item.price
        item.seller.wallet_balance += item.price
        item.status = "sold"

        db.session.add(order)
        db.session.add(payment)
        db.session.commit()

        flash("Purchase successful!", "success")
        return redirect(url_for("marketplace_item", item_id=item_id))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error processing purchase: {e}")
        flash("An error occurred while processing the purchase. Please try again.", "error")
        return redirect(url_for("marketplace_item", item_id=item_id))

# -----------------------------------------------------------------------------
# Search
# -----------------------------------------------------------------------------
@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return redirect(url_for("index"))

    items = (
        Item.query.filter(
            Item.status == "active",
            or_(
                Item.title.ilike(f"%{query}%"),
                Item.description.ilike(f"%{query}%"),
                Item.location.ilike(f"%{query}%"),
                Item.category.ilike(f"%{query}%"),
            ),
        )
        .order_by(Item.date_posted.desc()).all()
    )

    return render_template(
        "browse.html",
        items=items,
        item_type="search",
        categories=CATEGORIES,
        search_query=query,
    )

# -----------------------------------------------------------------------------
# Entrypoint (works for gunicorn app:app)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
