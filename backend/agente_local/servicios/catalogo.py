"""
Catálogo para la toma de pedidos.

Todo sale de la BD de la empresa (siempre al día, sin abrir turno): categoria_platos, platos,
novedades_categorias, plato_impresoras/impresoras, lista_precios_cliente, plato_producto,
inventario_porciones_plato, y el armado: plato_armar (grupos de cada plato), plato_armar_detalle,
categoria_productos, inventario_porciones y menu_diario (menú del día, Seleccionado = 1).
De datatemppos solo se usa la fecha del turno.

platos.Activo está invertido en el escritorio: Activo = 0 es el plato visible.
Prioridad_Ofrecer <> 0 marca los platos de menú del día (sus grupos en plato_armar se llenan con el
menú armado para la fecha); los demás con grupos en plato_armar son platos para armar.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import date

_COLUMNAS_PLATO = """
    p.Id_Plato, p.Nombre, p.Valor, p.Cod_Categoria, p.Impuesto, p.Prioridad_Ofrecer,
    p.Pedir_Valor_Venta_Producto, p.Pedir_Descripcion_Producto, p.Impresora
"""


async def platos_visibles(emp: AsyncSession) -> list[dict]:
    filas = (await emp.execute(text(f"""
        SELECT {_COLUMNAS_PLATO}
        FROM platos p
        JOIN categoria_platos c ON c.Cod_Categoria = p.Cod_Categoria AND c.Activa = 1
        WHERE p.Activo = 0
        ORDER BY p.Nombre
    """))).mappings().all()
    return [dict(f) for f in filas]


async def plato_visible(emp: AsyncSession, id_plato: int) -> dict | None:
    fila = (await emp.execute(text(f"""
        SELECT {_COLUMNAS_PLATO}
        FROM platos p
        JOIN categoria_platos c ON c.Cod_Categoria = p.Cod_Categoria AND c.Activa = 1
        WHERE p.Activo = 0 AND p.Id_Plato = :id
    """), {"id": id_plato})).mappings().first()
    return dict(fila) if fila else None


async def categorias(emp: AsyncSession) -> list[dict]:
    filas = (await emp.execute(text("""
        SELECT c.Cod_Categoria, c.Nombre FROM categoria_platos c
        WHERE c.Activa = 1
          AND EXISTS (SELECT 1 FROM platos p WHERE p.Cod_Categoria = c.Cod_Categoria AND p.Activo = 0)
        ORDER BY c.Nombre
    """))).all()
    return [{"id": int(c), "nombre": (n or "").strip()} for c, n in filas]


async def novedades(emp: AsyncSession) -> dict[int, list[dict]]:
    filas = (await emp.execute(text("""
        SELECT Cod_Categoria, Id_Novedad, Novedad FROM novedades_categorias ORDER BY Novedad
    """))).all()
    salida: dict[int, list[dict]] = {}
    for cat, idn, nombre in filas:
        salida.setdefault(int(cat), []).append({"id": int(idn), "nombre": (nombre or "").strip()})
    return salida


async def presentaciones(emp: AsyncSession, id_plato: int | None = None) -> dict[int, list[dict]]:
    """Presentaciones de venta (plato_producto) de los productos que tienen 2 o más.
    Ej.: UNIDAD $2.000 descarga 1, BLISTER $18.000 descarga 10, CAJA $175.000 descarga 100.
    Con una sola presentación el producto se vende a platos.Valor (Unidades_Minimas no es
    confiable en ese caso). Activo = 0 es la presentación vigente, como en platos."""
    filtro = "AND Id_Plato = :p" if id_plato is not None else ""
    filas = (await emp.execute(text(f"""
        SELECT Id_Plato, Id_Forma_Medida, Unidades_Minimas, Valor_Presentacion, Descripcion
        FROM plato_producto
        WHERE Activo = 0 {filtro}
          AND Id_Plato IN (SELECT Id_Plato FROM plato_producto WHERE Activo = 0 GROUP BY Id_Plato HAVING COUNT(*) > 1)
        ORDER BY Id_Plato, Unidades_Minimas, Id_Forma_Medida
    """), {"p": id_plato})).mappings().all()
    salida: dict[int, list[dict]] = {}
    for f in filas:
        salida.setdefault(int(f["Id_Plato"]), []).append(dict(f))
    return salida


async def platos_para_armar(emp: AsyncSession) -> set[int]:
    filas = (await emp.execute(text("SELECT DISTINCT Id_Plato FROM plato_armar WHERE Activa = 1"))).all()
    return {int(f[0]) for f in filas}


def tipo_armado(plato: dict, para_armar: set[int]) -> str | None:
    if int(plato["Prioridad_Ofrecer"] or 0) != 0:
        return "menu"
    if int(plato["Id_Plato"]) in para_armar:
        return "armado"
    return None


async def opciones(emp: AsyncSession, plato: dict, fecha: date, para_armar: set[int] | None = None) -> list[dict]:
    """Grupos de opciones del plato. Cada opción trae lo que se descuenta de inventario.

    menu:   [{grupo, nombre, max, exigir, opciones:[{id (Id_Item), nombre, id_grupo_inv, cantidad, precio}]}]
            con el menú armado en el escritorio para la fecha del turno.
    armado: igual; id = Posicion del insumo, con por_defecto y precio adicional (Precio_Insumo).
    Lista vacía en un plato de menú = el menú del día no está armado (el plato se bloquea).
    """
    if para_armar is None:
        para_armar = await platos_para_armar(emp)
    tipo = tipo_armado(plato, para_armar)
    grupos: dict[int, dict] = {}

    if tipo == "menu":
        filas = (await emp.execute(text("""
            SELECT pa.Cod_Categoria, pa.Cantidad_Elegir, pa.Exgir_Seleccion,
                   md.Categoria, md.Id_Item, md.Descripcion,
                   (SELECT ip.Id_Grupo FROM inventario_porciones ip WHERE ip.Id_Item = md.Id_Item
                    ORDER BY ip.Agrupar = md.Agrupar DESC LIMIT 1) AS Id_Grupo
            FROM plato_armar pa
            JOIN menu_diario md ON md.Agrupar = pa.Cod_Categoria
            WHERE pa.Id_Plato = :p AND pa.Activa = 1 AND md.Fecha = :f AND md.Seleccionado = 1
            ORDER BY pa.Cod_Categoria, md.Descripcion
        """), {"p": plato["Id_Plato"], "f": fecha})).mappings().all()
        for r in filas:
            g = grupos.setdefault(int(r["Cod_Categoria"]), {
                "grupo": int(r["Cod_Categoria"]), "nombre": (r["Categoria"] or "").strip(),
                "max": int(r["Cantidad_Elegir"] or 0), "exigir": int(r["Exgir_Seleccion"] or 0), "opciones": []})
            g["opciones"].append({"id": int(r["Id_Item"]), "nombre": (r["Descripcion"] or "").strip(),
                                  "id_item": int(r["Id_Item"]), "id_grupo_inv": int(r["Id_Grupo"] or 0),
                                  "posicion": int(r["Id_Item"]), "cantidad": 1.0, "por_defecto": 0, "precio": 0.0})

    elif tipo == "armado":
        filas = (await emp.execute(text("""
            SELECT pa.Cod_Categoria, pa.Cantidad_Elegir, pa.Exgir_Seleccion, cp.Nombre AS grupo,
                   d.Posicion, d.Cantidad_Descontar, d.Por_Default, d.Precio_Insumo,
                   ip.Descripcion, ip.Id_Item, ip.Id_Grupo
            FROM plato_armar pa
            JOIN categoria_productos cp ON cp.Cod_Categoria = pa.Cod_Categoria
            JOIN plato_armar_detalle d ON d.Id_Plato = pa.Id_Plato AND d.Cod_Categoria = pa.Cod_Categoria
            JOIN inventario_porciones ip ON ip.Posicion = d.Posicion
            WHERE pa.Id_Plato = :p AND pa.Activa = 1
            ORDER BY cp.Nombre, ip.Descripcion
        """), {"p": plato["Id_Plato"]})).mappings().all()
        for r in filas:
            g = grupos.setdefault(int(r["Cod_Categoria"]), {
                "grupo": int(r["Cod_Categoria"]), "nombre": (r["grupo"] or "").strip(),
                "max": int(r["Cantidad_Elegir"] or 0), "exigir": int(r["Exgir_Seleccion"] or 0), "opciones": []})
            g["opciones"].append({"id": int(r["Posicion"]), "nombre": (r["Descripcion"] or "").strip(),
                                  "id_item": int(r["Id_Item"]), "id_grupo_inv": int(r["Id_Grupo"] or 0),
                                  "posicion": int(r["Posicion"]), "cantidad": float(r["Cantidad_Descontar"] or 0),
                                  "por_defecto": int(r["Por_Default"] or 0),
                                  # Adicional que se suma al valor del plato en ese pedido
                                  "precio": float(r["Precio_Insumo"] or 0)})
    return list(grupos.values())


async def impresoras_plato(emp: AsyncSession, plato: dict) -> list[str]:
    """Impresoras de destino del plato (el escritorio imprime una copia en cada una)."""
    filas = (await emp.execute(text("""
        SELECT i.Nombre FROM plato_impresoras pi
        JOIN impresoras i ON i.Id_Impresora = pi.Id_Impresora
        WHERE pi.Id_Plato = :p
        ORDER BY pi.Id_Impresora
    """), {"p": plato["Id_Plato"]})).all()
    nombres = [n.strip() for (n,) in filas if (n or "").strip()]
    if not nombres and (plato.get("Impresora") or "").strip():
        nombres = [plato["Impresora"].strip()]
    return nombres or [""]


async def receta_fija(emp: AsyncSession, id_plato: int) -> list[dict]:
    filas = (await emp.execute(text("""
        SELECT Id_Grupo, Id_Item, Cantidad, Posicion, Opcion_Cambiar
        FROM inventario_porciones_plato WHERE Id_Plato = :p
    """), {"p": id_plato})).mappings().all()
    return [dict(f) for f in filas]
