-- Migración 0002: Foto, precio comparativo, orden y variantes en artículos POS
-- Ejecutar en el servidor: mysql -u root -p123456 easyposweb < 0002_platos_variantes_foto.sql

ALTER TABLE pos_dishes
    ADD COLUMN IF NOT EXISTS compare_price INT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS order_index   INT DEFAULT 0;

ALTER TABLE pos_item_categories
    ADD COLUMN IF NOT EXISTS order_index INT DEFAULT 0;

CREATE TABLE IF NOT EXISTS pos_dish_variants (
    id           INT          AUTO_INCREMENT,
    company_id   INT          NOT NULL DEFAULT 0,
    dish_id      INT          NOT NULL,
    name         VARCHAR(100) NOT NULL,
    price        INT          NOT NULL DEFAULT 0,
    compare_price INT         DEFAULT NULL,
    order_index  INT          DEFAULT 0,
    is_active    TINYINT(1)   DEFAULT 1,
    PRIMARY KEY (id, company_id),
    INDEX idx_dish_company (dish_id, company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
