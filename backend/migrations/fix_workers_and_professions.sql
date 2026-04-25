-- ================================================================
-- MIGRACIÓN: Professions + Workers refactor + Fix tasks.worker_id
-- Ejecutar UNA sola vez en MySQL, en este orden exacto
-- ================================================================

-- 1. Fix tasks.worker_id: NOT NULL → NULL
ALTER TABLE tasks MODIFY COLUMN worker_id INT NULL;

-- ----------------------------------------------------------------
-- 2. Crear tabla professions
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS professions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255) NULL
);

-- 3. Seed professions
INSERT INTO professions (name, description) VALUES
  ('Electricista',   'Instalaciones y mantenimiento eléctrico'),
  ('Plomero',        'Instalaciones sanitarias y tuberías'),
  ('Pintor',         'Pintura interior y exterior'),
  ('Carpintero',     'Trabajos en madera y muebles'),
  ('Albañil',        'Construcción y obra civil'),
  ('Técnico HVAC',   'Aire acondicionado y ventilación');

-- ----------------------------------------------------------------
-- 4. Modificar tabla workers: agregar profession_id, quitar profession
-- ----------------------------------------------------------------
ALTER TABLE workers ADD COLUMN profession_id INT NULL;
ALTER TABLE workers ADD CONSTRAINT fk_workers_profession
    FOREIGN KEY (profession_id) REFERENCES professions(id);

-- Eliminar columna de texto libre (solo si existe)
ALTER TABLE workers DROP COLUMN IF EXISTS profession;

-- 5. Seed workers de prueba
INSERT INTO workers (name, profession_id, phone) VALUES
  ('Carlos Rodríguez', 1, '3001234567'),
  ('Juan Pérez',       2, '3019876543'),
  ('Miguel Torres',    3, '3024567890'),
  ('Luis Gómez',       4, '3031234567'),
  ('Pedro Martínez',   5, '3041234567'),
  ('Andrés López',     6, '3051234567');
