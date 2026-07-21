import json
from decimal import Decimal
from datetime import datetime, date


class TestAuthRoutes:
    def test_login_page_get(self, client):
        resp = client.get('/auth/login')
        assert resp.status_code == 200
        assert b'Iniciar' in resp.data or b'Usuario' in resp.data

    def test_login_success(self, client, admin_user):
        resp = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_fail(self, client, admin_user):
        resp = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'wrong'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_logout(self, logged_client):
        resp = logged_client.get('/auth/logout', follow_redirects=True)
        assert resp.status_code == 200


class TestClientesRoutes:
    def test_listar_clientes(self, logged_client, cliente):
        resp = logged_client.get('/clientes/')
        assert resp.status_code == 200

    def test_detalle_cliente(self, logged_client, cliente):
        resp = logged_client.get(f'/clientes/{cliente.id}')
        assert resp.status_code == 200

    def test_eliminar_cliente(self, logged_client, cliente):
        resp = logged_client.post(f'/clientes/{cliente.id}/eliminar', follow_redirects=True)
        assert resp.status_code == 200


class TestPrestamosRoutes:
    def test_listar_prestamos(self, logged_client, prestamo_activo):
        resp = logged_client.get('/prestamos/')
        assert resp.status_code == 200

    def test_detalle_prestamo(self, logged_client, prestamo_activo):
        resp = logged_client.get(f'/prestamos/{prestamo_activo.id}')
        assert resp.status_code == 200

    def test_proyectar_prestamo(self, logged_client):
        resp = logged_client.post('/prestamos/proyectar', data={
            'monto': '5000',
            'tasa': '36',
            'plazo': '12'
        })
        assert resp.status_code == 200

    def test_nuevo_prestamo_get(self, logged_client, cliente, tasa_default):
        resp = logged_client.get('/prestamos/nuevo')
        assert resp.status_code == 200


class TestPagosRoutes:
    def test_listar_pagos(self, logged_client):
        resp = logged_client.get('/pagos/')
        assert resp.status_code == 200

    def test_obtener_cuotas_api(self, logged_client, prestamo_activo, amortizaciones):
        resp = logged_client.get(f'/pagos/cuotas/{prestamo_activo.id}')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) == 6
        assert data[0]['numero'] == 1


class TestReportesRoutes:
    def test_reportes_index(self, logged_client):
        resp = logged_client.get('/reportes/')
        assert resp.status_code == 200

    def test_cartera(self, logged_client, prestamo_activo):
        resp = logged_client.get('/reportes/cartera')
        assert resp.status_code == 200

    def test_api_estadisticas(self, logged_client, prestamo_activo):
        resp = logged_client.get('/reportes/api/estadisticas')
        assert resp.status_code == 200

    def test_api_morosidad(self, logged_client, prestamo_activo):
        resp = logged_client.get('/reportes/api/morosidad')
        assert resp.status_code == 200


class TestMainRoutes:
    def test_dashboard(self, logged_client, prestamo_activo, cliente):
        resp = logged_client.get('/')
        assert resp.status_code == 200

    def test_dashboard_redirect_if_not_logged(self, client):
        resp = client.get('/', follow_redirects=True)
        assert resp.status_code == 200
