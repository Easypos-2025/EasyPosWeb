-- 035 — Índice de las formas de pago de recibos y facturas por empresa + documento + item
--
-- · La fila de pago se identifica por factura + pedido + item (formas_pago.pago_vigente_sql):
--   "Pasar Crédito/Débito" del escritorio cambia la forma de pago de la misma fila y vale la más
--   reciente. Las consultas (cuadre, métricas, consultas, impresión) buscan por empresa + documento;
--   la llave primaria empieza por item y no sirve para eso.

ALTER TABLE pos_invoice_payment_methods
    ADD INDEX IF NOT EXISTS idx_ipm_doc_item (company_id, invoice_number, item);

ALTER TABLE pos_receipt_payment_methods
    ADD INDEX IF NOT EXISTS idx_rpm_doc_item (company_id, invoice_number, item);
