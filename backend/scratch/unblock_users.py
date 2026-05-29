
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Configuración
DATABASE_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

emails = [
    "xdreicarlos@gmail.com",
    "fitgo61@gmail.com",
    "ramosvargabrayan@gmail.com"
]

NEW_PASSWORD = "Password123"
hashed = pwd_context.hash(NEW_PASSWORD)

def unblock_users():
    db = SessionLocal()
    try:
        print("--- Desbloqueando Usuarios Demo ---")
        for email in emails:
            # Primero verificamos si existe
            user = db.execute(text("SELECT id FROM usuarios WHERE email = :email"), {"email": email}).fetchone()
            if user:
                db.execute(
                    text("""
                        UPDATE usuarios 
                        SET esta_activo = True, 
                            intentos_fallidos = 0, 
                            bloqueado_hasta = NULL,
                            hashed_password = :password
                        WHERE email = :email
                    """),
                    {"email": email, "password": hashed}
                )
                print(f"User {email}: UNBLOCKED and PASSWORD RESET to '{NEW_PASSWORD}'")
            else:
                print(f"User {email}: NOT FOUND, skipping...")
        
        db.commit()
        print("\n✅ Todos los cambios guardados en la base de datos.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la operación: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    unblock_users()
