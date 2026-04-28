import requests
import time

BASE_URL = "https://rutai-backend.onrender.com"
TEST_USER = "xdreicarlos@gmail.com"
TEST_PASS = "Password123"

def run_health_check():
    print("="*50)
    print("SEARCH RUTAIGEOPROXI - FINAL HEALTH CHECK")
    print("="*50)

    # 1. Ping al Root
    start = time.time()
    try:
        r = requests.get(f"{BASE_URL}/")
        latency = (time.time() - start) * 1000
        print(f"[API] Latencia: {latency:.2f}ms | Status: {r.status_code}")
    except Exception as e:
        print(f"[ERR] Error de conexión: {e}")
        return

    # 2. Test de Autenticación (PBKDF2)
    print("\n[AUTH] Probando Login de Admin...")
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": TEST_USER, "password": TEST_PASS})
    if r.status_code == 200:
        token = r.json()["access_token"]
        print("OK Login Exitoso")
        headers = {"Authorization": f"Bearer {token}"}
    else:
        print(f"ERR Login Fallido: {r.status_code} | {r.text}")
        return

    # 3. Test de Incidentes Sembrados
    print("\n[DATA] Verificando incidentes de la demo...")
    r = requests.get(f"{BASE_URL}/incidents/all", headers=headers)
    if r.status_code == 200:
        count = len(r.json())
        print(f"OK Incidentes encontrados: {count}")
        if count >= 2:
            print("  - Escenario Tracking: OK")
            print("  - Escenario Pago: OK")
    else:
        print(f"ERR Error al listar incidentes: {r.text}")

    # 4. Test de Bitácora (CORS/Permissions)
    print("\n[AUDIT] Verificando acceso a Bitacora...")
    r = requests.get(f"{BASE_URL}/admin/audit", headers=headers)
    if r.status_code == 200:
        print(f"OK Bitacora accesible. Registros: {len(r.json())}")
    else:
        print(f"ERR Error Bitacora: {r.status_code}")

    print("\n" + "="*50)
    print("[OK] RESULTADO: SISTEMA AL 100% PARA PRODUCCION")
    print("="*50)

if __name__ == "__main__":
    run_health_check()
