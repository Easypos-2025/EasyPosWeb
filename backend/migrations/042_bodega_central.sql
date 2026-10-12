-- 042 — Bodega Central multisede (F0)
--
--   company_configs.has_bodega_central = 1  la empresa es la BODEGA CENTRAL de las empresas activas con su
--       mismo NIT (sus sedes). Solo la activa SYSADMIN (Empresas → editar). La bodega existe solo en la web:
--       su catálogo es el catálogo web de esa empresa y su stock su inventario_actual_porciones.
--
--   configuracion_sede.cargar_1_inventario_automatico = 1  "cargue unitario" (cliente especial, ej. celulares
--       con IMEI): cada unidad es un producto propio (Codigo_Producto = IMEI) que entra al inventario con
--       cantidad 1 al crearlo, exige proveedor y se puede replicar. En el escritorio es la variable
--       Var_Cargar_1_Inventario_Automatico (= registro_observacion_cierre.Turno); S3 la bajará en F1.
--
--   bc_producto_sede  producto de la bodega ↔ el mismo producto en cada sede (id del plato en la sede).
--                     PENDIENTE = aún no existe en la sede; VINCULADO = ya tiene su id en la sede.
--   bc_movimientos    kardex y auditoría de la bodega (nunca se borra). clave = idempotencia por operación.

ALTER TABLE company_configs
    ADD COLUMN IF NOT EXISTS has_bodega_central TINYINT NOT NULL DEFAULT 0;

ALTER TABLE configuracion_sede
    ADD COLUMN IF NOT EXISTS cargar_1_inventario_automatico TINYINT NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS bc_producto_sede (
    id            INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bodega_id     INT          NOT NULL,
    dish_id       INT          NOT NULL,
    sede_id       INT          NOT NULL,
    sede_dish_id  INT          NULL,
    estado        VARCHAR(12)  NOT NULL DEFAULT 'PENDIENTE',
    error         VARCHAR(255) NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_bc_ps (bodega_id, dish_id, sede_id),
    KEY idx_bc_ps_sede (sede_id, sede_dish_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bc_movimientos (
    id          BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bodega_id   INT           NOT NULL,
    tipo        VARCHAR(20)   NOT NULL,          -- CREACION | REPLICA | ENTRADA | IMPORTACION
    dish_id     INT           NULL,
    cantidad    DECIMAL(14,4) NOT NULL DEFAULT 0,
    sede_id     INT           NULL,
    referencia  VARCHAR(60)   NULL,
    detalle     VARCHAR(255)  NULL,
    clave       VARCHAR(64)   NULL,
    usuario_id  INT           NULL,
    usuario     VARCHAR(150)  NULL,
    ip          VARCHAR(45)   NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_bc_mov_clave (bodega_id, clave, tipo, dish_id),
    KEY idx_bc_mov_bodega (bodega_id, created_at),
    KEY idx_bc_mov_dish (bodega_id, dish_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Bodega Central', '/bodega-central', 'bi-boxes', NULL, 1, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_modules WHERE route = '/bodega-central');
