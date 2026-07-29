from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    usuarios = db.relationship('Usuario', backref='rol', lazy=True)

    def __repr__(self):
        return self.nombre


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_completo = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    ultimo_acceso = db.Column(db.DateTime)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return self.rol and self.rol.nombre == role_name

    def has_any_role(self, *roles):
        return self.rol and self.rol.nombre in roles

    def __repr__(self):
        return f'{self.nombre_completo} ({self.username})'


class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_cliente = db.Column(db.String(20), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(200), nullable=False)
    tipo_documento = db.Column(db.String(20), default='DNI')
    numero_documento = db.Column(db.String(20), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date)
    genero = db.Column(db.String(1))
    estado_civil = db.Column(db.String(20))
    telefono = db.Column(db.String(20))
    celular = db.Column(db.String(20))
    email = db.Column(db.String(100))
    direccion = db.Column(db.Text)
    distrito = db.Column(db.String(100))
    provincia = db.Column(db.String(100))
    departamento = db.Column(db.String(100))
    ocupacion = db.Column(db.String(150))
    ingresos_mensuales = db.Column(db.Numeric(12, 2), default=0)
    referencia_nombre = db.Column(db.String(150))
    referencia_telefono = db.Column(db.String(20))
    latitud = db.Column(db.Numeric(10, 7), nullable=True)
    longitud = db.Column(db.Numeric(10, 7), nullable=True)
    foto = db.Column(db.Text, nullable=True)
    observaciones = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)

    prestamos = db.relationship('Prestamo', backref='cliente', lazy=True)
    pagos = db.relationship('Pago', backref='cliente', lazy=True)

    def __repr__(self):
        return f'{self.nombre_completo} ({self.numero_documento})'


class TasaInteres(db.Model):
    __tablename__ = 'tasas_interes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo_tasa = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Numeric(5, 4), nullable=False)
    tipo_moneda = db.Column(db.String(10), default='BOB')
    activo = db.Column(db.Boolean, default=True)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    usuario_creo = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'{self.nombre} ({self.valor * 100}%)'


class Prestamo(db.Model):
    __tablename__ = 'prestamos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_prestamo = db.Column(db.String(20), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    monto_solicitado = db.Column(db.Numeric(12, 2), nullable=False)
    monto_aprobado = db.Column(db.Numeric(12, 2))
    tasa_interes_id = db.Column(db.Integer, db.ForeignKey('tasas_interes.id'))
    tasa_interes_valor = db.Column(db.Numeric(5, 4))
    tipo_tasa = db.Column(db.String(20))
    plazo_meses = db.Column(db.Integer, nullable=False)
    tipo_garantia = db.Column(db.String(30), default='personal')
    metodo_amortizacion = db.Column(db.String(30), default='frances')
    frecuencia_pago = db.Column(db.String(20), default='mensual')
    monto_cuota = db.Column(db.Numeric(12, 2))
    total_interes = db.Column(db.Numeric(12, 2))
    total_a_pagar = db.Column(db.Numeric(12, 2))
    saldo_pendiente = db.Column(db.Numeric(12, 2))
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_aprobacion = db.Column(db.DateTime)
    fecha_desembolso = db.Column(db.DateTime)
    fecha_vencimiento = db.Column(db.Date)
    estado = db.Column(db.String(30), default='pendiente')
    usuario_solicito = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario_aprobo = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    motivo_rechazo = db.Column(db.String(500))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)

    amortizaciones = db.relationship('Amortizacion', backref='prestamo', lazy=True,
                                      order_by='Amortizacion.numero_cuota')
    pagos = db.relationship('Pago', backref='prestamo', lazy=True)
    documentos = db.relationship('DocumentoPrestamo', backref='prestamo', lazy=True)
    historial_estados = db.relationship('HistorialEstado', backref='prestamo', lazy=True,
                                         order_by='HistorialEstado.fecha_cambio.desc()')

    @property
    def cuotas_pagadas(self):
        return sum(1 for a in self.amortizaciones if a.estado == 'pagada')

    @property
    def cuotas_pendientes(self):
        return sum(1 for a in self.amortizaciones if a.estado == 'pendiente')

    @property
    def progreso_pct(self):
        total = len(self.amortizaciones)
        if total == 0:
            return 0
        return round(self.cuotas_pagadas / total * 100, 1)

    def __repr__(self):
        return f'{self.codigo_prestamo} - {self.cliente.nombre_completo}'


class Amortizacion(db.Model):
    __tablename__ = 'amortizacion'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prestamo_id = db.Column(db.Integer, db.ForeignKey('prestamos.id'), nullable=False)
    numero_cuota = db.Column(db.Integer, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    saldo_inicial = db.Column(db.Numeric(12, 2))
    monto_cuota = db.Column(db.Numeric(12, 2))
    interes = db.Column(db.Numeric(12, 2))
    amortizacion = db.Column(db.Numeric(12, 2))
    saldo_final = db.Column(db.Numeric(12, 2))
    seguro_desgravamen = db.Column(db.Numeric(12, 2), default=0)
    seguro_bien = db.Column(db.Numeric(12, 2), default=0)
    total_cuota = db.Column(db.Numeric(12, 2))
    dias_atraso = db.Column(db.Integer, default=0)
    mora = db.Column(db.Numeric(12, 2), default=0)
    estado = db.Column(db.String(30), default='pendiente')
    fecha_pago = db.Column(db.DateTime)
    pago_id = db.Column(db.Integer, db.ForeignKey('pagos.id'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    pago = db.relationship('Pago', backref='cuotas_pagadas_ref', foreign_keys=[pago_id])

    def __repr__(self):
        return f'Cuota #{self.numero_cuota} - {self.estado}'


class Pago(db.Model):
    __tablename__ = 'pagos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_pago = db.Column(db.String(20), unique=True, nullable=False)
    prestamo_id = db.Column(db.Integer, db.ForeignKey('prestamos.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    monto_total = db.Column(db.Numeric(12, 2), nullable=False)
    monto_cuota = db.Column(db.Numeric(12, 2))
    monto_mora = db.Column(db.Numeric(12, 2), default=0)
    monto_interes = db.Column(db.Numeric(12, 2), default=0)
    monto_amortizacion = db.Column(db.Numeric(12, 2), default=0)
    monto_seguro = db.Column(db.Numeric(12, 2), default=0)
    cuotas_pagadas = db.Column(db.Integer, default=1)
    fecha_pago = db.Column(db.DateTime, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    metodo_pago = db.Column(db.String(30), default='efectivo')
    numero_operacion = db.Column(db.String(100))
    usuario_registro = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    estado = db.Column(db.String(20), default='confirmado')

    usuario = db.relationship('Usuario', backref='pagos_registrados', foreign_keys=[usuario_registro])

    def __repr__(self):
        return f'{self.codigo_pago} - Bs/{self.monto_total}'


class DocumentoPrestamo(db.Model):
    __tablename__ = 'documentos_prestamo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prestamo_id = db.Column(db.Integer, db.ForeignKey('prestamos.id'), nullable=False)
    tipo_documento = db.Column(db.String(50), nullable=False)
    nombre_archivo = db.Column(db.String(255))
    contenido = db.Column(db.LargeBinary)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_genero = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    def __repr__(self):
        return f'{self.tipo_documento} - {self.prestamo.codigo_prestamo}'


class HistorialEstado(db.Model):
    __tablename__ = 'historial_estados'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prestamo_id = db.Column(db.Integer, db.ForeignKey('prestamos.id'), nullable=False)
    estado_anterior = db.Column(db.String(30))
    estado_nuevo = db.Column(db.String(30), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    fecha_cambio = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref='cambios_estado', foreign_keys=[usuario_id])

    def __repr__(self):
        return f'{self.estado_anterior} -> {self.estado_nuevo}'


class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo = db.Column(db.String(30), nullable=False)
    destino = db.Column(db.String(100))
    mensaje = db.Column(db.Text)
    prestamo_id = db.Column(db.Integer, db.ForeignKey('prestamos.id'))
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    leido = db.Column(db.Boolean, default=False)
    fecha_envio = db.Column(db.DateTime)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
