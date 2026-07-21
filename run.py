from app import create_app, db
from app.models import Rol, Usuario, TasaInteres
from app.scheduler import iniciar_scheduler
from datetime import date

app = create_app('development')


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Rol': Rol,
        'Usuario': Usuario,
        'TasaInteres': TasaInteres
    }


@app.cli.command('init-db')
def init_db():
    """Inicializar la base de datos con datos básicos"""
    from werkzeug.security import generate_password_hash

    roles = [
        Rol(nombre='administrador', descripcion='Acceso total al sistema'),
        Rol(nombre='gerente', descripcion='Aprueba préstamos y genera reportes'),
        Rol(nombre='asesor', descripcion='Gestiona clientes y solicitudes'),
        Rol(nombre='cajero', descripcion='Registra pagos y desembolsos'),
    ]

    for rol in roles:
        existing = Rol.query.filter_by(nombre=rol.nombre).first()
        if not existing:
            db.session.add(rol)

    admin = Usuario(
        nombre_completo='Administrador del Sistema',
        email='admin@micredit.com',
        username='admin',
        password_hash=generate_password_hash('admin123'),
        rol_id=1
    )

    if not Usuario.query.filter_by(username='admin').first():
        db.session.add(admin)

    if not TasaInteres.query.first():
        tasa = TasaInteres(
            nombre='Tasa Microcrédito Estándar',
            tipo_tasa='mensual',
            valor=0.03,
            fecha_inicio=date.today()
        )
        db.session.add(tasa)

    db.session.commit()
    print('Base de datos inicializada correctamente.')
    print('Usuario: admin / Contraseña: admin123')


@app.cli.command('create-user')
def create_user():
    """Crear un nuevo usuario interactivamente"""
    username = input('Username: ')
    nombre = input('Nombre completo: ')
    email = input('Email: ')
    password = input('Password: ')

    print('Roles disponibles:')
    roles = Rol.query.all()
    for r in roles:
        print(f'  {r.id}: {r.nombre}')

    rol_id = int(input('Rol ID: '))

    user = Usuario(
        username=username,
        nombre_completo=nombre,
        email=email,
        rol_id=rol_id
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f'Usuario {username} creado exitosamente.')


if __name__ == '__main__':
    with app.app_context():
        from app import db
        db.create_all()
        try:
            iniciar_scheduler(app)
        except Exception as e:
            print(f'Scheduler no disponible: {e}')

    app.run(host='0.0.0.0', port=5000, debug=True)
