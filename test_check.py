import requests, re

s = requests.Session()
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', s.get('http://127.0.0.1:5000/auth/login').text)
s.post('http://127.0.0.1:5000/auth/login', data={'csrf_token': m.group(1), 'username': 'admin', 'password': 'admin123'}, allow_redirects=True)

r = s.get('http://127.0.0.1:5000/clientes/')
print('Clients:', r.status_code, 'Maria' in r.text)
r = s.get('http://127.0.0.1:5000/prestamos/')
print('Loans:', r.status_code, 'PRE-' in r.text)

# Check loan 1
r = s.get('http://127.0.0.1:5000/prestamos/1')
print('Loan 1:', r.status_code, 'desembolsado' in r.text if r.status_code==200 else 'N/A')
