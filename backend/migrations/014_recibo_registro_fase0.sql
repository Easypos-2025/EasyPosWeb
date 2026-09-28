-- ============================================================
-- Migración 014: Fase 0 del Registro de Recibo/Factura
--   - Catálogo de Tipificaciones de Descuento (datatemppos)
-- Ejecutar en LOCAL y PRODUCCIÓN
--
-- NOTA IMPORTANTE: esta tabla vive en la base `datatemppos`, NO en
-- `easyposweb`. Conectarse a esa base antes de ejecutar este script
-- (USE datatemppos;).
--
-- `consecutivo_factura_manual` y `consecutivo_factura_sistema` (usadas
-- por el servicio de consecutivos) ya existen desde la migración 006
-- (backend/migrations/006_apidian_consecutivo_tables.sql) — no se
-- tocan aquí.
--
-- `pos_cash_register_closings` (apertura/cierre de turno de caja) y
-- `pos_receipt_discounts` (destino permanente de los descuentos
-- aplicados) ya existen en `easyposweb` — tampoco se tocan aquí.
-- ============================================================

CREATE TABLE IF NOT EXISTS temp_tipificaciones_descuentos (
    Id_Tipificacion             INT     NOT NULL DEFAULT 0,
    company_id                  INT     NOT NULL DEFAULT 0,
    Nombre                      VARCHAR(100) DEFAULT NULL,
    Info_Adicional               TINYINT DEFAULT 0,
    Enviar_Correo                TINYINT DEFAULT 0,
    Enviada_MySql                TINYINT DEFAULT 0,
    Desactivada                  TINYINT DEFAULT 0,
    Texto                        TINYINT DEFAULT 0,
    Combo                        TINYINT DEFAULT 0,
    Exigir_Info_Cliente          TINYINT DEFAULT 0,
    Valor_Descuento_Pesos        DOUBLE  DEFAULT 0,
    Valor_Descuento_Porcentaje   INT     DEFAULT 0,
    PRIMARY KEY (company_id, Id_Tipificacion),
    INDEX idx_ttd_company (company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Si en algún entorno esta tabla ya existía SIN `company_id` (copia
-- 1:1 del esquema de escritorio, mono-tenant), NO ejecutar el CREATE
-- de arriba (no hace nada por el IF NOT EXISTS) — hay que migrarla a
-- mano con algo como:
--
--   ALTER TABLE temp_tipificaciones_descuentos DROP PRIMARY KEY;
--   ALTER TABLE temp_tipificaciones_descuentos
--       ADD COLUMN company_id INT NOT NULL DEFAULT 0 AFTER Id_Tipificacion;
--   UPDATE temp_tipificaciones_descuentos SET company_id = <id de la empresa dueña de estas filas>;
--   ALTER TABLE temp_tipificaciones_descuentos ADD PRIMARY KEY (company_id, Id_Tipificacion);
--   ALTER TABLE temp_tipificaciones_descuentos ADD INDEX idx_ttd_company (company_id);
--
-- (Este fue exactamente el caso en el entorno LOCAL de desarrollo,
-- donde ya existían 6 filas de prueba sin company_id; se asignaron a
-- la empresa "Test" id=14.)

-- ============================================================
-- Fase 1: descuento por ítem al montar el pedido
-- Recuerda qué tipificación (temp_tipificaciones_descuentos.Id_Tipificacion)
-- se aplicó a cada línea, para poder deshabilitar el descuento global en la
-- pantalla de pago (Fase 2) y para escribir pos_receipt_discounts.typification_id
-- al registrar el recibo.
-- ============================================================
ALTER TABLE temp_detalle_comanda_parcial
    ADD COLUMN IF NOT EXISTS Id_Tipificacion INT NOT NULL DEFAULT 0 AFTER Porc_Descuento_General;
