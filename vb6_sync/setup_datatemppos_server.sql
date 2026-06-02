-- ============================================================
-- setup_datatemppos_server.sql
-- Crea la base de datos datatemppos en el servidor VPS
-- Replica las 5 tablas operativas de EasyPOS Desktop
-- con company_id agregado para soporte multitenant
-- ============================================================

CREATE DATABASE IF NOT EXISTS datatemppos
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE datatemppos;

-- ── temp_comanda ──────────────────────────────────────────────
-- Cabecera de pedidos activos.
-- Movil=0 = origen desktop/VB6, Movil=1 = origen web/tablet
CREATE TABLE IF NOT EXISTS `temp_comanda` (
  `company_id`          INT(11)       NOT NULL DEFAULT 0,
  `Nro_Pedido`          VARCHAR(255)  NOT NULL,
  `Fecha`               VARCHAR(10)   NOT NULL DEFAULT '0',
  `Nro_Factura`         VARCHAR(50)   NOT NULL DEFAULT '0',
  `Mesa`                VARCHAR(200)  DEFAULT '0',
  `Hora`                VARCHAR(50)   DEFAULT NULL,
  `Mesero`              INT(11)       DEFAULT 0,
  `Cancelado`           TINYINT(4)    DEFAULT 0,
  `Valor`               INT(11)       DEFAULT 0,
  `Salio`               TINYINT(4)    DEFAULT 0,
  `Novedad`             VARCHAR(250)  DEFAULT NULL,
  `Cortesia`            TINYINT(4)    DEFAULT 0,
  `Imprimio_Precuenta`  INT(11)       DEFAULT 0,
  `Nro_Comenzales`      INT(11)       DEFAULT 0,
  `Mostrar`             TINYINT(4)    DEFAULT 0,
  `Nro_Puestos`         INT(11)       DEFAULT 0,
  `Domicilio`           TINYINT(4)    DEFAULT 0,
  `Id_Cliente`          INT(11)       DEFAULT 0,
  `Movil`               TINYINT(4)    DEFAULT 0,
  `updated_at`          DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`company_id`, `Nro_Pedido`, `Fecha`, `Nro_Factura`),
  KEY `idx_fecha`        (`company_id`, `Fecha`),
  KEY `idx_mesa`         (`company_id`, `Mesa`(50)),
  KEY `idx_cancelado`    (`company_id`, `Fecha`, `Cancelado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ── temp_detalle_comanda_parcial ──────────────────────────────
-- Items activos de cada pedido. Mostrar=1 = registro maestro.
-- Nota: sin Enviada_MySql (flag solo para VB6 local)
CREATE TABLE IF NOT EXISTS `temp_detalle_comanda_parcial` (
  `company_id`              INT(11)        NOT NULL DEFAULT 0,
  `Nro_pedido`              VARCHAR(255)   NOT NULL DEFAULT '0',
  `Fecha`                   DATE           NOT NULL,
  `Nro_Factura`             VARCHAR(100)   DEFAULT '0',
  `Id_Plato`                INT(11)        NOT NULL DEFAULT 0,
  `Item`                    INT(11)        NOT NULL DEFAULT 0,
  `Descripcion`             VARCHAR(255)   DEFAULT NULL,
  `Cantidad`                FLOAT          NOT NULL DEFAULT 0,
  `Valor`                   INT(11)        DEFAULT 0,
  `Min`                     INT(11)        DEFAULT 0,
  `Min_S`                   INT(11)        DEFAULT 0,
  `Hora`                    TEXT           DEFAULT NULL,
  `Salio`                   TINYINT(1)     DEFAULT 0,
  `Novedad`                 VARCHAR(250)   DEFAULT NULL,
  `Cortesia`                TINYINT(4)     DEFAULT 0,
  `Porc_Descuento_Plato`    FLOAT          DEFAULT 0,
  `Porc_Descuento_General`  FLOAT          DEFAULT 0,
  `Impreso`                 TINYINT(4)     DEFAULT 0,
  `Cambios`                 VARCHAR(255)   DEFAULT NULL,
  `Mostrar`                 TINYINT(4)     DEFAULT 0,
  `Impresora`               VARCHAR(255)   DEFAULT NULL,
  `Depende`                 VARCHAR(50)    NOT NULL DEFAULT '',
  `Nro_Puesto`              INT(11)        DEFAULT 1,
  `Cod_Categoria_Plato`     INT(11)        DEFAULT 0,
  `Hora_Plato`              VARCHAR(50)    DEFAULT '0',
  `Paga_Impuesto`           TINYINT(4)     DEFAULT 0,
  `Impuesto`                DECIMAL(10,0)  DEFAULT 0,
  `Impuesto_Original`       DECIMAL(10,0)  DEFAULT 0,
  `Paga_Plato`              TINYINT(4)     DEFAULT 0,
  `Item_Original`           INT(11)        DEFAULT 0,
  `Producto_Personalizado`  MEDIUMTEXT     DEFAULT NULL,
  `updated_at`              DATETIME       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`company_id`, `Nro_pedido`, `Fecha`, `Id_Plato`, `Item`, `Depende`),
  KEY `idx_pedido`  (`company_id`, `Nro_pedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ── temp_plato_producto_parcial ───────────────────────────────
-- Modificadores/armados seleccionados por item de pedido
CREATE TABLE IF NOT EXISTS `temp_plato_producto_parcial` (
  `company_id`             INT(11)      NOT NULL DEFAULT 0,
  `Nro_Pedido`             VARCHAR(255) NOT NULL DEFAULT '0',
  `Fecha`                  VARCHAR(50)  NOT NULL DEFAULT '0',
  `Nro_Factura`            VARCHAR(50)  NOT NULL DEFAULT '0',
  `Id_Plato`               INT(11)      NOT NULL DEFAULT 0,
  `Item`                   INT(11)      NOT NULL DEFAULT 0,
  `Id_Grupo`               INT(11)      NOT NULL DEFAULT 0,
  `Id_Item`                INT(11)      NOT NULL DEFAULT 0,
  `Cantidad`               FLOAT        DEFAULT 0,
  `Item_Original`          INT(11)      DEFAULT 0,
  `Posicion`               INT(11)      DEFAULT 0,
  `Opcion_Cambiar`         TINYINT(4)   DEFAULT 0,
  `Valor_Adicional_Armar`  DOUBLE       DEFAULT 0,
  `updated_at`             DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`company_id`, `Nro_Pedido`, `Fecha`, `Nro_Factura`, `Id_Plato`, `Item`, `Id_Grupo`, `Id_Item`),
  KEY `idx_pedido`  (`company_id`, `Nro_Pedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ── temp_mesa_abierta ─────────────────────────────────────────
-- Estado de apertura de mesas (sincronizado desde VB6)
CREATE TABLE IF NOT EXISTS `temp_mesa_abierta` (
  `company_id`    INT(11)      NOT NULL DEFAULT 0,
  `Id_Mesa`       INT(11)      NOT NULL DEFAULT 0,
  `Mesa`          VARCHAR(255) DEFAULT NULL,
  `Abierta`       TINYINT(4)   DEFAULT 0,
  `Abierta_Desde` VARCHAR(100) DEFAULT NULL,
  `updated_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`company_id`, `Id_Mesa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ── temp_novedades_plato_pedido ───────────────────────────────
-- Notas/modificaciones especiales por item de pedido
CREATE TABLE IF NOT EXISTS `temp_novedades_plato_pedido` (
  `company_id`     INT(11)      NOT NULL DEFAULT 0,
  `Id_Consecutivo` INT(11)      NOT NULL DEFAULT 0,
  `Nro_Pedido`     VARCHAR(255) NOT NULL DEFAULT '0',
  `Item`           INT(11)      NOT NULL DEFAULT 0,
  `Depende`        INT(11)      NOT NULL DEFAULT 0,
  `Cod_Categoria`  INT(11)      NOT NULL DEFAULT 0,
  `Id_Novedad`     INT(11)      NOT NULL DEFAULT 0,
  `Novedad`        MEDIUMTEXT   DEFAULT NULL,
  `updated_at`     DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`company_id`, `Id_Consecutivo`, `Nro_Pedido`, `Item`, `Depende`, `Cod_Categoria`, `Id_Novedad`),
  KEY `idx_pedido`  (`company_id`, `Nro_Pedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
