import psycopg2

DB_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"

try:
    print("Conectando a Render para limpieza total...")
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    print("Borrando esquema público (CASCADE)...")
    cur.execute("DROP SCHEMA public CASCADE;")
    cur.execute("CREATE SCHEMA public;")
    cur.execute("GRANT ALL ON SCHEMA public TO public;")
    cur.execute("GRANT ALL ON SCHEMA public TO rutai_db_user;")
    
    print("¡Base de datos en Render totalmente limpia!")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error limpiando DB: {e}")
