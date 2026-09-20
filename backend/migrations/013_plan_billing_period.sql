-- Permite parametrizar el periodo de cobro de cada plan en la landing page
-- (mes / trimestre / semestre / año) en vez de tener "/mes" quemado
ALTER TABLE plans ADD COLUMN billing_period VARCHAR(20) NULL DEFAULT 'mes' AFTER button_text;
UPDATE plans SET billing_period = 'mes' WHERE billing_period IS NULL;
