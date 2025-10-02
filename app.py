from flask import Flask, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

# Połączenie z MongoDB (użyj swoich danych)
client = MongoClient('mongodb://myFlaskAppUser:anotherStrongPassword@172.31.41.176:27017/test_database')
db = client.test_database

@app.route('/')
def home():
    return jsonify({
        'message': 'Flask MongoDB CRUD',
        'endpoints': [
            '/products',
            '/products/electronics',
            '/products/available',
            '/users'
        ]
    })

# 🎯 Endpoint do odczytu WSZYSTKICH produktów
@app.route('/products')
def get_products():
    try:
        products = list(db.products.find())
        for product in products:
            product['_id'] = str(product['_id'])
        return jsonify(products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 🎯 Endpoint do odczytu produktów z konkretnej kategorii
@app.route('/products/<category>')
def get_products_by_category(category):
    try:
        products = list(db.products.find({'category': category}))
        for product in products:
            product['_id'] = str(product['_id'])
        return jsonify({
            'category': category,
            'count': len(products),
            'products': products
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 🎯 Endpoint do odczytu tylko dostępnych produktów
@app.route('/products/available')
def get_available_products():
    try:
        products = list(db.products.find({'in_stock': True}))
        for product in products:
            product['_id'] = str(product['_id'])
        return jsonify({
            'available_count': len(products),
            'products': products
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 🎯 Endpoint do odczytu użytkowników
@app.route('/users')
def get_users():
    try:
        users = list(db.users.find())
        for user in users:
            user['_id'] = str(user['_id'])
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)