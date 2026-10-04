"""
Tablas propias del agente en datatemppos (el programa de escritorio las ignora).
Se crean al arrancar si no existen; nunca se alteran tablas del escritorio.
"""
from sqlalchemy import text

from .db import motor_temp

TABLAS = [
    # Un registro por usuario de dispositivo: clave cifrada y secreto del navegador.
    # registro_dispositivos.Contrasena del escritorio queda con una cadena aleatoria.
    """
    CREATE TABLE IF NOT EXISTS ag_dispositivos (
        id                 INT AUTO_INCREMENT PRIMARY KEY,
        usuario            VARCHAR(25)  NOT NULL,
        cod_empleado       BIGINT       NOT NULL,
        nombre_dispositivo VARCHAR(150) NOT NULL,
        clave_hash         VARCHAR(100) NOT NULL,
        secreto_hash       CHAR(64)     NULL,
        version_token      INT          NOT NULL DEFAULT 1,
        revocado           TINYINT      NOT NULL DEFAULT 0,
        creado             DATETIME     NOT NULL,
        ultimo_acceso      DATETIME     NULL,
        ultima_ip          VARCHAR(45)  NULL,
        UNIQUE KEY uq_ag_disp_usuario (usuario),
        KEY ix_ag_disp_secreto (secreto_hash)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    # Bloqueo de mesa con vencimiento (temp_mesa_abierta del escritorio no tiene hora)
    """
    CREATE TABLE IF NOT EXISTS ag_bloqueo_mesa (
        id_mesa        INT          NOT NULL,
        mesa           VARCHAR(255) NOT NULL,
        cod_empleado   BIGINT       NOT NULL,
        id_dispositivo INT          NOT NULL,
        desde          DATETIME     NOT NULL,
        vence          DATETIME     NOT NULL,
        PRIMARY KEY (id_mesa, mesa)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    # Quién hizo qué, cuándo y desde dónde. También alimenta el límite de intentos.
    """
    CREATE TABLE IF NOT EXISTS ag_auditoria (
        id             BIGINT AUTO_INCREMENT PRIMARY KEY,
        fecha          DATETIME     NOT NULL,
        evento         VARCHAR(40)  NOT NULL,
        resultado      VARCHAR(10)  NOT NULL,
        usuario        VARCHAR(25)  NULL,
        cod_empleado   BIGINT       NULL,
        id_dispositivo INT          NULL,
        ip             VARCHAR(45)  NULL,
        detalle        VARCHAR(255) NULL,
        KEY ix_ag_aud_evento (evento, fecha),
        KEY ix_ag_aud_ip (ip, fecha),
        KEY ix_ag_aud_usuario (usuario, fecha)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    # Errores del agente y de sus dispositivos (mismo criterio del Monitor de Errores de la nube:
    # un registro por error distinto, con contador; se marca resuelto con nota)
    """
    CREATE TABLE IF NOT EXISTS ag_errores (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        huella          CHAR(40)      NOT NULL,
        origen          VARCHAR(12)   NOT NULL,
        tipo            VARCHAR(20)   NOT NULL,
        nivel           VARCHAR(12)   NOT NULL,
        titulo          VARCHAR(255)  NOT NULL,
        mensaje         TEXT          NULL,
        detalle         MEDIUMTEXT    NULL,
        vista           VARCHAR(255)  NULL,
        dispositivo     VARCHAR(150)  NULL,
        ip              VARCHAR(45)   NULL,
        ocurrencias     INT           NOT NULL DEFAULT 1,
        primera         DATETIME      NOT NULL,
        ultima          DATETIME      NOT NULL,
        estado          VARCHAR(12)   NOT NULL DEFAULT 'NUEVO',
        regresiones     INT           NOT NULL DEFAULT 0,
        nota            TEXT          NULL,
        resuelto_en     DATETIME      NULL,
        pendiente_nube  INT           NOT NULL DEFAULT 1,
        UNIQUE KEY uq_ag_err_huella (huella),
        KEY ix_ag_err_estado (estado, ultima)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    # Configuración del agente (clave de administrador cifrada, versión de su sesión…)
    """
    CREATE TABLE IF NOT EXISTS ag_config (
        clave   VARCHAR(60)  NOT NULL PRIMARY KEY,
        valor   VARCHAR(255) NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


async def crear_esquema() -> None:
    async with motor_temp.begin() as conn:
        for ddl in TABLAS:
            await conn.execute(text(ddl))
