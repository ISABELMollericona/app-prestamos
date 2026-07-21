"""
Script para pruebas de UI con SQLite
Ejecutar: python run_test.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db as _db
from app.models import Rol, Usuario, Cliente, TasaInteres, Prestamo, Amortizacion, Pago, HistorialEstado, Notificacion
from werkzeug.security import generate_password_hash
from app.amortization import generar_tabla_frances
from decimal import Decimal
from datetime import datetime, date, timedelta
import random

app = create_app('test')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_prestamos.db'
app.config['SERVER_NAME'] = 'localhost:5000'
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    _db.create_all()

    roles_data = [
        ('administrador', 'Acceso total al sistema'),
        ('gerente', 'Aprueba prestamos y genera reportes'),
        ('asesor', 'Gestiona clientes y solicitudes'),
        ('cajero', 'Registra pagos y desembolsos'),
    ]
    for nombre, desc in roles_data:
        if not Rol.query.filter_by(nombre=nombre).first():
            _db.session.add(Rol(nombre=nombre, descripcion=desc))

    if not Usuario.query.filter_by(username='admin').first():
        admin = Usuario(
            nombre_completo='Administrador del Sistema',
            email='admin@micredit.com',
            username='admin',
            password_hash=generate_password_hash('admin123'),
            rol_id=1,
            activo=True
        )
        _db.session.add(admin)

    if not TasaInteres.query.first():
        _db.session.add(TasaInteres(nombre='Tasa Estandar Microcredito', tipo_tasa='mensual', valor=0.03, fecha_inicio=date.today() - timedelta(days=365)))
        _db.session.add(TasaInteres(nombre='Tasa Preferencial', tipo_tasa='mensual', valor=0.025, fecha_inicio=date.today() - timedelta(days=180)))
        _db.session.add(TasaInteres(nombre='Tasa Premium', tipo_tasa='mensual', valor=0.02, fecha_inicio=date.today() - timedelta(days=90)))

    _db.session.commit()

    if Cliente.query.count() == 0:
        clientes_data = [
            ('CLI-0001', 'Maria Elena Quispe Mamani', 'DNI', '12345678', '1985-03-15', 'F', 'Casado',
             '987654321', 'maria.quispe@gmail.com', 'Av. Los Olivos 123', 'Cercado', 'Lima', 'Lima',
             'Comerciante', 1500.00, 'Juan Perez', '987654322'),
            ('CLI-0002', 'Carlos Alberto Huaman Condori', 'DNI', '23456789', '1990-07-22', 'M', 'Soltero',
             '976543210', 'carlos.huaman@hotmail.com', 'Jr. Las Flores 456', 'Arequipa', 'Arequipa', 'Arequipa',
             'Taxista', 1800.00, 'Rosa Huaman', '976543211'),
            ('CLI-0003', 'Juana Rosa Lopez Garcia', 'DNI', '34567890', '1978-11-08', 'F', 'Viudo',
             '965432109', 'juana.lopez@yahoo.com', 'Calle Real 789', 'Huancayo', 'Huancayo', 'Junin',
             'Bodeguera', 2000.00, 'Pedro Lopez', '965432110'),
        ]
        for c in clientes_data:
            cli = Cliente(
                codigo_cliente=c[0], nombre_completo=c[1], tipo_documento=c[2], numero_documento=c[3],
                fecha_nacimiento=datetime.strptime(c[4], '%Y-%m-%d').date(),
                genero=c[5], estado_civil=c[6], celular=c[7], email=c[8],
                direccion=c[9], distrito=c[10], provincia=c[11], departamento=c[12],
                ocupacion=c[13], ingresos_mensuales=c[14],
                referencia_nombre=c[15], referencia_telefono=c[16]
            )
            _db.session.add(cli)
        _db.session.flush()

        tasa_defecto = TasaInteres.query.first()
        prestamos_data = [
            (1, 2000.00, 12, '2026-01-15', 'activo'),
            (1, 3000.00, 18, '2026-03-01', 'activo'),
            (2, 1500.00, 6, '2026-02-01', 'activo'),
            (3, 5000.00, 24, '2025-11-01', 'activo'),
        ]
        todos_clientes = Cliente.query.all()
        cliente_map = {i+1: c for i, c in enumerate(todos_clientes)}

        for idx, (cliente_idx, monto, plazo, fecha_str, estado) in enumerate(prestamos_data):
            cliente = cliente_map[cliente_idx]
            fecha_desembolso = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            codigo = f'PRE-{idx+1:04d}'

            prestamo = Prestamo(
                codigo_prestamo=codigo,
                cliente_id=cliente.id,
                monto_solicitado=monto,
                monto_aprobado=monto,
                tasa_interes_id=tasa_defecto.id,
                tasa_interes_valor=tasa_defecto.valor,
                tipo_tasa='mensual',
                plazo_meses=plazo,
                metodo_amortizacion='frances',
                frecuencia_pago='mensual',
                fecha_solicitud=datetime.combine(fecha_desembolso - timedelta(days=7), datetime.min.time()),
                fecha_aprobacion=datetime.combine(fecha_desembolso - timedelta(days=3), datetime.min.time()),
                fecha_desembolso=datetime.combine(fecha_desembolso, datetime.min.time()),
                estado=estado,
                usuario_solicito=1,
                usuario_aprobo=1
            )
            _db.session.add(prestamo)
            _db.session.flush()

            amortizaciones, cuota = generar_tabla_frances(
                Decimal(str(monto)),
                Decimal(str(tasa_defecto.valor * 100 * 12)),
                plazo,
                fecha_desembolso
            )

            for item in amortizaciones:
                estado_cuota = 'pendiente'
                if item['fecha_vencimiento'] < date.today() - timedelta(days=15):
                    estado_cuota = 'vencida'

                am = Amortizacion(
                    prestamo_id=prestamo.id,
                    numero_cuota=item['numero'],
                    fecha_vencimiento=item['fecha_vencimiento'],
                    saldo_inicial=item['saldo_inicial'],
                    monto_cuota=item['monto_cuota'],
                    interes=item['interes'],
                    amortizacion=item['amortizacion'],
                    saldo_final=item['saldo_final'],
                    seguro_desgravamen=item['seguro_desgravamen'],
                    total_cuota=item['total_cuota'],
                    estado=estado_cuota
                )
                if estado_cuota == 'vencida':
                    dias = (date.today() - item['fecha_vencimiento']).days
                    am.dias_atraso = dias
                    am.mora = (item['total_cuota'] * Decimal('0.005') * dias).quantize(Decimal('0.01'))
                _db.session.add(am)

            prestamo.monto_cuota = cuota
            prestamo.total_interes = sum(a['interes'] for a in amortizaciones)
            prestamo.total_a_pagar = sum(a['total_cuota'] for a in amortizaciones)
            prestamo.saldo_pendiente = Decimal(str(monto))
            prestamo.fecha_vencimiento = amortizaciones[-1]['fecha_vencimiento']

            print(f'  Prestamo {codigo} - {cliente.nombre_completo[:20]} - Bs/{monto} - {plazo} meses')

        _db.session.commit()
        print('Datos de prueba cargados')
        print('Usuario: admin / Contrasena: admin123')

print('Iniciando servidor en http://localhost:5000')
app.run(host='0.0.0.0', port=5000, debug=True)
