import requests

BASE_URL = "https://rutai-backend.onrender.com"
EMAIL = "xdreicarlos@gmail.com"
PASSWORD = "Password123"

def test_login():
    print(f"Probando login para {EMAIL}...")
    url = f"{BASE_URL}/auth/login"
    try:
        resp = requests.post(url, json={"email": EMAIL, "password": PASSWORD})
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("✅ Login EXITOSO")
            print(f"Token: {resp.json().get('access_token')[:20]}...")
        else:
            print("❌ Login FALLIDO")
            print(f"Respuesta: {resp.json()}")
    except Exception as e:
        print(f"🔥 Error: {e}")

if __name__ == "__main__":
    test_login()
