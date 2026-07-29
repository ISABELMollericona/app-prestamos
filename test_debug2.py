import requests
import re

s = requests.Session()

# Login
r = s.get('http://127.0.0.1:5000/auth/login')
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
r2 = s.post('http://127.0.0.1:5000/auth/login',
            data={'csrf_token': m.group(1), 'username': 'admin', 'password': 'admin123'},
            allow_redirects=True)
print(f'Login OK: {r2.url}')

# Get the form and submit it properly
r = s.get('http://127.0.0.1:5000/clientes/nuevo')
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
token = m.group(1)

# Check for genero and estado_civil select names
selects = re.findall(r'<select[^>]*name="([^"]+)"', r.text)
print(f'Select fields: {selects}')

# Build proper data dict with all Select fields
data = {
    'csrf_token': token,
    'nombre_completo': 'Maria Rodriguez',
    'tipo_documento': 'DNI',
    'numero_documento': '87654321',
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
    'foto': 'https://i.pravatar.cc/150?u=maria',
    'observaciones': ''
}

r3 = s.post('http://127.0.0.1:5000/clientes/nuevo', data=data, allow_redirects=False)
print(f'POST status: {r3.status_code} Location: {r3.headers.get("Location")}')

if r3.status_code == 200:
    # Print part of the response to find the error
    error_sections = re.findall(r'(?:is-invalid|invalid-feedback|alert[^>]*)', r3.text[:10000])
    print(f'Error indicators: {error_sections[:10]}')
    
    # Check for duplicate
    if 'Ya existe' in r3.text or 'ya existe' in r3.text:
        print('ERROR: Client duplicate')
    
    # Print the first 2000 chars around the form
    form_start = r3.text.find('<form')
    if form_start >= 0:
        snippet = r3.text[form_start:form_start+3000]
        # Find any error messages
        for err in re.finditer(r'(?:is-invalid[^>]*>|invalid-feedback[^>]*>)([^<]+)', snippet):
            print(f'Error: {err.group(1)[:100]}')
else:
    print(f'Redirected: {r3.headers.get("Location")}')
    r4 = s.get('http://127.0.0.1:5000' + r3.headers.get('Location', ''))
    print(f'Final page: {r4.status_code}')
    print(f'Has map-detail: {"map-detail" in r4.text}')
