-- 028 — Control de Acceso por rol (como el "Control de Acceso" del escritorio) y Conceptos de Caja
--
-- access_permissions:      catálogo de permisos especiales (agregar uno nuevo = una fila)
-- role_access_permissions: permisos habilitados por rol
-- Movimientos de caja: nunca se eliminan, se anulan (voided + motivo, quién y cuándo)

CREATE TABLE IF NOT EXISTS access_permissions (
  perm_key    VARCHAR(50)  NOT NULL,
  name        VARCHAR(120) NOT NULL,
  group_name  VARCHAR(60)  NOT NULL,
  description VARCHAR(255) DEFAULT NULL,
  order_index INT          NOT NULL DEFAULT 0,
  is_active   TINYINT      NOT NULL DEFAULT 1,
  PRIMARY KEY (perm_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS role_access_permissions (
  role_id  INT         NOT NULL,
  perm_key VARCHAR(50) NOT NULL,
  PRIMARY KEY (role_id, perm_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO access_permissions (perm_key, name, group_name, description, order_index) VALUES
  ('consultar_anteriores', 'Consultar Facturas y Cuadres Anteriores', 'Caja', 'Ver cuadres y movimientos de fechas anteriores a hoy', 10),
  ('ver_periodos',         'Ver Cuadres y Movimientos por Mes y Año', 'Caja', 'Consultar un mes o un año completo', 20),
  ('anular_movimientos',   'Anular Movimientos de Caja', 'Caja', 'Gastos, compras, otros ingresos y egresos, vales y abonos', 30),
  ('hacer_cierre',         'Hacer Cierre de Caja', 'Caja', 'Cerrar su Id_Caja desde el Cuadre de Caja', 40),
  ('usuario_caja',         'Es Usuario Caja', 'Caja', NULL, 50),
  ('cambiar_propina',      'Cambiar Propina', 'Ventas', NULL, 110),
  ('realizar_descuentos',  'Realizar Descuentos', 'Ventas', NULL, 120),
  ('reimprimir_facturas',  'Reimprimir Facturas', 'Ventas', NULL, 130),
  ('facturar',             'Facturar', 'Ventas', NULL, 140),
  ('generar_recibo',       'Generar Recibo', 'Ventas', NULL, 150),
  ('anular_facturas',      'Anular Facturas', 'Ventas', NULL, 160),
  ('obligar_imprimir',     'Obligar Imprimir Factura', 'Ventas', NULL, 170),
  ('ver_ventas',           'Ver Ventas', 'Ventas', NULL, 180),
  ('eliminar_cuentas',     'Eliminar Cuentas', 'Ventas', NULL, 190),
  ('eliminar_productos',   'Eliminar Productos', 'Ventas', NULL, 200),
  ('modulo_administrativo','Activar Módulo Administrativo', 'Administración', NULL, 310),
  ('panel_configuracion',  'Activar Panel Configuración', 'Administración', NULL, 320),
  ('registro_usuarios',    'Activar Registro Usuarios - Vendedores', 'Administración', NULL, 330)
ON DUPLICATE KEY UPDATE name = VALUES(name), group_name = VALUES(group_name),
                        description = VALUES(description), order_index = VALUES(order_index);

-- Valores iniciales: roles Admin con todo; los demás con "Hacer Cierre de Caja" (regla actual:
-- el dueño del Id_Caja puede cerrarlo). Solo para roles que aún no tienen ningún permiso.
INSERT IGNORE INTO role_access_permissions (role_id, perm_key)
SELECT r.id, p.perm_key
FROM roles r
JOIN access_permissions p
WHERE (UPPER(r.name) LIKE '%ADMIN%' OR p.perm_key = 'hacer_cierre')
  AND NOT EXISTS (SELECT 1 FROM role_access_permissions x WHERE x.role_id = r.id);

-- Anulación de movimientos (las tablas web; el escritorio no las toca al sincronizar)
ALTER TABLE pos_expenses       ADD COLUMN IF NOT EXISTS voided TINYINT NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS void_reason VARCHAR(255) NULL, ADD COLUMN IF NOT EXISTS voided_by INT NULL, ADD COLUMN IF NOT EXISTS voided_at DATETIME NULL, ADD COLUMN IF NOT EXISTS created_by INT NULL, ADD COLUMN IF NOT EXISTS created_at DATETIME NULL;
ALTER TABLE pos_purchases      ADD COLUMN IF NOT EXISTS voided TINYINT NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS void_reason VARCHAR(255) NULL, ADD COLUMN IF NOT EXISTS voided_by INT NULL, ADD COLUMN IF NOT EXISTS voided_at DATETIME NULL, ADD COLUMN IF NOT EXISTS created_by INT NULL, ADD COLUMN IF NOT EXISTS created_at DATETIME NULL;
ALTER TABLE pos_other_incomes  ADD COLUMN IF NOT EXISTS voided TINYINT NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS void_reason VARCHAR(255) NULL, ADD COLUMN IF NOT EXISTS voided_by INT NULL, ADD COLUMN IF NOT EXISTS voided_at DATETIME NULL, ADD COLUMN IF NOT EXISTS created_by INT NULL, ADD COLUMN IF NOT EXISTS created_at DATETIME NULL;
ALTER TABLE pos_other_expenses ADD COLUMN IF NOT EXISTS voided TINYINT NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS void_reason VARCHAR(255) NULL, ADD COLUMN IF NOT EXISTS voided_by INT NULL, ADD COLUMN IF NOT EXISTS voided_at DATETIME NULL, ADD COLUMN IF NOT EXISTS created_by INT NULL, ADD COLUMN IF NOT EXISTS created_at DATETIME NULL;
ALTER TABLE pos_cash_advances  ADD COLUMN IF NOT EXISTS voided TINYINT NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS void_reason VARCHAR(255) NULL, ADD COLUMN IF NOT EXISTS voided_by INT NULL, ADD COLUMN IF NOT EXISTS voided_at DATETIME NULL, ADD COLUMN IF NOT EXISTS created_by INT NULL, ADD COLUMN IF NOT EXISTS created_at DATETIME NULL;

-- ── Menú: "Conceptos de Caja" dentro de Configuración (mismo padre que Configuración Facturación) ──
INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Conceptos de Caja', '/configuration/conceptos-caja', 'bi-tags', NULL, 1, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_modules WHERE route = '/configuration/conceptos-caja');
SET @mod_conc = (SELECT id FROM system_modules WHERE route = '/configuration/conceptos-caja' LIMIT 1);
SET @bpm_cfg = (SELECT b.parent_id FROM business_profile_modules b JOIN system_modules s ON s.id = b.module_id
                WHERE b.business_profile_id = 1 AND s.route = '/configuration/facturacion' LIMIT 1);
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT 1, @mod_conc, @bpm_cfg, 90 FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM business_profile_modules WHERE business_profile_id = 1 AND module_id = @mod_conc);
INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
SELECT DISTINCT r.id, @mod_conc, 1, 1, 1, 0
FROM roles r JOIN companies c ON c.id_company = r.company_id AND c.business_profile_id = 1
WHERE UPPER(r.name) LIKE '%ADMIN%'
  AND NOT EXISTS (SELECT 1 FROM role_modules rm WHERE rm.role_id = r.id AND rm.module_id = @mod_conc);
