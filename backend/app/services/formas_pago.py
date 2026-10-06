"""
Regla única de formas de pago (forma_pago = pos_payment_types), para todos los perfiles:
EFECTIVO es la forma de pago cuya descripción es "EFECTIVO"; todas las demás son "Otros".
Las sumas salen siempre de recibos_forma_pago / facturas_forma_pago.
"""


def es_efectivo_sql(alias: str = "pt") -> str:
    """Expresión SQL (1/0) que indica si la forma de pago es EFECTIVO."""
    return f"(UPPER(TRIM(COALESCE({alias}.name, ''))) = 'EFECTIVO')"


def es_efectivo(nombre: str | None) -> bool:
    return (nombre or "").strip().upper() == "EFECTIVO"


def pago_vigente_sql(alias: str, tabla: str) -> str:
    """Condición SQL: la fila de recibos_forma_pago / facturas_forma_pago es la vigente.
    Una fila de pago se identifica por factura + pedido + item; "Pasar Crédito/Débito" del escritorio
    cambia la forma de pago de esa misma fila y la web pudo conservar la anterior (nunca se borra),
    así que vale solo la más reciente."""
    return f"""NOT EXISTS (
        SELECT 1 FROM {tabla} pv
        WHERE pv.company_id = {alias}.company_id AND pv.invoice_number = {alias}.invoice_number
          AND pv.item = {alias}.item AND COALESCE(pv.order_number, '') = COALESCE({alias}.order_number, '')
          AND (pv.updated_at > {alias}.updated_at
               OR (pv.updated_at = {alias}.updated_at
                   AND (pv.payment_method_id > {alias}.payment_method_id
                        OR (pv.payment_method_id = {alias}.payment_method_id AND pv.card_id > {alias}.card_id)))))"""
