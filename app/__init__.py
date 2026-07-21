from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from config import config_by_name
from datetime import datetime, date

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder.'

    @app.context_processor
    def inject_now():
        return {'now': datetime.now, 'today': date.today()}

    from app.models import Usuario
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.clientes import clientes_bp
    from app.routes.prestamos import prestamos_bp
    from app.routes.pagos import pagos_bp
    from app.routes.reportes import reportes_bp
    from app.routes.main import main_bp
    from app.routes.perfil import perfil_bp
    from app.routes.usuarios import usuarios_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(prestamos_bp)
    app.register_blueprint(pagos_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(usuarios_bp)

    return app
