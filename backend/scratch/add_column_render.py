from sqlalchemy import create_engine, text

RENDER_DB_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db?sslmode=require"

engine = create_engine(RENDER_DB_URL)

with engine.begin() as conn:
    print("Añadiendo columna 'estado_registro' a 'talleres'...")
    try:
        conn.execute(text("ALTER TABLE talleres ADD COLUMN estado_registro VARCHAR(30) DEFAULT 'pendiente_tecnicos' NOT NULL;"))
        print("Columna añadida con éxito.")
    except Exception as e:
        print("Error al añadir la columna (quizás ya existe):", e)
