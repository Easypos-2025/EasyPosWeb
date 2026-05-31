-- Agrega campo bill_requested a pos_orders para tracking de solicitud de cuenta
-- sin romper compatibilidad con el POS desktop (campo ignorado por desktop).

ALTER TABLE pos_orders
    ADD COLUMN IF NOT EXISTS `bill_requested` TINYINT(1) NOT NULL DEFAULT 0;

-- Módulos de sistema para vistas de comandera y cocina TV
-- parent_id=NULL: el admin lo ubica en el menú desde SidebarMenuManager
INSERT IGNORE INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
VALUES
  ('Comandera', '/pos/comanda/login', 'bi-tablet', NULL, 1, 0, 0),
  ('Cocina TV', '/pos/cocina', 'bi-display', NULL, 1, 0, 0);
