-- ================================================================
-- MIGRACIÓN: tasks — columnas opcionales deben aceptar NULL
-- Ya aplicado en BD. Archivo para documentación/referencia.
-- ================================================================
ALTER TABLE tasks
  MODIFY COLUMN asset_id          INT      NULL,
  MODIFY COLUMN description       TEXT     NULL,
  MODIFY COLUMN created_by        INT      NULL,
  MODIFY COLUMN assigned_to       INT      NULL,
  MODIFY COLUMN due_date          DATETIME NULL,
  MODIFY COLUMN budget_labor_cost FLOAT    NULL DEFAULT 0,
  MODIFY COLUMN actual_labor_cost FLOAT    NULL DEFAULT 0,
  MODIFY COLUMN progress          INT      NULL DEFAULT 0;
