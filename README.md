# MiCredit - Sistema de Gestión de Microcréditos

Sistema web interactivo para la gestión integral de préstamos y créditos de una microempresa de microfinanzas. Construido con **Flask** + **SQL Server**.

## Funcionalidades

### Gestión de Clientes
- Registro, edición y consulta de clientes
- Historial crediticio por cliente

### Gestión de Préstamos
- Solicitud de préstamo con selección de tasa y método de amortización
- Flujo de evaluación → aprobación/rechazo → desembolso
- **Generación automática de tabla de amortización** al desembolsar
- Cronograma de pagos descargable en PDF
- Simulador interactivo de préstamos

### Gestión de Pagos
- Registro de pagos con selección visual de cuotas
- **Cálculo automático de mora** según días de atraso (0.5% diario)
- Voucher de pago descargable en PDF
- Actualización automática del saldo pendiente

### Automatización (APScheduler)
- **Actualización diaria de mora** a las 00:05
- **Castigo automático** de préstamos con +30 días de mora a las 00:10
- **Recordatorios de pago** a las 08:00 (3 días antes del vencimiento)

### Reportes
- Dashboard con indicadores clave
- Gráficos de cartera y morosidad (Chart.js)
- Reporte de cartera de créditos
- API de estadísticas

### Seguridad
- Autenticación por roles (administrador, gerente, asesor, cajero)
- Protección CSRF
- Permisos por endpoint
- Contraseñas hasheadas con Werkzeug

## Flujo de Trabajo

```
Cliente → Solicitud → Evaluación → Aprobación → Desembolso → 
           (automático: genera amortización y cronograma)
           → Activo → Pagos → Cierre
```

## Requisitos

- Python 3.9+
- SQL Server (2016+) con ODBC Driver 17
- Pip

## Instalación

### 1. Clonar el repositorio

```bash
cd PRESTAMOS
```

### 2. Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos SQL Server

Ejecutar el script SQL en SQL Server Management Studio:

```bash
sqlcmd -S SERVIDOR -U sa -P password -i database\schema.sql
```

O abrir `database/schema.sql` en SSMS y ejecutarlo.

### 5. Configurar variables de entorno

Crear archivo `.env` basado en `.env.example`:

```
SECRET_KEY=clave_segura_aqui
SQLALCHEMY_DATABASE_URI=mssql+pyodbc://sa:Password123@localhost/GestionPrestamos?driver=ODBC+Driver+17+for+SQL+Server
FLASK_APP=run.py
FLASK_ENV=development
```

### 6. Inicializar la base de datos

```bash
python manage.py init-db
```

Esto crea:
- 4 roles (administrador, gerente, asesor, cajero)
- Usuario admin: **admin** / contraseña: **admin123**
- Tasa de interés por defecto (3% mensual)

### 7. Ejecutar

```bash
python manage.py run
```

O directamente:

```bash
python run.py
```

Servidor en: http://localhost:5000

### 8. Crear usuarios (opcional)

```bash
python manage.py create-user
```

## Estructura del Proyecto

```
PRESTAMOS/
├── app/                    # Aplicación Flask
│   ├── __init__.py         # Factory pattern
│   ├── models.py           # SQLAlchemy models
│   ├── forms.py            # WTForms
│   ├── amortization.py     # Motor financiero
│   ├── documents.py        # Generación PDF
│   ├── scheduler.py        # Tareas automáticas
│   ├── routes/             # Blueprints
│   │   ├── auth.py         # Autenticación
│   │   ├── main.py         # Dashboard
│   │   ├── clientes.py     # CRUD clientes
│   │   ├── prestamos.py    # Ciclo de préstamos
│   │   ├── pagos.py        # Pagos
│   │   └── reportes.py     # Estadísticas
│   ├── templates/          # Jinja2 templates
│   └── static/             # Archivos estáticos
├── database/
│   └── schema.sql          # Esquema SQL Server completo
├── config.py               # Configuración
├── run.py                  # Punto de entrada
├── manage.py               # Script de gestión
├── requirements.txt
└── README.md
```

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/pagos/cuotas/<id>` | JSON con cuotas pendientes de un préstamo |
| GET | `/reportes/api/estadisticas` | JSON con estadísticas de préstamos y pagos |
| GET | `/reportes/api/morosidad` | JSON con distribución de morosidad |

## Roles y Permisos

| Rol | Acciones |
|-----|----------|
| **Administrador** | Acceso total + gestión de usuarios/tasas |
| **Gerente** | Aprueba/rechaza préstamos + reportes |
| **Asesor** | Gestiona clientes y solicitudes |
| **Cajero** | Registra pagos y desembolsos |

## Personalización

- **Tasas de interés**: Configurables desde la interfaz administrativa
- **Métodos de amortización**: Francés (cuota fija) y Alemán (amortización constante)
- **Frecuencia de pago**: Mensual, quincenal, semanal
