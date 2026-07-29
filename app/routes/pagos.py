from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Prestamo, Cliente, Amortizacion, Pago
from app.forms import PagoForm
from app import db
from app.documents import generar_voucher_pago
from datetime import datetime, date
from decimal import Decimal

pagos_bp = Blueprint('pagos', __name__, url_prefix='/pagos')


def generar_codigo_pago():
    ultimo = Pago.query.order_by(Pago.id.desc()).first()
    if ultimo:
        num = int(ultimo.codigo_pago.split('-')[-1]) + 1
    else:
        num = 1
    return f'PAG-{datetime.now().strftime("%Y%m%d")}-{num:04d}'


@pagos_bp.route('/')
@login_required
def listar():
    if not current_user.has_any_role('administrador', 'cajero'):
        flash('No tiene permisos para ver la sección de pagos.', 'error')
        return redirect(url_for('main.dashboard'))
    busqueda = request.args.get('q', '')
    query = Pago.query

    if busqueda:
        query = query.join(Cliente).filter(
            db.or_(
                Pago.codigo_pago.ilike(f'%{busqueda}%'),
                Cliente.nombre_completo.ilike(f'%{busqueda}%')
            )
        )

    pagos = query.order_by(Pago.fecha_registro.desc()).all()
    return render_template('pagos/listar.html', pagos=pagos, busqueda=busqueda)


@pagos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if not current_user.has_any_role('cajero', 'administrador'):
        flash('No tiene permisos para registrar pagos.', 'error')
        return redirect(url_for('main.dashboard'))

    form = PagoForm()
    prestamos_activos = Prestamo.query.filter(
        Prestamo.estado.in_(['activo', 'reprogramado'])
    ).order_by(Prestamo.codigo_prestamo).all()

    form.prestamo_id.choices = [
        (p.id, f'{p.codigo_prestamo} - {p.cliente.nombre_completo} (Bs/{float(p.saldo_pendiente):,.2f})')
        for p in prestamos_activos
    ]

    if form.validate_on_submit():
        prestamo = Prestamo.query.get(form.prestamo_id.data)
        if not prestamo:
            flash('Préstamo no encontrado.', 'error')
            return render_template('pagos/form.html', form=form)

        cuotas_ids = request.form.get('cuotas_ids', '')
        if not cuotas_ids:
            flash('Debe seleccionar al menos una cuota a pagar.', 'error')
            return render_template('pagos/form.html', form=form)

        try:
            cuotas_seleccionadas = [int(x.strip()) for x in cuotas_ids.split(',') if x.strip()]
        except ValueError:
            flash('Datos de cuotas inválidos.', 'error')
            return render_template('pagos/form.html', form=form)

        total_cuotas = Decimal('0.00')
        total_mora = Decimal('0.00')
        cuotas_pagadas_list = []

        for num_cuota in cuotas_seleccionadas:
            cuota = Amortizacion.query.filter_by(
                prestamo_id=prestamo.id,
                numero_cuota=num_cuota,
                estado='pendiente'
            ).first()

            if not cuota:
                flash(f'Cuota #{num_cuota} no disponible.', 'error')
                return render_template('pagos/form.html', form=form)

            total_cuotas += cuota.total_cuota
            total_mora += cuota.mora or Decimal('0.00')
            cuotas_pagadas_list.append(cuota)

        monto_total = total_cuotas + total_mora

        pago = Pago(
            codigo_pago=generar_codigo_pago(),
            prestamo_id=prestamo.id,
            cliente_id=prestamo.cliente_id,
            monto_total=monto_total,
            monto_cuota=total_cuotas,
            monto_mora=total_mora,
            cuotas_pagadas=len(cuotas_pagadas_list),
            fecha_pago=datetime.now(),
            metodo_pago=form.metodo_pago.data,
            numero_operacion=form.numero_operacion.data,
            usuario_registro=current_user.id,
            observaciones=form.observaciones.data,
            estado='confirmado'
        )
        db.session.add(pago)
        db.session.flush()

        for cuota in cuotas_pagadas_list:
            cuota.estado = 'pagada'
            cuota.fecha_pago = datetime.now()
            cuota.pago_id = pago.id

        prestamo.saldo_pendiente -= sum(
            a.amortizacion for a in cuotas_pagadas_list
        )
        prestamo.fecha_actualizacion = datetime.now()

        todas_pagadas = not Amortizacion.query.filter(
            Amortizacion.prestamo_id == prestamo.id,
            Amortizacion.estado == 'pendiente'
        ).first()

        if todas_pagadas:
            prestamo.estado = 'cerrado'

        db.session.commit()

        flash(f'Pago registrado exitosamente. Código: {pago.codigo_pago}', 'success')
        return redirect(url_for('pagos.detalle', id=pago.id))

    return render_template('pagos/form.html', form=form)


@pagos_bp.route('/<int:id>')
@login_required
def detalle(id):
    if not current_user.has_any_role('administrador', 'cajero'):
        flash('No tiene permisos para ver pagos.', 'error')
        return redirect(url_for('main.dashboard'))
    pago = Pago.query.get_or_404(id)
    cuotas = Amortizacion.query.filter_by(pago_id=pago.id).order_by(Amortizacion.numero_cuota).all()
    return render_template('pagos/detalle.html', pago=pago, cuotas=cuotas)


@pagos_bp.route('/<int:id>/voucher')
@login_required
def voucher_pdf(id):
    if not current_user.has_any_role('administrador', 'cajero'):
        flash('No tiene permisos para ver pagos.', 'error')
        return redirect(url_for('main.dashboard'))
    from flask import send_file
    pago = Pago.query.get_or_404(id)
    cuotas = Amortizacion.query.filter_by(pago_id=pago.id).order_by(Amortizacion.numero_cuota).all()

    pdf = generar_voucher_pago(pago, cuotas)
    return send_file(pdf, download_name=f'voucher_{pago.codigo_pago}.pdf',
                     as_attachment=False, mimetype='application/pdf')


@pagos_bp.route('/cuotas/<int:prestamo_id>')
@login_required
def obtener_cuotas(prestamo_id):
    if not current_user.has_any_role('administrador', 'cajero'):
        return jsonify({'error': 'Sin permisos'}), 403
    cuotas = Amortizacion.query.filter_by(
        prestamo_id=prestamo_id,
        estado='pendiente'
    ).order_by(Amortizacion.numero_cuota).all()

    return jsonify([{
        'id': c.id,
        'numero': c.numero_cuota,
        'fecha_vencimiento': c.fecha_vencimiento.strftime('%d/%m/%Y'),
        'total_cuota': float(c.total_cuota or 0),
        'mora': float(c.mora or 0),
        'saldo_inicial': float(c.saldo_inicial or 0),
        'dias_atraso': c.dias_atraso or 0
    } for c in cuotas])
