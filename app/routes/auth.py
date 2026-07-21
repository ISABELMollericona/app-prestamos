from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Usuario
from app.forms import LoginForm
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if not user.activo:
                flash('Usuario inactivo. Contacte al administrador.', 'error')
                return render_template('auth/login.html', form=form)

            login_user(user)
            user.ultimo_acceso = datetime.now()
            from app import db
            db.session.commit()

            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))

        flash('Usuario o contraseña incorrectos.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
