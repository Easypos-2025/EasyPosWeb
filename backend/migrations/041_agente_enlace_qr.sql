-- 041 — QR fijo de la toma de pedidos (enlace por la nube)
--
-- El QR de los celulares apunta a https://easyposweb.com/c/<enlace>: la nube redirige a la IP local que el
-- agente reportó en su último latido (solo IP privada de la red del negocio). El QR no cambia aunque el
-- router le cambie la IP al PC de caja. <enlace> es aleatorio (no el código de la sede, que se puede adivinar).

ALTER TABLE company_local_agents
    ADD COLUMN enlace VARCHAR(24) NULL,
    ADD UNIQUE KEY uq_cla_enlace (enlace);

UPDATE company_local_agents
SET enlace = LOWER(SUBSTRING(SHA2(CONCAT(id, '-', company_id, '-', RAND(), '-', NOW(6)), 256), 1, 12))
WHERE enlace IS NULL;
