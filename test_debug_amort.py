import requests, re

s = requests.Session()

def csrf(html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else ''

# Login
r = s.get('http://127.0.0.1:5000/auth/login')
r2 = s.post('http://127.0.0.1:5000/auth/login',
            data={'csrf_token': csrf(r.text), 'username': 'admin', 'password': 'admin123'},
            allow_redirects=True)

# Get the first loan that is desembolsado
r = s.get('http://127.0.0.1:5000/prestamos/')
# Find loan link
loans = re.findall(r'/prestamos/(\d+)">\s*PRE-\d+', r.text)
print(f'Found loans: {loans}')

for lid in loans:
    r = s.get(f'http://127.0.0.1:5000/prestamos/{lid}')
    if 'desembolsado' in r.text or 'activo' in r.text or 'reprogramado' in r.text:
        print(f'Loan {lid}: estado found - checking amortizable')
        print(f'  saldo: {"saldo" in r.text}')
        saldo_match = re.search(r'Saldo[^<]*<[^>]*>([^<]+)', r.text)
        print(f'  saldo text: {saldo_match.group(1).strip() if saldo_match else "N/A"}')
        
        # Try amortizar
        r_amort = s.get(f'http://127.0.0.1:5000/prestamos/{lid}/amortizar')
        print(f'\nAmortizar page: status={r_amort.status_code}')
        print(f'  Monto field: {"Monto a Amortizar" in r_amort.text}')
        print(f'  Cuotas table: {"Cuotas Pendientes" in r_amort.text}')
        
        r_post = s.post(f'http://127.0.0.1:5000/prestamos/{lid}/amortizar', data={
            'csrf_token': csrf(r_amort.text), 'monto_amortizar': '2000'
        }, allow_redirects=False)
        print(f'\nAmortizar POST: status={r_post.status_code} loc={r_post.headers.get("Location")}')
        if r_post.status_code == 302:
            r_final = s.get('http://127.0.0.1:5000' + r_post.headers.get('Location', f'/prestamos/{lid}'))
            print(f'  Final status: {r_final.status_code}')
            print(f'  URL: {r_final.url}')
            print(f'  Contains "reprogramado": {"reprogramado" in r_final.text}')
            print(f'  Contains "Tabla de Amortizacion": {"Tabla de Amortizacion" in r_final.text}')
            # Show first 1000 chars
            tab_idx = r_final.text.find('Tabla')
            if tab_idx >= 0:
                print(f'  Tabla found at char {tab_idx}')
            else:
                print(f'  First 1500 chars: {r_final.text[:1500]}')
        else:
            print(f'  Body: {r_post.text[:800]}')
        break
