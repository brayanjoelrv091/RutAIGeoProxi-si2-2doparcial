
import requests

BASE_URL = "https://rutai-backend.onrender.com"
EMAIL = "test_ai_agent@example.com"
PASSWORD = "Password123"

def test_register_login():
    print("Registrando nuevo usuario...")
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "nombre": "AI Test Agent",
        "email": EMAIL,
        "password": PASSWORD,
        "rol": "cliente"
    })
    print(f"Registro Status: {r.status_code}")
    if r.status_code != 201:
        print(f"Error registro: {r.text}")
        if "ya está registrado" not in r.text:
            return
    
    print("Probando login con el nuevo usuario...")
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "email": EMAIL,
        "password": PASSWORD
    })
    print(f"Login Status: {r.status_code}")
    if r.status_code == 200:
        print("✅ Login EXITOSO para el nuevo usuario")
    else:
        print(f"❌ Login FALLIDO para el nuevo usuario: {r.text}")

if __name__ == "__main__":
    test_register_login()
