-- 029 — Vales y Abono de Vales (menú Transaccional)
--
-- Vales (vales del escritorio → pos_cash_advances): dinero que sale de la caja a un empleado.
--   status (Estado): 0 = pendiente, 1 = pagado. Forma de pago en pos_cash_movement_payments type_id = 5.
-- Abono de Vales (solo web): el empleado devuelve el vale completo; entra a la caja del Id_Caja abierto.
--   pos_cash_advance_payments, forma de pago type_id = 6 (EFECTIVO por defecto). Al abonar, el vale
--   queda status = 1; al anular el abono vuelve a 0. Nunca se elimina: se anula.

CREATE TABLE IF NOT EXISTS pos_cash_advance_payments (
  id            BIGINT NOT NULL AUTO_INCREMENT,
  id_registro   BIGINT NOT NULL DEFAULT 0,
  company_id    INT NOT NULL DEFAULT 0,
  register_id   BIGINT NOT NULL DEFAULT 0,          -- Id_Caja donde entra el abono
  advance_id    BIGINT NOT NULL DEFAULT 0,          -- Cod_Vale (pos_cash_advances.id_registro)
  date          DATE DEFAULT NULL,
  amount        DOUBLE DEFAULT 0,
  employee_code VARCHAR(15) DEFAULT NULL,           -- empleado del vale
  detail        VARCHAR(255) DEFAULT NULL,
  shift         TINYINT DEFAULT 0,
  synced        TINYINT DEFAULT 0,
  voided        TINYINT NOT NULL DEFAULT 0,
  void_reason   VARCHAR(255) DEFAULT NULL,
  voided_by     INT DEFAULT NULL,
  voided_at     DATETIME DEFAULT NULL,
  created_by    INT DEFAULT NULL,
  created_at    DATETIME DEFAULT NULL,
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cadvp (id_registro, company_id),
  KEY ix_cadvp_reg (company_id, register_id),
  KEY ix_cadvp_vale (company_id, advance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE INDEX IF NOT EXISTS ix_cadv_status ON pos_cash_advances (company_id, status);

-- ── Menú: Vales y Abono Vales dentro de Transaccional (padre de /caja/cuadre) ──
SET @padre = (SELECT parent_id FROM system_modules WHERE route = '/caja/cuadre' LIMIT 1);
INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT x.name, x.route, x.icon, @padre, 1, x.ord, 0
FROM (SELECT 'Vales' name, '/caja/vales' route, 'bi-cash-coin' icon, 6 ord
      UNION ALL SELECT 'Abono Vales', '/caja/abono-vales', 'bi-arrow-return-left', 7) x
WHERE @padre IS NOT NULL AND NOT EXISTS (SELECT 1 FROM system_modules s WHERE s.route = x.route);

-- Perfil Restaurante (1): en el menú, bajo el mismo padre
SET @bpm_padre = (SELECT id FROM business_profile_modules WHERE business_profile_id = 1 AND module_id = @padre LIMIT 1);
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT 1, s.id, @bpm_padre, s.order_index
FROM system_modules s
WHERE s.route IN ('/caja/vales', '/caja/abono-vales') AND @bpm_padre IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM business_profile_modules b WHERE b.business_profile_id = 1 AND b.module_id = s.id);

-- Permiso de ver: los roles que ya ven Cuadre Caja
INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
SELECT DISTINCT rm.role_id, s.id, 1, 1, 1, 0
FROM role_modules rm
JOIN system_modules cu ON cu.id = rm.module_id AND cu.route = '/caja/cuadre'
JOIN system_modules s ON s.route IN ('/caja/vales', '/caja/abono-vales')
WHERE rm.can_view = 1
  AND NOT EXISTS (SELECT 1 FROM role_modules x WHERE x.role_id = rm.role_id AND x.module_id = s.id);
