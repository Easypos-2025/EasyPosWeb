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
