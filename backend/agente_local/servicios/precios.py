"""
Precio de venta de un plato para un cliente.

  1. Precio activo del cliente en lista_precios_cliente. Id_Presentacion = Id_Forma_Medida de
     la presentación (plato_producto). El consumidor final (Id_Cliente = 1) puede tener su
     propia lista: es la "lista default".
  2. Si no hay: el valor de la presentación escogida, o platos.Valor.
  3. + adicionales de las opciones de armado escogidas (Precio_Insumo).
  4. Si la empresa paga impuesto y sus precios no lo incluyen, se suma el impuesto del plato.

El dispositivo solo muestra estos precios; al guardar, el agente los vuelve a calcular.
"""
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

CLIENTE_CONSUMIDOR_FINAL = 1          # lo que manda el dispositivo cuando no se asignó cliente
CEDULA_CONSUMIDOR_FINAL = "222222222222"
MENSAJE_SIN_CONSUMIDOR_FINAL = ("No existe el cliente Consumidor Final (cédula 222222222222) en el escritorio: "
                                "créelo para poder tomar pedidos.")


async def consumidor_final(emp: AsyncSession) -> int | None:
    """Id_Cliente real del Consumidor Final (regla del usuario 2026-10-11: normalmente es el 1, pero se
    verifica). Primero por su cédula; si no, el id 1. None = no existe → se bloquea la toma de pedido."""
    por_cedula = (await emp.execute(text(
        "SELECT MIN(Id_Cliente) FROM clientes WHERE TRIM(cedula) = :c"), {"c": CEDULA_CONSUMIDOR_FINAL})).scalar()
    if por_cedula:
        return int(por_cedula)
    uno = (await emp.execute(text("SELECT Id_Cliente FROM clientes WHERE Id_Cliente = 1"))).scalar()
    return int(uno) if uno else None


async def lista_cliente(emp: AsyncSession, id_cliente: int,
                        ids_plato: list[int] | None = None) -> dict[int, dict[int, int]]:
    """{Id_Plato: {Id_Presentacion: precio}} activos del cliente."""
    sql = """
        SELECT Id_Producto, Id_Presentacion, Precio_Producto FROM lista_precios_cliente
        WHERE Id_Cliente = :c AND Activa = 1
    """
    params: dict = {"c": id_cliente}
    if ids_plato is not None:
        if not ids_plato:
            return {}
        sql += " AND Id_Producto IN :ids"
        params["ids"] = list(ids_plato)
    consulta = text(sql)
    if ids_plato is not None:
        consulta = consulta.bindparams(bindparam("ids", expanding=True))
    salida: dict[int, dict[int, int]] = {}
    for prod, pres, precio in (await emp.execute(consulta, params)).all():
        salida.setdefault(int(prod), {})[int(pres or 0)] = int(precio or 0)
    return salida


def con_impuesto(valor: float, impuesto, fact: dict) -> int:
    if fact["paga_impuesto"] == 1 and fact["precios_incluyen_impuesto"] == 0:
        return int(round(valor + valor * float(impuesto or 0) / 100))
    return int(round(valor))


def precio_base(plato: dict, lista: dict[int, dict[int, int]], presentacion: dict | None = None) -> int:
    """Precio sin impuesto ni adicionales."""
    del_cliente = lista.get(int(plato["Id_Plato"]), {})
    if presentacion:
        forma = int(presentacion["Id_Forma_Medida"])
        if forma in del_cliente:
            return del_cliente[forma]
        return int(round(float(presentacion["Valor_Presentacion"] or 0)))
    if del_cliente:
        # Producto de una sola presentación: su precio de lista (cualquiera sea la forma de medida)
        return del_cliente[min(del_cliente)]
    return int(plato["Valor"] or 0)


def precio_plato(plato: dict, lista: dict[int, dict[int, int]], fact: dict,
                 presentacion: dict | None = None, adicional: float = 0) -> int:
    return con_impuesto(precio_base(plato, lista, presentacion) + adicional, plato["Impuesto"], fact)
