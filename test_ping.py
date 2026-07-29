import requests
s = requests.Session()
r = s.get('http://127.0.0.1:5000/auth/login', timeout=10)
print('Status:', r.status_code, 'CSRF:', 'csrf_token' in r.text)
