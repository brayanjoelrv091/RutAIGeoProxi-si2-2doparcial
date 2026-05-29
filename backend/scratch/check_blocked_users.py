
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuración manual para rapidez
DATABASE_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

emails = [
    "xdreicarlos@gmail.com",
    "fitgo61@gmail.com",
    "ramosvargabrayan@gmail.com"
]

def check_users():
    db = SessionLocal()
    try:
        print("--- Estado de Usuarios Demo ---")
        for email in emails:
            result = db.execute(text("SELECT id, email, esta_activo, intentos_fallidos, bloqueado_hasta, rol FROM usuarios WHERE email = :email"), {"email": email}).fetchone()
            if result:
                print(f"User: {result.email}")
                print(f"  Activo: {result.esta_activo}")
                print(f"  Intentos fallidos: {result.intentos_fallidos}")
                print(f"  Bloqueado hasta: {result.bloqueado_hasta}")
                print(f"  Rol: {result.rol}")
            else:
                print(f"User {email} NOT FOUND")
            print("-" * 30)
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
