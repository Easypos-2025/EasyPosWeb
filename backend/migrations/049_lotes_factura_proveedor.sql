-- 049 — Factura de Proveedor, costeo por lotes (PEPS) y laboratorios (droguerías).
--
--   facturas_proveedor / facturas_proveedor_detalle
--       Una factura completa por pantalla (sin IVA, % de descuento por línea, costo = valor con descuento).
--       Empresa con escritorio: el agente la baja (inventario_porciones_precios + entrada manual tipificación 7
--       "REGISTRO PRECIOS" + costo); escritorio_estado / escritorio_registro llevan el control.
--   inv_lotes / inv_lote_consumos
--       Cada entrada al inventario crea un lote con su costo (y vencimiento en droguerías); cada salida gasta los
--       lotes del más viejo al más nuevo (PEPS) y deja el costo real de lo que salió (utilidad e inventario exactos).
--   laboratorios / laboratorio_insumo
--       Igual que el escritorio: el laboratorio de cada producto de droguería (laboratorio_insumo.Posicion_Insumo).

CREATE TABLE IF NOT EXISTS facturas_proveedor (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    company_id           INT NOT NULL,
    numero               INT NOT NULL,                       -- consecutivo de la empresa
    id_proveedor         INT NOT NULL,
    nro_factura          VARCHAR(40) NOT NULL,
    fecha                DATE NOT NULL,
    observacion          VARCHAR(255) NULL,
    subtotal             DECIMAL(16,2) NOT NULL DEFAULT 0,   -- antes de descuentos
    descuento            DECIMAL(16,2) NOT NULL DEFAULT 0,
    total                DECIMAL(16,2) NOT NULL DEFAULT 0,
    estado               VARCHAR(12) NOT NULL DEFAULT 'ACTIVA',   -- ACTIVA | ANULADA
    anulada_en           DATETIME NULL,
    anulada_por          VARCHAR(120) NULL,
    anulada_motivo       VARCHAR(255) NULL,
    escritorio_estado    VARCHAR(12) NOT NULL DEFAULT 'NO_APLICA', -- NO_APLICA | PENDIENTE | APLICADA | ERROR | REVERSA
    escritorio_registro  INT NULL,                           -- inventario_porciones_precios.Id_Registro del escritorio
    escritorio_error     VARCHAR(255) NULL,
    escritorio_en        DATETIME NULL,
    usuario_id           INT NULL,
    usuario              VARCHAR(120) NULL,
    ip                   VARCHAR(45) NULL,
    created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_fp_numero (company_id, numero),
    KEY idx_fp_prov (company_id, id_proveedor, nro_factura),
    KEY idx_fp_fecha (company_id, fecha),
    KEY idx_fp_escritorio (company_id, escritorio_estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS facturas_proveedor_detalle (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    factura_id           INT NOT NULL,
    company_id           INT NOT NULL,
    item                 INT NOT NULL,
    dish_id              INT NOT NULL,
    id_item              INT NOT NULL,                       -- insumo del producto (Id_Item = Id_Plato en comercio)
    nombre               VARCHAR(250) NOT NULL,
    codigo               VARCHAR(60) NULL,
    imei                 VARCHAR(60) NULL,                   -- unidad con IMEI (cargue unitario): producto propio, cantidad 1
    cantidad             DECIMAL(14,4) NOT NULL,
    valor_unitario       DECIMAL(16,2) NOT NULL,
    porc_descuento       DECIMAL(6,2) NOT NULL DEFAULT 0,
    valor_con_descuento  DECIMAL(16,4) NOT NULL,             -- costo nuevo del producto
    total                DECIMAL(16,2) NOT NULL,
    costo_anterior       DECIMAL(16,4) NOT NULL DEFAULT 0,
    fecha_vence          DATE NULL,                          -- droguerías
    lote_id              INT NULL,
    KEY idx_fpd_factura (factura_id),
    KEY idx_fpd_item (company_id, id_item),
    KEY idx_fpd_dish (company_id, dish_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inv_lotes (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    company_id           INT NOT NULL,
    id_item              INT NOT NULL,
    fecha                DATE NOT NULL,
    origen               VARCHAR(20) NOT NULL,               -- SALDO_INICIAL | FACTURA | ENTRADA | TRASLADO | AJUSTE | DEVOLUCION
    origen_id            INT NULL,
    costo_unitario       DECIMAL(16,4) NOT NULL DEFAULT 0,
    cantidad_inicial     DECIMAL(14,4) NOT NULL,
    cantidad_disponible  DECIMAL(14,4) NOT NULL,
    fecha_vence          DATE NULL,
    id_proveedor         INT NULL,
    nro_factura          VARCHAR(40) NULL,
    created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_lote_item (company_id, id_item, cantidad_disponible),
    KEY idx_lote_vence (company_id, fecha_vence),
    KEY idx_lote_origen (company_id, origen, origen_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inv_lote_consumos (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    company_id           INT NOT NULL,
    lote_id              INT NULL,                           -- NULL: salió sin lote (stock en negativo) al costo del producto
    id_item              INT NOT NULL,
    fecha                DATE NOT NULL,
    cantidad             DECIMAL(14,4) NOT NULL,
    costo_unitario       DECIMAL(16,4) NOT NULL DEFAULT 0,
    ref_tipo             VARCHAR(30) NOT NULL,               -- sale | exit | physical | traslado_bodega | factura_proveedor…
    ref_id               INT NULL,
    clave                VARCHAR(60) NULL,                   -- traslados: el destino copia el costo de lo que salió
    created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_cons_item (company_id, id_item, fecha),
    KEY idx_cons_lote (lote_id),
    KEY idx_cons_ref (company_id, ref_tipo, ref_id),
    KEY idx_cons_clave (company_id, clave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS laboratorios (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    company_id           INT NOT NULL,
    id_laboratorio       INT NOT NULL,                       -- Id_Laboratorio del escritorio
    nombre_laboratorio   VARCHAR(50) NOT NULL,
    porcentaje           INT NOT NULL DEFAULT 0,
    activo               TINYINT NOT NULL DEFAULT 1,
    synced               TINYINT NOT NULL DEFAULT 0,
    updated_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_lab (company_id, id_laboratorio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS laboratorio_insumo (
    company_id           INT NOT NULL,
    id_laboratorio       INT NOT NULL,
    posicion_insumo      INT NOT NULL,                       -- Posicion del insumo (= Id_Item = Id_Plato en comercio)
    PRIMARY KEY (company_id, id_laboratorio, posicion_insumo),
    KEY idx_labins_pos (company_id, posicion_insumo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Menú: "Factura de Proveedor" bajo el padre "Transaccional", en los perfiles que lo tienen y en los de comercio
-- (3 Droguerías, 7 Fruver, 8 Estancos, 11 Lujos Autos y Motos, 13 Mini-Market, 14 Almacén, 20 Ferreterías),
-- a los que se les agrega el padre al final del menú si no lo tienen.
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order, display_name)
SELECT bp.id, t.id, NULL,
       (SELECT COALESCE(MAX(x.sort_order), 0) + 1 FROM business_profile_modules x
        WHERE x.business_profile_id = bp.id AND x.parent_id IS NULL), NULL
FROM business_profiles bp
JOIN system_modules t ON t.name = 'Transaccional' AND t.route IS NULL
WHERE bp.id IN (3, 7, 8, 11, 13, 14, 20)
  AND NOT EXISTS (SELECT 1 FROM business_profile_modules y WHERE y.business_profile_id = bp.id AND y.module_id = t.id);

INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Factura de Proveedor', '/compras/factura-proveedor', 'bi-receipt-cutoff', NULL, 1, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_modules WHERE route = '/compras/factura-proveedor');

INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order, display_name)
SELECT DISTINCT b.business_profile_id, n.id, b.module_id,
       (SELECT COALESCE(MAX(x.sort_order), 0) + 1 FROM business_profile_modules x
        WHERE x.business_profile_id = b.business_profile_id AND x.parent_id = b.module_id), NULL
FROM business_profile_modules b
JOIN system_modules t ON t.id = b.module_id AND t.name = 'Transaccional' AND t.route IS NULL
JOIN system_modules n ON n.route = '/compras/factura-proveedor'
WHERE NOT EXISTS (SELECT 1 FROM business_profile_modules y
                  WHERE y.business_profile_id = b.business_profile_id AND y.module_id = n.id);

-- Los roles que registran compras de caja reciben la opción con los mismos permisos
INSERT INTO role_modules (role_id, module_id, can_view, can_view_all, can_create, can_edit, can_delete)
SELECT rm.role_id, n.id, rm.can_view, rm.can_view_all, rm.can_create, rm.can_edit, rm.can_delete
FROM role_modules rm
JOIN system_modules v ON v.id = rm.module_id AND v.route = '/caja/compras'
JOIN system_modules n ON n.route = '/compras/factura-proveedor'
WHERE NOT EXISTS (SELECT 1 FROM role_modules x WHERE x.role_id = rm.role_id AND x.module_id = n.id);
