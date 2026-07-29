import requests, re, uuid

s = requests.Session()
uniq = uuid.uuid4().hex[:6]

# Login
r = s.get('http://127.0.0.1:5000/auth/login')
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
token = m.group(1)
print(f'Session cookies before login: {dict(s.cookies)}')
r2 = s.post('http://127.0.0.1:5000/auth/login',
            data={'csrf_token': token, 'username': 'admin', 'password': 'admin123'},
            allow_redirects=True, timeout=10)
print(f'Login: {r2.status_code} {r2.url}')
print(f'Session cookies after login: {dict(s.cookies)}')

# GET create client form
r = s.get('http://127.0.0.1:5000/clientes/nuevo')
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
token2 = m.group(1)
print(f'\nClient form CSRF: {token2[:30]}...')
print(f'Session cookies before POST: {dict(s.cookies)}')

# Submit without CSRF to test
r3 = s.post('http://127.0.0.1:5000/clientes/nuevo', data={
    'csrf_token': token2,
    'nombre_completo': f'Maria Test {uniq}',
    'tipo_documento': 'DNI',
    'numero_documento': f'8765{uniq}',
    'fecha_nacimiento': '',
    'genero': '',
    'estado_civil': '',
    'telefono': '',
    'celular': '70011234',
    'email': '',
    'direccion': 'Av. Principal #456',
    'distrito': 'Equipetrol',
    'provincia': 'Santa Cruz',
    'departamento': 'Santa Cruz',
    'ocupacion': '',
    'ingresos_mensuales': '',
    'referencia_nombre': '',
    'referencia_telefono': '',
    'latitud': '-17.7833',
    'longitud': '-63.1822',
    'foto': f'https://i.pravatar.cc/150?u=maria{uniq}',
    'observaciones': ''
}, allow_redirects=False, timeout=10)
print(f'\nPOST result: status={r3.status_code} location={r3.headers.get("Location")}')
print(f'Response length: {len(r3.text)}')

# Check if it succeeded by looking at the client list
if r3.status_code == 302:
    r4 = s.get('http://127.0.0.1:5000' + r3.headers.get('Location', ''))
    print(f'Client list: {r4.status_code} contains today: {uniq in r4.text}')
else:
    # Check for CSRF error in the response
    if 'CSRF' in r3.text or 'csrf' in r3.text:
        print('CSRF ERROR IN RESPONSE')
    # Look for any error
    if 'error' in r3.text and 'flash' not in r3.text:
        for err in re.finditer(r'(?:class="[^"]*error[^"]*"|alert[^"]*error[^"]*"|invalid-feedback[^>]*>)([^<]+)', r3.text):
            print(f'Error found: {err.group(1)}')
    print('First 2000 chars:')
    print(r3.text[:2000])
