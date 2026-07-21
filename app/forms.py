from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, TextAreaField,
                     DateField, DecimalField, IntegerField, HiddenField, SubmitField)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')


class ClienteForm(FlaskForm):
    nombre_completo = StringField('Nombre Completo', validators=[DataRequired(), Length(max=200)])
    tipo_documento = SelectField('Tipo Documento', choices=[('DNI', 'DNI'), ('CE', 'Carné de Extranjería'), ('RUC', 'RUC')])
    numero_documento = StringField('N° Documento', validators=[DataRequired(), Length(max=20)])
    fecha_nacimiento = DateField('Fecha de Nacimiento', format='%Y-%m-%d', validators=[Optional()])
    genero = SelectField('Género', choices=[('', 'Seleccione...'), ('M', 'Masculino'), ('F', 'Femenino')])
    estado_civil = SelectField('Estado Civil', choices=[('', 'Seleccione...'), ('Soltero', 'Soltero'), ('Casado', 'Casado'), ('Divorciado', 'Divorciado'), ('Viudo', 'Viudo')])
    telefono = StringField('Teléfono', validators=[Length(max=20)])
    celular = StringField('Celular', validators=[Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    direccion = TextAreaField('Dirección')
    distrito = StringField('Distrito', validators=[Length(max=100)])
    provincia = StringField('Provincia', validators=[Length(max=100)])
    departamento = StringField('Departamento', validators=[Length(max=100)])
    ocupacion = StringField('Ocupación', validators=[Length(max=150)])
    ingresos_mensuales = DecimalField('Ingresos Mensuales (Bs)', places=2, validators=[Optional()])
    referencia_nombre = StringField('Nombre Referencia', validators=[Length(max=150)])
    referencia_telefono = StringField('Teléfono Referencia', validators=[Length(max=20)])
    observaciones = TextAreaField('Observaciones')
    submit = SubmitField('Guardar')


class PrestamoForm(FlaskForm):
    cliente_id = SelectField('Cliente', coerce=int, validators=[DataRequired()])
    monto_solicitado = DecimalField('Monto Solicitado (Bs)', places=2, validators=[DataRequired(), NumberRange(min=1)])
    tasa_interes_id = SelectField('Tasa de Interés', coerce=int, validators=[DataRequired()])
    plazo_meses = IntegerField('Plazo (Meses)', validators=[DataRequired(), NumberRange(min=1, max=120)])
    metodo_amortizacion = SelectField('Método Amortización',
                                       choices=[('frances', 'Francés (Cuota Fija)'), ('alemán', 'Alemán (Amortización Constante)')])
    frecuencia_pago = SelectField('Frecuencia de Pago',
                                   choices=[('mensual', 'Mensual'), ('quincenal', 'Quincenal'), ('semanal', 'Semanal')])
    observaciones = TextAreaField('Observaciones')
    submit = SubmitField('Solicitar Préstamo')


class EvaluarPrestamoForm(FlaskForm):
    monto_aprobado = DecimalField('Monto Aprobado (Bs)', places=2, validators=[DataRequired(), NumberRange(min=1)])
    submit_aprobar = SubmitField('Aprobar Préstamo')
    motivo_rechazo = TextAreaField('Motivo de Rechazo')
    submit_rechazar = SubmitField('Rechazar Préstamo')


class PagoForm(FlaskForm):
    prestamo_id = SelectField('Préstamo', coerce=int, validators=[DataRequired()])
    monto_total = DecimalField('Monto Total (Bs)', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    metodo_pago = SelectField('Método de Pago',
                               choices=[('efectivo', 'Efectivo'), ('transferencia', 'Transferencia'),
                                        ('deposito', 'Depósito'), ('tarjeta', 'Tarjeta'), ('app', 'App Móvil')])
    numero_operacion = StringField('N° Operación', validators=[Length(max=100)])
    observaciones = TextAreaField('Observaciones')
    submit = SubmitField('Registrar Pago')


class TasaInteresForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    tipo_tasa = SelectField('Tipo Tasa', choices=[('mensual', 'Mensual'), ('anual', 'Anual'), ('diaria', 'Diaria')])
    valor = DecimalField('Valor (%)', places=4, validators=[DataRequired(), NumberRange(min=0.0001, max=99.9999)])
    fecha_inicio = DateField('Fecha Inicio', format='%Y-%m-%d', validators=[DataRequired()])
    fecha_fin = DateField('Fecha Fin', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Guardar')
