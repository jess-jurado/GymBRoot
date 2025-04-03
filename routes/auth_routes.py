from flask import Blueprint, request, jsonify
import bcrypt
import jwt
import datetime
from config import get_db_connection
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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

# def send_email(recipient, token):
#     sender_email = "tu_email@gmail.com"
#     sender_password = "tu_contraseña"
    
#     subject = "Confirma tu cuenta"
#     confirm_link = f"http://tu-dominio.com/confirmar/{token}"
    
#     body = f"""
#     <html>
#     <body>
#         <h2>Confirmación de Registro</h2>
#         <p>Gracias por registrarte. Para activar tu cuenta, haz clic en el siguiente enlace:</p>
#         <a href="{confirm_link}">Confirmar Cuenta</a>
#     </body>
#     </html>
#     """

#     msg = MIMEMultipart()
#     msg["From"] = sender_email
#     msg["To"] = recipient
#     msg["Subject"] = subject
#     msg.attach(MIMEText(body, "html"))

#     try:
#         with smtplib.SMTP("smtp.gmail.com", 587) as server:
#             server.starttls()
#             server.login(sender_email, sender_password)
#             server.sendmail(sender_email, recipient, msg.as_string())
#             print(f"Correo enviado a {recipient}")
#     except Exception as e:
#         print(f"Error enviando correo: {e}")

# import jwt
# import datetime

# @auth_bp.route("/register", methods=["POST"])
# def register():
#     data = request.json
#     nombre = data.get("nombre")
#     email = data.get("email")
#     password = data.get("password")

#     if not nombre or not email or not password:
#         return jsonify({"error": "Faltan datos"}), 400

#     hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM Usuarios WHERE Email = ?", (email,))
#     existing_user = cursor.fetchone()

#     if existing_user:
#         return jsonify({"error": "El correo ya está registrado"}), 400

#     try:
#         cursor.execute(
#             "INSERT INTO Usuarios (Nombre, Email, Password_hash, Confirmado) VALUES (?, ?, ?, ?)",
#             (nombre, email, hashed_password, 0),  # 0 indica que aún no está confirmado
#         )
#         conn.commit()

#         # Generar un token de confirmación
#         token = jwt.encode({"email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, "super_secreto", algorithm="HS256")
        
#         # Enviar el correo de confirmación
#         send_email(email, token)

#         return jsonify({"mensaje": "Usuario registrado, revisa tu correo para confirmar la cuenta."}), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         cursor.close()
#         conn.close()

# @auth_bp.route("/confirmar/<token>", methods=["GET"])
# def confirmar_cuenta(token):
#     try:
#         decoded = jwt.decode(token, "super_secreto", algorithms=["HS256"])
#         email = decoded.get("email")

#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("UPDATE Usuarios SET Confirmado = 1 WHERE Email = ?", (email,))
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({"mensaje": "Cuenta confirmada correctamente. Ya puedes iniciar sesión."})
    
#     except jwt.ExpiredSignatureError:
#         return jsonify({"error": "El enlace ha expirado."}), 400
#     except jwt.InvalidTokenError:
#         return jsonify({"error": "Token inválido."}), 400
    
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