"""
Módulo de automatización - Tareas programadas
Ejecuta procesos automáticos del sistema de préstamos
"""
from datetime import datetime, date
from decimal import Decimal
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app import db
from app.models import Amortizacion, Prestamo, Notificacion, Cliente

scheduler = BackgroundScheduler()


def actualizar_mora():
    """Actualiza mora diariamente para todas las cuotas vencidas"""
    hoy = date.today()
    tasa_mora = Decimal('0.005')

    cuotas_vencidas = Amortizacion.query.filter(
        Amortizacion.estado == 'pendiente',
        Amortizacion.fecha_vencimiento < hoy
    ).all()

    for cuota in cuotas_vencidas:
        dias_atraso = (hoy - cuota.fecha_vencimiento).days
        cuota.dias_atraso = dias_atraso
        cuota.mora = (cuota.total_cuota * tasa_mora * dias_atraso).quantize(Decimal('0.01'))

    db.session.commit()


def castigar_prestamos_mora():
    """Castiga préstamos con más de 30 días de mora"""
    hoy = date.today()
    from sqlalchemy import func as sa_func

    subquery = db.session.query(
        Amortizacion.prestamo_id,
        sa_func.min(Amortizacion.fecha_vencimiento).label('primera_vencida')
    ).filter(
        Amortizacion.estado == 'pendiente',
        Amortizacion.fecha_vencimiento < hoy
    ).group_by(Amortizacion.prestamo_id).having(
        sa_func.min(Amortizacion.fecha_vencimiento) < hoy
    ).subquery()

    prestamos_mora = Prestamo.query.filter(
        Prestamo.estado.in_(['activo', 'reprogramado']),
        Prestamo.id.in_(db.session.query(subquery.c.prestamo_id))
    ).all()

    for p in prestamos_mora:
        peor_cuota = Amortizacion.query.filter(
            Amortizacion.prestamo_id == p.id,
            Amortizacion.estado == 'pendiente'
        ).order_by(Amortizacion.fecha_vencimiento.asc()).first()

        if peor_cuota and (hoy - peor_cuota.fecha_vencimiento).days > 30:
            p.estado = 'castigado'

    db.session.commit()


def generar_recordatorios():
    """Genera recordatorios para cuotas próximas a vencer (3 días antes)"""
    hoy = date.today()
    from dateutil.relativedelta import relativedelta
    fecha_limite = hoy + relativedelta(days=3)

    cuotas_proximas = Amortizacion.query.filter(
        Amortizacion.estado == 'pendiente',
        Amortizacion.fecha_vencimiento == fecha_limite
    ).all()

    for cuota in cuotas_proximas:
        prestamo = Prestamo.query.get(cuota.prestamo_id)
        cliente = Cliente.query.get(prestamo.cliente_id)

        mensaje = (
            f"Recordatorio: Su cuota #{cuota.numero_cuota} de "
            f"Bs {float(cuota.total_cuota):.2f} vence el "
            f"{cuota.fecha_vencimiento.strftime('%d/%m/%Y')}. "
            f"Préstamo: {prestamo.codigo_prestamo}. ¡Pague a tiempo!"
        )

        notif = Notificacion(
            tipo='recordatorio',
            destino=cliente.celular or cliente.email,
            mensaje=mensaje,
            prestamo_id=prestamo.id,
            cliente_id=cliente.id,
            fecha_envio=datetime.now()
        )
        db.session.add(notif)

    db.session.commit()


def iniciar_scheduler(app):
    """Inicia las tareas programadas"""
    scheduler.add_job(
        func=actualizar_mora,
        trigger=CronTrigger(hour=0, minute=5),
        id='actualizar_mora',
        name='Actualizar mora diaria',
        replace_existing=True
    )

    scheduler.add_job(
        func=castigar_prestamos_mora,
        trigger=CronTrigger(hour=0, minute=10),
        id='castigar_prestamos',
        name='Castigar préstamos en mora extrema',
        replace_existing=True
    )

    scheduler.add_job(
        func=generar_recordatorios,
        trigger=CronTrigger(hour=8, minute=0),
        id='recordatorios_pago',
        name='Generar recordatorios de pago',
        replace_existing=True
    )

    scheduler.start()
