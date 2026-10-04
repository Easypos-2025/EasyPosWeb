"""
Textos visibles que dependen del tipo de negocio (nunca quemados en pantallas ni mensajes).
Por defecto son universales; cada negocio los puede cambiar en agente_local/.env:

  AG_TEXTO_CUENTA=Cuenta       (lo que en un restaurante es la mesa)
  AG_TEXTO_PRODUCTO=Producto   (lo que en un restaurante es el plato)
  AG_TEXTO_MESERO=Mesero       (quien toma el pedido)
  Plurales opcionales: AG_TEXTO_CUENTAS, AG_TEXTO_PRODUCTOS, AG_TEXTO_MESEROS

Los mensajes se redactan sin artículos (la/el) para que sirvan con cualquier palabra.
"""
import os


def _texto(clave: str, defecto: str) -> str:
    return (os.getenv(f"AG_TEXTO_{clave}") or defecto).strip()[:30] or defecto


def _plural(palabra: str) -> str:
    return palabra + ("es" if palabra[-1:].lower() not in "aeiou" else "s")


def textos() -> dict:
    cuenta, producto, mesero = _texto("CUENTA", "Cuenta"), _texto("PRODUCTO", "Producto"), _texto("MESERO", "Mesero")
    return {
        "cuenta": cuenta, "cuentas": _texto("CUENTAS", _plural(cuenta)),
        "producto": producto, "productos": _texto("PRODUCTOS", _plural(producto)),
        "mesero": mesero, "meseros": _texto("MESEROS", _plural(mesero)),
    }


def t(clave: str) -> str:
    """Texto en minúscula para usar dentro de una frase."""
    return textos()[clave].lower()
