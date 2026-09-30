-- 021 — Configuración de facturación (espejo de escritorio `configuracion_facturacion`)
--       y foto de los billetes rápidos.
-- Idempotente: se puede ejecutar más de una vez.

-- ── 1. Foto del billete (tabla solo web) ─────────────────────────────────────
ALTER TABLE pos_cash_denominations
  ADD COLUMN IF NOT EXISTS image_path VARCHAR(255) NULL AFTER sort_order;

-- ── 2. configuracion_facturacion: mismas columnas del escritorio en minúscula,
--       una fila por empresa (el escritorio tiene una por sede) ─────────────────
CREATE TABLE IF NOT EXISTS configuracion_facturacion (
  id                                INT AUTO_INCREMENT PRIMARY KEY,
  company_id                        INT NOT NULL,
  id_sede                           INT NULL,
  impuesto_iva                      DOUBLE NOT NULL DEFAULT 0,
  impuesto_impoconsumo              DOUBLE NOT NULL DEFAULT 0,
  impuesto_rete_fuente              DOUBLE NOT NULL DEFAULT 0,
  liquidar_propina                  TINYINT NOT NULL DEFAULT 0,
  resolucion_propina                LONGTEXT NULL,
  paga_impuesto                     TINYINT NOT NULL DEFAULT 0,
  precios_incluyen_impuesto         TINYINT NOT NULL DEFAULT 0,
  imprimir_logo_factura             TINYINT NOT NULL DEFAULT 0,
  nombre_logo_factura               VARCHAR(200) NULL,
  tipo_moneda                       TINYINT NOT NULL DEFAULT 1,
  texto_numeracion                  VARCHAR(100) NULL,
  nombre_cliente_facturacion_varia  VARCHAR(100) NULL,
  codigo_cliente_facturacion_varia  VARCHAR(100) NULL,
  id_cliente_facturacion_varia      DOUBLE NULL,
  usa_lector_barras                 TINYINT NOT NULL DEFAULT 0,
  imprimir_encabezado_factura       TINYINT NOT NULL DEFAULT 1,
  impresora_facturas                INT NULL,
  mensaje_factura                   VARCHAR(255) NULL,
  longitud_factura_sistema          INT NOT NULL DEFAULT 1,
  longitud_factura_manual           INT NOT NULL DEFAULT 1,
  cantidad_impresiones_factura      INT NOT NULL DEFAULT 1,
  porcentaje_propina                FLOAT NOT NULL DEFAULT 0,
  activar_precio_x_mayor            TINYINT NOT NULL DEFAULT 0,
  usar_precuenta                    TINYINT NOT NULL DEFAULT 0,
  imprimir_resolucion_propina       TINYINT NOT NULL DEFAULT 0,
  imprimir_datos_legales            TINYINT NOT NULL DEFAULT 0,
  imprimir_datos_cliente            TINYINT NOT NULL DEFAULT 0,
  imprimir_recibo_domiciliario      TINYINT NOT NULL DEFAULT 0,
  preguntar_valor_propina           TINYINT NOT NULL DEFAULT 0,
  usar_comanda_corta                TINYINT NOT NULL DEFAULT 0,
  synced                            TINYINT NOT NULL DEFAULT 0,
  created_at                        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at                        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_config_facturacion_company (company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 3. Conservar la propina ya configurada en company_configs ───────────────
INSERT INTO configuracion_facturacion (company_id, liquidar_propina, porcentaje_propina)
SELECT cc.company_id, COALESCE(cc.has_tip, 0), COALESCE(cc.tip_percentage, 0)
FROM company_configs cc
WHERE NOT EXISTS (SELECT 1 FROM configuracion_facturacion cf WHERE cf.company_id = cc.company_id);

-- ── 4. Módulo de la vista (Configuración → Configuración Facturación) ───────
INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Configuración Facturación', '/configuration/facturacion', 'bi-receipt-cutoff', NULL, 1, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_modules WHERE route = '/configuration/facturacion');
