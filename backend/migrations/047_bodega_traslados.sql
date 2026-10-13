-- 047 — Traslados de inventario entre la Bodega Central y sus sedes (solo en la nube, nunca se borran)
--
-- bc_traslados        un traslado = un origen → un destino (bodega o sede del mismo NIT).
--   estado: PENDIENTE_SALIDA  origen con escritorio: su agente debe descontar (verifica que tenga el stock)
--           PENDIENTE_CARGUE  destino con escritorio: su agente debe cargarlo (crea o actualiza el producto)
--           CARGADO           terminado (origen descontó y destino cargó)
--           ANULADO           anulado antes de cargarse (motivo, fecha y quién); el origen recupera su stock
--           ERROR             no se pudo (ej. el origen ya no tenía la cantidad)
--   Origen y destino solo web: se descuenta y se carga al instante, automático (sin cajero).
--   reversa_pendiente = 1: se anuló después de que el agente del origen descontó; el agente debe devolverlo.
-- bc_traslado_items   la NOVEDAD por artículo: foto completa del producto al enviarlo, cantidad, stock antes y
--                     después en origen y destino, y si en destino se CREÓ o se ACTUALIZÓ.

CREATE TABLE IF NOT EXISTS bc_traslados (
    id                BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bodega_id         INT           NOT NULL,
    numero            INT           NOT NULL,
    origen_id         INT           NOT NULL,
    destino_id        INT           NOT NULL,
    estado            VARCHAR(20)   NOT NULL,
    observacion       VARCHAR(255)  NULL,
    enviado_en        DATETIME      NOT NULL,
    enviado_por       VARCHAR(150)  NULL,
    enviado_por_id    INT           NULL,
    ip                VARCHAR(45)   NULL,
    salida_en         DATETIME      NULL,
    salida_por        VARCHAR(150)  NULL,
    cargado_en        DATETIME      NULL,
    cargado_por       VARCHAR(150)  NULL,
    anulado_en        DATETIME      NULL,
    anulado_por       VARCHAR(150)  NULL,
    anulado_motivo    VARCHAR(255)  NULL,
    reversa_pendiente TINYINT       NOT NULL DEFAULT 0,
    error             VARCHAR(255)  NULL,
    clave             VARCHAR(64)   NULL,
    created_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_bct_numero (bodega_id, numero),
    KEY idx_bct_bodega (bodega_id, estado, enviado_en),
    KEY idx_bct_origen (origen_id, estado),
    KEY idx_bct_destino (destino_id, estado),
    KEY idx_bct_clave (bodega_id, clave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bc_traslado_items (
    id                     BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    traslado_id            BIGINT        NOT NULL,
    item                   INT           NOT NULL,
    origen_dish_id         INT           NOT NULL,
    destino_dish_id        INT           NULL,
    codigo                 VARCHAR(60)   NULL,
    nombre                 VARCHAR(250)  NOT NULL,
    categoria              VARCHAR(100)  NULL,
    proveedor              VARCHAR(150)  NULL,
    proveedor_nit          VARCHAR(50)   NULL,
    precio                 DECIMAL(14,2) NOT NULL DEFAULT 0,
    precio_minimo          DECIMAL(14,2) NOT NULL DEFAULT 0,
    costo                  DECIMAL(14,2) NOT NULL DEFAULT 0,
    iva                    DECIMAL(6,2)  NOT NULL DEFAULT 0,
    stock_minimo           DECIMAL(14,4) NOT NULL DEFAULT 0,
    desactivar_al_vender   TINYINT       NOT NULL DEFAULT 0,
    pedir_descripcion      TINYINT       NOT NULL DEFAULT 0,
    cantidad               DECIMAL(14,4) NOT NULL,
    stock_origen_antes     DECIMAL(14,4) NULL,
    stock_origen_despues   DECIMAL(14,4) NULL,
    stock_destino_antes    DECIMAL(14,4) NULL,
    stock_destino_despues  DECIMAL(14,4) NULL,
    resultado              VARCHAR(12)   NULL,
    estado                 VARCHAR(12)   NOT NULL DEFAULT 'PENDIENTE',
    error                  VARCHAR(255)  NULL,
    UNIQUE KEY uq_bcti (traslado_id, item),
    KEY idx_bcti_codigo (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Traslados', '/bodega-central/traslados', 'bi-truck', p.id, 1, 5, 0
FROM system_modules p
WHERE p.route = '/bodega-central'
  AND NOT EXISTS (SELECT 1 FROM system_modules x WHERE x.route = '/bodega-central/traslados');

INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT bp.business_profile_id, c.id, bp.id, c.order_index
FROM business_profile_modules bp
JOIN system_modules p ON p.id = bp.module_id AND p.route = '/bodega-central'
JOIN system_modules c ON c.parent_id = p.id AND c.route = '/bodega-central/traslados'
WHERE NOT EXISTS (SELECT 1 FROM business_profile_modules x
                  WHERE x.business_profile_id = bp.business_profile_id AND x.module_id = c.id);

INSERT INTO role_modules (role_id, module_id, can_view, can_view_all, can_create, can_edit, can_delete)
SELECT rm.role_id, c.id, rm.can_view, rm.can_view_all, rm.can_create, rm.can_edit, rm.can_delete
FROM role_modules rm
JOIN system_modules p ON p.id = rm.module_id AND p.route = '/bodega-central'
JOIN system_modules c ON c.parent_id = p.id AND c.route = '/bodega-central/traslados'
WHERE NOT EXISTS (SELECT 1 FROM role_modules x WHERE x.role_id = rm.role_id AND x.module_id = c.id);
