-- 038 — Configuración Sede (vista /configuration/sede, la maneja el admin de la empresa)
--
-- Espejo de la tabla `configuracion_sede` del escritorio (misma estructura y nombres) + company_id,
-- para los datos que salen en los documentos y para bajarlos al escritorio en S3.
-- Las rutas de fotos (Ruta_Foto_*) NO se guardan en la web: son carpetas del PC de caja.

CREATE TABLE IF NOT EXISTS configuracion_sede (
    company_id          INT           NOT NULL PRIMARY KEY,
    Id_Sede             INT           NULL,
    Nombre_Almacen      VARCHAR(250)  NULL,
    Nombre_Autorizado   VARCHAR(250)  NULL,
    Nit_Autorizado      VARCHAR(250)  NULL,
    Razon_Social        VARCHAR(255)  NULL,
    Direccion_Sede      VARCHAR(255)  NULL,
    Mail_Uno            VARCHAR(100)  NULL,
    Mail_Dos            VARCHAR(100)  NULL,
    Nombre_Logo_Empresa VARCHAR(200)  NULL,
    synced              TINYINT       NOT NULL DEFAULT 0,
    actualizado_por     VARCHAR(150)  NULL,
    updated_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Configuración Sede', '/configuration/sede', 'bi-shop', NULL, 1, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_modules WHERE route = '/configuration/sede');
