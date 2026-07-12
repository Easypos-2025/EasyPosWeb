-- Migración 010: historico_inventario_actual_porciones
-- Historial de cortes de inventario actual (snapshot completo de inventario_actual_porciones)
-- Cada corte agrupa un Id_Historico; todos los items del mismo corte comparten ese Id.
-- Sincronizado desde VB6 via SincronizarHistoricoInventarioActual → /sync/push/historico-inventario-actual

CREATE TABLE IF NOT EXISTS historico_inventario_actual_porciones (
    id               INT           NOT NULL AUTO_INCREMENT,
    company_id       INT           NOT NULL,
    id_historico     INT           NOT NULL DEFAULT 0,
    fecha            DATE          NOT NULL,
    id_grupo         INT           DEFAULT 0,
    id_item          INT           NOT NULL,
    codigo_insumo    VARCHAR(50)   DEFAULT NULL,
    descripcion      VARCHAR(200)  DEFAULT NULL,
    costo            FLOAT         DEFAULT 0,
    und_compra       INT           DEFAULT 0,
    valor_und_compra FLOAT         DEFAULT 0,
    und_min_utilizadas FLOAT       DEFAULT 0,
    posicion         INT           DEFAULT 0,
    agrupar          INT           DEFAULT 0,
    compras          TINYINT       DEFAULT 0,
    controlar        TINYINT       DEFAULT 0,
    opcion_cambios   TINYINT       DEFAULT 0,
    und_uso          INT           DEFAULT 0,
    centro_produccion TINYINT      DEFAULT 0,
    cantidad_actual  FLOAT         DEFAULT 0,
    cod_empleado     VARCHAR(50)   DEFAULT NULL,
    insumo_cp        TINYINT       DEFAULT 0,
    fecha_vence      DATE          DEFAULT NULL,
    stock_minimo     FLOAT         DEFAULT 0,
    synced           TINYINT       DEFAULT 0,
    created_at       DATETIME      DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_hist_corte_item (company_id, id_historico, id_item),
    INDEX idx_hist_fecha       (company_id, fecha),
    INDEX idx_hist_item        (company_id, id_item),
    INDEX idx_hist_synced      (synced)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
