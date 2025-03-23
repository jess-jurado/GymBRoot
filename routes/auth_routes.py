from flask import Blueprint, request, jsonify
import bcrypt
import jwt
import datetime
from config import get_db_connection
from functools import wraps



SECRET_KEY = "super_secreto"  # Cambia esto por una clave segura

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")

    if not nombre or not email or not password:
        return jsonify({"error": "Faltan datos"}), 400

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si el email ya existe
    cursor.execute("SELECT * FROM Usuarios WHERE Email = ?", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        return jsonify({"error": "El correo ya está registrado"}), 400

    try:
        cursor.execute(
            "INSERT INTO Usuarios (Nombre, Email, Password_hash) VALUES (?, ?, ?)",
            (nombre, email, hashed_password),
        )
        conn.commit()
        return jsonify({"mensaje": "Usuario registrado correctamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Faltan datos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Password_hash FROM Usuarios WHERE Email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "Credenciales incorrectas"}), 401

    user_id, stored_password = user

    if not bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    # Generar un token JWT
    token = jwt.encode(
        {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        SECRET_KEY,
        algorithm="HS256",
    )
    # Convertir el token a string si es necesario
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return jsonify({"token": token, "mensaje": "Inicio de sesión exitoso"})


@auth_bp.route("/protected", methods=["GET"])
def protected():
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "Token requerido"}), 401

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"mensaje": "Acceso permitido", "user_id": decoded["user_id"]})
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expirado"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token inválido"}), 401

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Token en formato Bearer

        if not token:
            return jsonify({'message': 'Token es necesario'}), 403

        try:
            # Verificar y decodificar el token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data['user_id']  # ID del usuario desde el payload
        except:
            return jsonify({'message': 'Token inválido'}), 403

        return f(current_user, *args, **kwargs)  # Pasar el current_user a la vista

    return decorated_function