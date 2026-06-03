-- ============================================================
-- migration_pos_kitchen_events.sql
-- Tabla de eventos efímeros para la pantalla de cocina TV
-- Ejecutar en easyposweb (no en datatemppos)
-- ============================================================
USE easyposweb;

CREATE TABLE IF NOT EXISTS `pos_kitchen_events` (
  `id`             BIGINT          AUTO_INCREMENT PRIMARY KEY,
  `company_id`     INT             NOT NULL,
  `event_type`     ENUM('cancelado','reimpresion') NOT NULL,
  `order_number`   VARCHAR(255)    NOT NULL,
  `table_name`     VARCHAR(200)    DEFAULT NULL,
  `waiter_id`      INT             DEFAULT 0,
  `items_snapshot` MEDIUMTEXT      DEFAULT NULL,
  `event_date`     DATE            NOT NULL,
  `created_at`     DATETIME        DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_active` (`company_id`, `event_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
