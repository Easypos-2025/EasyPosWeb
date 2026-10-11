-- 040 — Consumidor Final en todas las empresas (regla del usuario 2026-10-11)
--
-- Desde ahora la web NO lo crea sola: si no existe el cliente 1 (Consumidor Final), no se puede tomar
-- pedidos ni cobrar (409 SIN_CONSUMIDOR_FINAL). Esta migración lo crea UNA vez en las empresas que no
-- tienen ningún cliente con id_cliente = 1 (no pisa a nadie).
-- enviada_mysql = 1: no baja al escritorio con S3 (allá ya existe el cliente 1 y no se debe sobrescribir).

INSERT INTO clientes (company_id, id_cliente, cedula, nombres, enviada_mysql)
SELECT c.id_company, 1, '222222222222', 'Consumidor Final', 1
FROM companies c
WHERE NOT EXISTS (SELECT 1 FROM clientes x WHERE x.company_id = c.id_company AND x.id_cliente = 1);
