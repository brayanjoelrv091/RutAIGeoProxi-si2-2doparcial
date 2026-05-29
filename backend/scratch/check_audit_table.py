
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"
engine = create_engine(DATABASE_URL)

def check_table():
    with engine.connect() as conn:
        print("Verificando tabla 'bitacora'...")
        try:
            res = conn.execute(text("SELECT count(*) FROM bitacora")).fetchone()
            print(f"Registros en bitacora: {res[0]}")
        except Exception as e:
            print(f"Error al acceder a bitacora: {e}")

if __name__ == "__main__":
    check_table()
