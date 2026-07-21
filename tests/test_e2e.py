"""
Pruebas integrales de extremo a extremo (E2E) en un solo flujo
Simula el recorrido completo de un usuario en el sistema
"""
import json
from decimal import Decimal
from datetime import datetime, date, timedelta


class TestFlujoCompletoE2E:
    """Flujo E2E completo en un unico test: Login -> CRUD Cliente -> Prestamo -> Pago -> Reportes"""

    def test_flujo_completo(self, client, db, admin_user, tasa_default):
        from flask_login import login_user
        from app.models import Cliente, Prestamo, Amortizacion, Pago

        # Login via session (simula estar autenticado)
        with client.session_transaction() as sess:
            login_user(admin_user)

        # =========== 1. DASHBOARD ===========
        resp = client.get('/')
        assert resp.status_code == 200

        # =========== 2. CREAR CLIENTE ===========
        resp = client.post('/clientes/nuevo', data={
            'nombre_completo': 'Pedro Infante Test',
            'tipo_documento': 'DNI',
            'numero_documento': '87654321',
            'fecha_nacimiento': '1980-05-15',
            'genero': 'M',
            'estado_civil': 'Casado',
            'celular': '999111222',
            'email': 'pedro@test.com',
            'direccion': 'Av. Prueba 123',
            'distrito': 'Miraflores',
            'provincia': 'Lima',
            'departamento': 'Lima',
            'ocupacion': 'Ingeniero',
            'ingresos_mensuales': '3500.00',
        }, follow_redirects=True)
        assert resp.status_code == 200

        cliente = Cliente.query.filter_by(numero_documento='87654321').first()
        assert cliente is not None
        assert cliente.nombre_completo == 'Pedro Infante Test'

        # =========== 3. LISTAR CLIENTES ===========
        resp = client.get('/clientes/')
        assert resp.status_code == 200

        # =========== 4. CREAR PRESTAMO ===========
        resp = client.post('/prestamos/nuevo', data={
            'cliente_id': str(cliente.id),
            'monto_solicitado': '5000.00',
            'tasa_interes_id': str(tasa_default.id),
            'plazo_meses': '12',
            'metodo_amortizacion': 'frances',
            'frecuencia_pago': 'mensual',
            'observaciones': 'Prestamo de prueba E2E'
        }, follow_redirects=True)
        assert resp.status_code == 200

        prestamo = Prestamo.query.filter_by(estado='pendiente').first()
        assert prestamo is not None

        # =========== 5. DETALLE PRESTAMO ===========
        resp = client.get(f'/prestamos/{prestamo.id}')
        assert resp.status_code == 200

        # =========== 6. EVALUAR Y APROBAR ===========
        resp = client.post(f'/prestamos/{prestamo.id}/evaluar', data={
            'monto_aprobado': '4800.00',
            'submit_aprobar': 'Aprobar'
        }, follow_redirects=True)
        assert resp.status_code == 200

        prestamo = Prestamo.query.get(prestamo.id)
        assert prestamo.estado == 'aprobado'

        # =========== 7. DESEMBOLSAR ===========
        resp = client.post(f'/prestamos/{prestamo.id}/desembolsar', follow_redirects=True)
        assert resp.status_code == 200

        prestamo = Prestamo.query.get(prestamo.id)
        assert prestamo.estado == 'activo'

        cuotas = Amortizacion.query.filter_by(prestamo_id=prestamo.id).all()
        assert len(cuotas) == prestamo.plazo_meses

        # =========== 8. CRONOGRAMA PDF ===========
        resp = client.get(f'/prestamos/{prestamo.id}/cronograma')
        assert resp.status_code == 200
        assert resp.mimetype == 'application/pdf'

        # =========== 9. PROYECTAR ===========
        resp = client.get('/prestamos/proyectar')
        assert resp.status_code == 200
        resp = client.post('/prestamos/proyectar', data={
            'monto': '10000', 'tasa': '36', 'plazo': '24'
        })
        assert resp.status_code == 200

        # =========== 10. CUOTAS PENDIENTES API ===========
        resp = client.get(f'/pagos/cuotas/{prestamo.id}')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) > 0
        assert data[0]['numero'] == 1

        # =========== 11. REGISTRAR PAGO ===========
        cuotas = Amortizacion.query.filter_by(
            prestamo_id=prestamo.id, estado='pendiente'
        ).order_by(Amortizacion.numero_cuota).limit(2).all()
        assert len(cuotas) >= 2

        cuotas_ids = ','.join(str(c.numero_cuota) for c in cuotas)

        monto_total = float(sum(c.total_cuota for c in cuotas))
        resp = client.post('/pagos/nuevo', data={
            'prestamo_id': str(prestamo.id),
            'monto_total': str(monto_total),
            'metodo_pago': 'transferencia',
            'numero_operacion': 'OP-E2E-001',
            'observaciones': 'Pago de prueba E2E',
            'cuotas_ids': cuotas_ids
        }, follow_redirects=True)
        assert resp.status_code == 200, f'Pago fallo: {resp.data[:500]}'

        for c in cuotas:
            am = Amortizacion.query.get(c.id)
            assert am.estado == 'pagada', f'Cuota {c.numero_cuota} no pagada: estado={am.estado}'
            assert am.pago_id is not None

        # =========== 12. DETALLE PAGO ===========
        pago = Pago.query.order_by(Pago.id.desc()).first()
        assert pago is not None
        resp = client.get(f'/pagos/{pago.id}')
        assert resp.status_code == 200

        # =========== 13. VOUCHER PDF ===========
        resp = client.get(f'/pagos/{pago.id}/voucher')
        assert resp.status_code == 200
        assert resp.mimetype == 'application/pdf'

        # =========== 14. REPORTES ===========
        resp = client.get('/reportes/cartera')
        assert resp.status_code == 200

        resp = client.get('/reportes/api/estadisticas')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'prestamos_por_estado' in data

        resp = client.get('/reportes/api/morosidad')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'al_dia' in data

        # =========== 15. FILTROS PRESTAMOS ===========
        resp = client.get(f'/prestamos/?estado={prestamo.estado}')
        assert resp.status_code == 200
        resp = client.get(f'/prestamos/?q={prestamo.codigo_prestamo[:5]}')
        assert resp.status_code == 200

        # =========== 16. EDITAR CLIENTE ===========
        resp = client.post(f'/clientes/{cliente.id}/editar', data={
            'nombre_completo': 'Pedro Infante Modificado',
            'tipo_documento': 'DNI',
            'numero_documento': '87654321',
            'genero': 'M',
            'celular': '999111222',
            'email': 'pedro.mod@test.com',
            'ocupacion': 'Senior Engineer',
        }, follow_redirects=True)
        assert resp.status_code == 200
        cliente = Cliente.query.get(cliente.id)
        assert cliente.nombre_completo == 'Pedro Infante Modificado'

        # =========== 17. DESACTIVAR CLIENTE ===========
        assert cliente.activo is True
        resp = client.post(f'/clientes/{cliente.id}/eliminar', follow_redirects=True)
        assert resp.status_code == 200
        cliente = Cliente.query.get(cliente.id)
        assert cliente.activo is False

        # =========== 18. LOGOUT ===========
        resp = client.get('/auth/logout', follow_redirects=True)
        assert resp.status_code == 200
        resp = client.get('/', follow_redirects=True)
        assert resp.status_code == 200


class TestCalculosFinancieros:
    """Verifica que los calculos financieros cumplan la logica de negocio"""

    def test_cuota_frances_formula_correcta(self):
        from app.amortization import calcular_cuota_frances
        from decimal import Decimal

        monto = Decimal('10000')
        tasa_anual = Decimal('36')
        plazo = 12

        cuota = calcular_cuota_frances(monto, tasa_anual, plazo)
        assert cuota == Decimal('1004.62')

        total_pagado = cuota * plazo
        total_interes = total_pagado - monto
        assert total_interes == Decimal('2055.44')

    def test_amortizacion_cierra_saldo(self):
        from app.amortization import generar_tabla_frances
        from decimal import Decimal

        monto = Decimal('5000')
        tabla, _ = generar_tabla_frances(monto, Decimal('24'), 12)

        total_amortizado = sum(t['amortizacion'] for t in tabla)
        assert total_amortizado == monto
        assert tabla[-1]['saldo_final'] == Decimal('0.00')

    def test_interes_compuesto_mensual(self):
        from app.amortization import generar_tabla_frances
        from decimal import Decimal

        monto = Decimal('1000')
        tabla, _ = generar_tabla_frances(monto, Decimal('36'), 6)

        interes_total = sum(t['interes'] for t in tabla)
        assert interes_total > Decimal('100')
        for t in tabla:
            assert t['interes'] > 0
            assert t['amortizacion'] > 0
            assert t['monto_cuota'] > 0

    def test_calculo_mora_correcto(self):
        from app.amortization import calcular_mora
        from decimal import Decimal

        mora = calcular_mora(Decimal('500.00'), 10)
        assert mora == Decimal('25.00')
        mora = calcular_mora(Decimal('1000.00'), 30)
        assert mora == Decimal('150.00')
