-- ============================================================
-- SISTEMA DE GESTIÓN DE PRÉSTAMOS Y CRÉDITOS
-- Base de datos: neondb
-- Motor: PostgreSQL (Neon)
-- ============================================================

-- ============================================================
-- TABLAS PRINCIPALES
-- ============================================================

-- Roles de usuario
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usuarios del sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INTEGER NOT NULL REFERENCES roles(id),
    activo BOOLEAN DEFAULT TRUE,
    ultimo_acceso TIMESTAMP,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clientes / Prestatarios
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    codigo_cliente VARCHAR(20) NOT NULL UNIQUE,
    nombre_completo VARCHAR(200) NOT NULL,
    tipo_documento VARCHAR(20) DEFAULT 'DNI',
    numero_documento VARCHAR(20) NOT NULL UNIQUE,
    fecha_nacimiento DATE,
    genero CHAR(1),
    estado_civil VARCHAR(20),
    telefono VARCHAR(20),
    celular VARCHAR(20),
    email VARCHAR(100),
    direccion TEXT,
    distrito VARCHAR(100),
    provincia VARCHAR(100),
    departamento VARCHAR(100),
    ocupacion VARCHAR(150),
    ingresos_mensuales DECIMAL(12,2) DEFAULT 0,
    referencia_nombre VARCHAR(150),
    referencia_telefono VARCHAR(20),
    latitud DECIMAL(10,7),
    longitud DECIMAL(10,7),
    foto TEXT,
    observaciones TEXT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasas de interés configurables
CREATE TABLE IF NOT EXISTS tasas_interes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo_tasa VARCHAR(20) NOT NULL CHECK (tipo_tasa IN ('mensual', 'anual', 'diaria')),
    valor DECIMAL(5,4) NOT NULL,
    tipo_moneda VARCHAR(10) DEFAULT 'BOB',
    activo BOOLEAN DEFAULT TRUE,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    usuario_creo INTEGER REFERENCES usuarios(id),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Préstamos
CREATE TABLE IF NOT EXISTS prestamos (
    id SERIAL PRIMARY KEY,
    codigo_prestamo VARCHAR(20) NOT NULL UNIQUE,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    monto_solicitado DECIMAL(12,2) NOT NULL,
    monto_aprobado DECIMAL(12,2),
    tasa_interes_id INTEGER REFERENCES tasas_interes(id),
    tasa_interes_valor DECIMAL(5,4),
    tipo_tasa VARCHAR(20) CHECK (tipo_tasa IN ('mensual', 'anual', 'diaria')),
    plazo_meses INTEGER NOT NULL,
    tipo_garantia VARCHAR(30) DEFAULT 'personal',
    metodo_amortizacion VARCHAR(30) DEFAULT 'frances' CHECK (metodo_amortizacion IN ('frances', 'alemán', 'americano')),
    frecuencia_pago VARCHAR(20) DEFAULT 'mensual' CHECK (frecuencia_pago IN ('mensual', 'quincenal', 'semanal')),
    monto_cuota DECIMAL(12,2),
    total_interes DECIMAL(12,2),
    total_a_pagar DECIMAL(12,2),
    saldo_pendiente DECIMAL(12,2),
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_aprobacion TIMESTAMP,
    fecha_desembolso TIMESTAMP,
    fecha_vencimiento DATE,
    estado VARCHAR(30) DEFAULT 'pendiente' CHECK (estado IN ('pendiente','evaluacion','aprobado','rechazado','desembolsado','activo','reprogramado','cerrado','castigado')),
    usuario_solicito INTEGER REFERENCES usuarios(id),
    usuario_aprobo INTEGER REFERENCES usuarios(id),
    observaciones TEXT,
    motivo_rechazo VARCHAR(500),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documentos de préstamo
CREATE TABLE IF NOT EXISTS documentos_prestamo (
    id SERIAL PRIMARY KEY,
    prestamo_id INTEGER NOT NULL REFERENCES prestamos(id),
    tipo_documento VARCHAR(50) NOT NULL,
    nombre_archivo VARCHAR(255),
    contenido BYTEA,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_genero INTEGER REFERENCES usuarios(id)
);

-- Tabla de amortización (detalle de cuotas)
CREATE TABLE IF NOT EXISTS amortizacion (
    id SERIAL PRIMARY KEY,
    prestamo_id INTEGER NOT NULL REFERENCES prestamos(id),
    numero_cuota INTEGER NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    saldo_inicial DECIMAL(12,2),
    monto_cuota DECIMAL(12,2),
    interes DECIMAL(12,2),
    amortizacion DECIMAL(12,2),
    saldo_final DECIMAL(12,2),
    seguro_desgravamen DECIMAL(12,2) DEFAULT 0,
    seguro_bien DECIMAL(12,2) DEFAULT 0,
    total_cuota DECIMAL(12,2),
    dias_atraso INTEGER DEFAULT 0,
    mora DECIMAL(12,2) DEFAULT 0,
    estado VARCHAR(30) DEFAULT 'pendiente' CHECK (estado IN ('pendiente','pagada','vencida','castigada')),
    fecha_pago TIMESTAMP,
    pago_id INTEGER,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT UQ_prestamo_cuota UNIQUE (prestamo_id, numero_cuota)
);

-- Pagos recibidos
CREATE TABLE IF NOT EXISTS pagos (
    id SERIAL PRIMARY KEY,
    codigo_pago VARCHAR(20) NOT NULL UNIQUE,
    prestamo_id INTEGER NOT NULL REFERENCES prestamos(id),
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    monto_total DECIMAL(12,2) NOT NULL,
    monto_cuota DECIMAL(12,2),
    monto_mora DECIMAL(12,2) DEFAULT 0,
    monto_interes DECIMAL(12,2) DEFAULT 0,
    monto_amortizacion DECIMAL(12,2) DEFAULT 0,
    monto_seguro DECIMAL(12,2) DEFAULT 0,
    cuotas_pagadas INTEGER DEFAULT 1,
    fecha_pago TIMESTAMP NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metodo_pago VARCHAR(30) DEFAULT 'efectivo' CHECK (metodo_pago IN ('efectivo','transferencia','deposito','tarjeta','app')),
    numero_operacion VARCHAR(100),
    usuario_registro INTEGER REFERENCES usuarios(id),
    observaciones TEXT,
    estado VARCHAR(20) DEFAULT 'confirmado' CHECK (estado IN ('pendiente','confirmado','anulado'))
);

-- Agregar FK de amortizacion -> pagos
ALTER TABLE amortizacion ADD CONSTRAINT FK_amortizacion_pago
    FOREIGN KEY (pago_id) REFERENCES pagos(id);

-- Historial de cambios de estado
CREATE TABLE IF NOT EXISTS historial_estados (
    id SERIAL PRIMARY KEY,
    prestamo_id INTEGER NOT NULL REFERENCES prestamos(id),
    estado_anterior VARCHAR(30),
    estado_nuevo VARCHAR(30) NOT NULL,
    usuario_id INTEGER REFERENCES usuarios(id),
    observaciones TEXT,
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notificaciones / Recordatorios
CREATE TABLE IF NOT EXISTS notificaciones (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('recordatorio','alerta','notificacion')),
    destino VARCHAR(100),
    mensaje TEXT,
    prestamo_id INTEGER REFERENCES prestamos(id),
    cliente_id INTEGER REFERENCES clientes(id),
    leido BOOLEAN DEFAULT FALSE,
    fecha_envio TIMESTAMP,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX IF NOT EXISTS IX_clientes_documento ON clientes(numero_documento);
CREATE INDEX IF NOT EXISTS IX_prestamos_cliente ON prestamos(cliente_id);
CREATE INDEX IF NOT EXISTS IX_prestamos_estado ON prestamos(estado);
CREATE INDEX IF NOT EXISTS IX_amortizacion_prestamo ON amortizacion(prestamo_id);
CREATE INDEX IF NOT EXISTS IX_amortizacion_estado ON amortizacion(estado);
CREATE INDEX IF NOT EXISTS IX_pagos_prestamo ON pagos(prestamo_id);
CREATE INDEX IF NOT EXISTS IX_pagos_fecha ON pagos(fecha_pago);

-- ============================================================
-- VISTAS
-- ============================================================

CREATE OR REPLACE VIEW vw_resumen_prestamos_activos AS
SELECT
    p.id,
    p.codigo_prestamo,
    c.nombre_completo AS cliente,
    c.numero_documento,
    p.monto_aprobado,
    p.saldo_pendiente,
    p.tasa_interes_valor,
    p.plazo_meses,
    p.monto_cuota,
    p.fecha_desembolso,
    p.fecha_vencimiento::DATE,
    EXTRACT(DAY FROM CURRENT_DATE - p.fecha_vencimiento)::INTEGER AS dias_vencidos,
    (SELECT COUNT(*) FROM amortizacion a WHERE a.prestamo_id = p.id AND a.estado = 'pendiente') AS cuotas_pendientes,
    (SELECT COUNT(*) FROM amortizacion a WHERE a.prestamo_id = p.id AND a.estado = 'pagada') AS cuotas_pagadas
FROM prestamos p
INNER JOIN clientes c ON p.cliente_id = c.id
WHERE p.estado IN ('activo', 'reprogramado');

-- Cartera morosa
CREATE OR REPLACE VIEW vw_cartera_morosa AS
SELECT
    p.id,
    p.codigo_prestamo,
    c.nombre_completo AS cliente,
    c.telefono,
    c.celular,
    p.monto_aprobado,
    p.saldo_pendiente,
    p.monto_cuota,
    EXTRACT(DAY FROM CURRENT_DATE - a.fecha_vencimiento)::INTEGER AS dias_mora,
    a.monto_cuota AS cuota_vencida,
    a.mora,
    a.fecha_vencimiento,
    EXTRACT(DAY FROM CURRENT_DATE - a.fecha_vencimiento) * p.monto_cuota * 0.005 AS mora_calculada
FROM prestamos p
INNER JOIN clientes c ON p.cliente_id = c.id
INNER JOIN amortizacion a ON a.prestamo_id = p.id
WHERE p.estado IN ('activo', 'reprogramado')
  AND a.estado = 'pendiente'
  AND a.fecha_vencimiento < CURRENT_DATE;

-- ============================================================
-- FUNCIONES
-- ============================================================

CREATE OR REPLACE FUNCTION fn_calcular_interes_frances(
    p_monto DECIMAL(12,2),
    p_tasa DECIMAL(5,4),
    p_plazo INTEGER
)
RETURNS DECIMAL(12,2)
LANGUAGE plpgsql AS $$
DECLARE
    v_cuota DECIMAL(12,2);
    v_tasa_mensual DECIMAL(10,6);
BEGIN
    v_tasa_mensual := p_tasa / 12;
    IF v_tasa_mensual = 0 THEN
        v_cuota := p_monto / p_plazo;
    ELSE
        v_cuota := p_monto * (v_tasa_mensual * POWER(1 + v_tasa_mensual, p_plazo)) / (POWER(1 + v_tasa_mensual, p_plazo) - 1);
    END IF;
    RETURN ROUND(v_cuota, 2);
END;
$$;

-- ============================================================
-- SECUENCIA PARA CÓDIGOS
-- ============================================================
CREATE SEQUENCE IF NOT EXISTS seq_codigo_pago
    START WITH 1
    INCREMENT BY 1;

-- ============================================================
-- PROCEDIMIENTOS ALMACENADOS
-- ============================================================

-- Generar tabla de amortización (método francés)
CREATE OR REPLACE FUNCTION sp_generar_amortizacion(
    p_prestamo_id INTEGER,
    p_fecha_desembolso DATE
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_monto DECIMAL(12,2);
    v_tasa DECIMAL(5,4);
    v_plazo INTEGER;
    v_tasa_mensual DECIMAL(10,6);
    v_cuota_fija DECIMAL(12,2);
    v_saldo_actual DECIMAL(12,2);
    v_interes DECIMAL(12,2);
    v_amortizacion DECIMAL(12,2);
    v_total_cuota DECIMAL(12,2);
    v_i INTEGER := 1;
    v_fecha_venc DATE;
BEGIN
    SELECT monto_aprobado, tasa_interes_valor, plazo_meses
    INTO v_monto, v_tasa, v_plazo
    FROM prestamos WHERE id = p_prestamo_id;

    v_tasa_mensual := v_tasa / 12;
    v_saldo_actual := v_monto;

    DELETE FROM amortizacion WHERE prestamo_id = p_prestamo_id;

    WHILE v_i <= v_plazo LOOP
        v_interes := ROUND(v_saldo_actual * v_tasa_mensual, 2);
        v_cuota_fija := ROUND(fn_calcular_interes_frances(v_monto, v_tasa, v_plazo), 2);

        IF v_i = v_plazo THEN
            v_amortizacion := v_saldo_actual;
            v_cuota_fija := v_amortizacion + v_interes;
        ELSE
            v_amortizacion := v_cuota_fija - v_interes;
        END IF;

        v_total_cuota := v_cuota_fija;
        v_fecha_venc := p_fecha_desembolso + (v_i || ' months')::INTERVAL;

        INSERT INTO amortizacion (prestamo_id, numero_cuota, fecha_vencimiento, saldo_inicial, monto_cuota, interes, amortizacion, saldo_final, total_cuota, estado)
        VALUES (p_prestamo_id, v_i, v_fecha_venc, v_saldo_actual, v_cuota_fija, v_interes, v_amortizacion, v_saldo_actual - v_amortizacion, v_total_cuota, 'pendiente');

        v_saldo_actual := v_saldo_actual - v_amortizacion;
        v_i := v_i + 1;
    END LOOP;

    -- Actualizar totales del préstamo
    UPDATE prestamos SET
        monto_cuota = (SELECT monto_cuota FROM amortizacion WHERE prestamo_id = p_prestamo_id LIMIT 1),
        total_interes = (SELECT SUM(interes) FROM amortizacion WHERE prestamo_id = p_prestamo_id),
        total_a_pagar = (SELECT SUM(total_cuota) FROM amortizacion WHERE prestamo_id = p_prestamo_id),
        saldo_pendiente = v_monto
    WHERE id = p_prestamo_id;
END;
$$;

-- Registrar pago y actualizar amortización
CREATE OR REPLACE FUNCTION sp_registrar_pago(
    p_prestamo_id INTEGER,
    p_cliente_id INTEGER,
    p_monto_total DECIMAL(12,2),
    p_cuotas_a_pagar TEXT, -- JSON: [1,2,3]
    p_metodo_pago VARCHAR(30) DEFAULT 'efectivo',
    p_numero_operacion VARCHAR(100) DEFAULT NULL,
    p_usuario_registro INTEGER DEFAULT NULL
)
RETURNS TABLE(codigo_pago VARCHAR, pago_id INTEGER, resultado TEXT)
LANGUAGE plpgsql AS $$
DECLARE
    v_codigo_pago VARCHAR(20);
    v_pago_id INTEGER;
    v_monto_cuota DECIMAL(12,2) := 0;
    v_monto_mora DECIMAL(12,2) := 0;
    v_monto_interes DECIMAL(12,2) := 0;
    v_monto_amortizacion DECIMAL(12,2) := 0;
    v_cuotas_pagadas INTEGER := 0;
    v_cuota_monto DECIMAL(12,2);
    v_mora_calculada DECIMAL(12,2);
    v_num_cuota INTEGER;
    v_seq INTEGER;
BEGIN
    v_seq := nextval('seq_codigo_pago');
    v_codigo_pago := 'PAG-' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' || LPAD(v_seq::TEXT, 4, '0');

    -- Procesar cuotas del JSON
    FOR v_num_cuota IN
        SELECT value::INTEGER FROM jsonb_array_elements_text(p_cuotas_a_pagar::JSONB)
    LOOP
        SELECT a.total_cuota, COALESCE(a.mora, 0)
        INTO v_cuota_monto, v_mora_calculada
        FROM amortizacion a
        WHERE a.prestamo_id = p_prestamo_id
          AND a.numero_cuota = v_num_cuota
          AND a.estado = 'pendiente';

        IF FOUND THEN
            v_monto_cuota := v_monto_cuota + v_cuota_monto;
            v_monto_mora := v_monto_mora + v_mora_calculada;
            v_cuotas_pagadas := v_cuotas_pagadas + 1;
        END IF;
    END LOOP;

    -- Insertar pago
    INSERT INTO pagos (codigo_pago, prestamo_id, cliente_id, monto_total, monto_cuota, monto_mora, cuotas_pagadas, fecha_pago, metodo_pago, numero_operacion, usuario_registro, estado)
    VALUES (v_codigo_pago, p_prestamo_id, p_cliente_id, p_monto_total, v_monto_cuota, v_monto_mora, v_cuotas_pagadas, CURRENT_TIMESTAMP, p_metodo_pago, p_numero_operacion, p_usuario_registro, 'confirmado')
    RETURNING id INTO v_pago_id;

    -- Actualizar cuotas como pagadas
    UPDATE amortizacion a SET
        estado = 'pagada',
        fecha_pago = CURRENT_TIMESTAMP,
        pago_id = v_pago_id
    FROM jsonb_array_elements_text(p_cuotas_a_pagar::JSONB) AS j(num)
    WHERE a.prestamo_id = p_prestamo_id
      AND a.numero_cuota = j.value::INTEGER
      AND a.estado = 'pendiente';

    -- Actualizar saldo pendiente del préstamo
    UPDATE prestamos SET
        saldo_pendiente = saldo_pendiente - v_monto_amortizacion,
        fecha_actualizacion = CURRENT_TIMESTAMP
    WHERE id = p_prestamo_id;

    -- Verificar si el préstamo está completamente pagado
    IF NOT EXISTS (SELECT 1 FROM amortizacion WHERE prestamo_id = p_prestamo_id AND estado = 'pendiente') THEN
        UPDATE prestamos SET estado = 'cerrado', fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = p_prestamo_id;
    END IF;

    RETURN QUERY SELECT v_codigo_pago, v_pago_id, 'Éxito'::TEXT;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT ''::VARCHAR, 0::INTEGER, SQLERRM::TEXT;
END;
$$;

-- Calcular mora automáticamente
CREATE OR REPLACE FUNCTION sp_calcular_mora_masiva()
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_tasa_mora DECIMAL(5,4) := 0.005;
BEGIN
    UPDATE amortizacion SET
        dias_atraso = EXTRACT(DAY FROM CURRENT_DATE - fecha_vencimiento)::INTEGER,
        mora = CASE
            WHEN fecha_vencimiento < CURRENT_DATE AND estado = 'pendiente'
            THEN ROUND(total_cuota * v_tasa_mora * EXTRACT(DAY FROM CURRENT_DATE - fecha_vencimiento), 2)
            ELSE 0
        END
    WHERE estado = 'pendiente';

    -- Actualizar préstamos vencidos a castigado
    UPDATE prestamos SET
        estado = CASE
            WHEN EXISTS (
                SELECT 1 FROM amortizacion a
                WHERE a.prestamo_id = prestamos.id AND a.estado = 'pendiente'
                AND a.fecha_vencimiento < (CURRENT_DATE - INTERVAL '30 days')::DATE
            ) THEN 'castigado'
            ELSE estado
        END,
        fecha_actualizacion = CURRENT_TIMESTAMP
    WHERE estado IN ('activo', 'reprogramado');
END;
$$;

-- ============================================================
-- TRIGGERS - AUTOMATIZACIÓN
-- ============================================================

-- Al aprobar un préstamo, generar amortización
CREATE OR REPLACE FUNCTION trg_prestamo_aprobado_fn()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.estado = 'aprobado' AND OLD.estado IN ('pendiente', 'evaluacion') THEN
        PERFORM sp_generar_amortizacion(NEW.id, CURRENT_DATE);

        INSERT INTO historial_estados (prestamo_id, estado_anterior, estado_nuevo, observaciones, fecha_cambio)
        VALUES (NEW.id, OLD.estado, 'aprobado', 'Préstamo aprobado automáticamente', CURRENT_TIMESTAMP);
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_prestamo_aprobado
    AFTER UPDATE ON prestamos
    FOR EACH ROW
    EXECUTE FUNCTION trg_prestamo_aprobado_fn();

-- Al desembolsar, activar préstamo
CREATE OR REPLACE FUNCTION trg_prestamo_desembolsado_fn()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.estado = 'desembolsado' AND OLD.estado = 'aprobado' THEN
        NEW.estado := 'activo';
        NEW.fecha_actualizacion := CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_prestamo_desembolsado
    BEFORE UPDATE ON prestamos
    FOR EACH ROW
    EXECUTE FUNCTION trg_prestamo_desembolsado_fn();

-- Notificar cuotas próximas a vencer
CREATE OR REPLACE FUNCTION trg_notificar_vencimiento_fn()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO notificaciones (tipo, destino, mensaje, prestamo_id, cliente_id)
    SELECT
        'recordatorio',
        c.celular,
        'Recordatorio: Su cuota #' || NEW.numero_cuota::TEXT || ' de Bs ' || ROUND(NEW.total_cuota::NUMERIC, 2)::TEXT || ' vence el ' || TO_CHAR(NEW.fecha_vencimiento, 'DD/MM/YYYY') || '. Realice su pago a tiempo.',
        NEW.prestamo_id,
        p.cliente_id
    FROM prestamos p
    INNER JOIN clientes c ON p.cliente_id = c.id
    WHERE p.id = NEW.prestamo_id;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_notificar_vencimiento
    AFTER INSERT ON amortizacion
    FOR EACH ROW
    EXECUTE FUNCTION trg_notificar_vencimiento_fn();

-- ============================================================
-- DATOS INICIALES (SEED)
-- ============================================================

-- Roles
INSERT INTO roles (nombre, descripcion) VALUES
('administrador', 'Acceso total al sistema'),
('gerente', 'Aprueba préstamos y genera reportes'),
('asesor', 'Gestiona clientes y solicitudes'),
('cajero', 'Registra pagos y desembolsos')
ON CONFLICT (nombre) DO NOTHING;

-- Nota: El usuario admin se crea desde la app con `flask init-db`
-- porque requiere generar el hash de la contraseña con werkzeug.
-- Tasa de interés por defecto también se crea desde la app.

-- ============================================================
-- NOTA: Para inicializar la base de datos, ejecutar:
-- 1. Crear tablas: flask shell -> db.create_all()
-- 2. Seed data: flask init-db
-- 3. (Opcional) Cargar datos de prueba: python seed_data.py
-- ============================================================
