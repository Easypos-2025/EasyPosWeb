"""
Armado e inserción de pedidos en datatemppos, con la forma que espera el escritorio:

  temp_comanda                  1 fila por pedido (Movil = 1).
  temp_detalle_comanda          1 fila por UNIDAD y por IMPRESORA del plato. Cantidad decimal como el
                                escritorio: 2.34 → filas de 0.34, 1 y 1; Valor = precio × cantidad de la fila.
  temp_detalle_comanda_parcial  copia de la anterior.
      Mostrar = 1 solo en la fila de la primera impresora de cada unidad;
      Depende = Item inicial de la línea (agrupa todas las unidades de esa línea).
  temp_plato_producto           inventario a descontar, por UNIDAD (como el VB6):
  temp_plato_producto_parcial   (las dos; la parcial es la que más usa el escritorio)
      receta fija (inventario_porciones_plato.Cantidad × unidades de la presentación)
      + opciones escogidas (con su Valor_Adicional_Armar).
  temp_novedades_plato_pedido   novedades por línea (Item = Depende = Item inicial).

Presentaciones (plato_producto, solo productos con 2 o más): el dispositivo escoge una;
fija el precio y multiplica lo que se descarga de inventario.

El escritorio imprime las filas con Impreso = 0 en la impresora indicada.
Precio, impuesto e impresoras los calcula el agente; el dispositivo solo puede fijar el
precio o la descripción de los platos que tengan Pedir_Valor_Venta_Producto /
Pedir_Descripcion_Producto.
"""
import math
import re
from datetime import date, datetime

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from . import catalogo
from .negocio import facturacion, fecha_negocio
from ..textos import t
from .precios import con_impuesto, lista_cliente, precio_base

MAX_LINEAS          = 60
MAX_CANTIDAD_LINEA  = 50
MAX_UNIDADES        = 200
TOPE_PRECIO         = 100_000_000
MAX_DESCRIPCION     = 150
MAX_NOMBRE_CUENTA   = 50
MAX_NOTA            = 100            # novedad libre por línea


class OpcionIn(BaseModel):
    grupo: int = Field(ge=0)
    id: int = Field(ge=0)


class LineaIn(BaseModel):
    id_plato: int = Field(gt=0)
    cantidad: float = Field(gt=0, le=MAX_CANTIDAD_LINEA)       # admite decimales (fruver: 2.34 kg)
    presentacion: int | None = Field(default=None, ge=0)          # Id_Forma_Medida
    precio: int | None = Field(default=None, ge=0, le=TOPE_PRECIO)
    descripcion: str | None = Field(default=None, max_length=300)
    novedades: list[int] = Field(default_factory=list, max_length=30)
    nota: str | None = Field(default=None, max_length=MAX_NOTA)      # novedad libre (escrita por el mesero)
    opciones: list[OpcionIn] = Field(default_factory=list, max_length=40)

    @field_validator("cantidad")
    @classmethod
    def _tres_decimales(cls, v: float) -> float:
        v = round(v, 3)
        if v <= 0:
            raise ValueError("Cantidad no válida")
        return v


def limpiar_texto(valor: str | None, largo: int) -> str:
    """Sin caracteres de control ni espacios repetidos (va a tablas del escritorio y a tirillas)."""
    valor = re.sub(r"[\x00-\x1f\x7f]", " ", valor or "")
    return " ".join(valor.split())[:largo]


def partes_cantidad(cantidad: float) -> list[float]:
    """Como el escritorio: 2.34 → [0.34, 1, 1] (la fracción primero, luego unidades de 1)."""
    enteras = int(math.floor(cantidad + 1e-9))
    fraccion = round(cantidad - enteras, 3)
    return ([fraccion] if fraccion > 0 else []) + [1.0] * enteras


def valor_linea(valor_unitario: int, cantidad: float) -> int:
    return sum(int(round(valor_unitario * parte)) for parte in partes_cantidad(cantidad))


def hora_corta(ahora: datetime) -> str:
    return ahora.strftime("%I:%M %p")


async def preparar_lineas(emp: AsyncSession, tmp: AsyncSession, lineas: list[LineaIn], id_cliente: int) -> list[dict]:
    if not lineas:
        raise HTTPException(status_code=422, detail=f"El pedido no tiene {t('productos')}.")
    if len(lineas) > MAX_LINEAS or sum(math.ceil(l.cantidad) for l in lineas) > MAX_UNIDADES:
        raise HTTPException(status_code=422, detail=f"El pedido supera la cantidad máxima de {t('productos')}.")

    fact = await facturacion(emp)
    lista = await lista_cliente(emp, id_cliente, sorted({l.id_plato for l in lineas}))
    para_armar = await catalogo.platos_para_armar(emp)
    fecha = await fecha_negocio(emp)
    novedades_cat = await catalogo.novedades(emp)

    preparadas = []
    for l in lineas:
        plato = await catalogo.plato_visible(emp, l.id_plato)
        if not plato:
            raise HTTPException(status_code=422, detail=f"Uno de los {t('productos')} ya no está disponible. Actualice la carta.")
        nombre = (plato["Nombre"] or "").strip()

        # Novedades: deben ser de la categoría del plato
        disponibles = {n["id"]: n for n in novedades_cat.get(int(plato["Cod_Categoria"]), [])}
        novs = []
        for idn in dict.fromkeys(l.novedades):
            if idn not in disponibles:
                raise HTTPException(status_code=422, detail=f"Novedad no válida para '{nombre}'.")
            novs.append(disponibles[idn])

        # Menú del día / armado
        tipo = catalogo.tipo_armado(plato, para_armar)
        selecciones = []
        if tipo:
            grupos = {g["grupo"]: g for g in await catalogo.opciones(emp, plato, fecha, para_armar)}
            if tipo == "menu" and not grupos:
                raise HTTPException(status_code=409, detail=f"El menú del día de '{nombre}' no está armado para hoy.")
            por_grupo: dict[int, int] = {}
            vistos = set()
            for o in l.opciones:
                g = grupos.get(o.grupo)
                op = next((x for x in g["opciones"] if x["id"] == o.id), None) if g else None
                if not op or (o.grupo, o.id) in vistos:
                    raise HTTPException(status_code=422, detail=f"Opción no válida para '{nombre}'.")
                vistos.add((o.grupo, o.id))
                por_grupo[o.grupo] = por_grupo.get(o.grupo, 0) + 1
                selecciones.append(op)
            for g in grupos.values():
                n = por_grupo.get(g["grupo"], 0)
                if g["max"] and n > g["max"]:
                    raise HTTPException(status_code=422, detail=f"En '{g['nombre']}' puede escoger máximo {g['max']}.")
                if g["exigir"] and n == 0:
                    raise HTTPException(status_code=422, detail=f"Escoja una opción de '{g['nombre']}' para '{nombre}'.")
        elif l.opciones:
            raise HTTPException(status_code=422, detail=f"'{nombre}' no tiene opciones para escoger.")
        adicional = sum(s["precio"] for s in selecciones)

        # Presentación: obligatoria si el producto tiene varias
        presentacion = None
        pres_plato = (await catalogo.presentaciones(emp, l.id_plato)).get(l.id_plato, [])
        if pres_plato:
            presentacion = next((x for x in pres_plato if int(x["Id_Forma_Medida"]) == l.presentacion), None)
            if not presentacion:
                raise HTTPException(status_code=422, detail=f"Escoja la presentación de '{nombre}'.")
        elif l.presentacion is not None:
            raise HTTPException(status_code=422, detail=f"'{nombre}' no tiene presentaciones para escoger.")
        factor = float(presentacion["Unidades_Minimas"] or 1) if presentacion else 1.0

        # Precio: solo se acepta el del dispositivo si el plato lo pide
        if int(plato["Pedir_Valor_Venta_Producto"] or 0) == 1:
            if not l.precio:
                raise HTTPException(status_code=422, detail=f"Digite el precio de '{nombre}'.")
            base = l.precio
        else:
            base = precio_base(plato, lista, presentacion)
        valor = con_impuesto(base + adicional, plato["Impuesto"], fact)

        # Descripción: solo se acepta la del dispositivo si el plato la pide
        personalizado = nombre
        if presentacion:
            personalizado = f"{nombre} - {(presentacion['Descripcion'] or '').strip()}"[:MAX_DESCRIPCION]
        if int(plato["Pedir_Descripcion_Producto"] or 0) == 1:
            personalizado = limpiar_texto(l.descripcion, MAX_DESCRIPCION)
            if not personalizado:
                raise HTTPException(status_code=422, detail=f"Digite la descripción de '{nombre}'.")

        # Novedad libre: como el escritorio, Id_Novedad = 0 con la categoría del producto
        nota = limpiar_texto(l.nota, MAX_NOTA).upper()

        preparadas.append({
            "plato": plato, "nombre": nombre, "cantidad": l.cantidad, "valor": valor,
            "personalizado": personalizado, "novedades": novs, "nota": nota, "selecciones": selecciones,
            "novedad_txt": limpiar_texto(" - ".join([n["nombre"] for n in novs] + ([nota] if nota else [])
                                                    + [s["nombre"] for s in selecciones]), 250),
            "impresoras": await catalogo.impresoras_plato(emp, plato),
            "receta": await catalogo.receta_fija(emp, l.id_plato),
            "factor": factor,
            "paga_impuesto": fact["paga_impuesto"],
        })
    return preparadas


_COLS_DETALLE = """
    (Nro_pedido, Fecha, Nro_Factura, Id_Plato, Item, Descripcion, Cantidad, Valor, Hora, Salio,
     Novedad, Cortesia, Porc_Descuento_Plato, Porc_Descuento_General, Impreso, Cambios, Mostrar,
     Impresora, Depende, Enviada_MySql, Nro_Puesto, Cod_Categoria_Plato, Hora_Plato, Paga_Impuesto,
     Impuesto, Impuesto_Original, Paga_Plato, Item_Original, Producto_Personalizado)
    VALUES
    (:nro, :fecha, '0', :plato, :item, :desc, :cant, :valor, :hora, 0,
     :nov, 0, 0, :valor, 0, NULL, :mostrar,
     :impresora, :depende, 0, 1, :cat, :hora, :paga,
     :imp, :imp, 1, :item, :pers)
"""


async def insertar_lineas(tmp: AsyncSession, nro: str, fecha: date, ahora: datetime,
                          lineas: list[dict], item: int) -> int:
    """Inserta las líneas desde el Item indicado. Devuelve el siguiente Item libre."""
    hora = hora_corta(ahora)
    for L in lineas:
        plato = L["plato"]
        inicial = item
        for parte in partes_cantidad(L["cantidad"]):
            maestro = item
            valor = int(round(L["valor"] * parte))      # Valor de la fila = precio × cantidad de la fila
            for idx, impresora in enumerate(L["impresoras"]):
                p = {"nro": nro, "fecha": fecha, "plato": plato["Id_Plato"], "item": item,
                     "desc": L["nombre"][:255], "cant": parte, "valor": valor, "hora": hora, "nov": L["novedad_txt"],
                     "mostrar": 1 if idx == 0 else 0, "impresora": impresora[:255], "depende": str(inicial),
                     "cat": plato["Cod_Categoria"], "paga": L["paga_impuesto"], "imp": plato["Impuesto"] or 0,
                     "pers": L["personalizado"]}
                await tmp.execute(text("INSERT INTO temp_detalle_comanda " + _COLS_DETALLE), p)
                await tmp.execute(text("INSERT INTO temp_detalle_comanda_parcial " + _COLS_DETALLE), p)
                item += 1

            # Inventario por unidad: receta fija (× unidades de la presentación) + opciones escogidas
            insumos = [(r["Id_Grupo"] or 0, r["Id_Item"], round(float(r["Cantidad"] or 0) * L["factor"] * parte, 4),
                        r["Posicion"] or 0, r["Opcion_Cambiar"] or 0, 0) for r in L["receta"]]
            insumos += [(s["id_grupo_inv"] or 0, s["id_item"], round(s["cantidad"] * parte, 4), s["posicion"], 0, s["precio"])
                        for s in L["selecciones"]]
            for grupo, id_item, cantidad, posicion, cambiar, adicional in insumos:
                p = {"nro": nro, "fecha": fecha.strftime("%Y/%m/%d"), "plato": plato["Id_Plato"], "item": maestro,
                     "g": grupo, "i": id_item, "c": cantidad, "pos": posicion, "camb": cambiar, "adic": adicional}
                for tabla in ("temp_plato_producto", "temp_plato_producto_parcial"):
                    await tmp.execute(text(f"""
                        INSERT INTO {tabla}
                            (Nro_Pedido, Fecha, Nro_Factura, Id_Plato, Item, Id_Grupo, Id_Item, Cantidad,
                             Enviada_MySql, Item_Original, Posicion, Opcion_Cambiar, Valor_Adicional_Armar)
                        VALUES (:nro, :fecha, '0', :plato, :item, :g, :i, :c, 0, :item, :pos, :camb, :adic)
                    """), p)

        consecutivo = 0
        for n in L["novedades"]:
            consecutivo += 1
            await tmp.execute(text("""
                INSERT INTO temp_novedades_plato_pedido
                    (Id_Consecutivo, Nro_Pedido, Item, Depende, Cod_Categoria, Id_Novedad, Novedad)
                VALUES (:c, :nro, :item, :item, :cat, :idn, :nov)
            """), {"c": consecutivo, "nro": nro, "item": inicial, "cat": plato["Cod_Categoria"],
                   "idn": n["id"], "nov": n["nombre"]})
        if L["nota"]:
            consecutivo += 1
            await tmp.execute(text("""
                INSERT INTO temp_novedades_plato_pedido
                    (Id_Consecutivo, Nro_Pedido, Item, Depende, Cod_Categoria, Id_Novedad, Novedad)
                VALUES (:c, :nro, :item, :item, :cat, 0, :nov)
            """), {"c": consecutivo, "nro": nro, "item": inicial, "cat": plato["Cod_Categoria"], "nov": L["nota"] + " "})
        if L["selecciones"]:
            consecutivo += 1
            await tmp.execute(text("""
                INSERT INTO temp_novedades_plato_pedido
                    (Id_Consecutivo, Nro_Pedido, Item, Depende, Cod_Categoria, Id_Novedad, Novedad)
                VALUES (:c, :nro, :item, :item, :plato, :plato, :nov)
            """), {"c": consecutivo, "nro": nro, "item": inicial, "plato": plato["Id_Plato"],
                   "nov": " - ".join(s["nombre"] for s in L["selecciones"])})
    return item


async def siguiente_item(tmp: AsyncSession, nro: str) -> int:
    maximo = (await tmp.execute(text("""
        SELECT GREATEST(COALESCE((SELECT MAX(Item) FROM temp_detalle_comanda WHERE Nro_pedido = :n), 0),
                        COALESCE((SELECT MAX(Item) FROM temp_detalle_comanda_parcial WHERE Nro_pedido = :n), 0))
    """), {"n": nro})).scalar()
    return int(maximo or 0) + 1


def numero_pedido(nombre_dispositivo: str, fecha: date, ahora: datetime) -> str:
    """Igual que la app anterior: dispositivo + fecha de negocio + hora (no se repite por dispositivo)."""
    return f"{nombre_dispositivo}-{fecha:%Y/%m/%d}{ahora:%I:%M:%S %p}"
