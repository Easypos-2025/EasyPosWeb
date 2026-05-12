-- =====================================================
-- EasyPos Web - POS Sync Tables (English, prefix pos_)
-- Translated from local MariaDB (Spanish) schema
-- Fields added to all tables: company_id, updated_at, synced
-- Import into: easyposweb database
-- =====================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;

-- ---------------------------------------------------
-- pos_cash_register_closings (cajas_cierres)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_cash_register_closings` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `register_number` int(11) NOT NULL DEFAULT '0',
  `shift` int(11) DEFAULT '0',
  `date` date DEFAULT NULL,
  `base_amount` double DEFAULT '0',
  `total_sales` double DEFAULT '0',
  `cash_sales` double DEFAULT '0',
  `voucher_sales` double DEFAULT '0',
  `tips` double DEFAULT '0',
  `extra_tips` double DEFAULT '0',
  `expenses` double DEFAULT '0',
  `vouchers` double DEFAULT '0',
  `manager_consumption` double DEFAULT '0',
  `final_base` double DEFAULT '0',
  `total_invoices` int(11) DEFAULT '0',
  `voucher_invoices` int(11) DEFAULT '0',
  `copy_invoices` int(11) DEFAULT '0',
  `voided_invoices` int(11) DEFAULT '0',
  `invoice_start` varchar(50) DEFAULT '0',
  `invoice_end` varchar(50) DEFAULT '0',
  `bills` double DEFAULT '0',
  `coins` double DEFAULT '0',
  `purchases` double DEFAULT '0',
  `customer_sales` double DEFAULT '0',
  `closed` tinyint(4) DEFAULT '0',
  `invoice_start_manual` varchar(50) DEFAULT NULL,
  `invoice_end_manual` varchar(50) DEFAULT NULL,
  `delivery_income` double DEFAULT '0',
  `delivery_expense` double DEFAULT '0',
  `opened_pc` varchar(50) DEFAULT NULL,
  `closing_notes` mediumtext,
  `opening_datetime` varchar(50) DEFAULT NULL,
  `closing_datetime` varchar(50) DEFAULT NULL,
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_cash_register_invoices (caja_facturas)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_cash_register_invoices` (
  `register_number` int(11) NOT NULL DEFAULT '0',
  `closing_id` bigint(20) NOT NULL DEFAULT '0',
  `invoice_number` varchar(50) NOT NULL,
  `date` date DEFAULT NULL,
  `order_number` varchar(255) DEFAULT NULL,
  `amount` double DEFAULT '0',
  `base_amount` double DEFAULT '0',
  `tax_vat` double DEFAULT '0',
  `tax_consumption` double DEFAULT '0',
  `employee_id` int(11) DEFAULT '0',
  `shift` int(11) DEFAULT '0',
  `source_pc` varchar(255) DEFAULT NULL,
  `delivery_person_id` int(11) DEFAULT '0',
  `invoice_notes` mediumtext,
  `prefix` mediumtext,
  `fac_pe` mediumtext,
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_cash_register_receipts (caja_recibos)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_cash_register_receipts` (
  `register_number` int(11) NOT NULL DEFAULT '0',
  `closing_id` bigint(20) NOT NULL DEFAULT '0',
  `receipt_number` varchar(50) NOT NULL,
  `date` date DEFAULT NULL,
  `order_number` varchar(255) DEFAULT NULL,
  `amount` double DEFAULT '0',
  `base_amount` double DEFAULT '0',
  `tax_vat` double DEFAULT '0',
  `tax_consumption` double DEFAULT '0',
  `employee_id` int(11) DEFAULT '0',
  `shift` int(11) DEFAULT '0',
  `source_pc` varchar(255) DEFAULT NULL,
  `delivery_person_id` int(11) DEFAULT '0',
  `notes` mediumtext,
  `prefix` varchar(50) DEFAULT NULL,
  `fac_pe` varchar(50) DEFAULT NULL,
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_orders (comanda)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_orders` (
  `order_number` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `invoice_number` varchar(50) NOT NULL DEFAULT '0',
  `table_name` varchar(200) DEFAULT '0',
  `time` varchar(50) DEFAULT NULL,
  `waiter_id` int(11) DEFAULT '0',
  `cancelled` tinyint(4) DEFAULT '0',
  `amount` int(11) DEFAULT '0',
  `notes` varchar(250) DEFAULT NULL,
  `complimentary` tinyint(4) DEFAULT '0',
  `guests_count` int(11) DEFAULT '0',
  `delivery` tinyint(4) DEFAULT '0',
  `customer_id` int(11) DEFAULT '0',
  `table_id` int(11) DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`order_number`, `date`, `invoice_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_order_details (detalle_comanda)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_order_details` (
  `order_number` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `invoice_number` varchar(50) NOT NULL,
  `dish_id` int(11) NOT NULL DEFAULT '0',
  `item` int(11) NOT NULL DEFAULT '0',
  `quantity` float DEFAULT '0',
  `amount` int(11) DEFAULT '0',
  `notes` varchar(250) DEFAULT NULL,
  `complimentary` tinyint(1) DEFAULT '0',
  `dish_discount_pct` float DEFAULT '0',
  `general_discount_pct` float DEFAULT '0',
  `seat_number` tinyint(4) DEFAULT '0',
  `changes` varchar(250) DEFAULT NULL,
  `dish_time` varchar(250) DEFAULT NULL,
  `pays_tax` tinyint(4) DEFAULT '0',
  `tax` decimal(10,0) DEFAULT '0',
  `original_tax` decimal(10,0) DEFAULT '0',
  `pays_dish` tinyint(4) DEFAULT '0',
  `custom_product` mediumtext,
  `depends_on` int(11) NOT NULL DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`order_number`, `date`, `invoice_number`, `dish_id`, `item`, `depends_on`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_order_detail_products (detalle_comanda_producto)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_order_detail_products` (
  `order_number` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `invoice_number` varchar(50) NOT NULL,
  `dish_id` int(11) NOT NULL DEFAULT '0',
  `item` int(11) NOT NULL DEFAULT '0',
  `group_id` int(11) NOT NULL DEFAULT '0',
  `item_id` int(11) NOT NULL DEFAULT '0',
  `quantity` float DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`order_number`, `date`, `invoice_number`, `dish_id`, `item`, `group_id`, `item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_invoice_details (detalle_factura)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_invoice_details` (
  `invoice_number` varchar(50) NOT NULL,
  `order_number` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `dish_id` int(11) NOT NULL DEFAULT '0',
  `item` int(11) NOT NULL DEFAULT '0',
  `quantity` float DEFAULT '0',
  `notes` varchar(250) DEFAULT NULL,
  `dish_amount` int(11) DEFAULT '0',
  `complimentary` tinyint(1) DEFAULT '0',
  `discount_pct` float DEFAULT '0',
  `depends_on` int(11) NOT NULL DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`invoice_number`, `order_number`, `date`, `dish_id`, `item`, `depends_on`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_employees (empleados)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_employees` (
  `id` int(11) NOT NULL DEFAULT '0',
  `name` varchar(50) NOT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `address` varchar(50) DEFAULT NULL,
  `login` varchar(25) NOT NULL,
  `password` varchar(25) NOT NULL,
  `status` tinyint(4) NOT NULL DEFAULT '0',
  `employee_type` int(11) NOT NULL DEFAULT '0',
  `personal_skin` int(11) NOT NULL DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_invoices (facturas)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_invoices` (
  `invoice_number` varchar(50) NOT NULL,
  `date` date DEFAULT NULL,
  `cash_amount` int(11) DEFAULT '0',
  `discount` int(11) DEFAULT '0',
  `id_number` varchar(50) DEFAULT '1',
  `employee_id` int(11) DEFAULT '0',
  `voided` tinyint(4) DEFAULT '0',
  `paid_vat` tinyint(1) DEFAULT '0',
  `adjustment` tinyint(1) DEFAULT '0',
  `credit_card_amount` int(11) DEFAULT '0',
  `debit_card_amount` int(11) DEFAULT '0',
  `tip` int(11) DEFAULT '0',
  `shift` int(11) DEFAULT '0',
  `time` varchar(50) DEFAULT NULL,
  `time_text` varchar(50) DEFAULT NULL,
  `extra_tip` int(11) DEFAULT '0',
  `amount_without_tip` int(11) DEFAULT '0',
  `analyzed` tinyint(1) DEFAULT '0',
  `currency_type` int(11) DEFAULT '0',
  `foreign_amount` float DEFAULT '0',
  `manual_invoice` tinyint(1) DEFAULT '0',
  `resolution_id` int(11) DEFAULT '0',
  `customer_id` int(11) DEFAULT '0',
  `reservation_invoice` varchar(50) DEFAULT '0',
  `delivery_invoice` tinyint(4) DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`invoice_number`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_invoice_payment_methods (factura_forma_pago)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_invoice_payment_methods` (
  `item` int(11) NOT NULL DEFAULT '0',
  `payment_method_id` int(11) NOT NULL DEFAULT '0',
  `card_id` int(11) NOT NULL DEFAULT '0',
  `invoice_number` varchar(100) NOT NULL,
  `amount` double DEFAULT '0',
  `date` date NOT NULL,
  `authorization` double DEFAULT '0',
  `notes` varchar(255) DEFAULT NULL,
  `delivery_amount` double DEFAULT '0',
  `prefix` varchar(50) DEFAULT NULL,
  `fac_pe` varchar(50) DEFAULT NULL,
  `order_number` varchar(255) DEFAULT NULL,
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`item`, `payment_method_id`, `card_id`, `invoice_number`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_tables_layout (mesas)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_tables_layout` (
  `id` int(11) NOT NULL DEFAULT '0',
  `branch_id` int(11) NOT NULL DEFAULT '0',
  `name` varchar(50) NOT NULL,
  `location` varchar(50) NOT NULL,
  `seats` int(11) DEFAULT '0',
  `customer_id` bigint(20) NOT NULL DEFAULT '0',
  `dynamic_zone` tinyint(4) NOT NULL DEFAULT '0',
  `active` tinyint(4) NOT NULL DEFAULT '0',
  `zone_id` int(11) DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_waiters (meseros)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_waiters` (
  `id` int(11) NOT NULL DEFAULT '0',
  `name` varchar(50) NOT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `address` varchar(50) DEFAULT NULL,
  `status` tinyint(4) NOT NULL DEFAULT '0',
  `employee_type` int(11) DEFAULT '0',
  `password` varchar(50) DEFAULT NULL,
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_dishes (platos)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_dishes` (
  `id` int(11) NOT NULL DEFAULT '0',
  `name` varchar(250) DEFAULT NULL,
  `product_code` varchar(250) DEFAULT NULL,
  `price` int(11) DEFAULT '0',
  `preparation_time` int(11) DEFAULT '0',
  `active` tinyint(1) DEFAULT '0',
  `category_id` int(11) DEFAULT '0',
  `photo_path` varchar(255) DEFAULT NULL,
  `procedure` longtext,
  `description` longtext,
  `printer` varchar(250) DEFAULT NULL,
  `comment` varchar(255) DEFAULT NULL,
  `extra_print` varchar(255) DEFAULT NULL,
  `printer_2` varchar(250) DEFAULT NULL,
  `pre_preparation` tinyint(4) DEFAULT '0',
  `offer` tinyint(4) DEFAULT '0',
  `offer_priority` int(11) DEFAULT '0',
  `tax` decimal(10,0) DEFAULT '0',
  `wholesale_price` double DEFAULT '0',
  `product_cost` double DEFAULT '0',
  `minimum_stock` double DEFAULT '0',
  `ask_sale_price` tinyint(4) DEFAULT '0',
  `ask_product_description` tinyint(4) DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_dish_products (plato_producto)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_dish_products` (
  `dish_id` int(11) NOT NULL DEFAULT '0',
  `supplier_id` int(11) NOT NULL DEFAULT '0',
  `measure_id` int(11) NOT NULL DEFAULT '0',
  `minimum_units` double DEFAULT '0',
  `presentation_value` double DEFAULT '0',
  `description` varchar(50) DEFAULT NULL,
  `active` tinyint(4) DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`dish_id`, `supplier_id`, `measure_id`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_receipts (recibos)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_receipts` (
  `receipt_number` varchar(50) NOT NULL,
  `date` date DEFAULT NULL,
  `cash_amount` int(11) DEFAULT '0',
  `discount` int(11) DEFAULT '0',
  `id_number` varchar(50) DEFAULT '1',
  `employee_id` int(11) DEFAULT '0',
  `voided` tinyint(4) DEFAULT '0',
  `paid_vat` tinyint(1) DEFAULT '0',
  `adjustment` tinyint(1) DEFAULT '0',
  `credit_card_amount` int(11) DEFAULT '0',
  `debit_card_amount` int(11) DEFAULT '0',
  `tip` int(11) DEFAULT '0',
  `shift` int(11) DEFAULT '0',
  `time` varchar(50) DEFAULT NULL,
  `time_text` varchar(50) DEFAULT NULL,
  `extra_tip` int(11) DEFAULT '0',
  `amount_without_tip` int(11) DEFAULT '0',
  `analyzed` tinyint(1) DEFAULT '0',
  `currency_type` int(11) DEFAULT '0',
  `foreign_amount` float DEFAULT '0',
  `manual_receipt` tinyint(1) DEFAULT '0',
  `resolution_id` int(11) DEFAULT '0',
  `customer_id` int(11) DEFAULT '0',
  `reservation_receipt` varchar(50) DEFAULT '0',
  `delivery_receipt` tinyint(4) DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`receipt_number`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_receipt_orders (recibos_comanda)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_receipt_orders` (
  `order_number` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `receipt_number` varchar(50) NOT NULL DEFAULT '0',
  `table_name` varchar(200) DEFAULT '0',
  `time` varchar(50) DEFAULT NULL,
  `waiter_id` int(11) DEFAULT '0',
  `cancelled` tinyint(4) DEFAULT '0',
  `amount` int(11) DEFAULT '0',
  `notes` varchar(250) DEFAULT NULL,
  `complimentary` tinyint(4) DEFAULT '0',
  `guests_count` int(11) DEFAULT '0',
  `delivery` tinyint(4) DEFAULT '0',
  `customer_id` int(11) DEFAULT '0',
  `table_id` int(11) DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`order_number`, `date`, `receipt_number`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_receipt_order_details (recibos_detalle_comanda)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_receipt_order_details` (
  `order_number` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `receipt_number` varchar(50) NOT NULL,
  `dish_id` int(11) NOT NULL DEFAULT '0',
  `item` int(11) NOT NULL DEFAULT '0',
  `quantity` float DEFAULT '0',
  `amount` int(11) DEFAULT '0',
  `notes` varchar(250) DEFAULT NULL,
  `complimentary` tinyint(1) DEFAULT '0',
  `dish_discount_pct` float DEFAULT '0',
  `general_discount_pct` float DEFAULT '0',
  `seat_number` tinyint(4) DEFAULT '0',
  `changes` varchar(250) DEFAULT NULL,
  `dish_time` varchar(250) DEFAULT NULL,
  `pays_tax` tinyint(4) DEFAULT '0',
  `tax` decimal(10,0) DEFAULT '0',
  `original_tax` decimal(10,0) DEFAULT '0',
  `pays_dish` tinyint(4) DEFAULT '0',
  `custom_product` mediumtext,
  `depends_on` int(11) NOT NULL DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`order_number`, `date`, `receipt_number`, `dish_id`, `item`, `depends_on`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_receipt_order_detail_products (recibos_detalle_comanda_producto)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_receipt_order_detail_products` (
  `order_number` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `receipt_number` varchar(50) NOT NULL,
  `dish_id` int(11) NOT NULL DEFAULT '0',
  `item` int(11) NOT NULL DEFAULT '0',
  `group_id` int(11) NOT NULL DEFAULT '0',
  `item_id` int(11) NOT NULL DEFAULT '0',
  `quantity` float DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`order_number`, `date`, `receipt_number`, `dish_id`, `item`, `group_id`, `item_id`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_receipt_invoice_details (recibos_detalle_factura)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_receipt_invoice_details` (
  `receipt_number` varchar(50) NOT NULL,
  `order_number` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `dish_id` int(11) NOT NULL DEFAULT '0',
  `item` int(11) NOT NULL DEFAULT '0',
  `quantity` float DEFAULT NULL,
  `notes` varchar(250) DEFAULT NULL,
  `dish_amount` int(11) DEFAULT '0',
  `complimentary` tinyint(1) DEFAULT '0',
  `discount_pct` float DEFAULT '0',
  `depends_on` int(11) NOT NULL DEFAULT '0',
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`receipt_number`, `order_number`, `date`, `dish_id`, `item`, `depends_on`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------
-- pos_receipt_payment_methods (recibos_forma_pago)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS `pos_receipt_payment_methods` (
  `item` int(11) NOT NULL DEFAULT '0',
  `payment_method_id` int(11) NOT NULL DEFAULT '0',
  `card_id` int(11) NOT NULL DEFAULT '0',
  `receipt_number` varchar(100) NOT NULL,
  `amount` double DEFAULT '0',
  `date` varchar(50) NOT NULL DEFAULT '',
  `authorization` double DEFAULT '0',
  `notes` varchar(255) DEFAULT NULL,
  `delivery_amount` double DEFAULT '0',
  `prefix` varchar(50) DEFAULT NULL,
  `fac_pe` varchar(50) DEFAULT NULL,
  `order_number` varchar(255) DEFAULT NULL,
  `synced` tinyint(4) DEFAULT '0',
  `company_id` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`item`, `payment_method_id`, `card_id`, `receipt_number`, `company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS=1;
