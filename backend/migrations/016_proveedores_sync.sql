-- ============================================================
-- Migración 016: suppliers = espejo web de `proveedores` del escritorio
-- Base: easyposweb — Ejecutar en LOCAL y PRODUCCIÓN (después de la 015)
--
-- Mapeo escritorio → web:
--   Id_Proveedor      → id_proveedor  (consecutivo POR EMPRESA; es el que usan
--                                      plato_producto.id_proveedor e insumos_proveedor)
--   Nit               → nit
--   Empresa           → name
--   Mail_Empresa      → email
--   Direccion         → address
--   Telefono_Fijo     → phone
--   Telefono_Celular  → telefono_celular
--   Observaciones     → notes
--   Activo            → is_active   (1 = activo, igual en ambos lados)
-- ============================================================

ALTER TABLE suppliers
    ADD COLUMN id_proveedor     INT(11)     NULL AFTER company_id,
    ADD COLUMN telefono_celular VARCHAR(50) NULL AFTER phone,
    ADD COLUMN synced           TINYINT(4)  NOT NULL DEFAULT 0,
    ADD COLUMN updated_at       DATETIME    NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Proveedores creados antes en la web: consecutivo por empresa
UPDATE suppliers s
JOIN (SELECT id, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY id) AS rn
      FROM suppliers) x ON x.id = s.id
SET s.id_proveedor = x.rn
WHERE s.id_proveedor IS NULL;

ALTER TABLE suppliers
    ADD UNIQUE KEY uq_suppliers_prov (company_id, id_proveedor),
    ADD KEY idx_suppliers_sync (company_id, updated_at);
