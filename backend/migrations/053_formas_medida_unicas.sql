-- 053 — measurement_units desaparece: toda unidad es una forma de medida (pos_measure_forms = forma_medida
--   del escritorio). La usaban la bodega de herramientas (bodega_items.unidad_id) y los materiales de Tareas
--   (guardan el nombre como texto, no el id). La vista "Unidades de Medida" pasa a ser "Formas de Medida".
--   MariaDB 10.6 (REGEXP_REPLACE / ROW_NUMBER). Aplicar en el servidor; en local la tabla ya no existe.

-- 1) Equivalencia por nombre normalizado (minúsculas, solo letras, sin la "s" final):
--    "Gramos" = "Gramo (s)", "Botella/s" = "Botella (s)", "Litro" = "Litro (s)"
DROP TEMPORARY TABLE IF EXISTS _mu_map;
CREATE TEMPORARY TABLE _mu_map AS
SELECT mu.id AS mu_id, mu.company_id, LEFT(TRIM(mu.name), 100) AS name,
       TRIM(TRAILING 's' FROM REGEXP_REPLACE(LOWER(mu.name), '[^a-zñáéíóú]', '')) AS clave,
       CAST(NULL AS SIGNED) AS forma_id
FROM measurement_units mu;

UPDATE _mu_map m
SET m.forma_id = (
    SELECT f.id FROM pos_measure_forms f
    WHERE f.company_id = m.company_id
      AND TRIM(TRAILING 's' FROM REGEXP_REPLACE(LOWER(f.name), '[^a-zñáéíóú]', '')) COLLATE utf8mb4_general_ci
          = m.clave COLLATE utf8mb4_general_ci
    ORDER BY f.is_active DESC, f.id
    LIMIT 1);

-- 2) Las que no tienen equivalente se crean como forma de medida (activa, pendiente de enviar al escritorio).
--    Empresas con escritorio: número provisional (>= 900000000), como cualquier registro nuevo de la web.
INSERT INTO pos_measure_forms (id, company_id, name, is_active, synced)
SELECT x.base + x.n, x.company_id, x.name COLLATE utf8mb4_general_ci, 1, 0
FROM (
    SELECT m.company_id, m.name,
           ROW_NUMBER() OVER (PARTITION BY m.company_id ORDER BY m.mu_id) AS n,
           IF(EXISTS (SELECT 1 FROM company_local_agents a WHERE a.company_id = m.company_id AND a.activo = 1),
              GREATEST(COALESCE((SELECT MAX(f.id) FROM pos_measure_forms f
                                 WHERE f.company_id = m.company_id AND f.id >= 900000000), 0), 899999999),
              COALESCE((SELECT MAX(f.id) FROM pos_measure_forms f
                        WHERE f.company_id = m.company_id AND f.id < 900000000), 0)) AS base
    FROM _mu_map m
    WHERE m.forma_id IS NULL
) x;

UPDATE _mu_map m
SET m.forma_id = (SELECT f.id FROM pos_measure_forms f
                  WHERE f.company_id = m.company_id AND f.name = m.name COLLATE utf8mb4_general_ci
                  ORDER BY f.id DESC LIMIT 1)
WHERE m.forma_id IS NULL;

-- 3) La bodega de herramientas apunta a la forma de medida equivalente
ALTER TABLE bodega_items DROP FOREIGN KEY fk_bodega_unidad;
UPDATE bodega_items b
JOIN _mu_map m ON m.mu_id = b.unidad_id AND m.company_id = b.company_id
SET b.unidad_id = m.forma_id;
UPDATE bodega_items b
LEFT JOIN pos_measure_forms f ON f.id = b.unidad_id AND f.company_id = b.company_id
SET b.unidad_id = NULL
WHERE b.unidad_id IS NOT NULL AND f.id IS NULL;

-- 4) product_recipes.unit_id (sin datos) deja de apuntar a measurement_units
ALTER TABLE product_recipes DROP FOREIGN KEY fk_recipe_unit;
ALTER TABLE product_recipes DROP FOREIGN KEY product_recipes_ibfk_3;

-- 5) Fuera la tabla
DROP TABLE measurement_units;
DROP TEMPORARY TABLE IF EXISTS _mu_map;

-- 6) El módulo del menú: mismo id (permisos por rol intactos), nombre y ruta nuevos
UPDATE system_modules SET name = 'Formas de Medida', route = '/configuration/formas-medida'
WHERE route = '/configuration/unidades-medida';
