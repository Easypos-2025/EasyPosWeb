-- 023 — Variantes de plato (solo web): variante por defecto, receta por variante y
--       cantidad de sabores (opciones de armado) por variante. Idempotente.

-- Variante por defecto: su precio es el precio del plato
ALTER TABLE pos_dish_variants
  ADD COLUMN IF NOT EXISTS is_default TINYINT NOT NULL DEFAULT 0 AFTER is_active;

-- Receta por variante: SOLO ajusta la cantidad de los insumos fijos del plato
-- (inventario_porciones_plato). Si no hay fila, se usa la cantidad del plato.
CREATE TABLE IF NOT EXISTS pos_dish_variant_products (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  company_id  INT NOT NULL,
  variant_id  INT NOT NULL,
  id_item     INT NOT NULL,
  porciones   DECIMAL(14,4) NOT NULL DEFAULT 0,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_variant_item (company_id, variant_id, id_item)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sabores por variante: cuántas opciones lleva cada categoría de armado del plato en esta
-- variante (Personal 2, Dúo 3, Familiar 4). Si no hay fila, se usa plato_armar.Cantidad_Elegir.
CREATE TABLE IF NOT EXISTS pos_dish_variant_assembly (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  company_id    INT NOT NULL,
  variant_id    INT NOT NULL,
  category_code INT NOT NULL,
  max_choices   INT NOT NULL DEFAULT 1,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_variant_cat (company_id, variant_id, category_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
