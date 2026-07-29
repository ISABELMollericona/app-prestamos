import json
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Cliente, Prestamo
from app.forms import ClienteForm
from app import db
from datetime import datetime
from sqlalchemy import func

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')


def generar_codigo_cliente():
    ultimo = Cliente.query.order_by(Cliente.id.desc()).first()
    if ultimo:
        num = int(ultimo.codigo_cliente.split('-')[1]) + 1
    else:
        num = 1
    return f'CLI-{num:04d}'


@clientes_bp.route('/')
@login_required
def listar():
    busqueda = request.args.get('q', '')
    if busqueda:
        clientes = Cliente.query.filter(
            Cliente.activo == True,
            db.or_(
                Cliente.nombre_completo.ilike(f'%{busqueda}%'),
                Cliente.numero_documento.ilike(f'%{busqueda}%'),
                Cliente.celular.ilike(f'%{busqueda}%')
            )
        ).order_by(Cliente.nombre_completo).all()
    else:
        clientes = Cliente.query.filter_by(activo=True).order_by(Cliente.nombre_completo).all()
    return render_template('clientes/listar.html', clientes=clientes, busqueda=busqueda)


@clientes_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if not current_user.has_any_role('administrador', 'gerente', 'asesor'):
        flash('No tiene permisos para registrar clientes.', 'error')
        return redirect(url_for('clientes.listar'))
    form = ClienteForm()
    if form.validate_on_submit():
        if Cliente.query.filter_by(numero_documento=form.numero_documento.data).first():
            flash('Ya existe un cliente con ese número de documento.', 'error')
            return render_template('clientes/form.html', form=form, titulo='Nuevo Cliente')

        cliente = Cliente(
            codigo_cliente=generar_codigo_cliente(),
            nombre_completo=form.nombre_completo.data,
            tipo_documento=form.tipo_documento.data,
            numero_documento=form.numero_documento.data,
            fecha_nacimiento=form.fecha_nacimiento.data,
            genero=form.genero.data,
            estado_civil=form.estado_civil.data,
            telefono=form.telefono.data,
            celular=form.celular.data,
            email=form.email.data,
            direccion=form.direccion.data,
            distrito=form.distrito.data,
            provincia=form.provincia.data,
            departamento=form.departamento.data,
            ocupacion=form.ocupacion.data,
            ingresos_mensuales=form.ingresos_mensuales.data,
            referencia_nombre=form.referencia_nombre.data,
            referencia_telefono=form.referencia_telefono.data,
            latitud=form.latitud.data,
            longitud=form.longitud.data,
            foto=form.foto.data,
            observaciones=form.observaciones.data
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente registrado exitosamente.', 'success')
        return redirect(url_for('clientes.listar'))

    return render_template('clientes/form.html', form=form, titulo='Nuevo Cliente')


@clientes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.has_any_role('administrador', 'gerente', 'asesor'):
        flash('No tiene permisos para editar clientes.', 'error')
        return redirect(url_for('clientes.detalle', id=id))
    cliente = Cliente.query.get_or_404(id)
    form = ClienteForm(obj=cliente)
    if form.validate_on_submit():
        form.populate_obj(cliente)
        cliente.fecha_actualizacion = datetime.now()
        db.session.commit()
        flash('Cliente actualizado exitosamente.', 'success')
        return redirect(url_for('clientes.listar'))

    return render_template('clientes/form.html', form=form, cliente=cliente, titulo='Editar Cliente')


@clientes_bp.route('/<int:id>')
@login_required
def detalle(id):
    cliente = Cliente.query.get_or_404(id)
    prestamos = cliente.prestamos
    return render_template('clientes/detalle.html', cliente=cliente, prestamos=prestamos)


@clientes_bp.route('/mapa')
@login_required
def mapa():
    clientes = Cliente.query.filter(
        Cliente.activo == True,
        Cliente.latitud.isnot(None),
        Cliente.longitud.isnot(None)
    ).order_by(Cliente.nombre_completo).all()

    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError

    data = []
    for c in clientes:
        prestamos_activos = [p for p in c.prestamos if p.estado in ('activo', 'reprogramado', 'desembolsado')]
        prestamos_count = len(c.prestamos)
        activos_count = len(prestamos_activos)
        total_adeudado = sum(float(p.saldo_pendiente or 0) for p in prestamos_activos)

        data.append({
            'id': c.id,
            'codigo': c.codigo_cliente,
            'nombre': c.nombre_completo,
            'documento': f'{c.tipo_documento} {c.numero_documento}',
            'celular': c.celular or '',
            'direccion': c.direccion or '',
            'distrito': c.distrito or '',
            'latitud': float(c.latitud),
            'longitud': float(c.longitud),
            'total_prestamos': prestamos_count,
            'prestamos_activos': activos_count,
            'saldo_pendiente': total_adeudado
        })

    return render_template('clientes/mapa.html', clientes_json=json.dumps(data, default=decimal_default))


@clientes_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    if not current_user.has_role('administrador'):
        flash('No tiene permisos para eliminar clientes.', 'error')
        return redirect(url_for('clientes.listar'))

    cliente = Cliente.query.get_or_404(id)
    cliente.activo = False
    db.session.commit()
    flash('Cliente desactivado.', 'success')
    return redirect(url_for('clientes.listar'))
