-- 027 — Impresoras: la llave pasa a (id, company_id). El escritorio envía su Id_Impresora;
--       con la llave solo por `id` la impresora 3 de una empresa sobrescribía la 3 de otra.
ALTER TABLE pos_printers DROP PRIMARY KEY, ADD PRIMARY KEY (id, company_id);
