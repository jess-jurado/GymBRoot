from config import get_db_connection

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    print("✅ Conexión exitosa:", result)
except Exception as e:
    print("❌ Error de conexión:", e)
finally:
    cursor.close()
    conn.close()
