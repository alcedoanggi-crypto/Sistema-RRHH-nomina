# Sistema de Recursos Humanos (RRHH) y Nómina

Aplicación web con **arquitectura MVC** desarrollada en **Python (Flask)** y **PostgreSQL**,
con vistas HTML + **Bootstrap 5**, gráficos con **Chart.js** y generación de recibos de pago en **PDF**.

## Capturas de pantalla

| Inicio de sesión | Tablero ejecutivo |
|---|---|
| ![Login](docs/screenshots/01-login.png) | ![Dashboard](docs/screenshots/02-dashboard.png) |

| Empleados | Nómina |
|---|---|
| ![Empleados](docs/screenshots/03-empleados.png) | ![Nómina](docs/screenshots/04-nomina.png) |

| Permisos y vacaciones | Control de asistencia |
|---|---|
| ![Permisos](docs/screenshots/05-permisos.png) | ![Asistencia](docs/screenshots/06-asistencias.png) |

## Funcionalidades

| # | Módulo | Descripción |
|---|--------|-------------|
| 1 | Autenticación con roles | `admin_rrhh`, `jefe_area`, `empleado` (Flask-Login) |
| 2 | Dashboard ejecutivo | KPIs + gráficos: empleados por departamento, rotación, gasto en nómina mensual, ausentismo |
| 3 | Control de asistencia | Marcaje entrada/salida, registro manual, reporte mensual con % de asistencia |
| 4 | Permisos y vacaciones | Flujo de aprobación: Pendiente → Jefe de área → RRHH |
| 5 | Nómina automática | Sueldo proporcional, bono de antigüedad, bonos manuales, deducción IESS; generación individual o masiva |
| 6 | Evaluaciones de desempeño | Formulario con 5 criterios (1–5), puntaje y calificación, comentario del empleado |
| 7 | Perfil de empleado | Datos, contratos y **documentos digitales** (contratos, certificados) |
| 8 | Recibos de pago PDF | Rol individual con la paleta corporativa (ReportLab) |

## Arquitectura MVC

```
sistema-rrhh-nomina/
├── run.py                     # punto de entrada
├── config.py                  # configuración (lee .env)
├── seed.py                    # crea tablas + datos demo
├── sql/schema.sql             # esquema PostgreSQL de referencia
└── app/
    ├── __init__.py            # application factory, blueprints, error handlers
    ├── extensions.py          # db, login_manager, migrate
    ├── models/                # MODELO  (SQLAlchemy)
    │   ├── usuario.py  departamento.py  cargo.py  empleado.py
    │   ├── contrato.py  asistencia.py  permiso.py
    │   ├── nomina.py  evaluacion.py  documento.py
    ├── controllers/           # CONTROLADOR  (blueprints / rutas)
    │   ├── auth_controller.py       dashboard_controller.py
    │   ├── empleado_controller.py   asistencia_controller.py
    │   ├── permiso_controller.py    nomina_controller.py
    │   └── evaluacion_controller.py
    ├── services/              # lógica de negocio
    │   ├── nomina_service.py   (cálculo de nómina)
    │   └── pdf_service.py      (recibos PDF)
    ├── utils/                 # decoradores de rol, manejo de archivos
    ├── templates/             # VISTA  (Jinja2 + Bootstrap 5)
    └── static/
        ├── css/style.css      # paleta corporativa con variables CSS
        └── uploads/           # fotos, contratos y documentos
```

### Paleta corporativa (variables CSS en `app/static/css/style.css`)

| Variable | Color |
|----------|-------|
| `--azul-marino` | `#1E3A5F` |
| `--gris-perla`  | `#E2E8F0` |
| `--verde`       | `#10B981` |
| `--blanco`      | `#FFFFFF` |

## Instalación

### 1. Requisitos
- Python 3.10+
- PostgreSQL 13+

### 2. Entorno virtual e instalación de dependencias

```powershell
cd C:\Users\Pc\sistema-rrhh-nomina
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configuración

```powershell
copy .env.example .env
# edita .env y ajusta SECRET_KEY y DATABASE_URL
```

`DATABASE_URL` por defecto:
```
postgresql://postgres:TU_PASSWORD@localhost:5432/rrhh_nomina
```

### 4. Crear la base de datos

**Opción A — con el script incluido (recomendada):**
```powershell
& "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -U postgres rrhh_nomina
python seed.py            # crea las tablas y carga datos de demostración
```

**Opción B — SQL manual:**
```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE rrhh_nomina;"
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d rrhh_nomina -f sql\schema.sql
```

**Opción C — Flask-Migrate:**
```powershell
$env:FLASK_APP="run.py"
flask db init
flask db migrate -m "esquema inicial"
flask db upgrade
```

### 5. Ejecutar

```powershell
python run.py
```
Abre http://localhost:5000

## Usuarios de demostración (tras `python seed.py`)

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `admin` | `admin123` | Administrador RRHH |
| `jefe` | `jefe123` | Jefe de Área |
| `empleado` | `empleado123` | Empleado |

## Notas sobre el cálculo de nómina

Los parámetros están en `config.py` (`APORTE_IESS_PERSONAL`, etc.) y la lógica en
`app/services/nomina_service.py`. Ajusta porcentajes, tabla de impuesto a la renta y
conceptos según la legislación laboral de tu país. El cálculo actual incluye:

- Sueldo proporcional a días trabajados (descuenta permisos **no remunerados** aprobados)
- Bono de antigüedad (2 % del sueldo por año, tope 20 %)
- Bonos manuales (al generar la nómina individual)
- Deducción de aporte personal IESS (9,45 %)
