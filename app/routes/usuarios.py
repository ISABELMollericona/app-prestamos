from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Usuario, Rol
from app import db
from datetime import datetime

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')


def admin_required(f):
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.has_role('administrador'):
            flash('No tiene permisos de administrador para acceder a esta sección.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


@usuarios_bp.route('/')
@admin_required
def listar():
    busqueda = request.args.get('q', '')
    query = Usuario.query
    if busqueda:
        query = query.filter(
            db.or_(
                Usuario.nombre_completo.ilike(f'%{busqueda}%'),
                Usuario.username.ilike(f'%{busqueda}%'),
                Usuario.email.ilike(f'%{busqueda}%')
            )
        )
    usuarios = query.order_by(Usuario.nombre_completo).all()
    return render_template('usuarios/listar.html', usuarios=usuarios, busqueda=busqueda)


@usuarios_bp.route('/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        nombre = request.form.get('nombre_completo', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        rol_id = request.form.get('rol_id', type=int)

        if not all([username, nombre, email, password, rol_id]):
            flash('Todos los campos obligatorios deben ser completados.', 'error')
            return render_template('usuarios/form.html', roles=Rol.query.all())

        if Usuario.query.filter_by(username=username).first():
            flash(f'El usuario "{username}" ya existe.', 'error')
            return render_template('usuarios/form.html', roles=Rol.query.all())

        if Usuario.query.filter_by(email=email).first():
            flash(f'El email "{email}" ya está registrado.', 'error')
            return render_template('usuarios/form.html', roles=Rol.query.all())

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('usuarios/form.html', roles=Rol.query.all())

        user = Usuario(
            username=username,
            nombre_completo=nombre,
            email=email,
            rol_id=rol_id,
            activo=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'Usuario "{username}" creado exitosamente.', 'success')
        return redirect(url_for('usuarios.listar'))

    return render_template('usuarios/form.html', roles=Rol.query.all())


@usuarios_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@admin_required
def editar(id):
    user = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        user.nombre_completo = request.form.get('nombre_completo', user.nombre_completo).strip()
        user.email = request.form.get('email', user.email).strip()
        user.rol_id = request.form.get('rol_id', user.rol_id, type=int)
        password = request.form.get('password', '').strip()

        email_existente = Usuario.query.filter(
            Usuario.email == user.email, Usuario.id != id
        ).first()
        if email_existente:
            flash(f'El email "{user.email}" ya está registrado.', 'error')
            return render_template('usuarios/form.html', usuario=user, roles=Rol.query.all())

        if password:
            if len(password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'error')
                return render_template('usuarios/form.html', usuario=user, roles=Rol.query.all())
            user.set_password(password)

        user.fecha_actualizacion = datetime.now()
        db.session.commit()
        flash(f'Usuario "{user.username}" actualizado.', 'success')
        return redirect(url_for('usuarios.listar'))

    return render_template('usuarios/form.html', usuario=user, roles=Rol.query.all())


@usuarios_bp.route('/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle(id):
    if current_user.id == id:
        flash('No puede desactivarse a sí mismo.', 'error')
        return redirect(url_for('usuarios.listar'))

    user = Usuario.query.get_or_404(id)
    user.activo = not user.activo
    db.session.commit()
    estado = 'activado' if user.activo else 'desactivado'
    flash(f'Usuario "{user.username}" {estado}.', 'success')
    return redirect(url_for('usuarios.listar'))
