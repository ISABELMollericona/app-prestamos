from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Prestamo, Cliente, TasaInteres, Amortizacion, HistorialEstado
from app.forms import PrestamoForm, EvaluarPrestamoForm
from app import db
from app.amortization import (generar_tabla_frances, generar_tabla_aleman,
                               generar_tabla_americano, recalcular_plan_pagos,
                               proyectar_prestamo)
from app.documents import generar_cronograma_pagos, generar_contrato_prenda_venta, generar_contrato_prenda_dacion, generar_contrato_prenda_garantia
from datetime import datetime
from decimal import Decimal, InvalidOperation

prestamos_bp = Blueprint('prestamos', __name__, url_prefix='/prestamos')


def generar_codigo_prestamo():
    ultimo = Prestamo.query.order_by(Prestamo.id.desc()).first()
    if ultimo:
        num = int(ultimo.codigo_prestamo.split('-')[1]) + 1
    else:
        num = 1
    return f'PRE-{num:04d}'


@prestamos_bp.route('/')
@login_required
def listar():
    estado = request.args.get('estado', '')
    busqueda = request.args.get('q', '')
    query = Prestamo.query

    if estado:
        query = query.filter(Prestamo.estado == estado)
    if busqueda:
        query = query.join(Cliente).filter(
            db.or_(
                Prestamo.codigo_prestamo.ilike(f'%{busqueda}%'),
                Cliente.nombre_completo.ilike(f'%{busqueda}%'),
                Cliente.numero_documento.ilike(f'%{busqueda}%')
            )
        )

    prestamos = query.order_by(Prestamo.fecha_solicitud.desc()).all()
    return render_template('prestamos/listar.html', prestamos=prestamos, estado=estado, busqueda=busqueda)


@prestamos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if not current_user.has_any_role('administrador', 'asesor'):
        flash('No tiene permisos para solicitar préstamos.', 'error')
        return redirect(url_for('prestamos.listar'))
    form = PrestamoForm()
    form.cliente_id.choices = [(c.id, f'{c.nombre_completo} ({c.numero_documento})')
                                for c in Cliente.query.filter_by(activo=True).order_by(Cliente.nombre_completo).all()]
    form.tasa_interes_id.choices = [(t.id, f'{t.nombre} ({float(t.valor)*100}% {t.tipo_tasa})')
                                     for t in TasaInteres.query.filter_by(activo=True).all()]

    if form.validate_on_submit():
        tasa = TasaInteres.query.get(form.tasa_interes_id.data)
        prestamo = Prestamo(
            codigo_prestamo=generar_codigo_prestamo(),
            cliente_id=form.cliente_id.data,
            monto_solicitado=form.monto_solicitado.data,
            tasa_interes_id=tasa.id,
            tasa_interes_valor=tasa.valor,
            tipo_tasa=tasa.tipo_tasa,
            plazo_meses=form.plazo_meses.data,
            tipo_garantia=form.tipo_garantia.data,
            metodo_amortizacion=form.metodo_amortizacion.data,
            frecuencia_pago=form.frecuencia_pago.data,
            estado='pendiente',
            usuario_solicito=current_user.id,
            observaciones=form.observaciones.data
        )
        db.session.add(prestamo)
        db.session.commit()

        flash('Solicitud de préstamo registrada exitosamente.', 'success')
        return redirect(url_for('prestamos.detalle', id=prestamo.id))

    return render_template('prestamos/form.html', form=form, titulo='Nueva Solicitud')


@prestamos_bp.route('/<int:id>')
@login_required
def detalle(id):
    prestamo = Prestamo.query.get_or_404(id)
    amortizaciones = Amortizacion.query.filter_by(prestamo_id=id).order_by(Amortizacion.numero_cuota).all()
    return render_template('prestamos/detalle.html', prestamo=prestamo, amortizaciones=amortizaciones)


@prestamos_bp.route('/<int:id>/evaluar', methods=['GET', 'POST'])
@login_required
def evaluar(id):
    if not current_user.has_any_role('gerente', 'administrador'):
        flash('No tiene permisos para evaluar préstamos.', 'error')
        return redirect(url_for('prestamos.detalle', id=id))

    prestamo = Prestamo.query.get_or_404(id)
    if prestamo.estado not in ('pendiente', 'evaluacion'):
        flash('Este préstamo ya fue evaluado.', 'error')
        return redirect(url_for('prestamos.detalle', id=id))

    form = EvaluarPrestamoForm(obj=prestamo)
    if form.validate_on_submit():
        prestamo.estado_anterior = prestamo.estado

        if 'submit_aprobar' in request.form:
            prestamo.monto_aprobado = form.monto_aprobado.data
            prestamo.estado = 'aprobado'
            prestamo.fecha_aprobacion = datetime.now()
            prestamo.usuario_aprobo = current_user.id

            historial = HistorialEstado(
                prestamo_id=prestamo.id,
                estado_anterior=prestamo.estado_anterior,
                estado_nuevo='aprobado',
                usuario_id=current_user.id,
                observaciones='Préstamo aprobado'
            )
            db.session.add(historial)

            flash('Préstamo aprobado. La tabla de amortización se generará automáticamente al registrar el desembolso.', 'success')

        elif 'submit_rechazar' in request.form:
            prestamo.estado = 'rechazado'
            prestamo.motivo_rechazo = form.motivo_rechazo.data
            prestamo.fecha_actualizacion = datetime.now()

            historial = HistorialEstado(
                prestamo_id=prestamo.id,
                estado_anterior=prestamo.estado_anterior,
                estado_nuevo='rechazado',
                usuario_id=current_user.id,
                observaciones=form.motivo_rechazo.data
            )
            db.session.add(historial)
            flash('Préstamo rechazado.', 'info')

        db.session.commit()
        return redirect(url_for('prestamos.detalle', id=prestamo.id))

    return render_template('prestamos/evaluar.html', prestamo=prestamo, form=form)


@prestamos_bp.route('/<int:id>/desembolsar', methods=['POST'])
@login_required
def desembolsar(id):
    if not current_user.has_any_role('cajero', 'administrador'):
        flash('No tiene permisos para desembolsar.', 'error')
        return redirect(url_for('prestamos.detalle', id=id))

    prestamo = Prestamo.query.get_or_404(id)
    if prestamo.estado != 'aprobado':
        flash('El préstamo debe estar aprobado para desembolsar.', 'error')
        return redirect(url_for('prestamos.detalle', id=id))

    prestamo.estado_anterior = prestamo.estado
    prestamo.estado = 'activo'
    prestamo.fecha_desembolso = datetime.now()

    tasa = prestamo.tasa_interes_valor
    tipo = prestamo.tipo_tasa or 'mensual'
    if tasa:
        if tipo == 'anual':
            tasa_decimal = Decimal(str(tasa)) * Decimal('100')
        elif tipo == 'mensual':
            tasa_decimal = Decimal(str(tasa)) * Decimal('100') * Decimal('12')
        elif tipo == 'diaria':
            tasa_decimal = Decimal(str(tasa)) * Decimal('100') * Decimal('365')
        else:
            tasa_decimal = Decimal(str(tasa)) * Decimal('100') * Decimal('12')
    else:
        tasa_decimal = Decimal('36')

    if prestamo.metodo_amortizacion == 'frances':
        amortizaciones, cuota = generar_tabla_frances(
            Decimal(str(prestamo.monto_aprobado)),
            tasa_decimal,
            prestamo.plazo_meses,
            datetime.now().date()
        )
    elif prestamo.metodo_amortizacion == 'americano':
        amortizaciones, cuota = generar_tabla_americano(
            Decimal(str(prestamo.monto_aprobado)),
            tasa_decimal,
            prestamo.plazo_meses,
            datetime.now().date()
        )
    else:
        amortizaciones = generar_tabla_aleman(
            Decimal(str(prestamo.monto_aprobado)),
            tasa_decimal,
            prestamo.plazo_meses,
            datetime.now().date()
        )
        cuota = amortizaciones[0]['monto_cuota'] if amortizaciones else Decimal('0')

    for item in amortizaciones:
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
            estado='pendiente'
        )
        db.session.add(am)

    prestamo.monto_cuota = cuota
    prestamo.total_interes = sum(a['interes'] for a in amortizaciones)
    prestamo.total_a_pagar = sum(a['total_cuota'] for a in amortizaciones)
    prestamo.saldo_pendiente = Decimal(str(prestamo.monto_aprobado))
    prestamo.fecha_vencimiento = amortizaciones[-1]['fecha_vencimiento']
    prestamo.fecha_actualizacion = datetime.now()

    historial = HistorialEstado(
        prestamo_id=prestamo.id,
        estado_anterior=prestamo.estado_anterior,
        estado_nuevo='activo',
        usuario_id=current_user.id,
        observaciones='Préstamo desembolsado y activado'
    )
    db.session.add(historial)
    db.session.commit()

    flash(f'Préstamo desembolsado exitosamente. {prestamo.plazo_meses} cuotas generadas.', 'success')
    return redirect(url_for('prestamos.detalle', id=prestamo.id))


@prestamos_bp.route('/<int:id>/amortizar', methods=['GET', 'POST'])
@login_required
def amortizar(id):
    if not current_user.has_any_role('administrador', 'cajero'):
        flash('No tiene permisos para realizar amortizaciones.', 'error')
        return redirect(url_for('prestamos.detalle', id=id))

    prestamo = Prestamo.query.get_or_404(id)
    if prestamo.estado not in ('activo', 'reprogramado'):
        flash('Solo se pueden amortizar prestamos activos o reprogramados.', 'error')
        return redirect(url_for('prestamos.detalle', id=id))

    cuotas_pendientes = Amortizacion.query.filter_by(
        prestamo_id=id, estado='pendiente'
    ).order_by(Amortizacion.numero_cuota).all()

    if not cuotas_pendientes:
        flash('No hay cuotas pendientes.', 'error')
        return redirect(url_for('prestamos.detalle', id=id))

    if request.method == 'POST':
        try:
            monto_amortizar = Decimal(str(request.form.get('monto_amortizar', 0)))
            if monto_amortizar <= 0:
                flash('Monto invalido.', 'error')
                return render_template('prestamos/amortizar.html', prestamo=prestamo, cuotas=cuotas_pendientes)

            saldo_actual = cuotas_pendientes[0].saldo_inicial
            if monto_amortizar > saldo_actual:
                flash(f'El monto no puede superar el saldo pendiente (Bs {float(saldo_actual):,.2f}).', 'error')
                return render_template('prestamos/amortizar.html', prestamo=prestamo, cuotas=cuotas_pendientes)

            exito = recalcular_plan_pagos(prestamo, monto_amortizar, db)
            if exito:
                prestamo.fecha_actualizacion = datetime.now()
                historial = HistorialEstado(
                    prestamo_id=prestamo.id,
                    estado_anterior='activo',
                    estado_nuevo='reprogramado',
                    usuario_id=current_user.id,
                    observaciones=f'Amortizacion extraordinaria de Bs {float(monto_amortizar):,.2f}. Plan recalculado.'
                )
                db.session.add(historial)
                prestamo.estado = 'reprogramado'
                db.session.commit()
                flash(f'Amortizacion de Bs {float(monto_amortizar):,.2f} aplicada. Plan de pagos recalculado.', 'success')
            else:
                flash('Error al recalcular el plan.', 'error')
        except (ValueError, InvalidOperation) as e:
            flash(f'Error: {str(e)}', 'error')

        return redirect(url_for('prestamos.detalle', id=id))

    return render_template('prestamos/amortizar.html', prestamo=prestamo, cuotas=cuotas_pendientes)


@prestamos_bp.route('/proyectar', methods=['GET', 'POST'])
@login_required
def proyectar():
    resultado = None
    if request.method == 'POST':
        try:
            monto = Decimal(str(request.form.get('monto', 0)))
            tasa = Decimal(str(request.form.get('tasa', 36)))
            plazo = int(request.form.get('plazo', 12))
            resultado = proyectar_prestamo(monto, tasa, plazo)
        except (ValueError, InvalidOperation):
            flash('Datos inválidos para la proyección.', 'error')

    return render_template('prestamos/proyectar.html', resultado=resultado)


@prestamos_bp.route('/<int:id>/documento/<tipo>')
@login_required
def generar_documento(id, tipo):
    from flask import send_file
    prestamo = Prestamo.query.get_or_404(id)
    if prestamo.estado not in ('aprobado', 'activo'):
        flash('El prestamo debe estar aprobado o activo.', 'error')
        return redirect(url_for('prestamos.detalle', id=id))

    pdf = None
    if tipo == 'cronograma':
        amortizaciones = Amortizacion.query.filter_by(prestamo_id=id).order_by(Amortizacion.numero_cuota).all()
        if not amortizaciones:
            flash('No hay cronograma generado.', 'error')
            return redirect(url_for('prestamos.detalle', id=id))
        pdf = generar_cronograma_pagos(prestamo, amortizaciones)
        filename = f'cronograma_{prestamo.codigo_prestamo}.pdf'
    elif tipo == 'contrato_venta':
        pdf = generar_contrato_prenda_venta(prestamo)
        filename = f'contrato_venta_pacto_rescate_{prestamo.codigo_prestamo}.pdf'
    elif tipo == 'dacion_pago':
        pdf = generar_contrato_prenda_dacion(prestamo)
        filename = f'dacion_pago_{prestamo.codigo_prestamo}.pdf'
    elif tipo == 'garantia_prendaria':
        pdf = generar_contrato_prenda_garantia(prestamo)
        filename = f'garantia_prendaria_{prestamo.codigo_prestamo}.pdf'
    else:
        flash('Tipo de documento no valido.', 'error')
        return redirect(url_for('prestamos.detalle', id=id))

    return send_file(pdf, download_name=filename,
                     as_attachment=False, mimetype='application/pdf')


@prestamos_bp.route('/<int:id>/cronograma')
@login_required
def cronograma_pdf(id):
    from flask import send_file
    prestamo = Prestamo.query.get_or_404(id)
    amortizaciones = Amortizacion.query.filter_by(prestamo_id=id).order_by(Amortizacion.numero_cuota).all()

    if not amortizaciones:
        flash('No hay cronograma generado aún.', 'error')
        return redirect(url_for('prestamos.detalle', id=id))

    pdf = generar_cronograma_pagos(prestamo, amortizaciones)
    return send_file(pdf, download_name=f'cronograma_{prestamo.codigo_prestamo}.pdf',
                     as_attachment=False, mimetype='application/pdf')
