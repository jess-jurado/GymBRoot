from flask import Blueprint, request, jsonify
import jwt
from config import get_db_connection
from functools import wraps

user_bp = Blueprint('user', __name__)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token requerido"}), 401
        try:
            decoded = jwt.decode(token, "super_secreto", algorithms=["HS256"])
            current_user = decoded['user_id']
        except Exception as e:
            return jsonify({"error": str(e)}), 401
        return f(current_user, *args, **kwargs)
    return decorated_function

@user_bp.route("/profile", methods=["GET"])
@token_required
def profile(current_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Nombre, Email FROM Usuarios WHERE Id = ?", (current_user,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return jsonify({"nombre": user[0], "email": user[1]})
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404
