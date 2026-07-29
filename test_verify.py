import requests
import re

s = requests.Session()

# Login
r = s.get('http://127.0.0.1:5000/auth/login')
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
r2 = s.post('http://127.0.0.1:5000/auth/login',
            data={'csrf_token': m.group(1), 'username': 'admin', 'password': 'admin123'},
            allow_redirects=True)

# Check client detail
r = s.get('http://127.0.0.1:5000/clientes/1')
print(f'Client page status: {r.status_code}')
print(f'Has photo: {"pravatar" in r.text}')
print(f'Has latitud: {"-17.78" in r.text}')
print(f'Has map-detail div: {"map-detail" in r.text}')
print(f'Has map script: {"initDetailMap" in r.text}')

# Check loans
for pid in range(1, 4):
    r = s.get(f'http://127.0.0.1:5000/prestamos/{pid}')
    print(f'\nLoan {pid}:')
    print(f'  Status: {r.status_code}')
    print(f'  URL: {r.url}')
    if r.status_code == 200:
        # Get key info
        keys = ['Garantia:', 'Metodo:', 'Estado:', 'Tabla de Amortizacion', 'Amortizar', 'prendaria', 'hipotecaria', 'personal', 'Americano', 'Frances', 'Aleman']
        for k in keys:
            if k in r.text:
                line = ''
                idx = r.text.find(k)
                if k.endswith(':'):
                    line = r.text[idx:idx+80].replace('\n', ' ').strip()
                print(f'  Found: {k}')

print('\nDONE')
