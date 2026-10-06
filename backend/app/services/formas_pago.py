"""
Regla única de formas de pago (forma_pago = pos_payment_types), para todos los perfiles:
EFECTIVO es la forma de pago marcada como default (forma_pago.Forma_Pago_Default = 1) y activa
(Activo = 1), igual que el escritorio (Var_Id_forma_pago_Efectivo); todas las demás son "Otros".
Debe existir exactamente una: si no, no se registra nada ni se genera ningún reporte hasta que el
administrador de caja lo corrija (app.auth.efectivo_guard → 409 EFECTIVO_NO_CONFIGURADO).
forma_pago.Suma_Efectivo NO se usa. Las sumas salen siempre de recibos_forma_pago / facturas_forma_pago.
"""
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

EFECTIVO_NO_CONFIGURADO = "EFECTIVO_NO_CONFIGURADO"
CREDITO_NO_CONFIGURADO = "CREDITO_NO_CONFIGURADO"


def es_efectivo_sql(alias: str = "pt") -> str:
    """Expresión SQL (1/0) que indica si la forma de pago es EFECTIVO (default y activa)."""
    return f"(COALESCE({alias}.is_default, 0) = 1 AND COALESCE({alias}.is_active, 0) = 1)"


async def estado_efectivo(db: AsyncSession, cid: int) -> dict:
    """¿La empresa tiene exactamente una forma de pago default y activa? Con el problema exacto."""
    rows = (await db.execute(text(
        "SELECT id, name, COALESCE(is_active, 0) is_active FROM pos_payment_types "
        "WHERE company_id = :cid AND COALESCE(is_default, 0) = 1 ORDER BY id"
    ), {"cid": cid})).mappings().all()
    nombres = [str(r["name"] or "").strip() for r in rows]
    total = int((await db.execute(text(
        "SELECT COUNT(*) FROM pos_payment_types WHERE company_id = :cid"), {"cid": cid})).scalar() or 0)
    if len(rows) == 1 and int(rows[0]["is_active"]):
        return {"ok": True, "problema": None, "id": int(rows[0]["id"]), "nombre": nombres[0],
                "defaults": nombres, "total": total, "mensaje": ""}
    if not rows:
        problema, detalle = "ninguna", "no hay ninguna forma de pago marcada como Default"
    elif len(rows) > 1:
        problema, detalle = "varias", f"hay {len(rows)} formas de pago marcadas como Default ({', '.join(nombres)}) y solo puede haber una"
    else:
        problema, detalle = "inactiva", f"la forma de pago Default «{nombres[0]}» está inactiva"
    return {"ok": False, "problema": problema, "id": None, "nombre": None, "defaults": nombres,
            "total": total, "mensaje": ("No se puede registrar ni consultar: la forma de pago EFECTIVO no está configurada "
                        f"({detalle}). El administrador de caja debe marcar UNA forma de pago (EFECTIVO) "
                        "como Default y Activa en Configuración → Formas de Pago.")}


async def exigir_efectivo(db: AsyncSession, cid: int) -> dict:
    est = await estado_efectivo(db, cid)
    if not est["ok"]:
        raise HTTPException(status_code=409, detail=est["mensaje"],
                            headers={"X-Error-Code": EFECTIVO_NO_CONFIGURADO})
    return est


def es_credito(nombre: str | None) -> bool:
    return (nombre or "").strip().upper() == "CREDITO"


def validar_credito(tipo: dict) -> None:
    """La forma de pago CREDITO solo se puede usar si exige cliente (Pedir_Cliente = 1)."""
    if es_credito(tipo.get("name")) and not int(tipo.get("ask_customer") or 0):
        raise HTTPException(
            status_code=409,
            detail=("No se puede pagar a CREDITO: la forma de pago CREDITO debe tener activa la opción "
                    "«Pedir cliente» para asignar el deudor. El administrador de caja debe activarla en "
                    "Configuración → Formas de Pago."),
            headers={"X-Error-Code": CREDITO_NO_CONFIGURADO})


# Comanda de cada documento (para el Nro_Pedido): facturas → comanda, recibos → recibos_comanda
_COMANDA = {"pos_invoice_payment_methods": ("pos_orders", "invoice_number"),
            "pos_receipt_payment_methods": ("pos_receipt_orders", "receipt_number")}


def pedido_sql(alias: str, tabla: str) -> str:
    """Nro_Pedido de una fila de forma de pago: el suyo o, si llegó vacío del escritorio (recibos_forma_pago
    casi nunca lo guarda; "Pasar Crédito/Débito" sube la fila sin él), el de la comanda del documento."""
    ordenes, num = _COMANDA[tabla]
    return (f"COALESCE(NULLIF({alias}.order_number, ''), (SELECT MIN(o.order_number) FROM {ordenes} o "
            f"WHERE o.company_id = {alias}.company_id AND o.{num} = {alias}.invoice_number), '')")


async def pedido_documento(db: AsyncSession, tabla: str, cid: int, numero: str) -> str:
    ordenes, num = _COMANDA[tabla]
    return str((await db.execute(text(
        f"SELECT MIN(order_number) FROM {ordenes} WHERE company_id = :cid AND {num} = :n"
    ), {"cid": cid, "n": numero})).scalar() or "")


def pago_vigente_sql(alias: str, tabla: str) -> str:
    """Condición SQL: la fila de recibos_forma_pago / facturas_forma_pago es la vigente.
    Una fila de pago se identifica por factura + Nro_Pedido + item (pedido_sql); "Pasar Crédito/Débito"
    del escritorio cambia la forma de pago de esa misma fila y la web pudo conservar la anterior
    (nunca se borra), así que vale solo la más reciente."""
    return f"""NOT EXISTS (
        SELECT 1 FROM {tabla} pv
        WHERE pv.company_id = {alias}.company_id AND pv.invoice_number = {alias}.invoice_number
          AND pv.item = {alias}.item
          AND {pedido_sql('pv', tabla)} = {pedido_sql(alias, tabla)}
          AND (pv.updated_at > {alias}.updated_at
               OR (pv.updated_at = {alias}.updated_at
                   AND (pv.payment_method_id > {alias}.payment_method_id
                        OR (pv.payment_method_id = {alias}.payment_method_id AND pv.card_id > {alias}.card_id)))))"""
