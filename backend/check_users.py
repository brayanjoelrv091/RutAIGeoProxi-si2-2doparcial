from app.shared.database import SessionLocal
from app.modules.p1_usuarios.models import Usuario

db = SessionLocal()
users = db.query(Usuario).all()
print(f"{'ID':<5} | {'Email':<30} | {'Rol':<10} | {'Activo':<8}")
print("-" * 60)
for u in users:
    print(f"{u.id:<5} | {u.email:<30} | {u.rol:<10} | {u.esta_activo:<8}")
db.close()
