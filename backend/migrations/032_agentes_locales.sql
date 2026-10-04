-- 032 — Agentes Locales (toma de pedidos contra la BD del escritorio en el PC de caja)
--
-- · Un agente por empresa (un PC de caja). Código = el de easypos_api.customer / Id_Sede del
--   escritorio (ej. 2022006): reemplaza ese directorio.
-- · Clave propia por empresa (no la clave global de la sincronización del escritorio): en la BD
--   solo queda su SHA-256; se muestra una sola vez al crearla o regenerarla.
-- · El agente reporta cada minuto su URL/IP local y versión (último contacto).
-- · Sus errores llegan al Monitor de Errores con el tipo AGENTE_LOCAL.

CREATE TABLE IF NOT EXISTS company_local_agents (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    company_id      INT          NOT NULL,
    codigo          VARCHAR(20)  NOT NULL,
    clave_hash      CHAR(64)     NOT NULL,
    clave_prefijo   VARCHAR(8)   NOT NULL,
    url_local       VARCHAR(200) NULL,
    ip_local        VARCHAR(45)  NULL,
    ip_publica      VARCHAR(45)  NULL,
    version         VARCHAR(40)  NULL,
    ultimo_contacto DATETIME     NULL,
    activo          TINYINT      NOT NULL DEFAULT 1,
    creado_por      INT          NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_cla_company (company_id),
    UNIQUE KEY uq_cla_codigo (codigo),
    UNIQUE KEY uq_cla_clave (clave_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE system_error_groups MODIFY tipo_error
    ENUM('SERVIDOR','BASE_DATOS','VISTA','RED','SINCRONIZACION','IMPRESION','INTEGRACION','SEGURIDAD',
         'VERSION_DESACTUALIZADA','AGENTE_LOCAL') NOT NULL;

INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Agentes Locales', '/sysadmin/agentes-locales', 'bi-hdd-network', NULL, 1, 0, 1
WHERE NOT EXISTS (SELECT 1 FROM system_modules WHERE route = '/sysadmin/agentes-locales');
