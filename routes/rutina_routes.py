from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from config import get_db_connection
from functools import wraps
import jwt
import datetime
import cloudinary
import cloudinary.api
import cloudinary.uploader

rutinas_bp = Blueprint('rutinas', __name__)

cloudinary.config(
    cloud_name='dntqaxsko',
    api_key='323523837582744',
    api_secret='ES85Ti4VrGNKOJ07wiBLBRFE8u8'
)


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:
            # Si se envía token, se procesa
            if token.startswith("Bearer "):
                token = token[7:]
            try:
                decoded = jwt.decode(token, "super_secreto", algorithms=["HS256"])
                current_user = decoded['user_id']
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token ha expirado"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Token inválido"}), 401
            except Exception as e:
                return jsonify({"error": str(e)}), 401
        else:
            # Si no hay token, se revisa la sesión
            current_user = session.get("user_id")
            if not current_user:
                return jsonify({"error": "Token requerido"}), 401
        return f(current_user, *args, **kwargs)
    return decorated_function

# Ruta para crear una rutina con múltiples ejercicios
@rutinas_bp.route("/rutinas", methods=["POST"])
@token_required
def crear_rutina(current_user):
    # Obtener los datos de la rutina desde el cuerpo de la solicitud
    data = request.get_json()
    
    print("Datos recibidos en el servidor:", data)  # Depuración

    nombre_rutina = data.get("nombre_rutina")
    dias = data.get("dias")  # Días con sus respectivos ejercicios

    # Validación básica
    if not nombre_rutina or not dias or not isinstance(dias, dict):
        return jsonify({"error": "Faltan datos o el formato de días es inválido"}), 400

    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verificar si ya existe una rutina con el mismo nombre para el usuario
        cursor.execute(
            "SELECT id FROM Rutinas WHERE Usuario_id = ? AND Nombre_rutina = ?",
            (current_user, nombre_rutina)
        )
        if cursor.fetchone():
            return jsonify({"error": "Ya tienes una rutina con este nombre"}), 400
        
        # Insertar la nueva rutina en la base de datos para cada ejercicio seleccionado
        for dia, ejercicios_dia in dias.items():
            for ejercicio_info in ejercicios_dia:
                # Aquí insertamos solo los valores necesarios: Usuario_id, Nombre_rutina, Dia, Id_ejercicio
                id_ejercicios = ejercicio_info.get("ejercicios", [])
                for id_ejercicio in id_ejercicios:
                    print(f"Insertando ejercicio ID: {id_ejercicio} en el día {dia}")  # Depuración
                    cursor.execute(
                        "INSERT INTO Rutinas (Usuario_id, Nombre_rutina, Dia, Id_ejercicio) VALUES (?, ?, ?, ?)",
                        (current_user, nombre_rutina, dia, id_ejercicio)
                    )

        conn.commit()
        return jsonify({"mensaje": "Rutina creada correctamente"}), 201

    except Exception as e:
        print("Error:", str(e))  # Depuración en consola
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Ruta para obtener las rutinas del usuario autenticado
@rutinas_bp.route("/rutinas", methods=["GET"])
@token_required
def obtener_rutinas(current_user):
    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Consultar las rutinas asociadas al usuario
        cursor.execute(
            "SELECT id, Nombre_rutina, Dia, Id_ejercicio FROM Rutinas WHERE Usuario_id = ?",
            (current_user,)
        )
        rows = cursor.fetchall()

        # Convertir los resultados a una lista de diccionarios
        rutinas = []
        for row in rows:
            rutina = {
                "id": row[0],
                "nombre_rutina": row[1],
                "dia": row[2],
                "id_ejercicio": row[3]
            }
            rutinas.append(rutina)

        return jsonify({"rutinas": rutinas}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Ruta para actualizar una rutina
@rutinas_bp.route("/rutinas/<int:rutina_id>", methods=["PUT"])
@token_required
def actualizar_rutina(current_user, rutina_id):
    data = request.get_json()

    # Permitir actualizar uno o más campos
    nombre_rutina = data.get("nombre_rutina")
    dia = data.get("dia")
    id_ejercicio = data.get("id_ejercicio")

    if not (nombre_rutina or dia or id_ejercicio):
        return jsonify({"error": "Debes proporcionar al menos un campo para actualizar"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verificar que la rutina existe y pertenece al usuario
        cursor.execute("SELECT * FROM Rutinas WHERE id = ? AND Usuario_id = ?", (rutina_id, current_user))
        if not cursor.fetchone():
            return jsonify({"error": "Rutina no encontrada o no autorizada"}), 404

        # Si se quiere actualizar el id_ejercicio, verificar que exista en la tabla Ejercicios
        if id_ejercicio:
            cursor.execute("SELECT id FROM Ejercicios WHERE id = ?", (id_ejercicio,))
            if not cursor.fetchone():
                return jsonify({"error": "El id_ejercicio proporcionado no existe"}), 400

        # Construir la sentencia UPDATE dinámicamente
        campos = []
        params = []
        if nombre_rutina:
            campos.append("Nombre_rutina = ?")
            params.append(nombre_rutina)
        if dia:
            campos.append("Dia = ?")
            params.append(dia)
        if id_ejercicio:
            campos.append("Id_ejercicio = ?")
            params.append(id_ejercicio)

        params.extend([rutina_id, current_user])
        query = "UPDATE Rutinas SET " + ", ".join(campos) + " WHERE id = ? AND Usuario_id = ?"
        cursor.execute(query, tuple(params))
        conn.commit()

        return jsonify({"mensaje": "Rutina actualizada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Ruta para eliminar una rutina
@rutinas_bp.route("/rutinas/<int:rutina_id>", methods=["DELETE"])
@token_required
def eliminar_rutina(current_user, rutina_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verificar que la rutina exista y pertenezca al usuario
        cursor.execute("SELECT * FROM Rutinas WHERE id = ? AND Usuario_id = ?", (rutina_id, current_user))
        if not cursor.fetchone():
            return jsonify({"error": "Rutina no encontrada o no autorizada"}), 404

        cursor.execute("DELETE FROM Rutinas WHERE id = ? AND Usuario_id = ?", (rutina_id, current_user))
        conn.commit()
        return jsonify({"mensaje": "Rutina eliminada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@rutinas_bp.route('/get_ejercicios_por_grupo', methods=['GET'])
def get_ejercicios_por_grupo():
    grupo = request.args.get('grupo', '').strip()

    if not grupo:
        return jsonify({'error': 'El grupo muscular es obligatorio'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, Subgrupo_muscular, Nombre_ejercicio, imagen_url
            FROM Ejercicios
            WHERE Grupo_muscular = ?
        """, (grupo,))

        ejercicios = cursor.fetchall()

        resultado = [
            {
                'id': e[0],
                'Subgrupo_muscular': e[1],
                'Nombre_ejercicio': e[2],
                'imagen_url': e[3]
            }
            for e in ejercicios
        ]

        return jsonify({'ejercicios': resultado})

    except Exception as e:
        return jsonify({'error': f'Error en la consulta: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()

def buscar_imagen_en_cloudinary(prefijo):
    try:
        # Realizar una búsqueda en Cloudinary con el prefijo
        recursos = cloudinary.api.resources(type='upload', prefix=prefijo, max_results=1)
        
        # Si encontramos resultados
        if recursos['resources']:
            # Obtenemos la URL de la imagen
            imagen_url = recursos['resources'][0]['url']
            return imagen_url
        else:
            return None
    except cloudinary.exceptions.Error as e:
        print(f"Error buscando la imagen: {e}")
        return None
