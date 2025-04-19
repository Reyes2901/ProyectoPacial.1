from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text
from werkzeug.security import check_password_hash  # Usado para verificar contraseñas hash

#C:/Users/Reyes/Desktop/1-2025/SI2/parcial1/theGit/ecomerceia/data/PostgreSQL/ecomerce.sql

# Crear app y configurar CORS
app = Flask(__name__)
#CORS(app, origins=["http://localhost:3000"])
CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})


# Configuración de PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/ecomerciaia'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar base de datos
db = SQLAlchemy(app)

# Modelo de Usuario
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
# Modelo de Producto
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)

# Ruta para probar conexión
@app.route('/')
def home():
    try:
        db.session.execute(text('SELECT 1'))  # 👈 Envolver el SQL con text()
        return 'Conexión a PostgreSQL exitosa 🐘'
    except Exception as e:
        return f'Error en conexión: {str(e)}'

# Ruta para obtener productos
@app.route('/productos', methods=['GET'])
def get_productos():
    productos = [
        {"id": 1, "nombre": "Camisa", "precio": 25},
        {"id": 2, "nombre": "Pantalón", "precio": 40}
    ]
    return jsonify(productos)

@app.route('/productos', methods=['POST'])
def add_producto():
    data = request.get_json()
    nombre = data.get('nombre')
    precio = data.get('precio')

    nuevo_producto = Producto(nombre=nombre, precio=precio)
    db.session.add(nuevo_producto)
    db.session.commit()

    return jsonify({"message": "Producto agregado exitosamente"}), 201
@app.route('/carrito', methods=['POST'])
def agregar_al_carrito():
    data = request.get_json()
    producto_id = data.get('producto_id')
    cantidad = data.get('cantidad')

    # Lógica para agregar al carrito
    return jsonify({"message": "Producto agregado al carrito"})

# Ruta de login (fake por ahora)
# Ruta de login con conexión a la base de datos
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # Buscar usuario por email
    usuario = Usuario.query.filter_by(email=email).first()

    if usuario:
        # Verificar si la contraseña es correcta
        if check_password_hash(usuario.password, password):  # Aquí se compara la contraseña con el hash
            return jsonify({"success": True, "message": "Login exitoso"}), 200
        else:
            return jsonify({"success": False, "message": "Contraseña incorrecta"}), 401
    else:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
# Ruta para registro
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    nuevo_usuario = Usuario(username=username, email=email, password=password)
    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({"message": "Usuario registrado exitosamente"}), 201

@app.route('/pedido', methods=['POST'])
def crear_pedido():
    data = request.get_json()
    carrito = data.get('carrito')  # Aquí se pasaría el carrito
    # Lógica para crear pedido
    return jsonify({"message": "Pedido creado exitosamente"})

# Punto de inicio
if __name__ == '__main__':
    app.run(debug=True)
