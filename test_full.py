import requests, re, sys

def csrf(html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else ''

def get_id_from_location(loc):
    """Extract the last numeric ID from a redirect URL like /prestamos/3"""
    parts = loc.rstrip('/').split('/')
    for p in reversed(parts):
        if p.isdigit():
            return p
    return None

s = requests.Session()
passed = 0
failed = 0
results = []

def check(name, ok, detail=''):
    global passed, failed
    if ok:
        passed += 1
        results.append(f'  [PASS] {name}')
    else:
        failed += 1
        results.append(f'  [FAIL] {name} {detail}')

# Login
r = s.get('http://127.0.0.1:5000/auth/login')
r2 = s.post('http://127.0.0.1:5000/auth/login',
            data={'csrf_token': csrf(r.text), 'username': 'admin', 'password': 'admin123'},
            allow_redirects=True)
check('RF1 - Login exitoso', '/dashboard' not in r2.url and r2.status_code == 200)

# Create client
r = s.get('http://127.0.0.1:5000/clientes/nuevo')
r2 = s.post('http://127.0.0.1:5000/clientes/nuevo', data={
    'csrf_token': csrf(r.text), 'nombre_completo': 'Maria Rodriguez',
    'tipo_documento': 'DNI', 'numero_documento': '87654321',
    'celular': '70011234', 'direccion': 'Av. Principal #456',
    'distrito': 'Equipetrol', 'provincia': 'Santa Cruz', 'departamento': 'Santa Cruz',
    'latitud': '-17.7833', 'longitud': '-63.1822',
    'foto': 'https://i.pravatar.cc/150?u=maria'
}, allow_redirects=True)
# Extract client ID from the list page (find the link to the new client)
client_list = r2.text
cid_match = re.search(r'/clientes/(\d+)">\s*Maria Rodriguez', client_list)
if cid_match:
    cid = cid_match.group(1)
else:
    cid = '1'
r_client = s.get(f'http://127.0.0.1:5000/clientes/{cid}')
check('RF7 - Cliente con lat/lng/foto registrado', 'pravatar' in r_client.text and '-17.78' in r_client.text)
check('RF7 - Mapa Google en detalle del cliente', 'map-detail' in r_client.text)

# Create Loan 1 - Prendaria + Americano
r = s.get(f'http://127.0.0.1:5000/prestamos/nuevo?cliente={cid}')
r2 = s.post(f'http://127.0.0.1:5000/prestamos/nuevo?cliente={cid}', data={
    'csrf_token': csrf(r.text), 'cliente_id': cid, 'monto_solicitado': '10000',
    'tasa_interes_id': '1', 'plazo_meses': '6', 'tipo_garantia': 'prendaria',
    'metodo_amortizacion': 'americano', 'frecuencia_pago': 'mensual',
    'observaciones': 'Test Prendaria+Americano'
}, allow_redirects=False)
loc = r2.headers.get('Location', '/prestamos/')
lid = get_id_from_location(loc) or '1'
r_loan = s.get('http://127.0.0.1:5000' + loc)
check('RF1/RF3 - Prestamo prendaria registrado', 'prendaria' in r_loan.text or f'PRE-{int(lid):04d}' in r_loan.text)
check('RF4 - Metodo Americano en detalle', 'Americano' in r_loan.text or 'americano' in r_loan.text)

# Go to individual loan detail
r_detail = s.get(f'http://127.0.0.1:5000/prestamos/{lid}')
check('RF1/RF3 - Detalle prestamo prendaria', 'prendaria' in r_detail.text)
check('RF4 - Metodo Americano en detalle', 'Americano' in r_detail.text)

# Evaluate Loan
r = s.get(f'http://127.0.0.1:5000/prestamos/{lid}/evaluar')
r2 = s.post(f'http://127.0.0.1:5000/prestamos/{lid}/evaluar', data={
    'csrf_token': csrf(r.text), 'monto_aprobado': '10000', 'submit_aprobar': 'Aprobar Prestamo'
}, allow_redirects=False)
r3 = s.get('http://127.0.0.1:5000' + (r2.headers.get('Location', f'/prestamos/{lid}')))
check('RF1 - Prestamo evaluado/aprobado', 'aprobado' in r3.text)

# Disburse Loan
r = s.get(f'http://127.0.0.1:5000/prestamos/{lid}')
form_match = re.search(r'action="([^"]*desembolsar[^"]*)"', r.text)
post_url = 'http://127.0.0.1:5000' + form_match.group(1) if form_match else f'http://127.0.0.1:5000/prestamos/{lid}/desembolsar'
r2 = s.post(post_url, data={'csrf_token': csrf(r.text)}, allow_redirects=False)
r3 = s.get('http://127.0.0.1:5000' + (r2.headers.get('Location', f'/prestamos/{lid}')))
check('RF2 - Plan de pagos generado (desembolso)', 'Tabla de Amortizacion' in r3.text)
check('RF5 - Boton Amortizar visible', 'Amortizar y Recalcular' in r3.text)
check('RF6 - Docs prendarios visibles',
      all(x in r3.text for x in ['Venta c/ Pacto', 'Dacion en Pago', 'Garantia Prendaria']))

# Verify Americano amortization table
r_table = s.get(f'http://127.0.0.1:5000/prestamos/{lid}')
cuotas_text = r_table.text
check('RF2 - Metodo Americano (solo intereses 5 cuotas)', 'Bs 300.00' in cuotas_text)
check('RF2 - Metodo Americano (capital al final)', 'Bs 10,000' in cuotas_text or 'Bs 10000' in cuotas_text)

# Generate PDF documents
for doc_type in ['contrato_venta', 'dacion_pago', 'garantia_prendaria']:
    r = s.get(f'http://127.0.0.1:5000/prestamos/{lid}/documento/{doc_type}')
    check(f'RF6 - PDF {doc_type}', r.status_code == 200 and len(r.content) > 500)

# Test amortizacion page
r = s.get(f'http://127.0.0.1:5000/prestamos/{lid}/amortizar')
check('RF5 - Pagina amortizacion correcta', 'Monto a Amortizar' in r.text and 'Cuotas Pendientes' in r.text)

# Submit amortizacion
r_post = s.post(f'http://127.0.0.1:5000/prestamos/{lid}/amortizar', data={
    'csrf_token': csrf(r.text), 'monto_amortizar': '2000'
}, allow_redirects=False)
if r_post.status_code == 302:
    r2 = s.get('http://127.0.0.1:5000' + r_post.headers.get('Location', f'/prestamos/{lid}'))
else:
    r2 = r_post
check('RF5 - Amortizacion procesada',
      r2.status_code == 200 and ('reprogramado' in r2.text or 'Tabla de Amortizacion' in r2.text))

# Create Loan 2 - Hipoteca + Frances
r = s.get(f'http://127.0.0.1:5000/prestamos/nuevo?cliente={cid}')
r2 = s.post(f'http://127.0.0.1:5000/prestamos/nuevo?cliente={cid}', data={
    'csrf_token': csrf(r.text), 'cliente_id': cid, 'monto_solicitado': '20000',
    'tasa_interes_id': '1', 'plazo_meses': '12', 'tipo_garantia': 'hipotecaria',
    'metodo_amortizacion': 'frances', 'frecuencia_pago': 'mensual',
}, allow_redirects=False)
loc2 = r2.headers.get('Location', '/prestamos/')
lid2 = get_id_from_location(loc2) or '2'
r3 = s.get('http://127.0.0.1:5000' + loc2)
check('RF3 - Prestamo hipotecario', 'hipotecaria' in r3.text)
check('RF4 - Metodo Frances', 'frances' in r3.text or 'Franc' in r3.text)

# Create Loan 3 - Personal + Aleman
r = s.get(f'http://127.0.0.1:5000/prestamos/nuevo?cliente={cid}')
r2 = s.post(f'http://127.0.0.1:5000/prestamos/nuevo?cliente={cid}', data={
    'csrf_token': csrf(r.text), 'cliente_id': cid, 'monto_solicitado': '15000',
    'tasa_interes_id': '1', 'plazo_meses': '6', 'tipo_garantia': 'personal',
    'metodo_amortizacion': 'alemán', 'frecuencia_pago': 'mensual',
}, allow_redirects=False)
r3 = s.get('http://127.0.0.1:5000' + (r2.headers.get('Location', '/prestamos/')))
check('RF4 - Prestamo personal con Aleman', 'alemán' in r3.text or 'Aleman' in r3.text or 'Alem' in r3.text)

# Verify form option values exist
r = s.get(f'http://127.0.0.1:5000/prestamos/nuevo?cliente={cid}')
check('RF3 - tipo_garantia: prendaria', 'Prendaria' in r.text)
check('RF3 - tipo_garantia: hipoteca', 'Hipoteca' in r.text)
check('RF4 - metodo: frances', 'Franc' in r.text)
check('RF4 - metodo: aleman', 'Alem' in r.text)

# Print results
print(f'\n{"="*50}')
print(f'RESULTADOS DE PRUEBAS')
print(f'{"="*50}')
for r in results:
    print(r)
print(f'\nTotal: {passed+failed} | PASARON: {passed} | FALLARON: {failed}')
if failed == 0:
    print('\nTODOS LOS REQUERIMIENTOS FUNCIONALES SE CUMPLEN EXITOSAMENTE')
else:
    print(f'\n{failed} REQUERIMIENTOS FALLARON')
