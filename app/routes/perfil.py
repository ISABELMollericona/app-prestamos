from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Usuario
from datetime import datetime

perfil_bp = Blueprint('perfil', __name__, url_prefix='/perfil')


@perfil_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        nombre = request.form.get('nombre_completo', '').strip()
        email = request.form.get('email', '').strip()
        password_actual = request.form.get('password_actual', '')
        password_nuevo = request.form.get('password_nuevo', '')
        password_confirmar = request.form.get('password_confirmar', '')

        if nombre:
            current_user.nombre_completo = nombre

        if email:
            if Usuario.query.filter(Usuario.email == email, Usuario.id != current_user.id).first():
                flash('El email ya está siendo usado por otro usuario.', 'error')
                return render_template('perfil/perfil.html')
            current_user.email = email

        if password_actual and password_nuevo:
            if not current_user.check_password(password_actual):
                flash('La contraseña actual no es correcta.', 'error')
                return render_template('perfil/perfil.html')
            if password_nuevo != password_confirmar:
                flash('Las contraseñas nuevas no coinciden.', 'error')
                return render_template('perfil/perfil.html')
            current_user.set_password(password_nuevo)
            flash('Contraseña actualizada exitosamente.', 'success')

        current_user.fecha_actualizacion = datetime.now()
        db.session.commit()
        flash('Perfil actualizado exitosamente.', 'success')
        return redirect(url_for('perfil.index'))

    return render_template('perfil/perfil.html')
