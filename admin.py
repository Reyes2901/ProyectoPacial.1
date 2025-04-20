# app/admin_routes.py
import bcrypt
import psycopg2
import numpy as np
from flask import Blueprint, request, redirect, url_for, flash, session, jsonify
from psycopg2.extras import RealDictCursor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import DB_CONFIG

client_bp = Blueprint('client', __name__)

def get_db():
    config = DB_CONFIG.copy()
    config.pop('cursor_factory', None)
    return psycopg2.connect(cursor_factory=RealDictCursor, **config)

def require_login():
    if 'user_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión.'}), 401
    return None

@client_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if len(password) < 8:
        return jsonify({'error': 'La contraseña debe tener al menos 8 caracteres.'}), 400

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    return jsonify({'error': 'Este correo ya está registrado.'}), 400
                cur.execute("""
                    INSERT INTO users (username, email, password, role)
                    VALUES (%s, %s, %s, %s)
                """, (username, email, hashed_password.decode(), 'client'))
                conn.commit()
        return jsonify({'success': 'Registro exitoso.'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                if user and bcrypt.checkpw(password.encode(), user['password'].encode()):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    return jsonify({'success': 'Sesión iniciada.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Correo o contraseña incorrectos.'}), 401

@client_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': 'Sesión cerrada.'}), 200

@client_bp.route('/products', methods=['GET'])
def index():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM products")
                products = cur.fetchall()
        return jsonify(products), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/ranking', methods=['GET'])
def ranking():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, description, price, image_url FROM products")
                all_products = cur.fetchall()

                user_id = session.get("user_id", 1)
                cur.execute("SELECT product_id FROM cart WHERE user_id = %s", (user_id,))
                cart_product_ids = {row[0] for row in cur.fetchall()}

        if cart_product_ids:
            texts = [f"{prod[1]} {prod[2]}" for prod in all_products]
            product_ids = [prod[0] for prod in all_products]
            vectorizer = TfidfVectorizer(stop_words='spanish')
            tfidf_matrix = vectorizer.fit_transform(texts)

            cart_indices = [i for i, pid in enumerate(product_ids) if pid in cart_product_ids]
            cart_vectors = tfidf_matrix[cart_indices]
            similarity_scores = cosine_similarity(cart_vectors, tfidf_matrix)
            avg_similarity = np.mean(similarity_scores, axis=0)
            ranked_indices = np.argsort(avg_similarity)[::-1]

            recommended = []
            for i in ranked_indices:
                if product_ids[i] not in cart_product_ids:
                    recommended.append(all_products[i])
                if len(recommended) >= 4:
                    break

            return jsonify({
                'recommended': recommended,
                'mean_score': float(np.max(avg_similarity))
            }), 200
        else:
            return jsonify({'recommended': [], 'mean_score': 0.0}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if not session.get('user_id'):
        return jsonify({'error': 'Debes iniciar sesión.'}), 401

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                if not cur.fetchone():
                    return jsonify({'error': 'Producto no encontrado.'}), 404

                cur.execute("""
                    SELECT 1 FROM cart WHERE user_id = %s AND product_id = %s
                """, (session['user_id'], product_id))

                if cur.fetchone():
                    cur.execute("""
                        UPDATE cart SET quantity = quantity + 1
                        WHERE user_id = %s AND product_id = %s
                    """, (session['user_id'], product_id))
                else:
                    cur.execute("""
                        INSERT INTO cart (user_id, product_id, quantity)
                        VALUES (%s, %s, 1)
                    """, (session['user_id'], product_id))
                conn.commit()
        return jsonify({'success': 'Producto agregado al carrito.'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/cart', methods=['GET'])
def cart():
    if not session.get('user_id'):
        return jsonify({'error': 'Debes iniciar sesión.'}), 401

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.name, p.price, c.quantity,
                           (p.price * c.quantity) AS total_price, c.product_id
                    FROM cart c
                    JOIN products p ON c.product_id = p.id
                    WHERE c.user_id = %s
                """, (session['user_id'],))
                items = cur.fetchall()
        total = sum(item['total_price'] for item in items)
        return jsonify({'cart_items': items, 'total': total}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/remove_from_cart/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    if not session.get('user_id'):
        return jsonify({'error': 'Debes iniciar sesión.'}), 401

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM cart WHERE user_id = %s AND product_id = %s",
                            (session['user_id'], product_id))
                conn.commit()
        return jsonify({'success': 'Producto eliminado.'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/checkout', methods=['POST'])
def checkout():
    if not session.get('user_id'):
        return jsonify({'error': 'Debes iniciar sesión.'}), 401

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.price, c.quantity
                    FROM cart c
                    JOIN products p ON c.product_id = p.id
                    WHERE c.user_id = %s
                """, (session['user_id'],))
                items = cur.fetchall()

                total = sum(i['price'] * i['quantity'] for i in items)

                cur.execute("INSERT INTO orders (user_id, total) VALUES (%s, %s) RETURNING id",
                            (session['user_id'], total))
                order_id = cur.fetchone()['id']

                cur.execute("DELETE FROM cart WHERE user_id = %s", (session['user_id'],))
                conn.commit()

        return jsonify({'success': 'Compra realizada.', 'order_id': order_id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/order_summary/<int:order_id>', methods=['GET'])
def order_summary(order_id):
    if not session.get('user_id'):
        return jsonify({'error': 'Debes iniciar sesión.'}), 401

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s",
                            (order_id, session['user_id']))
                order = cur.fetchone()

        if not order:
            return jsonify({'error': 'Orden no encontrada.'}), 404

        return jsonify({'order': order}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

