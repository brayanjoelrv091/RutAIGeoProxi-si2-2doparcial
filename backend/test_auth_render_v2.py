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
        try:
            print(f"Respuesta JSON: {resp.json()}")
        except:
            print(f"Respuesta TEXTO: {resp.text[:500]}")
            
        if resp.status_code == 200:
            print("Login EXITOSO")
        else:
            print("Login FALLIDO")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
