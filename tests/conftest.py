import pytest
from app import create_app, db as _db
from app.models import Rol, Usuario, Cliente, TasaInteres, Prestamo, Amortizacion, Pago, HistorialEstado, Notificacion
from datetime import datetime, date
from decimal import Decimal
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='session')
def app():
    app = create_app('test')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key',
    })
    return app


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    return app.test_client()


@pytest.fixture(scope='function')
def session(app, db):
    return db.session


@pytest.fixture(scope='function')
def roles(db):
    roles_data = [
        Rol(nombre='administrador', descripcion='Acceso total'),
        Rol(nombre='gerente', descripcion='Aprueba préstamos'),
        Rol(nombre='asesor', descripcion='Gestiona clientes'),
        Rol(nombre='cajero', descripcion='Registra pagos'),
    ]
    for r in roles_data:
        db.session.add(r)
    db.session.commit()
    return roles_data


@pytest.fixture(scope='function')
def admin_user(db, roles):
    user = Usuario(
        nombre_completo='Admin Test',
        email='admin@test.com',
        username='admin',
        password_hash=generate_password_hash('admin123'),
        rol_id=1,
        activo=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def tasa_default(db):
    tasa = TasaInteres(
        nombre='Tasa Test',
        tipo_tasa='mensual',
        valor=Decimal('0.03'),
        fecha_inicio=date.today()
    )
    db.session.add(tasa)
    db.session.commit()
    return tasa


@pytest.fixture(scope='function')
def cliente(db):
    c = Cliente(
        codigo_cliente='CLI-0001',
        nombre_completo='Juan Pérez Test',
        tipo_documento='DNI',
        numero_documento='12345678',
        celular='999888777',
        ingresos_mensuales=Decimal('2000.00'),
        activo=True
    )
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture(scope='function')
def prestamo_activo(db, cliente, tasa_default):
    p = Prestamo(
        codigo_prestamo='PRE-0001',
        cliente_id=cliente.id,
        monto_solicitado=Decimal('1000.00'),
        monto_aprobado=Decimal('1000.00'),
        tasa_interes_id=tasa_default.id,
        tasa_interes_valor=Decimal('0.03'),
        tipo_tasa='mensual',
        plazo_meses=6,
        metodo_amortizacion='frances',
        frecuencia_pago='mensual',
        estado='activo',
        saldo_pendiente=Decimal('1000.00'),
        usuario_solicito=1,
        usuario_aprobo=1,
        fecha_solicitud=datetime.now(),
        fecha_aprobacion=datetime.now(),
        fecha_desembolso=datetime.now(),
    )
    db.session.add(p)
    db.session.commit()
    return p


@pytest.fixture(scope='function')
def amortizaciones(db, prestamo_activo):
    from app.amortization import generar_tabla_frances
    monto = Decimal('1000.00')
    tasa_anual = Decimal('36')
    plazo = 6
    tabla, cuota = generar_tabla_frances(monto, tasa_anual, plazo)
    items = []
    for item in tabla:
        a = Amortizacion(
            prestamo_id=prestamo_activo.id,
            numero_cuota=item['numero'],
            fecha_vencimiento=item['fecha_vencimiento'],
            saldo_inicial=item['saldo_inicial'],
            monto_cuota=item['monto_cuota'],
            interes=item['interes'],
            amortizacion=item['amortizacion'],
            saldo_final=item['saldo_final'],
            seguro_desgravamen=item['seguro_desgravamen'],
            total_cuota=item['total_cuota'],
            estado='pendiente'
        )
        db.session.add(a)
        items.append(a)
    prestamo_activo.monto_cuota = cuota
    prestamo_activo.total_interes = sum(item['interes'] for item in tabla)
    prestamo_activo.total_a_pagar = sum(item['total_cuota'] for item in tabla)
    prestamo_activo.saldo_pendiente = monto
    prestamo_activo.fecha_vencimiento = tabla[-1]['fecha_vencimiento']
    db.session.commit()
    return items


@pytest.fixture(scope='function')
def logged_client(client, admin_user):
    with client.session_transaction() as sess:
        from flask_login import login_user
        login_user(admin_user)
    return client
