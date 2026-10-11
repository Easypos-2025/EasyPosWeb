-- 037 — Pedidos web hacia el escritorio: lo decide el admin de la empresa (Configuración Sede)
--
--   pedidos_web_escritorio = 1  los pedidos web de una empresa con Agente Local activo bajan al
--                               escritorio y esperan la aceptación en caja (036).
--                          = 0  se montan solo en la web (como una empresa sin escritorio).
--   Por defecto 1: las empresas con agente siguen como estaban.
--   Un pedido que ya tiene algo enviado a la caja sigue bajando aunque se cambie la opción.
--   _por / _en: quién y cuándo la cambió (solo ADMIN de la empresa o SYSADMIN).

ALTER TABLE company_configs
    ADD COLUMN pedidos_web_escritorio     TINYINT      NOT NULL DEFAULT 1,
    ADD COLUMN pedidos_web_escritorio_por VARCHAR(150) NULL,
    ADD COLUMN pedidos_web_escritorio_en  DATETIME     NULL;
