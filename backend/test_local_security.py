from app.shared.security import get_password_hash, verify_password

pw = "Password123"
h = get_password_hash(pw)
print(f"Hash: {h}")
v = verify_password(pw, h)
print(f"Verify: {v}")
