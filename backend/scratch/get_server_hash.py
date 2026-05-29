
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"
engine = create_engine(DATABASE_URL)

def get_server_hash():
    email = "test_ai_agent@example.com"
    with engine.connect() as conn:
        res = conn.execute(text("SELECT hashed_password FROM usuarios WHERE email = :email"), {"email": email}).fetchone()
        if res:
            print(f"SERVER_HASH: {res[0]}")
        else:
            print("Not found")

if __name__ == "__main__":
    get_server_hash()
