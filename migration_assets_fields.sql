-- ============================================================
-- MIGRACIÓN: Activos — nuevos campos + company_id
-- ============================================================

-- 1. Agregar company_id (nullable — activos existentes quedan NULL)
ALTER TABLE assets
  ADD COLUMN company_id INT NULL AFTER id,
  ADD CONSTRAINT fk_assets_company FOREIGN KEY (company_id) REFERENCES companies(id_company) ON DELETE SET NULL;

-- 2. Agregar campos de información pública
ALTER TABLE assets
  ADD COLUMN rental_requirements  TEXT NULL AFTER additional_reference,
  ADD COLUMN general_observations TEXT NULL AFTER rental_requirements;

-- 3. (Opcional) Asignar company_id a activos existentes si todos pertenecen a una sola empresa
-- Descomentar y ajustar el company_id si aplica:
-- UPDATE assets SET company_id = 1 WHERE company_id IS NULL;
