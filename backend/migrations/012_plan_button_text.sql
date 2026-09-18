-- Permite parametrizar el texto del boton de cada plan en la landing page
-- (por defecto: "Empezar Gratis" para el plan gratuito, "Comenzar" para el resto)
ALTER TABLE plans ADD COLUMN button_text VARCHAR(50) NULL AFTER is_active;
