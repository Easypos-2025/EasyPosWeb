-- ============================================================
-- Migración 020: billetes rápidos para pago en efectivo
-- Base: easyposweb — Ejecutar en LOCAL y PRODUCCIÓN
--
-- Al escoger EFECTIVO en la pantalla de pago se muestran como tarjetas
-- (máximo 6 por empresa) para sumar el valor recibido; se configuran en
-- la vista Formas de Pago.
-- ============================================================

CREATE TABLE IF NOT EXISTS `pos_cash_denominations` (
  `id`         INT(11)    NOT NULL AUTO_INCREMENT,
  `company_id` INT(11)    NOT NULL,
  `value`      INT(11)    NOT NULL,
  `sort_order` INT(11)    NOT NULL DEFAULT 0,
  `updated_at` DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_pcd` (`company_id`, `value`),
  KEY `idx_pcd_company` (`company_id`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
