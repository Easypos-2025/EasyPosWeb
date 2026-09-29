-- ============================================================
-- Migración 017: espejos web de insumos_proveedor e insumos_forma_medida
-- Base: easyposweb — Ejecutar en LOCAL y PRODUCCIÓN (después de la 016)
--
-- Convención (igual que inventario_porciones_plato): nombre y columnas del
-- escritorio en minúscula + company_id.
--   id_insumo       = supply_items.id_item   (Id_Insumo = Id_Item en el escritorio)
--   id_proveedor    = suppliers.id_proveedor
--   id_forma_medida = pos_measure_forms.id
-- Fechas de negociación y precio_pactado: por ahora se llenan por defecto
-- (fecha de hoy, 0), como el escritorio. Su funcionalidad se desarrollará después.
-- ============================================================

CREATE TABLE IF NOT EXISTS `insumos_proveedor` (
  `id`                        INT(11)     NOT NULL AUTO_INCREMENT,
  `company_id`                INT(11)     NOT NULL,
  `id_proveedor`              INT(11)     NOT NULL DEFAULT 0,
  `id_insumo`                 INT(11)     NOT NULL DEFAULT 0,
  `fecha_inicial_negociacion` DATE        DEFAULT NULL,
  `fecha_final_negociacion`   DATE        DEFAULT NULL,
  `precio_pactado`            INT(11)     NOT NULL DEFAULT 0,
  `id_forma_medida`           INT(11)     NOT NULL DEFAULT 0,
  `nombre_forma_medida`       VARCHAR(50) DEFAULT NULL,
  `observacion`               TEXT        DEFAULT NULL,
  `enviada_mysql`             TINYINT(4)  NOT NULL DEFAULT 0,
  `updated_at`                DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_insprov` (`company_id`, `id_proveedor`, `id_insumo`),
  KEY `idx_insprov_insumo` (`company_id`, `id_insumo`),
  KEY `idx_insprov_sync`   (`company_id`, `updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS `insumos_forma_medida` (
  `id`                    INT(11)    NOT NULL AUTO_INCREMENT,
  `company_id`            INT(11)    NOT NULL,
  `id_insumo`             INT(11)    NOT NULL DEFAULT 0,
  `id_forma_medida`       INT(11)    NOT NULL DEFAULT 0,
  `cant_unidades_minimas` FLOAT      NOT NULL DEFAULT 0,
  `enviada_mysql`         TINYINT(4) NOT NULL DEFAULT 0,
  `updated_at`            DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_insfm` (`company_id`, `id_forma_medida`, `id_insumo`),
  KEY `idx_insfm_insumo` (`company_id`, `id_insumo`),
  KEY `idx_insfm_sync`   (`company_id`, `updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
