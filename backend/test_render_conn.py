import os
import psycopg2
from sqlalchemy import create_engine

# URL de Render sacada del .env
DB_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"

try:
    print(f"Conectando a Render PostgreSQL...")
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("¡Conexión exitosa a Render!")
except Exception as e:
    print(f"Error de conexión: {e}")
