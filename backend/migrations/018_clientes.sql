-- ============================================================
-- Migración 018: clientes = espejo web de la tabla `clientes` del escritorio
-- Base: easyposweb — Ejecutar en LOCAL y PRODUCCIÓN (después de la 017)
--
-- Columnas del escritorio en minúscula + company_id (misma convención que
-- inventario_porciones_plato). id_cliente = clientes.Id_Cliente del escritorio.
-- id_cliente = 1 → "Consumidor Final" (cédula 222222222222); el servidor lo crea
-- la primera vez que una empresa lo necesite (CLAUDE.md §8.1).
-- Es la tabla que referencian temp_comanda.Id_Cliente y lista_precios_cliente.Id_Cliente.
-- ============================================================

CREATE TABLE IF NOT EXISTS `clientes` (
  `id`                INT(11)      NOT NULL AUTO_INCREMENT,
  `company_id`        INT(11)      NOT NULL,
  `id_cliente`        BIGINT(20)   NOT NULL,
  `cedula`            VARCHAR(50)  DEFAULT NULL,
  `nombres`           VARCHAR(150) DEFAULT NULL,
  `apellidos`         VARCHAR(150) DEFAULT NULL,
  `direccion`         VARCHAR(255) DEFAULT NULL,
  `telefono`          VARCHAR(250) DEFAULT NULL,
  `barrio`            VARCHAR(100) DEFAULT NULL,
  `mail`              VARCHAR(150) DEFAULT NULL,
  `dia_cumple`        VARCHAR(50)  DEFAULT NULL,
  `mes_cumple`        VARCHAR(50)  DEFAULT NULL,
  `edad`              VARCHAR(50)  DEFAULT NULL,
  `ocupacion`         VARCHAR(50)  DEFAULT NULL,
  `porc_descuento`    VARCHAR(50)  DEFAULT NULL,
  `observaciones`     VARCHAR(255) DEFAULT NULL,
  `fecha_aniversario` DATE         DEFAULT NULL,
  `fecha_grado`       DATE         DEFAULT NULL,
  `empresa`           VARCHAR(150) DEFAULT NULL,
  `id_klob`           VARCHAR(50)  DEFAULT NULL,
  `tarjeta_fiel`      VARCHAR(50)  DEFAULT NULL,
  `cod_barrio`        INT(11)      NOT NULL DEFAULT 0,
  `id_sede`           INT(11)      NOT NULL DEFAULT 0,
  `referencia`        VARCHAR(255) DEFAULT NULL,
  `enviada_mysql`     TINYINT(4)   NOT NULL DEFAULT 0,
  `updated_at`        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_clientes` (`company_id`, `id_cliente`),
  KEY `idx_clientes_cedula` (`company_id`, `cedula`),
  KEY `idx_clientes_nombres` (`company_id`, `nombres`),
  KEY `idx_clientes_sync` (`company_id`, `updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
