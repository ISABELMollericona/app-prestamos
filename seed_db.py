from app import create_app, db
from app.models import Rol, Usuario, TasaInteres
from datetime import date
from werkzeug.security import generate_password_hash

app = create_app('development')
app.app_context().push()

if not Usuario.query.filter_by(username='admin').first():
    roles = Rol.query.all()
    if not roles:
        roles_data = [
            Rol(nombre='administrador', descripcion='Acceso total'),
            Rol(nombre='gerente', descripcion='Aprueba prestamos'),
            Rol(nombre='asesor', descripcion='Gestiona clientes'),
            Rol(nombre='cajero', descripcion='Pagos y desembolsos')
        ]
        for r in roles_data:
            db.session.add(r)
        db.session.flush()

    admin_role = Rol.query.filter_by(nombre='administrador').first()
    if admin_role:
        admin = Usuario(
            nombre_completo='Admin Sistema',
            email='admin@micredit.com',
            username='admin',
            password_hash=generate_password_hash('admin123'),
            rol_id=admin_role.id
        )
        db.session.add(admin)
        print('Admin user created')

    if not TasaInteres.query.first():
        db.session.add(TasaInteres(
            nombre='Tasa Estandar',
            tipo_tasa='mensual',
            valor=0.03,
            fecha_inicio=date.today()
        ))
        print('Tasa created')
    db.session.commit()
else:
    print('Admin already exists')

u = Usuario.query.filter_by(username='admin').first()
if u:
    pw_ok = u.check_password('admin123')
    print(f'Admin: {u.nombre_completo}, pw ok: {pw_ok}')
