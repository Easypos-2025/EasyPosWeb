-- 054 — Meseros y Empleados en la web.
--   Escritorio: empleados → pos_employees y meseros → pos_waiters (mismo código = cod_empleado).
--   En la web un registro se guarda en AMBAS tablas con el mismo código. user_id lo liga al usuario web
--   ("Agregarme como mesero"). tipo_empleado del escritorio → pos_employee_types (lo sube el agente;
--   las empresas sin escritorio arrancan con los mismos tipos del escritorio).
--   Revisar transacciones abiertas y usar lock_wait_timeout=10 antes de aplicar en el servidor.

CREATE TABLE IF NOT EXISTS pos_employee_types (
    company_id  INT          NOT NULL,
    cod_tipo    INT          NOT NULL,                 -- tipo_empleado.Cod_Tipo
    name        VARCHAR(50)  NOT NULL,                 -- tipo_empleado.Nombre
    porcentaje  DOUBLE       NOT NULL DEFAULT 0,       -- tipo_empleado.Porcentaje
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (company_id, cod_tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

ALTER TABLE pos_waiters   ADD COLUMN user_id INT NULL, ADD KEY idx_pw_user (company_id, user_id);
ALTER TABLE pos_employees ADD COLUMN user_id INT NULL, ADD KEY idx_pe_user (company_id, user_id);

-- Vista nueva, colgada del padre "Configuracion"
INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Meseros y Empleados', '/configuration/meseros', 'bi-person-badge',
       (SELECT id FROM system_modules WHERE name = 'Configuracion' AND (route IS NULL OR route = '') ORDER BY id LIMIT 1),
       1, 0, 0
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM system_modules WHERE route = '/configuration/meseros');

-- En el menú de cada perfil que tiene "Configuracion", debajo de ella
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT p.business_profile_id, m.id, p.id, 999
FROM business_profile_modules p
JOIN system_modules c ON c.id = p.module_id AND c.name = 'Configuracion' AND (c.route IS NULL OR c.route = '')
JOIN system_modules m ON m.route = '/configuration/meseros'
WHERE NOT EXISTS (SELECT 1 FROM business_profile_modules y
                  WHERE y.business_profile_id = p.business_profile_id AND y.module_id = m.id);

-- Permiso solo para el rol Admin de esas empresas (los demás roles lo asigna el administrador)
INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
SELECT DISTINCT r.id, m.id, 1, 1, 1, 0
FROM roles r
JOIN companies co ON co.id_company = r.company_id
JOIN business_profile_modules b ON b.business_profile_id = co.business_profile_id
JOIN system_modules m ON m.id = b.module_id AND m.route = '/configuration/meseros'
WHERE UPPER(r.name) LIKE '%ADMIN%'
  AND NOT EXISTS (SELECT 1 FROM role_modules rm WHERE rm.role_id = r.id AND rm.module_id = m.id);

-- Formas de Medida queda en el menú de Insumos (aplicado a mano el 2026-10-15 junto con la 053)
UPDATE system_modules f
JOIN system_modules i ON i.route = '/inventory/supply-items'
SET f.parent_id = i.parent_id
WHERE f.route = '/configuration/formas-medida' AND NOT (f.parent_id <=> i.parent_id);
