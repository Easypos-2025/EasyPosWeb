-- 031 — Control de Acceso de Ventas aplicado (todo por rol, sin importar el perfil de negocio)
--
-- · Meseros-vendedores (meseros = pos_waiters, entran con PIN a la comanda / TPV) con rol de su empresa.
--   En cada empresa con meseros se crea el rol "VENDEDOR-MESERO" (sin permisos especiales: tomar
--   pedidos y quitar productos aún no impresos no requieren permiso) y se asigna a sus meseros.
--   Eliminar productos impresos, eliminar cuentas, descuentos, cobrar… se activan por rol.
-- · Reimprimir Facturas sin límite de tiempo: pos_receipts.print_count; los recibos existentes ya
--   se imprimieron (quedan en 1).

-- Tipo de acceso del rol: interno (panel / TPV) · remoto_login (cliente o vendedor externo con login,
-- solo sus pedidos) · remoto_publico (cliente final tipo Rappi, sin login). Cada tipo remoto tendrá su URL.
ALTER TABLE roles        ADD COLUMN IF NOT EXISTS access_type VARCHAR(20) NOT NULL DEFAULT 'interno';
ALTER TABLE pos_waiters  ADD COLUMN IF NOT EXISTS role_id INT NULL;
ALTER TABLE pos_receipts ADD COLUMN IF NOT EXISTS print_count INT NOT NULL DEFAULT 0;
UPDATE pos_receipts SET print_count = 1 WHERE print_count = 0;

INSERT INTO roles (name, description, company_id, is_system)
SELECT DISTINCT 'VENDEDOR-MESERO', 'Toma de pedidos (comanda / TPV)', w.company_id, 0
FROM pos_waiters w
WHERE w.company_id > 0
  AND NOT EXISTS (SELECT 1 FROM roles r WHERE r.company_id = w.company_id AND r.name = 'VENDEDOR-MESERO');

UPDATE pos_waiters w
JOIN roles r ON r.company_id = w.company_id AND r.name = 'VENDEDOR-MESERO'
SET w.role_id = r.id
WHERE w.role_id IS NULL;
