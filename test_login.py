import requests
import re

s = requests.Session()
r = s.get('http://127.0.0.1:5000/auth/login')
match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
if match:
    token = match.group(1)
    r2 = s.post('http://127.0.0.1:5000/auth/login', 
                data={'csrf_token': token, 'username': 'admin', 'password': 'admin123'}, 
                allow_redirects=False)
    print(f'Login status: {r2.status_code} Location: {r2.headers.get("Location")}')
    if r2.status_code in (301, 302):
        loc = r2.headers.get('Location', '')
        if loc.startswith('/'):
            r3 = s.get(f'http://127.0.0.1:5000{loc}')
        else:
            r3 = s.get('http://127.0.0.1:5000/')
        print(f'Dashboard status: {r3.status_code}')
        print(f'Dashboard text includes Admin: {"Admin" in r3.text}')
        
        # Now let's create a client via the API
        r4 = s.get('http://127.0.0.1:5000/clientes/nuevo')
        match2 = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r4.text)
        if match2:
            token2 = match2.group(1)
            r5 = s.post('http://127.0.0.1:5000/clientes/nuevo',
                       data={
                           'csrf_token': token2,
                           'nombre_completo': 'Test User',
                           'tipo_documento': 'DNI',
                           'numero_documento': '99999999',
                           'celular': '70000001',
                           'direccion': 'Test Address',
                           'distrito': 'Test',
                           'provincia': 'Test',
                           'departamento': 'Test',
                           'latitud': '-17.7800000',
                           'longitud': '-63.1800000',
                           'foto': 'https://example.com/foto.jpg'
                       },
                       allow_redirects=False)
            print(f'Client create status: {r5.status_code}')
            loc2 = r5.headers.get('Location', '')
            if loc2.startswith('/'):
                r6 = s.get(f'http://127.0.0.1:5000{loc2}')
                print(f'Client page: {r6.status_code}')
                print(f'Has lat/lng: {"latitud" in r6.text} {"-17.78" in r6.text}')
                print(f'Has foto: {"example.com/foto" in r6.text}')
                print(f'Has map: {"map-detail" in r6.text}')
        else:
            print('No CSRF on client page')
else:
    print('No CSRF token found')
