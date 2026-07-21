-- ============================================================
-- SISTEMA DE GESTIÓN DE PRÉSTAMOS Y CRÉDITOS
-- Base de datos: GestionPrestamos
-- Motor: SQL Server
-- ============================================================

CREATE DATABASE GestionPrestamos;
GO

USE GestionPrestamos;
GO

-- ============================================================
-- TABLAS PRINCIPALES
-- ============================================================

-- Roles de usuario
CREATE TABLE roles (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    fecha_creacion DATETIME DEFAULT GETDATE()
);

-- Usuarios del sistema
CREATE TABLE usuarios (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INT NOT NULL FOREIGN KEY REFERENCES roles(id),
    activo BIT DEFAULT 1,
    ultimo_acceso DATETIME,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME DEFAULT GETDATE()
);

-- Clientes / Prestatarios
CREATE TABLE clientes (
    id INT IDENTITY(1,1) PRIMARY KEY,
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
    observaciones TEXT,
    foto VARBINARY(MAX),
    activo BIT DEFAULT 1,
    fecha_registro DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME DEFAULT GETDATE()
);

-- Tasas de interés configurables
CREATE TABLE tasas_interes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo_tasa VARCHAR(20) NOT NULL CHECK (tipo_tasa IN ('mensual', 'anual', 'diaria')),
    valor DECIMAL(5,4) NOT NULL,
    tipo_moneda VARCHAR(10) DEFAULT 'PEN',
    activo BIT DEFAULT 1,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    usuario_creo INT FOREIGN KEY REFERENCES usuarios(id),
    fecha_creacion DATETIME DEFAULT GETDATE()
);

-- Préstamos
CREATE TABLE prestamos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    codigo_prestamo VARCHAR(20) NOT NULL UNIQUE,
    cliente_id INT NOT NULL FOREIGN KEY REFERENCES clientes(id),
    monto_solicitado DECIMAL(12,2) NOT NULL,
    monto_aprobado DECIMAL(12,2),
    tasa_interes_id INT FOREIGN KEY REFERENCES tasas_interes(id),
    tasa_interes_valor DECIMAL(5,4),
    tipo_tasa VARCHAR(20) CHECK (tipo_tasa IN ('mensual', 'anual', 'diaria')),
    plazo_meses INT NOT NULL,
    metodo_amortizacion VARCHAR(30) DEFAULT 'frances' CHECK (metodo_amortizacion IN ('frances', 'alemán', 'americano')),
    frecuencia_pago VARCHAR(20) DEFAULT 'mensual' CHECK (frecuencia_pago IN ('mensual', 'quincenal', 'semanal')),
    monto_cuota DECIMAL(12,2),
    total_interes DECIMAL(12,2),
    total_a_pagar DECIMAL(12,2),
    saldo_pendiente DECIMAL(12,2),
    fecha_solicitud DATETIME DEFAULT GETDATE(),
    fecha_aprobacion DATETIME,
    fecha_desembolso DATETIME,
    fecha_vencimiento DATE,
    estado VARCHAR(30) DEFAULT 'pendiente' CHECK (estado IN ('pendiente','evaluacion','aprobado','rechazado','desembolsado','activo','reprogramado','cerrado','castigado')),
    usuario_solicito INT FOREIGN KEY REFERENCES usuarios(id),
    usuario_aprobo INT FOREIGN KEY REFERENCES usuarios(id),
    observaciones TEXT,
    motivo_rechazo VARCHAR(500),
    fecha_creacion DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME DEFAULT GETDATE()
);

-- Documentos de préstamo
CREATE TABLE documentos_prestamo (
    id INT IDENTITY(1,1) PRIMARY KEY,
    prestamo_id INT NOT NULL FOREIGN KEY REFERENCES prestamos(id),
    tipo_documento VARCHAR(50) NOT NULL,
    nombre_archivo VARCHAR(255),
    contenido VARBINARY(MAX),
    fecha_generacion DATETIME DEFAULT GETDATE(),
    usuario_genero INT FOREIGN KEY REFERENCES usuarios(id)
);

-- Tabla de amortización (detalle de cuotas)
CREATE TABLE amortizacion (
    id INT IDENTITY(1,1) PRIMARY KEY,
    prestamo_id INT NOT NULL FOREIGN KEY REFERENCES prestamos(id),
    numero_cuota INT NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    saldo_inicial DECIMAL(12,2),
    monto_cuota DECIMAL(12,2),
    interes DECIMAL(12,2),
    amortizacion DECIMAL(12,2),
    saldo_final DECIMAL(12,2),
    seguro_desgravamen DECIMAL(12,2) DEFAULT 0,
    seguro_bien DECIMAL(12,2) DEFAULT 0,
    total_cuota DECIMAL(12,2),
    dias_atraso INT DEFAULT 0,
    mora DECIMAL(12,2) DEFAULT 0,
    estado VARCHAR(30) DEFAULT 'pendiente' CHECK (estado IN ('pendiente','pagada','vencida','castigada')),
    fecha_pago DATETIME,
    pago_id INT,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_prestamo_cuota UNIQUE (prestamo_id, numero_cuota)
);

-- Pagos recibidos
CREATE TABLE pagos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    codigo_pago VARCHAR(20) NOT NULL UNIQUE,
    prestamo_id INT NOT NULL FOREIGN KEY REFERENCES prestamos(id),
    cliente_id INT NOT NULL FOREIGN KEY REFERENCES clientes(id),
    monto_total DECIMAL(12,2) NOT NULL,
    monto_cuota DECIMAL(12,2),
    monto_mora DECIMAL(12,2) DEFAULT 0,
    monto_interes DECIMAL(12,2) DEFAULT 0,
    monto_amortizacion DECIMAL(12,2) DEFAULT 0,
    monto_seguro DECIMAL(12,2) DEFAULT 0,
    cuotas_pagadas INT DEFAULT 1,
    fecha_pago DATETIME NOT NULL,
    fecha_registro DATETIME DEFAULT GETDATE(),
    metodo_pago VARCHAR(30) DEFAULT 'efectivo' CHECK (metodo_pago IN ('efectivo','transferencia','deposito','tarjeta','app')),
    numero_operacion VARCHAR(100),
    usuario_registro INT FOREIGN KEY REFERENCES usuarios(id),
    observaciones TEXT,
    estado VARCHAR(20) DEFAULT 'confirmado' CHECK (estado IN ('pendiente','confirmado','anulado'))
);

-- Agregar FK de amortizacion -> pagos
ALTER TABLE amortizacion ADD CONSTRAINT FK_amortizacion_pago
    FOREIGN KEY (pago_id) REFERENCES pagos(id);

-- Historial de cambios de estado
CREATE TABLE historial_estados (
    id INT IDENTITY(1,1) PRIMARY KEY,
    prestamo_id INT NOT NULL FOREIGN KEY REFERENCES prestamos(id),
    estado_anterior VARCHAR(30),
    estado_nuevo VARCHAR(30) NOT NULL,
    usuario_id INT FOREIGN KEY REFERENCES usuarios(id),
    observaciones TEXT,
    fecha_cambio DATETIME DEFAULT GETDATE()
);

-- Notificaciones / Recordatorios
CREATE TABLE notificaciones (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('recordatorio','alerta','notificacion')),
    destino VARCHAR(100),
    mensaje TEXT,
    prestamo_id INT FOREIGN KEY REFERENCES prestamos(id),
    cliente_id INT FOREIGN KEY REFERENCES clientes(id),
    leido BIT DEFAULT 0,
    fecha_envio DATETIME,
    fecha_creacion DATETIME DEFAULT GETDATE()
);

-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX IX_clientes_documento ON clientes(numero_documento);
CREATE INDEX IX_prestamos_cliente ON prestamos(cliente_id);
CREATE INDEX IX_prestamos_estado ON prestamos(estado);
CREATE INDEX IX_amortizacion_prestamo ON amortizacion(prestamo_id);
CREATE INDEX IX_amortizacion_estado ON amortizacion(estado);
CREATE INDEX IX_pagos_prestamo ON pagos(prestamo_id);
CREATE INDEX IX_pagos_fecha ON pagos(fecha_pago);

-- ============================================================
-- VISTAS
-- ============================================================

-- Resumen de préstamos activos
GO
CREATE VIEW vw_resumen_prestamos_activos AS
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
    p.fecha_vencimiento,
    DATEDIFF(DAY, p.fecha_vencimiento, GETDATE()) AS dias_vencidos,
    (SELECT COUNT(*) FROM amortizacion a WHERE a.prestamo_id = p.id AND a.estado = 'pendiente') AS cuotas_pendientes,
    (SELECT COUNT(*) FROM amortizacion a WHERE a.prestamo_id = p.id AND a.estado = 'pagada') AS cuotas_pagadas
FROM prestamos p
INNER JOIN clientes c ON p.cliente_id = c.id
WHERE p.estado IN ('activo', 'reprogramado');
GO

-- Cartera morosa
GO
CREATE VIEW vw_cartera_morosa AS
SELECT
    p.id,
    p.codigo_prestamo,
    c.nombre_completo AS cliente,
    c.telefono,
    c.celular,
    p.monto_aprobado,
    p.saldo_pendiente,
    p.monto_cuota,
    DATEDIFF(DAY, a.fecha_vencimiento, GETDATE()) AS dias_mora,
    a.monto_cuota AS cuota_vencida,
    a.mora,
    a.fecha_vencimiento,
    DATEDIFF(DAY, a.fecha_vencimiento, GETDATE()) * p.monto_cuota * 0.005 AS mora_calculada
FROM prestamos p
INNER JOIN clientes c ON p.cliente_id = c.id
INNER JOIN amortizacion a ON a.prestamo_id = p.id
WHERE p.estado IN ('activo', 'reprogramado')
  AND a.estado = 'pendiente'
  AND a.fecha_vencimiento < GETDATE();
GO

-- ============================================================
-- FUNCIONES
-- ============================================================

GO
CREATE FUNCTION fn_calcular_interes_frances (
    @monto DECIMAL(12,2),
    @tasa DECIMAL(5,4),
    @plazo INT
)
RETURNS DECIMAL(12,2)
AS
BEGIN
    DECLARE @cuota DECIMAL(12,2);
    DECLARE @tasa_mensual DECIMAL(10,6) = @tasa / 12;
    IF @tasa_mensual = 0
        SET @cuota = @monto / @plazo;
    ELSE
        SET @cuota = @monto * (@tasa_mensual * POWER(1 + @tasa_mensual, @plazo)) / (POWER(1 + @tasa_mensual, @plazo) - 1);
    RETURN ROUND(@cuota, 2);
END;
GO

-- ============================================================
-- PROCEDIMIENTOS ALMACENADOS
-- ============================================================

-- Generar tabla de amortización (método francés)
GO
CREATE PROCEDURE sp_generar_amortizacion
    @prestamo_id INT,
    @fecha_desembolso DATE
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @monto DECIMAL(12,2), @tasa DECIMAL(5,4), @plazo INT;
    DECLARE @tasa_mensual DECIMAL(10,6), @cuota_fija DECIMAL(12,2);
    DECLARE @saldo_actual DECIMAL(12,2), @interes DECIMAL(12,2);
    DECLARE @amortizacion DECIMAL(12,2), @total_cuota DECIMAL(12,2);
    DECLARE @i INT = 1;
    DECLARE @fecha_venc DATE;

    SELECT @monto = monto_aprobado, @tasa = tasa_interes_valor, @plazo = plazo_meses
    FROM prestamos WHERE id = @prestamo_id;

    SET @tasa_mensual = @tasa / 12;
    SET @saldo_actual = @monto;

    DELETE FROM amortizacion WHERE prestamo_id = @prestamo_id;

    WHILE @i <= @plazo
    BEGIN
        SET @interes = ROUND(@saldo_actual * @tasa_mensual, 2);
        SET @cuota_fija = ROUND(dbo.fn_calcular_interes_frances(@monto, @tasa, @plazo), 2);

        IF @i = @plazo
        BEGIN
            SET @amortizacion = @saldo_actual;
            SET @cuota_fija = @amortizacion + @interes;
        END
        ELSE
            SET @amortizacion = @cuota_fija - @interes;

        SET @total_cuota = @cuota_fija;
        SET @fecha_venc = DATEADD(MONTH, @i, @fecha_desembolso);

        INSERT INTO amortizacion (prestamo_id, numero_cuota, fecha_vencimiento, saldo_inicial, monto_cuota, interes, amortizacion, saldo_final, total_cuota, estado)
        VALUES (@prestamo_id, @i, @fecha_venc, @saldo_actual, @cuota_fija, @interes, @amortizacion, @saldo_actual - @amortizacion, @total_cuota, 'pendiente');

        SET @saldo_actual = @saldo_actual - @amortizacion;
        SET @i = @i + 1;
    END;

    -- Actualizar totales del préstamo
    UPDATE prestamos SET
        monto_cuota = (SELECT TOP 1 monto_cuota FROM amortizacion WHERE prestamo_id = @prestamo_id),
        total_interes = (SELECT SUM(interes) FROM amortizacion WHERE prestamo_id = @prestamo_id),
        total_a_pagar = (SELECT SUM(total_cuota) FROM amortizacion WHERE prestamo_id = @prestamo_id),
        saldo_pendiente = @monto
    WHERE id = @prestamo_id;
END;
GO

-- Registrar pago y actualizar amortización
GO
CREATE PROCEDURE sp_registrar_pago
    @prestamo_id INT,
    @cliente_id INT,
    @monto_total DECIMAL(12,2),
    @cuotas_a_pagar NVARCHAR(MAX), -- JSON: [1,2,3]
    @metodo_pago VARCHAR(30) = 'efectivo',
    @numero_operacion VARCHAR(100) = NULL,
    @usuario_registro INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @codigo_pago VARCHAR(20);
        DECLARE @pago_id INT;
        DECLARE @monto_cuota DECIMAL(12,2) = 0;
        DECLARE @monto_mora DECIMAL(12,2) = 0;
        DECLARE @monto_interes DECIMAL(12,2) = 0;
        DECLARE @monto_amortizacion DECIMAL(12,2) = 0;
        DECLARE @cuotas_pagadas INT = 0;
        DECLARE @cuota_id INT, @cuota_num INT, @cuota_monto DECIMAL(12,2);
        DECLARE @mora_calculada DECIMAL(12,2);

        SET @codigo_pago = 'PAG-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('0000' + CAST(NEXT VALUE FOR seq_codigo_pago AS VARCHAR), 4);

        -- Tabla temporal con las cuotas a pagar
        DECLARE @cuotas TABLE (num_cuota INT);

        INSERT INTO @cuotas (num_cuota)
        SELECT value FROM OPENJSON(@cuotas_a_pagar);

        DECLARE cuota_cursor CURSOR FOR
            SELECT a.id, a.numero_cuota, a.total_cuota, a.mora
            FROM amortizacion a
            INNER JOIN @cuotas c ON a.numero_cuota = c.num_cuota
            WHERE a.prestamo_id = @prestamo_id AND a.estado = 'pendiente'
            ORDER BY a.numero_cuota;

        OPEN cuota_cursor;

        FETCH NEXT FROM cuota_cursor INTO @cuota_id, @cuota_num, @cuota_monto, @mora_calculada;

        WHILE @@FETCH_STATUS = 0
        BEGIN
            SET @monto_cuota = @monto_cuota + @cuota_monto;
            SET @monto_mora = @monto_mora + ISNULL(@mora_calculada, 0);
            SET @cuotas_pagadas = @cuotas_pagadas + 1;

            FETCH NEXT FROM cuota_cursor INTO @cuota_id, @cuota_num, @cuota_monto, @mora_calculada;
        END;

        CLOSE cuota_cursor;
        DEALLOCATE cuota_cursor;

        -- Insertar pago
        INSERT INTO pagos (codigo_pago, prestamo_id, cliente_id, monto_total, monto_cuota, monto_mora, cuotas_pagadas, fecha_pago, metodo_pago, numero_operacion, usuario_registro, estado)
        VALUES (@codigo_pago, @prestamo_id, @cliente_id, @monto_total, @monto_cuota, @monto_mora, @cuotas_pagadas, GETDATE(), @metodo_pago, @numero_operacion, @usuario_registro, 'confirmado');

        SET @pago_id = SCOPE_IDENTITY();

        -- Actualizar cuotas como pagadas
        UPDATE a SET
            a.estado = 'pagada',
            a.fecha_pago = GETDATE(),
            a.pago_id = @pago_id
        FROM amortizacion a
        INNER JOIN @cuotas c ON a.numero_cuota = c.num_cuota
        WHERE a.prestamo_id = @prestamo_id;

        -- Actualizar saldo pendiente del préstamo
        UPDATE prestamos SET
            saldo_pendiente = saldo_pendiente - @monto_amortizacion,
            fecha_actualizacion = GETDATE()
        WHERE id = @prestamo_id;

        -- Verificar si el préstamo está completamente pagado
        IF NOT EXISTS (SELECT 1 FROM amortizacion WHERE prestamo_id = @prestamo_id AND estado = 'pendiente')
        BEGIN
            UPDATE prestamos SET estado = 'cerrado', fecha_actualizacion = GETDATE() WHERE id = @prestamo_id;
        END;

        COMMIT TRANSACTION;
        SELECT @codigo_pago AS codigo_pago, @pago_id AS pago_id, 'Éxito' AS resultado;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        SELECT ERROR_MESSAGE() AS error;
    END CATCH;
END;
GO

-- Calcular mora automáticamente
GO
CREATE PROCEDURE sp_calcular_mora_masiva
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @tasa_mora DECIMAL(5,4) = 0.005; -- 0.5% diario

    UPDATE amortizacion SET
        dias_atraso = DATEDIFF(DAY, fecha_vencimiento, GETDATE()),
        mora = CASE
            WHEN fecha_vencimiento < GETDATE() AND estado = 'pendiente'
            THEN ROUND(total_cuota * @tasa_mora * DATEDIFF(DAY, fecha_vencimiento, GETDATE()), 2)
            ELSE 0
        END
    WHERE estado = 'pendiente';

    -- Actualizar préstamos vencidos a mora
    UPDATE prestamos SET
        estado = CASE
            WHEN EXISTS (
                SELECT 1 FROM amortizacion a
                WHERE a.prestamo_id = prestamos.id AND a.estado = 'pendiente'
                AND a.fecha_vencimiento < DATEADD(DAY, -30, GETDATE())
            ) THEN 'castigado'
            ELSE estado
        END,
        fecha_actualizacion = GETDATE()
    WHERE estado IN ('activo', 'reprogramado');
END;
GO

-- ============================================================
-- TRIGGERS - AUTOMATIZACIÓN
-- ============================================================

-- Al aprobar un préstamo, generar amortización y documentos
GO
CREATE TRIGGER trg_prestamo_aprobado
ON prestamos
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM inserted WHERE estado = 'aprobado' AND EXISTS (SELECT 1 FROM deleted WHERE estado IN ('pendiente','evaluacion')))
    BEGIN
        DECLARE @prestamo_id INT, @cliente_id INT, @codigo VARCHAR(20);
        DECLARE @fecha DATE = GETDATE();

        DECLARE cur CURSOR FOR
            SELECT i.id, i.cliente_id, i.codigo_prestamo
            FROM inserted i
            INNER JOIN deleted d ON i.id = d.id
            WHERE i.estado = 'aprobado' AND d.estado IN ('pendiente','evaluacion');

        OPEN cur;
        FETCH NEXT FROM cur INTO @prestamo_id, @cliente_id, @codigo;

        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Generar tabla de amortización automáticamente
            EXEC sp_generar_amortizacion @prestamo_id, @fecha;

            -- Registrar en historial
            INSERT INTO historial_estados (prestamo_id, estado_anterior, estado_nuevo, observaciones, fecha_cambio)
            SELECT @prestamo_id, d.estado, 'aprobado', 'Préstamo aprobado automáticamente', GETDATE()
            FROM deleted d WHERE d.id = @prestamo_id;

            FETCH NEXT FROM cur INTO @prestamo_id, @cliente_id, @codigo;
        END;

        CLOSE cur;
        DEALLOCATE cur;
    END;
END;
GO

-- Al desembolsar, activar préstamo
GO
CREATE TRIGGER trg_prestamo_desembolsado
ON prestamos
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM inserted WHERE estado = 'desembolsado' AND EXISTS (SELECT 1 FROM deleted WHERE estado = 'aprobado'))
    BEGIN
        UPDATE prestamos SET
            estado = 'activo',
            fecha_actualizacion = GETDATE()
        WHERE id IN (SELECT i.id FROM inserted i INNER JOIN deleted d ON i.id = d.id WHERE i.estado = 'desembolsado' AND d.estado = 'aprobado');
    END;
END;
GO

-- Notificar cuotas próximas a vencer
GO
CREATE TRIGGER trg_notificar_vencimiento
ON amortizacion
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO notificaciones (tipo, destino, mensaje, prestamo_id, cliente_id)
    SELECT
        'recordatorio',
        c.celular,
        'Recordatorio: Su cuota #' + CAST(i.numero_cuota AS VARCHAR) + ' de Bs ' + CAST(i.total_cuota AS VARCHAR) + ' vence el ' + CONVERT(VARCHAR, i.fecha_vencimiento, 103) + '. Realice su pago a tiempo.',
        i.prestamo_id,
        p.cliente_id
    FROM inserted i
    INNER JOIN prestamos p ON i.prestamo_id = p.id
    INNER JOIN clientes c ON p.cliente_id = c.id;
END;
GO

-- ============================================================
-- SECUENCIA PARA CÓDIGOS
-- ============================================================
CREATE SEQUENCE seq_codigo_pago
    START WITH 1
    INCREMENT BY 1;
GO

-- ============================================================
-- DATOS INICIALES (SEED)
-- ============================================================

-- Roles
INSERT INTO roles (nombre, descripcion) VALUES
('administrador', 'Acceso total al sistema'),
('gerente', 'Aprueba préstamos y genera reportes'),
('asesor', 'Gestiona clientes y solicitudes'),
('cajero', 'Registra pagos y desembolsos');

-- Usuario administrador por defecto (password: admin123)
-- El hash debe generarse con werkzeug.security.generate_password_hash
INSERT INTO usuarios (nombre_completo, email, username, password_hash, rol_id)
VALUES ('Administrador del Sistema', 'admin@micredit.com', 'admin', 'pbkdf2:sha256:600000$salt$hash', 1);

-- Tasa de interés por defecto
INSERT INTO tasas_interes (nombre, tipo_tasa, valor, fecha_inicio)
VALUES ('Tasa Microcrédito Estándar', 'anual', 0.36, GETDATE());
GO

PRINT 'Base de datos GestionPrestamos creada exitosamente.';
GO
