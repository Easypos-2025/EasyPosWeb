"""
Archive helper: copies temp_comanda + temp_detalle_comanda_parcial to
order_command_history + order_command_history_items BEFORE deletion.
All writes go to easyposweb (db_write); reads come from datatemppos (db_read).
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def archive_commands_to_history(
    db_read:  AsyncSession,
    db_write: AsyncSession,
    cid:      int,
    nro_pedidos: list,
    reason:   str,
) -> None:
    if not nro_pedidos:
        return

    ph = ",".join(f":np_{i}" for i in range(len(nro_pedidos)))
    params: dict = {"cid": cid}
    params.update({f"np_{i}": v for i, v in enumerate(nro_pedidos)})

    try:
        headers = (await db_read.execute(text(f"""
            SELECT Nro_Pedido, Fecha, Mesa, Hora, Mesero, Valor, Cancelado, Movil
            FROM temp_comanda
            WHERE company_id = :cid AND Nro_Pedido IN ({ph})
        """), params)).mappings().all()
    except Exception:
        return

    try:
        items = (await db_read.execute(text(f"""
            SELECT Nro_pedido, Fecha, Id_Plato, Item, Cantidad, Valor,
                   Novedad, Cambios, Hora_Plato, Mostrar
            FROM temp_detalle_comanda_parcial
            WHERE company_id = :cid AND Nro_pedido IN ({ph})
        """), params)).mappings().all()
    except Exception:
        items = []

    for h in headers:
        try:
            await db_write.execute(text("""
                INSERT IGNORE INTO order_command_history
                  (company_id, Nro_Pedido, Fecha, Mesa, Hora, Mesero,
                   Valor, Cancelado, Movil, archive_reason)
                VALUES (:cid, :np, :fecha, :mesa, :hora, :mesero,
                        :valor, :cancelado, :movil, :reason)
            """), {
                "cid":       cid,
                "np":        h["Nro_Pedido"],
                "fecha":     h["Fecha"],
                "mesa":      str(h["Mesa"]    or ""),
                "hora":      str(h["Hora"]    or ""),
                "mesero":    str(h["Mesero"]  or ""),
                "valor":     float(h["Valor"] or 0),
                "cancelado": int(h["Cancelado"] or 0),
                "movil":     int(h["Movil"]   or 0),
                "reason":    reason,
            })
        except Exception:
            pass

    for it in items:
        try:
            await db_write.execute(text("""
                INSERT IGNORE INTO order_command_history_items
                  (company_id, Nro_Pedido, Fecha, Id_Plato, Item, Cantidad,
                   Valor, Novedad, Cambios, Hora_Plato, Mostrar)
                VALUES (:cid, :np, :fecha, :id_plato, :item, :cantidad,
                        :valor, :novedad, :cambios, :hora_plato, :mostrar)
            """), {
                "cid":        cid,
                "np":         it["Nro_pedido"],
                "fecha":      it["Fecha"],
                "id_plato":   int(it["Id_Plato"]  or 0),
                "item":       int(it["Item"]       or 0),
                "cantidad":   float(it["Cantidad"] or 0),
                "valor":      float(it["Valor"]    or 0),
                "novedad":    str(it["Novedad"]    or ""),
                "cambios":    str(it["Cambios"]    or ""),
                "hora_plato": str(it["Hora_Plato"] or ""),
                "mostrar":    int(it["Mostrar"]    or 1),
            })
        except Exception:
            pass

    try:
        await db_write.commit()
    except Exception:
        pass
