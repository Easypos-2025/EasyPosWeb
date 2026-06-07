-- ============================================================
-- datatemppos_sync — BD de control de sincronización
-- Aplicar en LOCAL y en servidor DO
-- No toca ninguna tabla de datatemppos existente
-- ============================================================

CREATE DATABASE IF NOT EXISTS datatemppos_sync
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE datatemppos_sync;

-- ------------------------------------------------------------
-- 1. Cola de salida: cambios locales pendientes de subir al servidor
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sync_outbox (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    tabla        VARCHAR(60)  NOT NULL,
    operacion    ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    nro_pedido   VARCHAR(255) NOT NULL,
    payload      MEDIUMTEXT   NOT NULL,          -- JSON con el row completo
    creado_en    DATETIME     DEFAULT NOW(),
    enviado_en   DATETIME     NULL,              -- NULL = pendiente
    intentos     TINYINT      DEFAULT 0,
    error_msg    TEXT         NULL,
    INDEX idx_pendientes (enviado_en, creado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------
-- 2. Cola de entrada: cambios recibidos del servidor pendientes de aplicar en local
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sync_inbox (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    tabla        VARCHAR(60)  NOT NULL,
    operacion    ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    nro_pedido   VARCHAR(255) NOT NULL,
    origen       VARCHAR(20)  NOT NULL DEFAULT 'web',
    payload      MEDIUMTEXT   NOT NULL,
    recibido_en  DATETIME     DEFAULT NOW(),
    aplicado_en  DATETIME     NULL,              -- NULL = pendiente de aplicar
    error_msg    TEXT         NULL,
    INDEX idx_pendientes_in (aplicado_en, recibido_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------
-- 3. Control de sincronización: timestamps por dirección 
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sync_control (
    id           INT          PRIMARY KEY DEFAULT 1,
    ultimo_push  DATETIME     NULL,    -- última vez que se subió al servidor
    ultimo_pull  DATETIME     NULL,    -- última vez que se bajó del servidor
    en_proceso   TINYINT      DEFAULT 0,
    version_app  VARCHAR(20)  NULL     -- versión del sync service instalado
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO sync_control (id, ultimo_push, ultimo_pull, en_proceso)
VALUES (1, NULL, NULL, 0)
ON DUPLICATE KEY UPDATE id = 1;

-- ------------------------------------------------------------
-- 4. Locks distribuidos: evita edición simultánea del mismo pedido
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sync_locks (
    nro_pedido    VARCHAR(255) NOT NULL PRIMARY KEY,
    bloqueado_por VARCHAR(20)  NOT NULL,          -- 'desktop' o 'web'
    bloqueado_en  DATETIME     NOT NULL,
    lock_token    VARCHAR(36)  NOT NULL,           -- UUID para validar dueño
    INDEX idx_vencidos (bloqueado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
