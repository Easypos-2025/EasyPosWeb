-- ============================================================
-- Migración 015: Insumos fijos por plato + Cabecera de listas de precios por cliente
-- Base: easyposweb — Ejecutar en LOCAL y PRODUCCIÓN
--
-- 1. inventario_porciones_plato
--    Espejo web de la tabla de escritorio `inventario_porciones_plato`
--    (insumos FIJOS que descuenta un plato cada vez que se vende).
--    Misma convención que `inventario_actual_porciones` (migración 009):
--    nombre y columnas del escritorio en minúscula + company_id.
--    Llave natural: (company_id, id_plato, id_grupo, id_item).
--
-- 2. pos_customer_price_list_header
--    Cabecera de las listas de precios por cliente. El detalle sigue en
--    `pos_customer_price_list` (lista_precios_cliente) relacionado por id_lista.
--    Reglas:
--      - id_lista es consecutivo por company_id y se genera en la WEB
--        (el escritorio solo descarga; no crea listas → no hay choque de ids).
--      - id_lista = 0 queda reservado para la lista general (platos.Valor).
--      - Un cliente tiene una sola lista activa.
-- ============================================================

CREATE TABLE IF NOT EXISTS `inventario_porciones_plato` (
  `id`                     INT(11)    NOT NULL AUTO_INCREMENT,
  `company_id`             INT(11)    NOT NULL,
  `id_plato`               INT(11)    NOT NULL DEFAULT 0,
  `id_grupo`               INT(11)    NOT NULL DEFAULT 0,
  `id_item`                INT(11)    NOT NULL DEFAULT 0,
  `cantidad`               FLOAT      NOT NULL DEFAULT 0,
  `unidad_minima`          FLOAT      NOT NULL DEFAULT 0,
  `porciones_a_desccontar` FLOAT      NOT NULL DEFAULT 0,
  `posicion`               INT(11)    NOT NULL DEFAULT 0,
  `opcion_cambiar`         TINYINT(4) NOT NULL DEFAULT 0,
  `enviada_mysql`          TINYINT(4) NOT NULL DEFAULT 0,
  `updated_at`             DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ipp` (`company_id`, `id_plato`, `id_grupo`, `id_item`),
  KEY `idx_ipp_plato` (`company_id`, `id_plato`),
  KEY `idx_ipp_sync`  (`company_id`, `updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS `pos_customer_price_list_header` (
  `id`          INT(11)      NOT NULL AUTO_INCREMENT,
  `company_id`  INT(11)      NOT NULL,
  `id_lista`    INT(11)      NOT NULL,
  `id_cliente`  INT(11)      NOT NULL,
  `nombre`      VARCHAR(100) NOT NULL,
  `fecha`       DATE         DEFAULT NULL,
  `activa`      TINYINT(4)   NOT NULL DEFAULT 1,
  `usuario`     VARCHAR(50)  DEFAULT NULL,
  `observacion` VARCHAR(255) DEFAULT NULL,
  `synced`      TINYINT(4)   NOT NULL DEFAULT 0,
  `created_at`  DATETIME     DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_cplh_lista` (`company_id`, `id_lista`),
  KEY `idx_cplh_cliente` (`company_id`, `id_cliente`, `activa`),
  KEY `idx_cplh_sync`    (`company_id`, `updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
