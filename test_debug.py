import requests
import re

s = requests.Session()

# Login
r = s.get('http://127.0.0.1:5000/auth/login')
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
token = m.group(1) if m else 'NOTFOUND'
print(f'Login CSRF: {token[:30]}...')
r2 = s.post('http://127.0.0.1:5000/auth/login',
            data={'csrf_token': token, 'username': 'admin', 'password': 'admin123'},
            allow_redirects=False)
print(f'Login: {r2.status_code} Location: {r2.headers.get("Location")}')

# Follow redirect
r3 = s.get('http://127.0.0.1:5000/')
print(f'Dashboard: {r3.status_code}, Admin in body: {"Admin" in r3.text}')

# Create client
r4 = s.get('http://127.0.0.1:5000/clientes/nuevo')
m2 = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r4.text)
token2 = m2.group(1) if m2 else 'NOTFOUND'
print(f'Client form CSRF: {token2[:30]}...')

r5 = s.post('http://127.0.0.1:5000/clientes/nuevo', data={
    'csrf_token': token2,
    'nombre_completo': 'Maria Rodriguez',
    'tipo_documento': 'DNI',
    'numero_documento': '87654321',
    'celular': '70011234',
    'direccion': 'Av. Principal #456',
    'distrito': 'Equipetrol',
    'provincia': 'Santa Cruz',
    'departamento': 'Santa Cruz',
    'latitud': '-17.7833000',
    'longitud': '-63.1822000',
    'foto': 'https://i.pravatar.cc/150?u=maria'
}, allow_redirects=False)
print(f'Client POST: {r5.status_code} Location: {r5.headers.get("Location")}')
if r5.status_code == 200:
    # Check for error messages
    errors = re.findall(r'invalid-feedback[^>]*>([^<]+)', r5.text)
    if errors:
        print(f'  Validation errors: {errors[:5]}')
    # Check if form has CSRF again (means re-render)
    m3 = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r5.text)
    if m3:
        print(f'  Form re-rendered (validation failed)')
    # Check for flash messages
    flashes = re.findall(r'alert[^>]*>[^<]*<[^>]*>([^<]+)', r5.text)
    if flashes:
        print(f'  Flash messages: {flashes[:3]}')
else:
    # Client created, follow redirect
    r6 = s.get('http://127.0.0.1:5000' + r5.headers.get('Location', ''))
    print(f'  Client page: {r6.status_code}')
    print(f'  map-detail: {"map-detail" in r6.text}')
    print(f'  foto: {"pravatar" in r6.text}')
