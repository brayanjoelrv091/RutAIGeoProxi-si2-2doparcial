import urllib.request, json, sys, time

email = f"test_{int(time.time())}@test.com"
pwd = "Password123!"

# Register
req_reg = urllib.request.Request(
    'http://127.0.0.1:8001/auth/register', 
    data=json.dumps({'nombre':'Test','email': email, 'password': pwd, 'rol':'cliente'}).encode('utf-8'), 
    headers={'Content-Type': 'application/json'}, 
    method='POST'
)
try:
    urllib.request.urlopen(req_reg)
    print("Registered successfully")
except urllib.error.HTTPError as e:
    print(f'REG HTTP {e.code}: {e.read().decode()}')

# Login
req_login = urllib.request.Request(
    'http://127.0.0.1:8001/auth/login', 
    data=json.dumps({'email': email, 'password': pwd}).encode('utf-8'), 
    headers={'Content-Type': 'application/json'}, 
    method='POST'
)
try:
    resp = urllib.request.urlopen(req_login)
    print("LOGIN SUCCESS", resp.read().decode())
except urllib.error.HTTPError as e:
    print(f'LOGIN HTTP {e.code}: {e.read().decode()}')
except Exception as e:
    print(f"Error: {e}")
