from app.shared.database import SessionLocal
from app.shared.security import verify_password
from app.modules.p1_usuarios.models import Usuario

db = SessionLocal()
email = "ramosvargabrayan@gmail.com"
password = "Password123"

user = db.query(Usuario).filter(Usuario.email == email).first()
if user:
    is_valid = verify_password(password, user.hashed_password)
    print(f"Usuario: {email}")
    print(f"Password v\u00e1lido: {is_valid}")
else:
    print(f"Usuario {email} no encontrado.")
db.close()
