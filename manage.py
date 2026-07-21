"""
Script de gestión del sistema
Uso: python manage.py [comando]

Comandos:
  init-db      Inicializar base de datos con datos básicos
  create-user  Crear un usuario interactivamente
  run          Iniciar servidor de desarrollo
  shell        Abrir shell interactiva con contexto
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Rol, Usuario, TasaInteres
from app.scheduler import iniciar_scheduler
from datetime import date

app = create_app('development')


def cmd_init_db():
    with app.app_context():
        from werkzeug.security import generate_password_hash

        roles_data = [
            ('administrador', 'Acceso total al sistema'),
            ('gerente', 'Aprueba préstamos y genera reportes'),
            ('asesor', 'Gestiona clientes y solicitudes'),
            ('cajero', 'Registra pagos y desembolsos'),
        ]

        for nombre, desc in roles_data:
            if not Rol.query.filter_by(nombre=nombre).first():
                db.session.add(Rol(nombre=nombre, descripcion=desc))
                print(f'Rol creado: {nombre}')

        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(
                nombre_completo='Administrador del Sistema',
                email='admin@micredit.com',
                username='admin',
                password_hash=generate_password_hash('admin123'),
                rol_id=1
            )
            db.session.add(admin)
            print('Usuario admin creado (admin/admin123)')

        if not TasaInteres.query.first():
            db.session.add(TasaInteres(
                nombre='Tasa Microcrédito Estándar',
                tipo_tasa='mensual',
                valor=0.03,
                fecha_inicio=date.today()
            ))
            print('Tasa de interés por defecto creada.')

        db.session.commit()
        print('Base de datos inicializada correctamente.')


def cmd_create_user():
    with app.app_context():
        username = input('Username: ').strip()
        nombre = input('Nombre completo: ').strip()
        email = input('Email: ').strip()
        password = input('Password: ').strip()

        roles = Rol.query.all()
        print('Roles:')
        for r in roles:
            print(f'  [{r.id}] {r.nombre}')

        rol_id = int(input('Rol ID: ').strip())

        user = Usuario(
            username=username,
            nombre_completo=nombre,
            email=email,
            rol_id=rol_id
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'Usuario {username} creado.')


def cmd_run():
    with app.app_context():
        db.create_all()
        try:
            iniciar_scheduler(app)
            print('Tareas automáticas iniciadas (mora, recordatorios)')
        except Exception as e:
            print(f'Scheduler: {e}')
    app.run(host='0.0.0.0', port=5000, debug=True)


def cmd_shell():
    with app.app_context():
        import code
        code.interact(local={
            'app': app,
            'db': db,
            'Rol': Rol,
            'Usuario': Usuario,
            'TasaInteres': TasaInteres
        })


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    commands = {
        'init-db': cmd_init_db,
        'create-user': cmd_create_user,
        'run': cmd_run,
        'shell': cmd_shell,
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f'Comando desconocido: {cmd}')
        sys.exit(1)
