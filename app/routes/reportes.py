from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Prestamo, Cliente, Pago, Amortizacion, Notificacion
from app import db
from datetime import date, datetime, timedelta
from sqlalchemy import func

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')


@reportes_bp.route('/')
@login_required
def index():
    if not current_user.has_any_role('administrador', 'gerente'):
        flash('No tiene permisos para ver reportes.', 'error')
        return redirect(url_for('main.dashboard'))
    return render_template('reportes/index.html')


@reportes_bp.route('/cartera')
@login_required
def cartera():
    if not current_user.has_any_role('administrador', 'gerente'):
        flash('No tiene permisos para ver reportes.', 'error')
        return redirect(url_for('main.dashboard'))
    total_prestamos = Prestamo.query.filter(
        Prestamo.estado.in_(['activo', 'reprogramado'])
    ).count()

    total_desembolsado = db.session.query(
        func.sum(Prestamo.monto_aprobado)
    ).filter(
        Prestamo.estado.in_(['activo', 'reprogramado', 'cerrado'])
    ).scalar() or 0

    saldo_pendiente = db.session.query(
        func.sum(Prestamo.saldo_pendiente)
    ).filter(
        Prestamo.estado.in_(['activo', 'reprogramado'])
    ).scalar() or 0

    prestamos_mora = Prestamo.query.filter(
        Prestamo.estado.in_(['activo', 'reprogramado']),
        Prestamo.id.in_(
            db.session.query(Amortizacion.prestamo_id).filter(
                Amortizacion.estado == 'pendiente',
                Amortizacion.fecha_vencimiento < date.today()
            )
        )
    ).count()

    return render_template('reportes/cartera.html',
                           total_prestamos=total_prestamos,
                           total_desembolsado=total_desembolsado,
                           saldo_pendiente=saldo_pendiente,
                           prestamos_mora=prestamos_mora)


@reportes_bp.route('/api/estadisticas')
@login_required
def api_estadisticas():
    if not current_user.has_any_role('administrador', 'gerente'):
        return jsonify({'error': 'Sin permisos'}), 403
    prestamos_por_estado = db.session.query(
        Prestamo.estado, func.count(Prestamo.id)
    ).group_by(Prestamo.estado).all()

    pagos_por_mes = db.session.query(
        func.extract('year', Pago.fecha_pago),
        func.extract('month', Pago.fecha_pago),
        func.sum(Pago.monto_total)
    ).filter(
        Pago.fecha_pago >= date.today() - timedelta(days=365)
    ).group_by(
        func.extract('year', Pago.fecha_pago),
        func.extract('month', Pago.fecha_pago)
    ).order_by(
        func.extract('year', Pago.fecha_pago),
        func.extract('month', Pago.fecha_pago)
    ).all()

    data = {
        'prestamos_por_estado': {
            estado: int(count) for estado, count in prestamos_por_estado
        },
        'pagos_por_mes': [
            {
                'anio': anio,
                'mes': mes,
                'total': float(total)
            }
            for anio, mes, total in pagos_por_mes
        ]
    }
    return jsonify(data)


@reportes_bp.route('/api/morosidad')
@login_required
def api_morosidad():
    if not current_user.has_any_role('administrador', 'gerente'):
        return jsonify({'error': 'Sin permisos'}), 403
    hoy = date.today()

    rango1 = date.today() - timedelta(days=90)
    rango2 = date.today() - timedelta(days=60)
    rango3 = date.today() - timedelta(days=30)

    cuotas_mora = db.session.query(
        Amortizacion.prestamo_id,
        func.min(Amortizacion.fecha_vencimiento).label('primera_vencida'),
        func.count(Amortizacion.id).label('cuotas_vencidas')
    ).filter(
        Amortizacion.estado == 'pendiente',
        Amortizacion.fecha_vencimiento < hoy
    ).group_by(Amortizacion.prestamo_id).all()

    mora_90 = sum(1 for c in cuotas_mora if c.primera_vencida <= rango1)
    mora_60 = sum(1 for c in cuotas_mora if rango1 < c.primera_vencida <= rango2)
    mora_30 = sum(1 for c in cuotas_mora if rango2 < c.primera_vencida <= rango3)
    al_dia = Prestamo.query.filter(
        Prestamo.estado.in_(['activo', 'reprogramado']),
        ~Prestamo.id.in_([c.prestamo_id for c in cuotas_mora])
    ).count()

    return jsonify({
        'al_dia': al_dia,
        'mora_30': mora_30,
        'mora_60': mora_60,
        'mora_90': mora_90
    })
