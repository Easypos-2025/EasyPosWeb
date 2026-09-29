-- ============================================================
-- Migración 019: estado de los cortes automáticos de inventario en BD
-- Base: easyposweb — Ejecutar en LOCAL y PRODUCCIÓN
--
-- Antes el estado vivía en memoria de un proceso; con varios workers de gunicorn
-- la consulta de estado caía en otro proceso y respondía 404.
-- ============================================================

CREATE TABLE IF NOT EXISTS `inventory_snapshot_jobs` (
  `job_id`      VARCHAR(36)  NOT NULL,
  `company_id`  INT(11)      NOT NULL,
  `status`      VARCHAR(20)  NOT NULL DEFAULT 'running',   -- running | done | error
  `progress`    VARCHAR(120) DEFAULT NULL,
  `items_saved` INT(11)      DEFAULT NULL,
  `id_fisico`   INT(11)      DEFAULT NULL,
  `fecha`       DATE         DEFAULT NULL,
  `error`       VARCHAR(255) DEFAULT NULL,
  `created_by`  INT(11)      DEFAULT NULL,
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`job_id`),
  KEY `idx_isj_company` (`company_id`, `status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
