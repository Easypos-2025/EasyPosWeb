-- ============================================================
-- MIGRACIÓN: Renombrar tablas de español a inglés
-- IMPORTANTE: Ejecutar ANTES de reiniciar el backend
-- ============================================================

-- 1. Primero eliminar FKs que apuntan a unidades_medida
--    para poder renombrar sin conflicto
ALTER TABLE bodega_items   DROP FOREIGN KEY IF EXISTS bodega_items_ibfk_2;
ALTER TABLE bodega_items   DROP FOREIGN KEY IF EXISTS fk_bodega_unidad;
ALTER TABLE product_recipes DROP FOREIGN KEY IF EXISTS product_recipes_ibfk_2;
ALTER TABLE product_recipes DROP FOREIGN KEY IF EXISTS fk_recipe_unit;
ALTER TABLE supply_items   DROP FOREIGN KEY IF EXISTS supply_items_ibfk_2;
ALTER TABLE supply_items   DROP FOREIGN KEY IF EXISTS fk_supply_unit;

-- 2. Renombrar las 5 tablas
RENAME TABLE conceptos_compras TO purchase_concepts;
RENAME TABLE conceptos_gastos  TO expense_concepts;
RENAME TABLE insumos           TO supplies;
RENAME TABLE unidades_medida   TO measurement_units;
RENAME TABLE colaborador_tarea TO task_collaborators;

-- 3. Re-crear FKs con el nuevo nombre de tabla
ALTER TABLE bodega_items
  ADD CONSTRAINT fk_bodega_unidad FOREIGN KEY (unidad_id) REFERENCES measurement_units(id) ON DELETE SET NULL;

ALTER TABLE product_recipes
  ADD CONSTRAINT fk_recipe_unit FOREIGN KEY (unit_id) REFERENCES measurement_units(id) ON DELETE SET NULL;

ALTER TABLE supply_items
  ADD CONSTRAINT fk_supply_unit FOREIGN KEY (unit_id) REFERENCES measurement_units(id) ON DELETE SET NULL;
