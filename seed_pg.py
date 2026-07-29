from app import create_app, db
from app.models import Rol, Usuario, TasaInteres
from datetime import date
from werkzeug.security import generate_password_hash

app = create_app('development')
app.app_context().push()
db.create_all()

roles = [
    Rol(nombre='administrador', descripcion='Acceso total'),
    Rol(nombre='gerente', descripcion='Aprueba prestamos'),
    Rol(nombre='asesor', descripcion='Gestiona clientes'),
    Rol(nombre='cajero', descripcion='Pagos y desembolsos')
]
for r in roles:
    if not Rol.query.filter_by(nombre=r.nombre).first():
        db.session.add(r)
        print(f'Rol created: {r.nombre}')
db.session.flush()

admin_role = Rol.query.filter_by(nombre='administrador').first()
if not Usuario.query.filter_by(username='admin').first():
    admin = Usuario(
        nombre_completo='Admin Sistema',
        email='admin@micredit.com',
        username='admin',
        password_hash=generate_password_hash('admin123'),
        rol_id=admin_role.id
    )
    db.session.add(admin)
    print('Admin created')
else:
    u = Usuario.query.filter_by(username='admin').first()
    print(f'Admin exists: {u.nombre_completo}, pw ok: {u.check_password("admin123")}')

if not TasaInteres.query.first():
    db.session.add(TasaInteres(nombre='Tasa Estandar', tipo_tasa='mensual', valor=0.03, fecha_inicio=date.today()))
    print('Tasa created')

db.session.commit()
print('Done')
