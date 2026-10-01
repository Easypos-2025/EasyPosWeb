-- 025 — Movimientos de caja (Cuadre de Caja · Gastos · Compras · Otros Ingresos · Otros Egresos)
--
-- Tablas espejo del escritorio (mismas columnas que pos_expenses / pos_purchases):
--   conceptos                    → pos_cash_concepts      (concept_type = tipo_concepto: 1 Gastos,
--                                                          2 Compras, 3 Otros Egresos, 4 Otros Ingresos)
--   sub_conceptos                → pos_cash_subconcepts
--   otros_ingresos               → pos_other_incomes
--   otros_egresos                → pos_other_expenses
--   vales                        → pos_cash_advances
--   ingresos_egresos_forma_pago  → pos_cash_movement_payments (type_id = tipo_concepto, 5 = Vales)
--   caja_facturas                → pos_cash_register_invoices (ya existe en el servidor)
-- register_id = id del turno (pos_cash_register_closings.id), igual que caja_recibos.Id_Caja.
-- La sincronización con el escritorio de estas tablas queda pendiente.

CREATE TABLE IF NOT EXISTS pos_cash_concepts (
  id           BIGINT NOT NULL AUTO_INCREMENT,
  company_id   INT NOT NULL DEFAULT 0,
  concept_id   INT NOT NULL DEFAULT 0,
  description  VARCHAR(50) NOT NULL,
  concept_type INT DEFAULT 0,
  is_active    TINYINT DEFAULT 1,
  synced       TINYINT DEFAULT 0,
  updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cash_concept (company_id, concept_id),
  KEY ix_cash_concept_type (company_id, concept_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS pos_cash_subconcepts (
  id             BIGINT NOT NULL AUTO_INCREMENT,
  company_id     INT NOT NULL DEFAULT 0,
  concept_id     INT NOT NULL DEFAULT 0,
  subconcept_id  INT NOT NULL DEFAULT 0,
  description    VARCHAR(50) NOT NULL,
  is_active      TINYINT DEFAULT 1,
  synced         TINYINT DEFAULT 0,
  updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cash_subconcept (company_id, concept_id, subconcept_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS pos_other_incomes (
  id              BIGINT NOT NULL AUTO_INCREMENT,
  id_registro     BIGINT NOT NULL DEFAULT 0,
  company_id      INT NOT NULL DEFAULT 0,
  register_id     BIGINT NOT NULL DEFAULT 0,
  date            DATE DEFAULT NULL,
  amount          FLOAT DEFAULT 0,
  employee_code   VARCHAR(15) DEFAULT NULL,
  concept_id      INT DEFAULT 0,
  sub_concept_id  INT DEFAULT 0,
  shift           TINYINT DEFAULT 0,
  movement_number INT DEFAULT 0,
  detail          VARCHAR(255) DEFAULT NULL,
  synced          TINYINT DEFAULT 0,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_oinc (id_registro, company_id),
  KEY ix_oinc_reg (company_id, register_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS pos_other_expenses (
  id              BIGINT NOT NULL AUTO_INCREMENT,
  id_registro     BIGINT NOT NULL DEFAULT 0,
  company_id      INT NOT NULL DEFAULT 0,
  register_id     BIGINT NOT NULL DEFAULT 0,
  date            DATE DEFAULT NULL,
  amount          FLOAT DEFAULT 0,
  employee_code   VARCHAR(15) DEFAULT NULL,
  concept_id      INT DEFAULT 0,
  sub_concept_id  INT DEFAULT 0,
  shift           TINYINT DEFAULT 0,
  movement_number INT DEFAULT 0,
  detail          VARCHAR(255) DEFAULT NULL,
  synced          TINYINT DEFAULT 0,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_oexp (id_registro, company_id),
  KEY ix_oexp_reg (company_id, register_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS pos_cash_advances (
  id            BIGINT NOT NULL AUTO_INCREMENT,
  id_registro   BIGINT NOT NULL DEFAULT 0,
  company_id    INT NOT NULL DEFAULT 0,
  register_id   BIGINT NOT NULL DEFAULT 0,
  date          DATE DEFAULT NULL,
  amount        FLOAT DEFAULT 0,
  employee_code VARCHAR(15) DEFAULT NULL,
  status        TINYINT DEFAULT 0,
  description   VARCHAR(255) DEFAULT NULL,
  shift         TINYINT DEFAULT 0,
  synced        TINYINT DEFAULT 0,
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cadv (id_registro, company_id),
  KEY ix_cadv_reg (company_id, register_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS pos_cash_movement_payments (
  id                BIGINT NOT NULL AUTO_INCREMENT,
  id_registro       BIGINT NOT NULL DEFAULT 0,
  company_id        INT NOT NULL DEFAULT 0,
  register_id       BIGINT NOT NULL DEFAULT 0,
  item              INT DEFAULT 0,
  payment_method_id INT DEFAULT 0,
  card_id           INT DEFAULT 0,
  invoice_number    VARCHAR(50) DEFAULT NULL,
  type_id           INT DEFAULT 0,
  shift             INT DEFAULT 0,
  amount            DOUBLE DEFAULT 0,
  date              DATE DEFAULT NULL,
  authorization     DOUBLE DEFAULT 0,
  notes             VARCHAR(255) DEFAULT NULL,
  movement_id       BIGINT DEFAULT 0,
  synced            TINYINT DEFAULT 0,
  updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cmp (id_registro, company_id),
  KEY ix_cmp_mov (company_id, type_id, movement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS pos_cash_register_invoices (
  register_number    INT NOT NULL DEFAULT 0,
  closing_id         BIGINT NOT NULL DEFAULT 0,
  invoice_number     VARCHAR(50) NOT NULL,
  date               DATE DEFAULT NULL,
  order_number       VARCHAR(255) DEFAULT NULL,
  amount             DOUBLE DEFAULT 0,
  base_amount        DOUBLE DEFAULT 0,
  tax_vat            DOUBLE DEFAULT 0,
  tax_consumption    DOUBLE DEFAULT 0,
  employee_id        INT DEFAULT 0,
  shift              INT DEFAULT 0,
  source_pc          VARCHAR(255) DEFAULT NULL,
  delivery_person_id INT DEFAULT 0,
  invoice_notes      MEDIUMTEXT DEFAULT NULL,
  prefix             MEDIUMTEXT DEFAULT NULL,
  fac_pe             MEDIUMTEXT DEFAULT NULL,
  synced             TINYINT DEFAULT 0,
  company_id         INT NOT NULL DEFAULT 0,
  updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_cri_key (invoice_number, company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Índices para el cuadre (por turno)
CREATE INDEX IF NOT EXISTS ix_crr_closing ON pos_cash_register_receipts (company_id, closing_id);
CREATE INDEX IF NOT EXISTS ix_cri_closing ON pos_cash_register_invoices (company_id, closing_id);
CREATE INDEX IF NOT EXISTS ix_exp_reg ON pos_expenses (company_id, register_id);
CREATE INDEX IF NOT EXISTS ix_pur_reg ON pos_purchases (company_id, register_id);
CREATE INDEX IF NOT EXISTS ix_crc_date ON pos_cash_register_closings (company_id, date);

-- ── Menú: padre "Transaccional" (sin ruta, como los demás padres) + 5 hijos ──
-- Idempotente: el padre se ubica por su hijo /caja/cuadre (el nombre se puede cambiar desde SYSADMIN)
SET @padre = (SELECT parent_id FROM system_modules WHERE route = '/caja/cuadre' LIMIT 1);
INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Transaccional', NULL, 'bi-safe2', NULL, 1, 0, 0 FROM DUAL WHERE @padre IS NULL;
SET @padre = COALESCE(@padre, LAST_INSERT_ID());

INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT x.name, x.route, x.icon, @padre, 1, x.ord, 0
FROM (SELECT 'Cuadre Caja' name, '/caja/cuadre' route, 'bi-calculator' icon, 1 ord
      UNION ALL SELECT 'Registro Gastos', '/caja/gastos', 'bi-wallet2', 2
      UNION ALL SELECT 'Registro Compras', '/caja/compras', 'bi-bag', 3
      UNION ALL SELECT 'Otros Ingresos', '/caja/otros-ingresos', 'bi-box-arrow-in-down-right', 4
      UNION ALL SELECT 'Otros Egresos', '/caja/otros-egresos', 'bi-box-arrow-up-right', 5) x
WHERE NOT EXISTS (SELECT 1 FROM system_modules s WHERE s.route = x.route);

-- Perfil Restaurante (1): padre + hijos en su menú
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT 1, @padre, NULL, 50
WHERE NOT EXISTS (SELECT 1 FROM business_profile_modules WHERE business_profile_id = 1 AND module_id = @padre);
SET @bpm_padre = (SELECT id FROM business_profile_modules WHERE business_profile_id = 1 AND module_id = @padre LIMIT 1);
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT 1, s.id, @bpm_padre, s.order_index
FROM system_modules s
WHERE s.parent_id = @padre
  AND NOT EXISTS (SELECT 1 FROM business_profile_modules b WHERE b.business_profile_id = 1 AND b.module_id = s.id);

-- Permiso de ver para los roles de las empresas con perfil Restaurante
INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
SELECT DISTINCT r.id, s.id, 1, 1, 1, 0
FROM roles r
JOIN companies c ON c.id_company = r.company_id AND c.business_profile_id = 1
JOIN system_modules s ON s.id = @padre OR s.parent_id = @padre
WHERE NOT EXISTS (SELECT 1 FROM role_modules rm WHERE rm.role_id = r.id AND rm.module_id = s.id);
