import pyodbc

# Configuración de la conexión a SQL Server
DB_SERVER = "DESKTOP-RS20AM8\\SQLEXPRESS01"
DB_NAME = "GymApp"

def get_db_connection():
    conn = pyodbc.connect(
        f"DRIVER={{SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};Trusted_Connection=yes;"
    )
    return conn
