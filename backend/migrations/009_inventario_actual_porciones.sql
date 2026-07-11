-- ============================================================
-- Migración 009: Tabla inventario_actual_porciones
-- Tabla separada de supply_items para stock actual calculado.
-- Sincroniza con VB6 desktop via /sync/push/inventory-stock.
-- Ejecutar en LOCAL y PRODUCCIÓN
-- ============================================================

CREATE TABLE IF NOT EXISTS inventario_actual_porciones (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    company_id         INT             NOT NULL,
    id_grupo           INT             NOT NULL DEFAULT 0,
    id_item            INT             NOT NULL,
    codigo_insumo      VARCHAR(100),
    descripcion        VARCHAR(255),
    costo              FLOAT           NOT NULL DEFAULT 0,
    und_compra         INT             NOT NULL DEFAULT 0,
    valor_und_compra   FLOAT           NOT NULL DEFAULT 0,
    und_min_utilizadas FLOAT           NOT NULL DEFAULT 0,
    agrupar            INT             NOT NULL DEFAULT 0,
    compras            TINYINT         NOT NULL DEFAULT 0,
    controlar          TINYINT         NOT NULL DEFAULT 0,
    opcion_cambios     TINYINT         NOT NULL DEFAULT 0,
    und_uso            INT             NOT NULL DEFAULT 0,
    centro_produccion  TINYINT         NOT NULL DEFAULT 0,
    cantidad_actual    FLOAT           NOT NULL DEFAULT 0,
    bodega             TINYINT         NOT NULL DEFAULT 0,
    insumo_cp          TINYINT         NOT NULL DEFAULT 0,
    fecha_vence        DATE,
    stock_minimo       FLOAT           NOT NULL DEFAULT 0,
    enviada_mysql      TINYINT         NOT NULL DEFAULT 0,
    updated_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_iap (company_id, id_item),
    INDEX idx_iap_agrupar (company_id, agrupar),
    INDEX idx_iap_sync    (company_id, enviada_mysql)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
