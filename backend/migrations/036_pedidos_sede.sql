-- 036 — Pedidos web hacia el escritorio (sala de espera + aceptación en caja)
--
-- Empresas con Agente Local activo (company_local_agents.activo = 1): al "Enviar a cocina" en la web
-- el envío queda como un LOTE pendiente. El agente lo baja (cada 10 s), el cajero lo acepta o lo
-- rechaza (form VB6 o panel de la mini-app) y el agente lo pasa a los temporales del escritorio.
--   · Nada pasa sin intervención humana: pedido nuevo y productos agregados.
--   · Se respeta el precio de la nube.
--   · Los lotes NUNCA se borran: son el histórico para reclamos (también queda copia en el agente).
--
-- PARTE A: base easyposweb.

CREATE TABLE IF NOT EXISTS pos_sede_lotes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    company_id      INT           NOT NULL,
    nro_pedido      VARCHAR(255)  NOT NULL,
    tipo            ENUM('NUEVO','AGREGAR') NOT NULL,
    canal           VARCHAR(20)   NOT NULL DEFAULT 'MESA',
    id_mesa         INT           NOT NULL DEFAULT 0,
    mesa            VARCHAR(200)  NULL,
    mesero          INT           NOT NULL DEFAULT 0,
    mesero_nombre   VARCHAR(150)  NULL,
    id_cliente      INT           NOT NULL DEFAULT 1,
    comensales      INT           NOT NULL DEFAULT 1,
    total           INT           NOT NULL DEFAULT 0,
    items           INT           NOT NULL DEFAULT 0,
    estado          ENUM('PENDIENTE','RECIBIDO','ACEPTADO','APLICADO','RECHAZADO','ERROR') NOT NULL DEFAULT 'PENDIENTE',
    enviado_por     VARCHAR(150)  NULL,
    creado_en       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    recibido_en     DATETIME      NULL,
    procesado_en    DATETIME      NULL,
    aplicado_en     DATETIME      NULL,
    procesado_por   VARCHAR(150)  NULL,
    procesado_desde VARCHAR(20)   NULL,           -- VB / MINIAPP
    pc              VARCHAR(100)  NULL,
    motivo          VARCHAR(255)  NULL,           -- motivo del rechazo
    mensaje         VARCHAR(500)  NULL,           -- error al aplicar en el escritorio
    KEY ix_psl_estado (company_id, estado, id),
    KEY ix_psl_pedido (company_id, nro_pedido),
    KEY ix_psl_fecha  (company_id, creado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS pos_sede_lote_items (
    id                     INT AUTO_INCREMENT PRIMARY KEY,
    lote_id                INT            NOT NULL,
    company_id             INT            NOT NULL,
    item                   INT            NOT NULL,       -- Item en la nube (temp_detalle_comanda_parcial)
    id_plato               INT            NOT NULL,
    descripcion            VARCHAR(255)   NULL,
    cantidad               DECIMAL(12,3)  NOT NULL DEFAULT 1,
    valor                  INT            NOT NULL DEFAULT 0,
    novedad                VARCHAR(255)   NULL,
    cambios                VARCHAR(255)   NULL,
    producto_personalizado VARCHAR(1000)  NULL,
    insumos                TEXT           NULL,           -- JSON: temp_plato_producto_parcial del ítem
    novedades              TEXT           NULL,           -- JSON: temp_novedades_plato_pedido del ítem
    KEY ix_psli_lote (lote_id),
    KEY ix_psli_company (company_id, lote_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- PARTE B: base datatemppos DE LA WEB (la que usa DATATEMPPOS_URL en el servidor; tiene company_id).
-- Ejecutar conectado a esa base (USE datatemppos;). NO se ejecuta en el datatemppos de las sedes.
--   Sede_Pendiente = 1: el ítem se envió desde la web y espera la aceptación en caja
--   (bloqueado: no se edita, no se elimina, no sale en cocina ni se cobra en la web).
--
-- USE datatemppos;
-- ALTER TABLE temp_detalle_comanda_parcial ADD COLUMN Sede_Pendiente TINYINT NOT NULL DEFAULT 0;
