from flask import Flask, request, redirect, url_for, render_template, flash, jsonify
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.workout_routes import workout_bp
from routes.rutina_routes import rutinas_bp  # Importa el Blueprint de las rutinas
from routes.entrenamientos import entrenamientos_bp  # Importamos el blueprint de entrenamientos
from config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from models.workout_model import Workout
from flask import session
import cloudinary
import cloudinary.uploader
import cloudinary.api
from routes.rutina_routes import buscar_imagen_en_cloudinary


import pyodbc

app = Flask(__name__)
app.secret_key = "supersecreto"

# Crear la conexión a la base de datos
conn = get_db_connection()
cursor = conn.cursor()

# Configuración de Cloudinary
cloudinary.config(
    cloud_name='dntqaxsko',
    api_key='323523837582744',
    api_secret='ES85Ti4VrGNKOJ07wiBLBRFE8u8'
)

# Ruta de la raíz
@app.route('/')
def index():
    return render_template("index.html")

# Ruta para la página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM Usuarios WHERE Email = ?", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("El correo ya está registrado. Usa otro o inicia sesión.", "error")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO Usuarios (Nombre, Email, Password_hash) VALUES (?, ?, ?)", (nombre, email, hashed_password))
        conn.commit()

        flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for('login'))

    return render_template("register.html")



# Ruta para la página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT Id, Password_hash FROM Usuarios WHERE Email = ?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[1], password):  # user[1] es la contraseña hasheada
            session['user_id'] = user[0]
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Correo o contraseña incorrectos.", "error")
            return redirect(url_for('login'))  # Recarga login.html con el mensaje flash

    return render_template("login.html")
# # # Ruta para la página de inicio (después de login)
# # @app.route('/dashboard')
# # def dashboard():
# #     # Verificar que el usuario esté autenticado
# #     user_id = session.get("user_id")
# #     if not user_id:
# #         flash("Debes iniciar sesión para ver el dashboard.", "error")
# #         return redirect(url_for("login"))
    
# #     conn = get_db_connection()
# #     cursor = conn.cursor()
    
# #     # Consulta las rutinas del usuario autenticado
# #     cursor.execute("SELECT id, Nombre_rutina FROM Rutinas WHERE Usuario_id = ?", (user_id,))
# #     rows = cursor.fetchall()
    
# #     rutinas = []
# #     for row in rows:
# #         rutina = {
# #             "id": row[0],
# #             "nombre_rutina": row[1]
# #         }
# #         rutinas.append(rutina)
    
# #     cursor.close()
# #     conn.close()
    
# #     return render_template('dashboard.html', rutinas=rutinas)

@rutinas_bp.route("/crear_rutina", methods=["GET"])
def mostrar_formulario_crear_rutina():
    # Conectar a la base de datos para obtener, por ejemplo, la lista de ejercicios
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, Nombre_ejercicio FROM Ejercicios")
    ejercicios = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template("crear_rutina.html", ejercicios=ejercicios)

@app.route('/get_subgrupos', methods=['GET'])
def get_subgrupos():
    grupo = request.args.get('grupo')
    # Conectar a la base de datos y hacer la consulta
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Subgrupo_muscular FROM Ejercicios WHERE Grupo_muscular = ?", (grupo,))
    subgrupos = cursor.fetchall()
    conn.close()
    
    # Devolver los subgrupos como respuesta
    return jsonify({'subgrupos': [subgrupo[0] for subgrupo in subgrupos]})


# # @app.route('/get_ejercicios', methods=['GET'])
# # def get_ejercicios():
# #     grupo = request.args.get('grupo')
# #     subgrupo = request.args.get('subgrupo')

# #     # Establecer conexión con la base de datos
# #     conn = get_db_connection()
# #     cursor = conn.cursor()

# #     # Consulta SQL para obtener los ejercicios del grupo y subgrupo seleccionados
# #     query = """
# #         SELECT Nombre_ejercicio, imagen_url, Subgrupo_muscular
# #         FROM Ejercicios
# #         WHERE Grupo_muscular = ? AND Subgrupo_muscular = ?
# #     """
# #     cursor.execute(query, (grupo, subgrupo))

# #     # Recuperar los resultados
# #     rows = cursor.fetchall()
# #     # Convertir los resultados a un diccionario y construir la URL de la imagen
# #     ejercicios = []
# #     for row in rows:
# #         # Generar la URL de la imagen en Google Drive
# #         prefijo_imagen = row[1]
# #         imagen_url = buscar_imagen_en_cloudinary(prefijo_imagen) # Genera la URL pública segura

# #         # imagen_url = f"https://drive.google.com/uc?export=view&id={row[1]}"

# #         ejercicio = {
# #             'Nombre_ejercicio': row[0],
# #             'imagen_url': imagen_url,  # URL generada aquí
# #             'Subgrupo_muscular': row[2]
# #         }
# #         ejercicios.append(ejercicio)

# #     # Cerrar la conexión a la base de datos
# #     cursor.close()
# #     conn.close()

# #     # Enviar los datos como respuesta JSON
# #     return jsonify({"ejercicios": ejercicios})

@app.route('/get_ejercicios', methods=['GET'])
def get_ejercicios():
    grupo = request.args.get('grupo')
    subgrupo = request.args.get('subgrupo')

    # Establecer conexión con la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta SQL para obtener los ejercicios del grupo y subgrupo seleccionados
    query = """
        SELECT id, Nombre_ejercicio, imagen_url, Subgrupo_muscular
        FROM Ejercicios
        WHERE Grupo_muscular = ? AND Subgrupo_muscular = ?
    """
    cursor.execute(query, (grupo, subgrupo))

    # Recuperar los resultados
    rows = cursor.fetchall()

    # Convertir los resultados a un diccionario y construir la URL de la imagen
    ejercicios = []
    for row in rows:
        # Aquí suponemos que row[2] contiene el identificador de la imagen en Cloudinary o Drive
        # Por ejemplo, si usas Drive:
        prefijo_imagen = row[2]
        imagen_url = buscar_imagen_en_cloudinary(prefijo_imagen) 
        # Si usas Cloudinary y ya tienes una función para buscar la imagen, puedes usarla en lugar de la URL de Drive.
        
        ejercicio = {
            'id': row[0],
            'Nombre_ejercicio': row[1],
            'imagen_url': imagen_url,
            'Subgrupo_muscular': row[3]
        }
        ejercicios.append(ejercicio)

    # Cerrar la conexión a la base de datos
    cursor.close()
    conn.close()

    # Enviar los datos como respuesta JSON
    return jsonify({"ejercicios": ejercicios})


# # @app.route('/dashboard')
# # def dashboard():
# #     # Establecer conexión con la base de datos
# #     conn = get_db_connection()
# #     cursor = conn.cursor()

# #     # Obtener el ID del usuario desde la sesión (o el método de autenticación que uses)
# #     user_id = session.get('user_id')  # Cambia esto según cómo manejes la autenticación

# #     # Obtener solo las rutinas del usuario
# #     query = """
# #         SELECT id, nombre_rutina
# #         FROM Rutinas
# #         WHERE Usuario_id = ?  # Filtrar por el ID del usuario
# #     """
# #     cursor.execute(query, (user_id,))
# #     rutinas = cursor.fetchall()

# #     # Imprimir las rutinas para depuración
# #     print(rutinas)

# #     # Cerrar la conexión a la base de datos
# #     cursor.close()
# #     conn.close()

# #     # Pasar las rutinas a la plantilla
# #     return render_template('dashboard.html', rutinas=rutinas)

# Asumiendo que ya tienes una conexión a la base de datos
def obtener_rutinas():
    conn = pyodbc.connect('DRIVER={SQL Server};'
                          'SERVER=localhost;'
                          'DATABASE=GymDB;'
                          'UID=usuario;'
                          'PWD=contraseña')

    cursor = conn.cursor()
    cursor.execute("""
        SELECT rutina_id, nombre_rutina FROM rutinas
    """)
    return cursor.fetchall()


@app.route('/dashboard')
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        flash("Debes iniciar sesión para ver el dashboard.", "error")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener rutinas únicas con su ID
    cursor.execute("SELECT id, Nombre_rutina FROM Rutinas WHERE Usuario_id = ?", (user_id,))
    rows = cursor.fetchall()

    nombres_unicos = set()
    rutinas = []

    for row in rows:
        rutina_id, nombre_rutina = row
        if nombre_rutina not in nombres_unicos:
            nombres_unicos.add(nombre_rutina)
            rutinas.append({"id": rutina_id, "nombre_rutina": nombre_rutina})

    cursor.close()
    conn.close()

    return render_template('dashboard.html', rutinas=rutinas)



@app.route('/detalle_rutina/<int:id>')
def detalle_rutina(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener los detalles de la rutina
    query_rutina = "SELECT id, Nombre_rutina, Usuario_id FROM Rutinas WHERE id = ?"
    cursor.execute(query_rutina, (id,))
    rutina = cursor.fetchone()

    if not rutina:
        flash("Rutina no encontrada.", "error")
        return redirect(url_for("dashboard"))

    rutina_id = rutina[0]
    nombre_rutina = rutina[1]
    usuario_id = rutina[2]

    # Obtener los ejercicios agrupados por día
    query_ejercicios = """
        SELECT r.Dia, e.Nombre_ejercicio, e.Subgrupo_muscular
        FROM Rutinas r
        INNER JOIN Ejercicios e ON r.Id_ejercicio = e.id
        WHERE r.Nombre_rutina = ? AND r.Usuario_id = ?
    """
    cursor.execute(query_ejercicios, (nombre_rutina, usuario_id))
    ejercicios = cursor.fetchall()

    cursor.close()
    conn.close()

    if not ejercicios:
        flash("No hay ejercicios en esta rutina.", "warning")

    # Definir el orden correcto de los días de la semana
    orden_dias = {
        "Lunes": 1, "Martes": 2, "Miércoles": 3, "Jueves": 4,
        "Viernes": 5, "Sábado": 6, "Domingo": 7
    }

    # Organizar los ejercicios por día en un diccionario
    ejercicios_por_dia = {}
    for dia, ejercicio, subgrupo in ejercicios:
        if dia not in ejercicios_por_dia:
            ejercicios_por_dia[dia] = []
        ejercicios_por_dia[dia].append({"Nombre_ejercicio": ejercicio, "Subgrupo_muscular": subgrupo})

    # Ordenar el diccionario de ejercicios según el orden de los días de la semana
    ejercicios_por_dia_ordenado = dict(sorted(ejercicios_por_dia.items(), key=lambda x: orden_dias.get(x[0], 999)))

    return render_template(
        'detalle_rutina.html',
        rutina={"id": rutina_id, "Nombre_rutina": nombre_rutina},
        ejercicios_por_dia=ejercicios_por_dia_ordenado
    )




# Registrar las rutas
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(workout_bp)
app.register_blueprint(entrenamientos_bp, url_prefix='/api')
app.register_blueprint(rutinas_bp, url_prefix='/api')

if __name__ == "__main__":
    app.run(debug=True)
