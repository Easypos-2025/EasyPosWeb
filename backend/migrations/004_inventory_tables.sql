-- ============================================================
-- Migración 004: Tablas de inventario físico, entradas, salidas
-- + system_modules para las 3 vistas nuevas
-- + movement_date en stock_movements
-- + stock_deducted en tablas de detalle de ventas
-- Ejecutar en LOCAL y PRODUCCIÓN
-- ============================================================

-- 0. Columna stock_deducted para rastrear descuentos de stock por venta
ALTER TABLE pos_order_detail_products
    ADD COLUMN IF NOT EXISTS stock_deducted TINYINT NOT NULL DEFAULT 0;
ALTER TABLE pos_receipt_order_detail_products
    ADD COLUMN IF NOT EXISTS stock_deducted TINYINT NOT NULL DEFAULT 0;

-- 1. Agregar movement_date a stock_movements (si no existe)
ALTER TABLE stock_movements
    ADD COLUMN IF NOT EXISTS movement_date DATE NULL AFTER reference_id;

CREATE INDEX IF NOT EXISTS idx_smov_date ON stock_movements(movement_date);

-- 2. Inventarios Físicos
CREATE TABLE IF NOT EXISTS inventory_physical (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    id_fisico    INT         NOT NULL,
    id_item      INT         NOT NULL,
    company_id   INT         NOT NULL,
    fecha        DATE        NOT NULL,
    cantidad     DECIMAL(14,4) NOT NULL DEFAULT 0,
    cod_usuario  VARCHAR(100),
    hora         VARCHAR(50),
    observacion  VARCHAR(255),
    autorizada   TINYINT     NOT NULL DEFAULT 0,
    revisada     TINYINT     NOT NULL DEFAULT 0,
    cobrar       TINYINT     NOT NULL DEFAULT 0,
    agrupar      INT         NOT NULL DEFAULT 0,
    synced       TINYINT     NOT NULL DEFAULT 0,
    created_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_fisico (company_id, id_fisico),
    INDEX idx_ip_item (company_id, id_item),
    INDEX idx_ip_fecha (company_id, fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Inventarios Entradas
CREATE TABLE IF NOT EXISTS inventory_entries (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    id_entrada    INT         NOT NULL,
    id_item       INT         NOT NULL,
    id_proveedor  INT         NOT NULL DEFAULT 0,
    company_id    INT         NOT NULL,
    fecha         DATE        NOT NULL,
    cantidad      DECIMAL(14,4) NOT NULL DEFAULT 0,
    cod_empleado  VARCHAR(50),
    observacion   VARCHAR(255),
    autorizada    INT         NOT NULL DEFAULT 0,
    revisada      TINYINT     NOT NULL DEFAULT 0,
    cobrar        TINYINT     NOT NULL DEFAULT 0,
    agrupar       INT         NOT NULL DEFAULT 0,
    synced        TINYINT     NOT NULL DEFAULT 0,
    created_at    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_entrada (company_id, id_entrada),
    INDEX idx_ie_item (company_id, id_item),
    INDEX idx_ie_fecha (company_id, fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Inventarios Salidas
CREATE TABLE IF NOT EXISTS inventory_exits (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    id_salida     INT         NOT NULL,
    id_item       INT         NOT NULL,
    id_proveedor  INT         NOT NULL DEFAULT 0,
    company_id    INT         NOT NULL,
    fecha         DATE        NOT NULL,
    cantidad      DECIMAL(14,4) NOT NULL DEFAULT 0,
    cod_empleado  VARCHAR(50),
    observacion   VARCHAR(255),
    autorizada    INT         NOT NULL DEFAULT 0,
    revisada      TINYINT     NOT NULL DEFAULT 0,
    cobrar        TINYINT     NOT NULL DEFAULT 0,
    agrupar       INT         NOT NULL DEFAULT 0,
    synced        TINYINT     NOT NULL DEFAULT 0,
    created_at    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_salida (company_id, id_salida),
    INDEX idx_ix_item (company_id, id_item),
    INDEX idx_ix_fecha (company_id, fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Módulos en system_modules
INSERT IGNORE INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
VALUES
    ('Inventarios Fisicos', '/inventory/physical',  'bi-clipboard-check',   NULL, 1, 0, 0),
    ('Entradas Inventario', '/inventory/entries',   'bi-box-arrow-in-down', NULL, 1, 0, 0),
    ('Salidas Inventario',  '/inventory/exits',     'bi-box-arrow-up',      NULL, 1, 0, 0);
