
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"
engine = create_engine(DATABASE_URL)

def deep_check():
    email = "xdreicarlos@gmail.com"
    with engine.connect() as conn:
        print(f"Buscando email exacto: '{email}'")
        res = conn.execute(text("SELECT id, email, hashed_password, rol, esta_activo FROM usuarios WHERE email = :email"), {"email": email}).fetchall()
        print(f"Encontrados: {len(res)}")
        for r in res:
            print(f"ID: {r.id}, Email: '{r.email}', Rol: {r.rol}, Activo: {r.esta_activo}")
            print(f"Hash: {r.hashed_password}")
        
        print("\nBuscando emails similares (LIKE):")
        res2 = conn.execute(text("SELECT id, email FROM usuarios WHERE email ILIKE :email"), {"email": f"%{email}%"}).fetchall()
        for r in res2:
            print(f"ID: {r.id}, Email: '{r.email}'")

if __name__ == "__main__":
    deep_check()
