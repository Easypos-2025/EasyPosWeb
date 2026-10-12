-- 043 — Índice "empresa + número" en los catálogos cuya llave primaria es (id, company_id)
--
-- Sin un índice que empiece por company_id, "SELECT MAX(id) ... WHERE company_id = ? FOR UPDATE" (número del
-- siguiente registro: sede_maestros.siguiente_id, crear producto, bodega central) recorre y BLOQUEA la tabla
-- completa de TODAS las empresas (pos_dishes tiene 80.000+ filas). Si otra empresa está sincronizando, la
-- operación espera y falla con "Lock wait timeout" (ERR-FB33E6E1, importar catálogo en la bodega).
-- Con el índice cada empresa bloquea solo su propio rango. No cambia datos; MariaDB lo crea en línea.

ALTER TABLE pos_dishes             ADD INDEX IF NOT EXISTS idx_pd_company_id  (company_id, id), ALGORITHM=INPLACE, LOCK=NONE;
ALTER TABLE pos_dish_categories    ADD INDEX IF NOT EXISTS idx_pdc_company_id (company_id, id), ALGORITHM=INPLACE, LOCK=NONE;
ALTER TABLE pos_measure_forms      ADD INDEX IF NOT EXISTS idx_pmf_company_id (company_id, id), ALGORITHM=INPLACE, LOCK=NONE;
ALTER TABLE pos_product_categories ADD INDEX IF NOT EXISTS idx_ppc_company_id (company_id, id), ALGORITHM=INPLACE, LOCK=NONE;
