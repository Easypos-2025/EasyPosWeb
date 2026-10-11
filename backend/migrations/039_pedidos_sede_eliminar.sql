-- 039 — S2: eliminar productos y cancelar cuentas desde la web, con aceptación en caja
--
--   ELIMINAR: productos ya aceptados en caja que el mesero pide eliminar (motivo SIEMPRE obligatorio).
--   CANCELAR: la cuenta completa.
--   Mientras la caja no acepte, los productos quedan con Sede_Pendiente = 2 en el datatemppos de la
--   web ("Pendiente x Eliminar"): siguen en la cuenta, no se pueden tocar. Aceptado: salen del pedido;
--   rechazado: vuelven a la normalidad. motivo_solicitud = el motivo del mesero.

ALTER TABLE pos_sede_lotes
    MODIFY tipo ENUM('NUEVO','AGREGAR','ELIMINAR','CANCELAR') NOT NULL,
    ADD COLUMN motivo_solicitud VARCHAR(255) NULL AFTER enviado_por;
