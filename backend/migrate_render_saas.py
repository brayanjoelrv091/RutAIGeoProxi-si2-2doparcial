import os
from sqlalchemy import create_engine, text

RENDER_DB_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db?sslmode=require"

def migrate():
    print("Conectando a la base de datos de Render...")
    engine = create_engine(RENDER_DB_URL)

    queries = [
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS fecha_fin_plan TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS estado_pago VARCHAR(50) NOT NULL DEFAULT 'gratis';",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS metodo_pago VARCHAR(50) NOT NULL DEFAULT 'ninguno';",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS monto_pago INTEGER NOT NULL DEFAULT 0;"
    ]

    with engine.connect() as conn:
        for q in queries:
            print(f"Ejecutando: {q}")
            try:
                conn.execute(text(q))
                conn.commit()
                print("OK.")
            except Exception as e:
                print(f"Error: {e}")

    print("Migración de Render completada con éxito.")

if __name__ == '__main__':
    migrate()
