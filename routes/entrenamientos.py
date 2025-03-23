from flask import Blueprint, request, jsonify
from datetime import datetime
from config import get_db_connection
from routes.auth_routes import token_required

entrenamientos_bp  = Blueprint("entrenamientos", __name__)

@entrenamientos_bp .route("/entrenamientos", methods=["POST"])
@token_required
def registrar_entrenamiento(current_user):
    """ Registra un nuevo entrenamiento con sus series. """
    data = request.get_json()
    
    # Convertir la fecha a string en formato YYYY-MM-DD para SQL Server
    fecha = data.get("fecha")
    
    if fecha:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")  # Convertimos a objeto datetime
        except ValueError:
            return jsonify({"error": "Formato de fecha incorrecto. Use YYYY-MM-DD"}), 400
    else:
        fecha_obj = datetime.now()  # Fecha por defecto
    
    # Obtener el día de la semana
   
    dia_semana = fecha_obj.strftime("%A")  # 'Monday', 'Tuesday', etc. 
    # ejercicio_id = data.get("ejercicio_id")
    series = data.get("series")  # Lista de series
    if not series:
        return jsonify({"error": "Debes proporcionar al menos una serie"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insertar el entrenamiento con el día de la semana
        cursor.execute("INSERT INTO Entrenamientos (Usuario_id, Dia_semana) VALUES (?, ?)", (current_user, dia_semana))
        conn.commit()
        entrenamiento_id = cursor.execute("SELECT SCOPE_IDENTITY()").fetchone()[0]  # Obtener ID del último insertado

        # Insertar cada serie
        for serie in series:
            ejercicio_id = serie.get("ejercicio_id")
            peso = serie.get("peso")
            repeticiones = serie.get("repeticiones")

            cursor.execute("""
                INSERT INTO Series (Entrenamiento_id, Peso, Repeticiones, Fecha, Id_ejercicio)
                VALUES (?, ?, ?, ?, ?)
            """, (entrenamiento_id, peso, repeticiones, fecha_obj.strftime("%Y-%m-%d"), ejercicio_id))
        
        conn.commit()
        return jsonify({"mensaje": "Entrenamiento registrado correctamente"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
