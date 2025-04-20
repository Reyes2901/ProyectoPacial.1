# app/admin_routes.py

from flask import Blueprint, request, jsonify, flash
import psycopg2
from config import DB_CONFIG

admin_bp = Blueprint('admin', __name__)

def get_db():
    return psycopg2.connect(**DB_CONFIG)

@admin_bp.route('/')
def dashboard():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total_products FROM products")
    products = cur.fetchone()

    cur.execute("SELECT COUNT(*) AS total_users FROM users WHERE role='client'")
    users = cur.fetchone()

    cur.execute("SELECT COUNT(*) AS total_orders FROM orders")
    orders = cur.fetchone()

    conn.close()
    return jsonify({
        'total_products': products[0],
        'total_users': users[0],
        'total_orders': orders[0]
    })

@admin_bp.route('/products')
def products():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    data = cur.fetchall()
    conn.close()

    # Aquí, convertimos los datos a un formato adecuado para JSON
    products = [{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3], 'stock': row[4], 'image_url': row[5]} for row in data]

    return jsonify(products)

@admin_bp.route('/products/add', methods=['POST'])
def add_product():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')
    image_url = data.get('image_url')

    if not name or not description or not price or not stock or not image_url:
        return jsonify({'message': 'Por favor, completa todos los campos.'}), 400

    try:
        price = float(price)
        stock = int(stock)
    except ValueError:
        return jsonify({'message': 'El precio y el stock deben ser números válidos.'}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, description, price, stock, image_url) VALUES (%s, %s, %s, %s, %s)",
            (name, description, price, stock, image_url)
        )
        conn.commit()
        return jsonify({'message': 'Producto agregado con éxito.'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Error al agregar el producto: {str(e)}'}), 500
    finally:
        conn.close()

@admin_bp.route('/products/edit/<int:id>', methods=['POST'])
def edit_product(id):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')
    image_url = data.get('image_url')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE products 
        SET name=%s, description=%s, price=%s, stock=%s, image_url=%s 
        WHERE id=%s
    """, (name, description, price, stock, image_url, id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Producto actualizado con éxito.'})

@admin_bp.route('/products/delete/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Producto eliminado con éxito.'})
