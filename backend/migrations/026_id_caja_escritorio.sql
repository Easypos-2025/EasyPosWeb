-- 026 — Id_Caja único = pos_cash_register_closings.id_registro (cajas_cierres.Id_Caja del escritorio)
--
-- · Los Id_Caja abiertos en la web tenían id_registro negativo y sus recibos apuntaban al `id`
--   de la fila. Se iguala id_registro = id (positivo; no choca con el escritorio) y se marcan
--   como web (synced = 0). Los recibos no cambian: ya apuntan a ese número.
-- · El cajero web queda registrado en pos_employees (id = id del usuario = Venta_Clientes).
-- · Empresa 68 (pruebas): se borra el Id_Caja viejo del escritorio (2024) para que quede
--   como empresa solo web.

UPDATE pos_cash_register_closings c
JOIN (
    SELECT w.id
    FROM pos_cash_register_closings w
    WHERE w.id_registro < 0
      AND NOT EXISTS (SELECT 1 FROM pos_cash_register_closings x
                      WHERE x.company_id = w.company_id AND x.id_registro = w.id)
) t ON t.id = c.id
SET c.id_registro = c.id, c.synced = 0;

INSERT INTO pos_employees (id, company_id, name, login, password, status, employee_type, personal_skin, synced)
SELECT DISTINCT u.id, c.company_id, LEFT(COALESCE(u.nombre, CONCAT('Usuario ', u.id)), 50),
       LEFT(COALESCE(u.email, u.id), 25), '', 1, 0, 0, 0
FROM pos_cash_register_closings c
JOIN users u ON u.id = CAST(c.customer_sales AS SIGNED)
WHERE c.synced = 0
  AND NOT EXISTS (SELECT 1 FROM pos_employees e WHERE e.company_id = c.company_id AND e.id = u.id);

DELETE FROM pos_cash_register_closings
WHERE company_id = 68 AND synced = 1 AND id_registro = 0 AND date = '2024-01-01';
