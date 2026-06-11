-- ============================================================
-- Migración 006: Tablas apidian (facturación electrónica DIAN)
--               + consecutivos de factura manual y sistema
-- Ejecutar en LOCAL y PRODUCCIÓN
-- ============================================================

-- 1. apidian_caja_facturas
CREATE TABLE IF NOT EXISTS apidian_caja_facturas (
    id                   INT           AUTO_INCREMENT PRIMARY KEY,
    Nro_Caja             INT           NOT NULL DEFAULT 0,
    Nro_Factura          VARCHAR(100)  NOT NULL DEFAULT '',
    Fecha                DATE          NULL,
    Nro_Pedido           TEXT          NULL,
    Valor                DOUBLE        NOT NULL DEFAULT 0,
    Base                 DOUBLE        NOT NULL DEFAULT 0,
    Impuesto_Iva         DOUBLE        NOT NULL DEFAULT 0,
    Impuesto_Impoconsumo DOUBLE        NOT NULL DEFAULT 0,
    Empleado             INT           NOT NULL DEFAULT 0,
    Turno                INT           NOT NULL DEFAULT 0,
    Pc_Desde             VARCHAR(100)  NULL,
    Cod_Domiciliario     INT           NOT NULL DEFAULT 0,
    Observacion_Factura  LONGTEXT      NULL,
    Prefix               VARCHAR(50)   NULL,
    Fac_PE               VARCHAR(50)   NULL,
    Enviada_MySql        TINYINT       NOT NULL DEFAULT 1,
    company_id           INT           NOT NULL,
    created_at           TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_acf (company_id, Nro_Caja, Nro_Factura),
    INDEX idx_acf_fecha  (company_id, Fecha),
    INDEX idx_acf_pedido (company_id, Nro_Caja)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. apidian_clientes_adquiriente
CREATE TABLE IF NOT EXISTS apidian_clientes_adquiriente (
    id               INT           AUTO_INCREMENT PRIMARY KEY,
    Id_Cliente       BIGINT        NOT NULL,
    cedula           VARCHAR(50)   NULL,
    PersonaJuridica  TINYINT       NOT NULL DEFAULT 0,
    Tipo_Documento   VARCHAR(20)   NULL,
    DV               VARCHAR(5)    NULL,
    RegContributivo  VARCHAR(50)   NULL,
    nombres          VARCHAR(255)  NULL,
    direccion        VARCHAR(500)  NULL,
    telefono         VARCHAR(50)   NULL,
    Mail             VARCHAR(255)  NULL,
    Observaciones    VARCHAR(500)  NULL,
    Enviada_MySql    TINYINT       NOT NULL DEFAULT 1,
    Referencia       VARCHAR(100)  NULL,
    Cod_Municipio    INT           NOT NULL DEFAULT 0,
    Ciudad           INT           NOT NULL DEFAULT 0,
    Departamento     INT           NOT NULL DEFAULT 0,
    CodPais          INT           NOT NULL DEFAULT 0,
    company_id       INT           NOT NULL,
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_aca (company_id, Id_Cliente),
    INDEX idx_aca_cedula (company_id, cedula)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. apidian_facturas_cufe
CREATE TABLE IF NOT EXISTS apidian_facturas_cufe (
    id                   INT           AUTO_INCREMENT PRIMARY KEY,
    Nro_Caja             INT           NOT NULL DEFAULT 0,
    Prefix               VARCHAR(50)   NOT NULL DEFAULT '',
    Nro_Factura          VARCHAR(100)  NOT NULL DEFAULT '',
    Tipo_Pago            VARCHAR(50)   NULL,
    Cedula               VARCHAR(50)   NULL,
    Fecha                DATE          NULL,
    Nro_Pedido           VARCHAR(100)  NULL,
    cufe                 VARCHAR(200)  NULL,
    FEExitosa            TINYINT       NOT NULL DEFAULT 0,
    Valor                DOUBLE        NOT NULL DEFAULT 0,
    Descuento            DOUBLE        NOT NULL DEFAULT 0,
    Empleado             INT           NOT NULL DEFAULT 0,
    Pc_Desde             VARCHAR(100)  NULL,
    Estado               VARCHAR(50)   NULL,
    VentaCerrada         TINYINT       NOT NULL DEFAULT 0,
    Observacion_Factura  MEDIUMTEXT    NULL,
    Hora                 MEDIUMTEXT    NULL,
    Enviada_MySql        TINYINT       NOT NULL DEFAULT 1,
    company_id           INT           NOT NULL,
    created_at           TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_afc (company_id, Nro_Caja, Prefix, Nro_Factura),
    INDEX idx_afc_fecha  (company_id, Fecha),
    INDEX idx_afc_cedula (company_id, Cedula)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. consecutivo_factura_manual
CREATE TABLE IF NOT EXISTS consecutivo_factura_manual (
    id               INT           AUTO_INCREMENT PRIMARY KEY,
    Id_Consecutivo   INT           NOT NULL,
    Nro_Pedido       VARCHAR(100)  NULL,
    Fecha            DATE          NULL,
    Id_Resolucion    INT           NOT NULL DEFAULT 0,
    Enviada_MySql    TINYINT       NOT NULL DEFAULT 1,
    company_id       INT           NOT NULL,
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_cfm (company_id, Id_Consecutivo),
    INDEX idx_cfm_fecha      (company_id, Fecha),
    INDEX idx_cfm_resolucion (company_id, Id_Resolucion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. consecutivo_factura_sistema
CREATE TABLE IF NOT EXISTS consecutivo_factura_sistema (
    id               INT           AUTO_INCREMENT PRIMARY KEY,
    Id_Consecutivo   INT           NOT NULL,
    Nro_Pedido       VARCHAR(100)  NULL,
    Fecha            DATE          NULL,
    Id_Resolucion    INT           NOT NULL DEFAULT 0,
    Enviada_MySql    TINYINT       NOT NULL DEFAULT 1,
    company_id       INT           NOT NULL,
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_cfs (company_id, Id_Consecutivo),
    INDEX idx_cfs_fecha      (company_id, Fecha),
    INDEX idx_cfs_resolucion (company_id, Id_Resolucion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
