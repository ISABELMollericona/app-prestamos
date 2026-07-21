from decimal import Decimal
from datetime import datetime, date


class TestRolModel:
    def test_rol_creation(self, db, roles):
        from app.models import Rol
        admin_role = Rol.query.filter_by(nombre='administrador').first()
        assert admin_role is not None
        assert admin_role.nombre == 'administrador'

    def test_rol_str(self, roles):
        from app.models import Rol
        assert str(roles[0]) == 'administrador'


class TestUsuarioModel:
    def test_create_usuario(self, db, roles):
        from app.models import Usuario
        from werkzeug.security import generate_password_hash
        user = Usuario(
            nombre_completo='Test User',
            email='test@test.com',
            username='testuser',
            password_hash=generate_password_hash('test123'),
            rol_id=1,
            activo=True
        )
        db.session.add(user)
        db.session.commit()
        assert user.id is not None

    def test_password_validation(self, db, roles):
        from app.models import Usuario
        from werkzeug.security import generate_password_hash
        user = Usuario(
            nombre_completo='Test User',
            email='test2@test.com',
            username='testuser2',
            password_hash=generate_password_hash('secret'),
            rol_id=1,
        )
        user.set_password('newpassword')
        assert user.check_password('newpassword')
        assert not user.check_password('wrongpassword')

    def test_has_role(self, admin_user):
        assert admin_user.has_role('administrador')
        assert not admin_user.has_role('gerente')

    def test_has_any_role(self, admin_user):
        assert admin_user.has_any_role('administrador', 'gerente')
        assert not admin_user.has_any_role('cajero', 'asesor')

    def test_usuario_str(self, admin_user):
        assert 'Admin Test' in str(admin_user)


class TestClienteModel:
    def test_create_cliente(self, db):
        from app.models import Cliente
        c = Cliente(
            codigo_cliente='CLI-TEST-1',
            nombre_completo='Test Client',
            numero_documento='99999999',
            celular='111222333',
            activo=True
        )
        db.session.add(c)
        db.session.commit()
        assert c.id is not None
        assert 'Test Client' in str(c)

    def test_cliente_prestamos_relation(self, db, cliente, prestamo_activo):
        assert len(cliente.prestamos) == 1
        assert cliente.prestamos[0].codigo_prestamo == 'PRE-0001'


class TestTasaInteresModel:
    def test_create_tasa(self, db):
        from app.models import TasaInteres
        tasa = TasaInteres(
            nombre='Tasa Test',
            tipo_tasa='mensual',
            valor=Decimal('0.03'),
            fecha_inicio=date.today()
        )
        db.session.add(tasa)
        db.session.commit()
        assert 'Tasa Test' in str(tasa)

    def test_tasa_activa_default(self, tasa_default):
        assert tasa_default.activo is True


class TestPrestamoModel:
    def test_create_prestamo(self, db, cliente, tasa_default):
        from app.models import Prestamo
        p = Prestamo(
            codigo_prestamo='PRE-TEST-1',
            cliente_id=cliente.id,
            monto_solicitado=Decimal('5000.00'),
            monto_aprobado=Decimal('5000.00'),
            tasa_interes_id=tasa_default.id,
            tasa_interes_valor=Decimal('0.03'),
            tipo_tasa='mensual',
            plazo_meses=12,
            estado='pendiente',
            usuario_solicito=1
        )
        db.session.add(p)
        db.session.commit()
        assert 'PRE-TEST-1' in str(p)

    def test_prestamo_progreso(self, db, prestamo_activo, amortizaciones):
        assert prestamo_activo.cuotas_pendientes == 6
        assert prestamo_activo.cuotas_pagadas == 0
        assert prestamo_activo.progreso_pct == 0.0

    def test_prestamo_con_pagos(self, db, prestamo_activo, amortizaciones, admin_user):
        from app.models import Amortizacion, Pago
        primera_cuota = amortizaciones[0]
        pago = Pago(
            codigo_pago='PAG-TEST-1',
            prestamo_id=prestamo_activo.id,
            cliente_id=prestamo_activo.cliente_id,
            monto_total=primera_cuota.total_cuota,
            monto_cuota=primera_cuota.total_cuota,
            cuotas_pagadas=1,
            fecha_pago=datetime.now(),
            metodo_pago='efectivo',
            usuario_registro=admin_user.id,
            estado='confirmado'
        )
        db.session.add(pago)
        db.session.flush()
        primera_cuota.estado = 'pagada'
        primera_cuota.fecha_pago = datetime.now()
        primera_cuota.pago_id = pago.id
        db.session.commit()
        assert prestamo_activo.cuotas_pagadas == 1
        assert prestamo_activo.cuotas_pendientes == 5
        assert prestamo_activo.progreso_pct > 0


class TestAmortizacionModel:
    def test_amortizacion_creation(self, db, prestamo_activo, amortizaciones):
        assert len(amortizaciones) == 6
        assert amortizaciones[0].numero_cuota == 1
        assert amortizaciones[0].estado == 'pendiente'
        assert str(amortizaciones[0]) == 'Cuota #1 - pendiente'

    def test_amortizacion_importes(self, amortizaciones):
        for a in amortizaciones:
            assert a.monto_cuota > 0
            assert a.interes >= 0
            assert a.amortizacion > 0
            assert a.total_cuota > 0

    def test_amortizacion_vencida_mora(self, db, prestamo_activo):
        from app.models import Amortizacion
        from datetime import timedelta
        a = Amortizacion(
            prestamo_id=prestamo_activo.id,
            numero_cuota=99,
            fecha_vencimiento=date.today() - timedelta(days=10),
            saldo_inicial=Decimal('100.00'),
            monto_cuota=Decimal('50.00'),
            interes=Decimal('10.00'),
            amortizacion=Decimal('40.00'),
            saldo_final=Decimal('60.00'),
            total_cuota=Decimal('60.00'),
            estado='vencida',
            dias_atraso=10,
            mora=Decimal('3.00')
        )
        db.session.add(a)
        db.session.commit()
        assert a.dias_atraso == 10
        assert a.mora == Decimal('3.00')


class TestPagoModel:
    def test_create_pago(self, db, prestamo_activo, admin_user):
        from app.models import Pago
        pago = Pago(
            codigo_pago='PAG-TEST-1',
            prestamo_id=prestamo_activo.id,
            cliente_id=prestamo_activo.cliente_id,
            monto_total=Decimal('200.00'),
            monto_cuota=Decimal('180.00'),
            monto_mora=Decimal('20.00'),
            cuotas_pagadas=1,
            fecha_pago=datetime.now(),
            metodo_pago='transferencia',
            numero_operacion='OP-001',
            usuario_registro=admin_user.id,
            estado='confirmado'
        )
        db.session.add(pago)
        db.session.commit()
        assert pago.id is not None
        assert 'PAG-TEST-1' in str(pago)

    def test_pago_relations(self, db, prestamo_activo, admin_user):
        from app.models import Pago
        pago = Pago(
            codigo_pago='PAG-TEST-2',
            prestamo_id=prestamo_activo.id,
            cliente_id=prestamo_activo.cliente_id,
            monto_total=Decimal('150.00'),
            cuotas_pagadas=1,
            fecha_pago=datetime.now(),
            metodo_pago='efectivo',
            usuario_registro=admin_user.id,
            estado='confirmado'
        )
        db.session.add(pago)
        db.session.commit()
        assert pago.prestamo.codigo_prestamo == 'PRE-0001'
        assert pago.cliente.nombre_completo == 'Juan Pérez Test'


class TestHistorialEstadoModel:
    def test_create_historial(self, db, prestamo_activo, admin_user):
        from app.models import HistorialEstado
        h = HistorialEstado(
            prestamo_id=prestamo_activo.id,
            estado_anterior='pendiente',
            estado_nuevo='aprobado',
            usuario_id=admin_user.id,
            observaciones='Aprobado'
        )
        db.session.add(h)
        db.session.commit()
        assert h.id is not None
        assert 'pendiente -> aprobado' in str(h)


class TestNotificacionModel:
    def test_create_notificacion(self, db, prestamo_activo):
        from app.models import Notificacion
        n = Notificacion(
            tipo='recordatorio',
            destino='999888777',
            mensaje='Su cuota esta proxima a vencer',
            prestamo_id=prestamo_activo.id,
            cliente_id=prestamo_activo.cliente_id
        )
        db.session.add(n)
        db.session.commit()
        assert n.id is not None
        assert n.leido is False
