import jwt
import datetime
from flask import jsonify

SECRET_KEY = "super_secreto"  # Asegúrate de almacenar esto de forma segura (no hardcodeado)

def encode_auth_token(user_id):
    """
    Genera un token JWT para un usuario.
    :param user_id: El ID del usuario a quien se le va a generar el token.
    :return: token JWT.
    """
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),  # Expiración en 1 día
            'iat': datetime.datetime.utcnow(),  # Fecha de creación
            'user_id': user_id  # Incluye el user_id para que pueda ser recuperado al verificar el token
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
