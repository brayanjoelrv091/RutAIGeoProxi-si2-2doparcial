
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"
engine = create_engine(DATABASE_URL)

def inspect_audit():
    with engine.connect() as conn:
        print("Estructura de tabla 'bitacora':")
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'bitacora'")).fetchall()
        for r in res:
            print(f"Columna: {r[0]}, Tipo: {r[1]}")
        
        print("\nDatos en 'bitacora':")
        res2 = conn.execute(text("SELECT * FROM bitacora LIMIT 5")).fetchall()
        for r in res2:
            print(r)

if __name__ == "__main__":
    inspect_audit()
