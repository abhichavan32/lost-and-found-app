from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
app.secret_key = "vercel-secret-key"

# Simple in-memory storage for demo
items = [
    {
        "id": 1,
        "type": "lost",
        "title": "iPhone 13",
        "description": "Lost my iPhone at the mall",
        "location": "Shopping Mall",
        "category": "Electronics"
    },
    {
        "id": 2,
        "type": "found",
        "title": "Car Keys",
        "description": "Found car keys in parking lot",
        "location": "Parking Lot",
        "category": "Keys"
    }
]

@app.route("/")
def home():
    return render_template('vercel_home.html', items=items)

@app.route("/api/items")
def get_items():
    return jsonify(items)

@app.route("/api/items", methods=['POST'])
def add_item():
    data = request.get_json()
    new_item = {
        "id": len(items) + 1,
        "type": data.get('type', 'lost'),
        "title": data.get('title', ''),
        "description": data.get('description', ''),
        "location": data.get('location', ''),
        "category": data.get('category', 'Other')
    }
    items.append(new_item)
    return jsonify(new_item), 201

@app.route("/health")
def health():
    return {"status": "healthy", "message": "Lost & Found API is running!"}

if __name__ == "__main__":
    app.run(debug=True)
