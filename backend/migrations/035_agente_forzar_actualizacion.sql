-- 035 — Agente Local: forzar la actualización desde SYSADMIN
--
-- · forzar_actualizacion = 1: el agente aplica la versión vigente apenas la tenga descargada
--   (se lo informa la nube en el latido). Vuelve a 0 sola cuando el agente reporta la versión vigente.

ALTER TABLE company_local_agents
    ADD COLUMN IF NOT EXISTS forzar_actualizacion TINYINT NOT NULL DEFAULT 0 AFTER actualizacion_en;
