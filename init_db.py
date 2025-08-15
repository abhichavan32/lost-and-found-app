#!/usr/bin/env python3
"""
Database initialization script for Lost & Found application
"""

from app import app, db
from models import User, Item, Notification, MarketItem, Order, Payment, Review

def init_database():
    """Initialize the database with all tables"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Check if we need to create a default admin user
            if not User.query.first():
                from werkzeug.security import generate_password_hash
                
                # Create a default admin user
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
                db.session.commit()
                print("✅ Default admin user created!")
                print("   Username: admin")
                print("   Password: admin123")
            
            print("\n🎉 Database initialization completed!")
            print("You can now run the application with: python app.py")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_database()