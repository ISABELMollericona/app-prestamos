from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Prestamo, Cliente, Pago, Amortizacion
from app import db
from datetime import date, datetime, timedelta

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def dashboard():
    total_prestamos_activos = Prestamo.query.filter(
        Prestamo.estado.in_(['activo', 'desembolsado', 'reprogramado'])
    ).count()

    total_clientes = Cliente.query.filter_by(activo=True).count()

    total_cartera = db.session.query(
        db.func.sum(Prestamo.saldo_pendiente)
    ).filter(
        Prestamo.estado.in_(['activo', 'reprogramado'])
    ).scalar() or 0

    hoy = date.today()
    manana = hoy + timedelta(days=1)
    cobranza_hoy = db.session.query(
        db.func.sum(Pago.monto_total)
    ).filter(
        Pago.fecha_pago >= hoy,
        Pago.fecha_pago < manana
    ).scalar() or 0

    cuotas_vencer_hoy = Amortizacion.query.filter(
        Amortizacion.fecha_vencimiento == date.today(),
        Amortizacion.estado == 'pendiente'
    ).count()

    prestamos_recientes = Prestamo.query.order_by(
        Prestamo.fecha_solicitud.desc()
    ).limit(5).all()

    ultimos_pagos = Pago.query.order_by(
        Pago.fecha_registro.desc()
    ).limit(5).all()

    return render_template('dashboard.html',
                           total_prestamos_activos=total_prestamos_activos,
                           total_clientes=total_clientes,
                           total_cartera=total_cartera,
                           cobranza_hoy=cobranza_hoy,
                           cuotas_vencer_hoy=cuotas_vencer_hoy,
                           prestamos_recientes=prestamos_recientes,
                           ultimos_pagos=ultimos_pagos)
