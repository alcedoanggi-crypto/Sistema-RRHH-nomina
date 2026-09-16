-- ============================================================
--  Sistema de Recursos Humanos y Nómina — Esquema PostgreSQL
--  Ejecutar sobre una base de datos vacía llamada rrhh_nomina
--  (Flask-Migrate / db.create_all() también pueden crear esto)
-- ============================================================

-- ---------- Tipos enumerados ----------
DO $$ BEGIN
  CREATE TYPE rolenum AS ENUM ('ADMIN_RRHH', 'JEFE_AREA', 'EMPLEADO');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE tipocontratoenum AS ENUM ('INDEFINIDO','PLAZO_FIJO','EVENTUAL','PASANTIA','SERVICIOS');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE estadocontratoenum AS ENUM ('ACTIVO','FINALIZADO','SUSPENDIDO');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE tipopermisoenum AS ENUM ('VACACIONES','MEDICO','PERSONAL','MATERNIDAD','CALAMIDAD','NO_REMUNERADO');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE estadosolicitudenum AS ENUM ('PENDIENTE','APROBADO_JEFE','APROBADO','RECHAZADO','CANCELADO');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---------- Tablas base ----------
CREATE TABLE IF NOT EXISTS departamentos (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(120) UNIQUE NOT NULL,
    descripcion  VARCHAR(255),
    jefe_id      INTEGER
);

CREATE TABLE IF NOT EXISTS cargos (
    id             SERIAL PRIMARY KEY,
    nombre         VARCHAR(120) NOT NULL,
    descripcion    VARCHAR(255),
    salario_base   NUMERIC(10,2) NOT NULL DEFAULT 0,
    departamento_id INTEGER NOT NULL REFERENCES departamentos(id),
    CONSTRAINT uq_cargo_departamento UNIQUE (nombre, departamento_id)
);

CREATE TABLE IF NOT EXISTS empleados (
    id                SERIAL PRIMARY KEY,
    cedula            VARCHAR(20) UNIQUE NOT NULL,
    nombres           VARCHAR(120) NOT NULL,
    apellidos         VARCHAR(120) NOT NULL,
    fecha_nacimiento  DATE,
    genero            VARCHAR(20),
    telefono          VARCHAR(30),
    email             VARCHAR(120),
    direccion         VARCHAR(255),
    foto              VARCHAR(255),
    fecha_ingreso     DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_salida      DATE,
    activo            BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en         TIMESTAMP DEFAULT NOW(),
    departamento_id   INTEGER REFERENCES departamentos(id),
    cargo_id          INTEGER REFERENCES cargos(id)
);

ALTER TABLE departamentos
    ADD CONSTRAINT fk_departamento_jefe FOREIGN KEY (jefe_id) REFERENCES empleados(id);

CREATE TABLE IF NOT EXISTS usuarios (
    id             SERIAL PRIMARY KEY,
    username       VARCHAR(80) UNIQUE NOT NULL,
    email          VARCHAR(120) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    rol            rolenum NOT NULL DEFAULT 'EMPLEADO',
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en      TIMESTAMP DEFAULT NOW(),
    empleado_id    INTEGER UNIQUE REFERENCES empleados(id)
);

CREATE TABLE IF NOT EXISTS contratos (
    id             SERIAL PRIMARY KEY,
    empleado_id    INTEGER NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    tipo           tipocontratoenum NOT NULL DEFAULT 'INDEFINIDO',
    estado         estadocontratoenum NOT NULL DEFAULT 'ACTIVO',
    fecha_inicio   DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_fin      DATE,
    salario        NUMERIC(10,2) NOT NULL DEFAULT 0,
    jornada_horas  INTEGER DEFAULT 160,
    archivo        VARCHAR(255),
    observaciones  TEXT
);

CREATE TABLE IF NOT EXISTS asistencias (
    id            SERIAL PRIMARY KEY,
    empleado_id   INTEGER NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    fecha         DATE NOT NULL DEFAULT CURRENT_DATE,
    hora_entrada  TIMESTAMP,
    hora_salida   TIMESTAMP,
    observacion   VARCHAR(255),
    estado        VARCHAR(20) DEFAULT 'presente',
    CONSTRAINT uq_asistencia_empleado_fecha UNIQUE (empleado_id, fecha)
);
CREATE INDEX IF NOT EXISTS ix_asistencias_fecha ON asistencias(fecha);

CREATE TABLE IF NOT EXISTS permisos (
    id                    SERIAL PRIMARY KEY,
    empleado_id           INTEGER NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    tipo                  tipopermisoenum NOT NULL,
    fecha_inicio          DATE NOT NULL,
    fecha_fin             DATE NOT NULL,
    motivo                TEXT NOT NULL,
    adjunto               VARCHAR(255),
    estado                estadosolicitudenum NOT NULL DEFAULT 'PENDIENTE',
    solicitado_en         TIMESTAMP DEFAULT NOW(),
    aprobado_jefe_id      INTEGER REFERENCES empleados(id),
    aprobado_rrhh_id      INTEGER REFERENCES usuarios(id),
    comentario_aprobacion VARCHAR(255),
    resuelto_en           TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nominas (
    id                SERIAL PRIMARY KEY,
    empleado_id       INTEGER NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    anio              INTEGER NOT NULL,
    mes               INTEGER NOT NULL,
    salario_base      NUMERIC(10,2) NOT NULL DEFAULT 0,
    dias_trabajados   INTEGER DEFAULT 30,
    total_ingresos    NUMERIC(10,2) NOT NULL DEFAULT 0,
    total_deducciones NUMERIC(10,2) NOT NULL DEFAULT 0,
    neto_pagar        NUMERIC(10,2) NOT NULL DEFAULT 0,
    estado            VARCHAR(20) DEFAULT 'generada',
    generada_en       TIMESTAMP DEFAULT NOW(),
    pagada_en         TIMESTAMP,
    CONSTRAINT uq_nomina_periodo UNIQUE (empleado_id, anio, mes)
);

CREATE TABLE IF NOT EXISTS detalle_nomina (
    id         SERIAL PRIMARY KEY,
    nomina_id  INTEGER NOT NULL REFERENCES nominas(id) ON DELETE CASCADE,
    concepto   VARCHAR(120) NOT NULL,
    tipo       VARCHAR(20) NOT NULL,          -- ingreso | deduccion
    monto      NUMERIC(10,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS evaluaciones (
    id                 SERIAL PRIMARY KEY,
    empleado_id        INTEGER NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    evaluador_id       INTEGER REFERENCES empleados(id),
    periodo            VARCHAR(30) NOT NULL,
    fecha              DATE NOT NULL DEFAULT CURRENT_DATE,
    productividad      INTEGER DEFAULT 3,
    calidad_trabajo    INTEGER DEFAULT 3,
    trabajo_equipo     INTEGER DEFAULT 3,
    puntualidad        INTEGER DEFAULT 3,
    iniciativa         INTEGER DEFAULT 3,
    fortalezas         TEXT,
    areas_mejora       TEXT,
    comentario_empleado TEXT,
    creada_en          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documentos (
    id           SERIAL PRIMARY KEY,
    empleado_id  INTEGER NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    nombre       VARCHAR(150) NOT NULL,
    tipo         VARCHAR(50),
    archivo      VARCHAR(255) NOT NULL,
    subido_en    TIMESTAMP DEFAULT NOW()
);
