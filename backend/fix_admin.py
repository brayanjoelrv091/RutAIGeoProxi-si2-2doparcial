import os
import sys

# Agregar la ruta base del proyecto para poder importar desde app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.shared.database import SessionLocal
from app.modules.p1_usuarios.models import Usuario
from app.shared.security import get_password_hash

def fix_admin():
    db = SessionLocal()
    try:
        email = "admin@rutaigeoproxi.com"
        password = "Admin123*"
        
        user = db.query(Usuario).filter(Usuario.email == email).first()
        
        if user:
            print(f"Usuario {email} ya existe. Actualizando contraseña y rol a SuperAdmin...")
            user.hashed_password = get_password_hash(password)
            user.rol = "admin"
            user.tenant_id = None # SuperAdmin no tiene tenant
            user.esta_activo = True
            db.commit()
            print("SuperAdmin actualizado correctamente.")
        else:
            print(f"Creando nuevo usuario SuperAdmin {email}...")
            nuevo_admin = Usuario(
                nombre="SuperAdmin Principal",
                email=email,
                hashed_password=get_password_hash(password),
                rol="admin",
                esta_activo=True,
                tenant_id=None
            )
            db.add(nuevo_admin)
            db.commit()
            print("SuperAdmin creado correctamente.")
            
        print(f"\nCredenciales para iniciar sesión:")
        print(f"Email: {email}")
        print(f"Contraseña: {password}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_admin()
