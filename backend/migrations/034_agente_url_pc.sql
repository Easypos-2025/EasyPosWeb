-- 034 — Agente Local: dirección por el nombre del PC de caja
--
-- · url_pc = http://NOMBRE-PC:8090. No cambia aunque el router le cambie la IP al PC; los PCs
--   Windows de la red la resuelven por nombre (acceso directo fijo). Los celulares siguen con el
--   QR por IP (url_local). La reporta el mismo agente en cada latido.

ALTER TABLE company_local_agents
    ADD COLUMN IF NOT EXISTS url_pc VARCHAR(200) NULL AFTER url_local;
