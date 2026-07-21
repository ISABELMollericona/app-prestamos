"""
Script para cargar datos de prueba en el sistema
Ejecutar: python seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Rol, Usuario, Cliente, TasaInteres, Prestamo, Amortizacion, Pago
from werkzeug.security import generate_password_hash
from app.amortization import generar_tabla_frances
from decimal import Decimal
from datetime import datetime, date, timedelta
import random

app = create_app('development')

with app.app_context():
    print('Cargando datos de prueba...')

    if Cliente.query.count() > 0:
        print('Ya hay datos cargados. Para recargar, ejecutá primero: python seed_data.py --clean')
        sys.exit(0)

    # --- CLIENTES ---
    clientes_data = [
        ('CLI-0001', 'María Elena Quispe Mamani', 'DNI', '12345678', '1985-03-15', 'F', 'Casado',
         '987654321', 'maria.quispe@gmail.com', 'Av. Los Olivos 123', 'Cercado', 'Lima', 'Lima',
         'Comerciante', 1500.00, 'Juan Pérez', '987654322'),
        ('CLI-0002', 'Carlos Alberto Huamán Condori', 'DNI', '23456789', '1990-07-22', 'M', 'Soltero',
         '976543210', 'carlos.huaman@hotmail.com', 'Jr. Las Flores 456', 'Arequipa', 'Arequipa', 'Arequipa',
         'Taxista', 1800.00, 'Rosa Huamán', '976543211'),
        ('CLI-0003', 'Juana Rosa López García', 'DNI', '34567890', '1978-11-08', 'F', 'Viudo',
         '965432109', 'juana.lopez@yahoo.com', 'Calle Real 789', 'Huancayo', 'Huancayo', 'Junín',
         'Bodeguera', 2000.00, 'Pedro López', '965432110'),
        ('CLI-0004', 'Miguel Ángel Torres Silva', 'DNI', '45678901', '1988-05-30', 'M', 'Casado',
         '954321098', 'miguel.torres@gmail.com', 'Av. Primavera 321', 'Santiago', 'Cusco', 'Cusco',
         'Agricultor', 1200.00, 'Ana Torres', '954321099'),
        ('CLI-0005', 'Rosa María Paredes Rojas', 'DNI', '56789012', '1995-01-14', 'F', 'Soltero',
         '943210987', 'rosa.paredes@outlook.com', 'Pasaje Los Pinos 654', 'Trujillo', 'Trujillo', 'La Libertad',
         'Vendedora ambulante', 900.00, 'Luis Paredes', '943210988'),
        ('CLI-0006', 'José Antonio Gutiérrez Mendoza', 'CE', 'CE0012345', '1982-09-25', 'M', 'Divorciado',
         '932109876', 'jose.gutierrez@gmail.com', 'Av. Industrial 987', 'San Juan', 'Lima', 'Lima',
         'Mecánico', 2200.00, 'Carmen Gutiérrez', '932109877'),
        ('CLI-0007', 'Lucía Beatriz Flores Vargas', 'DNI', '67890123', '1992-12-03', 'F', 'Casado',
         '921098765', 'lucia.flores@hotmail.com', 'Jr. Bolognesi 147', 'Juliaca', 'San Román', 'Puno',
         'Costurera', 1100.00, 'Marcos Flores', '921098766'),
        ('CLI-0008', 'Pedro Pablo Sánchez Ramos', 'DNI', '78901234', '1975-06-18', 'M', 'Casado',
         '910987654', 'pedro.sanchez@gmail.com', 'Calle Los Claveles 258', 'Paucarpata', 'Arequipa', 'Arequipa',
         'Constructor civil', 2500.00, 'Sonia Sánchez', '910987655'),
        ('CLI-0009', 'Ana Cecilia Ramos Tapia', 'DNI', '89012345', '2000-08-20', 'F', 'Soltero',
         '909876543', 'ana.ramos@gmail.com', 'Av. Universitaria 369', 'Pueblo Libre', 'Lima', 'Lima',
         'Estudiante/Emprendedora', 600.00, 'Carlos Ramos', '909876544'),
        ('CLI-0010', 'Juan Carlos Vilca Apaza', 'DNI', '90123456', '1980-04-10', 'M', 'Casado',
         '898765432', 'juan.vilca@yahoo.es', 'Jr. Independencia 741', 'Puno', 'Puno', 'Puno',
         'Ganadero', 3000.00, 'María Vilca', '898765433'),
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
        db.session.add(cli)

    db.session.flush()
    print(f'  ✓ {len(clientes_data)} clientes creados')

    # --- TASA DE INTERÉS ---
    if not TasaInteres.query.first():
        db.session.add(TasaInteres(nombre='Tasa Estándar Microcrédito', tipo_tasa='mensual', valor=0.03, fecha_inicio=date.today() - timedelta(days=365)))
        db.session.add(TasaInteres(nombre='Tasa Preferencial', tipo_tasa='mensual', valor=0.025, fecha_inicio=date.today() - timedelta(days=180)))
        db.session.add(TasaInteres(nombre='Tasa Premium', tipo_tasa='mensual', valor=0.02, fecha_inicio=date.today() - timedelta(days=90)))
        db.session.flush()
        print('  ✓ Tasas de interés creadas')

    tasa_defecto = TasaInteres.query.first()

    # --- PRÉSTAMOS Y AMORTIZACIONES ---
    prestamos_data = [
        (1, 2000.00, 12, '2026-01-15'),
        (1, 3000.00, 18, '2026-03-01'),
        (2, 1500.00, 6, '2026-02-01'),
        (3, 5000.00, 24, '2025-11-01'),
        (4, 1000.00, 4, '2026-04-01'),
        (5, 2500.00, 12, '2025-08-15'),
        (6, 4000.00, 18, '2025-10-01'),
        (7, 800.00, 3, '2026-05-01'),
        (8, 6000.00, 24, '2025-06-01'),
        (9, 1200.00, 6, '2026-05-15'),
        (10, 3500.00, 12, '2025-12-01'),
        (2, 2000.00, 12, '2025-09-01'),
        (4, 3000.00, 18, '2026-01-01'),
    ]

    estados_prestamo = ['activo', 'activo', 'activo', 'activo', 'cerrado', 'activo', 'activo', 'activo', 'cerrado', 'activo', 'activo', 'cerrado', 'activo']

    todos_clientes = Cliente.query.all()
    cliente_map = {i+1: c for i, c in enumerate(todos_clientes)}

    for idx, (cliente_idx, monto, plazo, fecha_str) in enumerate(prestamos_data):
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
            estado=estados_prestamo[idx],
            usuario_solicito=1,
            usuario_aprobo=1
        )
        db.session.add(prestamo)
        db.session.flush()

        amortizaciones, cuota = generar_tabla_frances(Decimal(str(monto)), Decimal('36'), plazo, fecha_desembolso)

        for item in amortizaciones:
            estado_cuota = 'pendiente'
            if estados_prestamo[idx] == 'cerrado':
                estado_cuota = 'pagada'
                fecha_pago_cuota = item['fecha_vencimiento'] - timedelta(days=random.randint(0, 3))
            elif item['fecha_vencimiento'] < date.today() - timedelta(days=15):
                estado_cuota = 'vencida'
                fecha_pago_cuota = None
            else:
                estado_cuota = 'pendiente'
                fecha_pago_cuota = None

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
            if estado_cuota == 'pagada' and fecha_pago_cuota:
                am.fecha_pago = datetime.combine(fecha_pago_cuota, datetime.min.time())
            if estado_cuota == 'vencida':
                dias = (date.today() - item['fecha_vencimiento']).days
                am.dias_atraso = dias
                am.mora = (item['total_cuota'] * Decimal('0.005') * dias).quantize(Decimal('0.01'))
            db.session.add(am)

        total_amortizacion = sum(a['amortizacion'] for a in amortizaciones)
        total_interes = sum(a['interes'] for a in amortizaciones)
        total_seguro = sum(a['seguro_desgravamen'] for a in amortizaciones)
        total_pagar = sum(a['total_cuota'] for a in amortizaciones)

        cuotas_pagadas = sum(1 for a in amortizaciones if a['fecha_vencimiento'] < date.today() and estados_prestamo[idx] == 'cerrado')
        amortizado_pagado = sum(a['amortizacion'] for a in amortizaciones[:cuotas_pagadas])
        saldo = Decimal(str(monto)) - Decimal(str(amortizado_pagado))

        prestamo.monto_cuota = cuota
        prestamo.total_interes = total_interes
        prestamo.total_a_pagar = total_pagar
        prestamo.saldo_pendiente = max(saldo, Decimal('0.00'))
        prestamo.fecha_vencimiento = amortizaciones[-1]['fecha_vencimiento']

        if estados_prestamo[idx] == 'cerrado':
            prestamo.saldo_pendiente = Decimal('0.00')

        # Registramos pagos simulados para los cerrados
        if estados_prestamo[idx] == 'cerrado':
            for item in amortizaciones:
                pago = Pago(
                    codigo_pago=f'PAG-{item["fecha_vencimiento"].strftime("%Y%m%d")}-{idx+1:03d}-{item["numero"]:02d}',
                    prestamo_id=prestamo.id,
                    cliente_id=cliente.id,
                    monto_total=item['total_cuota'],
                    monto_cuota=item['total_cuota'],
                    cuotas_pagadas=1,
                    fecha_pago=datetime.combine(item['fecha_vencimiento'] - timedelta(days=random.randint(0, 2)), datetime.min.time()),
                    metodo_pago=random.choice(['efectivo', 'transferencia', 'deposito']),
                    usuario_registro=1,
                    estado='confirmado'
                )
                db.session.add(pago)
                db.session.flush()

                am = Amortizacion.query.filter_by(prestamo_id=prestamo.id, numero_cuota=item['numero']).first()
                if am:
                    am.pago_id = pago.id

        print(f'  ✓ Préstamo {codigo} - Cliente: {cliente.nombre_completo[:20]} - Bs/{monto} - {plazo} meses')

    db.session.commit()
    print()
    print('✅ DATOS DE PRUEBA CARGADOS EXITOSAMENTE')
    print(f'   • 10 clientes')
    print(f'   • 13 préstamos con amortizaciones')
    print(f'   • Tasas de interés configuradas')
    print()
    print('   Usuarios disponibles:')
    print('   admin / admin123 (Administrador)')
