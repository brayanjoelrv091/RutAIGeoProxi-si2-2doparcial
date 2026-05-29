
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"
engine = create_engine(DATABASE_URL)

# Hash de bcrypt para "Password123" extraído del servidor funcional
BCRYPT_HASH = "$2b$12$pSSfuqwXgm4eTPd9jOK0F.JHHslgeVshbIPQcesWahCiY1f0pXTR6"

emails = [
    "xdreicarlos@gmail.com",
    "fitgo61@gmail.com",
    "ramosvargabrayan@gmail.com"
]

def final_fix():
    with engine.connect() as conn:
        print("--- Aplicando corrección final de BCRYPT ---")
        for email in emails:
            conn.execute(
                text("""
                    UPDATE usuarios 
                    SET esta_activo = True, 
                        intentos_fallidos = 0, 
                        bloqueado_hasta = NULL,
                        hashed_password = :password
                    WHERE email = :email
                """),
                {"email": email, "password": BCRYPT_HASH}
            )
            print(f"User {email}: FIXED with bcrypt hash")
        
        conn.commit()
        print("\n✅ Todos los usuarios demo han sido sincronizados con BCRYPT y desbloqueados.")

if __name__ == "__main__":
    final_fix()
