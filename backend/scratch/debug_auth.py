
import os
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

DATABASE_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

engine = create_engine(DATABASE_URL)

def debug_auth():
    email = "xdreicarlos@gmail.com"
    password = "Password123"
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT hashed_password FROM usuarios WHERE email = :email"), {"email": email}).fetchone()
        if not result:
            print(f"User {email} not found")
            return
        
        hashed_in_db = result[0]
        print(f"Hash in DB: {hashed_in_db}")
        
        is_correct = pwd_context.verify(password, hashed_in_db)
        print(f"Verification locally: {is_correct}")
        
        # Generar uno nuevo para comparar
        new_hash = pwd_context.hash(password)
        print(f"New hash generated: {new_hash}")
        
        is_correct_new = pwd_context.verify(password, new_hash)
        print(f"Verification of new hash: {is_correct_new}")

if __name__ == "__main__":
    debug_auth()
