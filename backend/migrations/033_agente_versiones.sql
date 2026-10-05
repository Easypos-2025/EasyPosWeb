-- 033 — Versiones del Agente Local (actualización de las sedes)
--
-- · Cada versión publicada (instalador_agente/construir.py --publicar) queda aquí con su huella
--   SHA-256; el archivo vive en /var/www/easyposweb/descargas_agente (privado: solo se entrega a
--   un agente con su clave). Una sola versión es la vigente (permite volver a una anterior).
-- · Cada agente reporta el resultado de su última actualización.

CREATE TABLE IF NOT EXISTS agente_versiones (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    version       VARCHAR(40)  NOT NULL,
    archivo       VARCHAR(200) NOT NULL,
    sha256        CHAR(64)     NOT NULL,
    tamano        BIGINT       NOT NULL,
    notas         TEXT         NULL,
    vigente       TINYINT      NOT NULL DEFAULT 0,
    publicado_en  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_av_version (version),
    KEY ix_av_vigente (vigente)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE company_local_agents
    ADD COLUMN IF NOT EXISTS actualizacion    VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS actualizacion_en DATETIME     NULL;
