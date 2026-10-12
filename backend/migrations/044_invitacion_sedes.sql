-- 044 — Invitación de usuarios desde la Bodega Central a varias empresas del mismo NIT
--
-- Una invitación de la bodega puede dar acceso a la bodega y/o a varias sedes, con un ROL DISTINTO en cada una.
-- invitation_tokens sigue guardando la primera empresa/rol (compatibilidad); aquí van TODAS las empresas.
-- Al registrarse, el invitado queda creado en cada empresa con la MISMA contraseña (una sola por correo) y
-- user_id guarda la fila creada, para activarlas todas cuando verifique su correo.

CREATE TABLE IF NOT EXISTS invitation_token_sedes (
    invitation_id INT NOT NULL,
    company_id    INT NOT NULL,
    role_id       INT NOT NULL,
    user_id       INT NULL,
    PRIMARY KEY (invitation_id, company_id),
    KEY idx_its_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
