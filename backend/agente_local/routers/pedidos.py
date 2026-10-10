"""
Pedidos abiertos: todos los dispositivos ven y agregan a TODOS los pedidos (de la toma de pedidos
o de caja), porque un mismo dispositivo lo usan varios meseros. Reglas del escritorio:
  · Salio = 0 en temp_comanda y en temp_detalle_comanda = enviado/abierto; Salio = 1 = se está
    montando en el escritorio (no se muestra en ninguna parte hasta que se envía).
  · Domicilio = 1: pedidos de domicilio, no se muestran aquí.
Cada pedido nuevo queda asignado al mesero del día que se escoge al montarlo (temp_comanda.Mesero),
no al usuario del dispositivo. Agregar productos conserva el mesero del pedido.

Las escrituras usan una conexión propia con un candado de MariaDB (GET_LOCK) para que dos
dispositivos no creen a la vez la misma cuenta, el mismo Nro_Pedido o los mismos Items.
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .. import auditoria
from ..db import get_emp, get_tmp, motor_temp
from ..seguridad import ip_cliente
from ..servicios import bloqueos, impresion, meseros
from ..servicios.negocio import MAX_COMENSALES, exigir_caja_abierta, pedir_comensales
from ..servicios.pedidos import (MAX_NOMBRE_CUENTA, LineaIn, insertar_lineas, limpiar_texto, numero_pedido,
                                 preparar_lineas, siguiente_item, valor_linea)
from ..servicios.precios import CLIENTE_CONSUMIDOR_FINAL
from ..sesion import Mesero, mesero_actual
from ..textos import t
from .catalogo import cliente_valido
from .mesas import mesa_existe

router = APIRouter(prefix="/api/ag", tags=["pedidos"])

ID_CUENTA_NUEVA = 1000      # cuentas sin mesa (zonas dinámicas / llevar), igual que la app anterior


class MesaPedidoIn(BaseModel):
    id: int = Field(ge=0)
    nombre: str = Field(min_length=1, max_length=200)


class PedidoNuevoIn(BaseModel):
    mesa: MesaPedidoIn | None = None                       # mesa existente…
    cuenta_nueva: str | None = Field(default=None, max_length=MAX_NOMBRE_CUENTA)   # …o cuenta con nombre
    id_cliente: int = Field(default=CLIENTE_CONSUMIDOR_FINAL, ge=0)
    mesero: int = Field(gt=0)                              # mesero del día al que se asigna
    comensales: int = Field(default=1, ge=1, le=MAX_COMENSALES)   # solo cuenta si la empresa los pide
    lineas: list[LineaIn] = Field(max_length=60)


class AgregarIn(BaseModel):
    nro_pedido: str = Field(min_length=1, max_length=255)
    lineas: list[LineaIn] = Field(max_length=60)


class ComensalesIn(BaseModel):
    nro_pedido: str = Field(min_length=1, max_length=255)
    comensales: int = Field(ge=1, le=MAX_COMENSALES)


class QuitarIn(BaseModel):
    nro_pedido: str = Field(min_length=1, max_length=255)
    depende: int = Field(ge=1)


@asynccontextmanager
async def _escritura():
    """Conexión con candado exclusivo para las escrituras de pedidos."""
    async with motor_temp.connect() as conn:
        obtenido = (await conn.execute(text("SELECT GET_LOCK('ag_pedidos', 10)"))).scalar()
        await conn.commit()
        if obtenido != 1:
            raise HTTPException(status_code=503, detail="El sistema está ocupado. Intente de nuevo.")
        try:
            yield conn
        except BaseException:
            await conn.rollback()
            raise
        finally:
            await conn.execute(text("SELECT RELEASE_LOCK('ag_pedidos')"))
            await conn.commit()


# Pedido visible: enviado (Salio = 0) y que no es domicilio
VISIBLE = "Salio = 0 AND COALESCE(Domicilio, 0) <> 1"


async def _pedido_abierto(db, nro: str):
    """Pedido abierto de cualquier origen (toma de pedidos o caja), que no sea domicilio."""
    fila = (await db.execute(text(f"""
        SELECT Nro_Pedido, Mesa, Imprimio_Precuenta, Id_Cliente, Hora, Salio, Mesero, Nro_Comenzales
        FROM temp_comanda WHERE Nro_Pedido = :n AND {VISIBLE}
    """), {"n": nro})).mappings().first()
    if not fila or int(fila["Salio"] or 0) != 0:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    return fila


# ───────────────────────────── consultas ─────────────────────────────

@router.get("/meseros-dia")
async def meseros_del_dia(_: Mesero = Depends(mesero_actual), tmp: AsyncSession = Depends(get_tmp)):
    lista = await meseros.del_dia(tmp)
    return {"meseros": lista, "aviso": None if lista else meseros.sin_meseros()}


@router.get("/pedidos")
async def pedidos_abiertos(_: Mesero = Depends(mesero_actual), emp: AsyncSession = Depends(get_emp),
                           tmp: AsyncSession = Depends(get_tmp)):
    """Todos los pedidos abiertos (de cualquier dispositivo, mesero o de caja), sin domicilios.
    Solo cuenta el detalle enviado (Salio = 0)."""
    filas = (await tmp.execute(text("""
        SELECT c.Nro_Pedido, c.Mesa, c.Imprimio_Precuenta, c.Hora, c.Id_Cliente, c.Mesero,
               COALESCE(SUM(CASE WHEN d.Mostrar = 1 THEN d.Valor END), 0) AS total,
               COALESCE(SUM(CASE WHEN d.Mostrar = 1 THEN d.Cantidad END), 0) AS unidades
        FROM temp_comanda c
        LEFT JOIN temp_detalle_comanda d ON d.Nro_pedido = c.Nro_Pedido AND d.Salio = 0
        WHERE c.Salio = 0 AND COALESCE(c.Domicilio, 0) <> 1
        GROUP BY c.Nro_Pedido, c.Mesa, c.Imprimio_Precuenta, c.Hora, c.Id_Cliente, c.Mesero
        ORDER BY c.Mesa
    """))).mappings().all()
    nombres = await meseros.nombres(emp, tmp, {f["Mesero"] for f in filas})
    return [{"nro_pedido": f["Nro_Pedido"], "mesa": f["Mesa"], "id_mesa": int(f["Imprimio_Precuenta"] or 0),
             "hora": f["Hora"], "id_cliente": int(f["Id_Cliente"] or 0),
             "mesero": nombres.get(int(f["Mesero"] or 0)) or "",
             "total": int(f["total"] or 0), "unidades": round(float(f["unidades"] or 0), 3)} for f in filas]


@router.get("/pedido")
async def ver_pedido(nro: str = Query(min_length=1, max_length=255), _: Mesero = Depends(mesero_actual),
                     emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    pedido = await _pedido_abierto(tmp, nro)
    filas = (await tmp.execute(text("""
        SELECT Item, Depende, Id_Plato, Descripcion, Producto_Personalizado, Cantidad, Valor, Novedad,
               Impreso, Salio, Mostrar
        FROM temp_detalle_comanda WHERE Nro_pedido = :n AND Salio = 0 ORDER BY Item
    """), {"n": nro})).mappings().all()
    lineas: dict[str, dict] = {}
    for f in filas:
        dep = str(f["Depende"])
        L = lineas.setdefault(dep, {
            "depende": int(dep) if dep.isdigit() else 0, "id_plato": int(f["Id_Plato"]),
            "nombre": (f["Producto_Personalizado"] or f["Descripcion"] or "").strip(),
            "novedad": (f["Novedad"] or "").strip(),
            "cantidad": 0.0, "subtotal": 0, "impreso": True, "puede_quitar": True})
        if int(f["Impreso"] or 0) or int(f["Salio"] or 0):
            L["puede_quitar"] = False
        if int(f["Mostrar"] or 0) == 1:
            L["cantidad"] = round(L["cantidad"] + float(f["Cantidad"] or 0), 3)
            L["subtotal"] += int(f["Valor"] or 0)
            L["impreso"] = L["impreso"] and bool(int(f["Impreso"] or 0))
    lista = list(lineas.values())
    cod = int(pedido["Mesero"] or 0)
    return {"nro_pedido": pedido["Nro_Pedido"], "mesa": pedido["Mesa"],
            "id_mesa": int(pedido["Imprimio_Precuenta"] or 0), "hora": pedido["Hora"],
            "comensales": max(1, int(pedido["Nro_Comenzales"] or 1)), "pedir_comensales": await pedir_comensales(emp),
            "mesero": (await meseros.nombres(emp, tmp, {cod})).get(cod) or "",
            "cliente": await cliente_valido(emp, int(pedido["Id_Cliente"] or CLIENTE_CONSUMIDOR_FINAL)),
            "lineas": lista, "total": sum(L["subtotal"] for L in lista)}


# ───────────────────────────── escrituras ─────────────────────────────

@router.post("/pedidos")
async def crear_pedido(data: PedidoNuevoIn, request: Request, mesero: Mesero = Depends(mesero_actual),
                       emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    if bool(data.mesa) == bool(data.cuenta_nueva):
        raise HTTPException(status_code=422, detail=f"Escoja dónde montar el pedido: una opción de {t('cuentas')} o un nombre nuevo.")
    fecha = await exigir_caja_abierta(emp)           # con la caja cerrada no se comanda
    cliente = await cliente_valido(emp, data.id_cliente)
    lineas = await preparar_lineas(emp, tmp, data.lineas, cliente["id"])
    # Sin Pedir_Cantidad_Comenzales la empresa no usa comensales: siempre 1 (no se toma lo que mande el navegador)
    comensales = data.comensales if await pedir_comensales(emp) else 1

    if data.mesa and not await mesa_existe(emp, data.mesa.id, data.mesa.nombre):
        raise HTTPException(status_code=404, detail=f"'{data.mesa.nombre.strip()}' no existe.")

    async with _escritura() as conn:
        if data.mesa:
            id_mesa, nombre_mesa = data.mesa.id, data.mesa.nombre
        else:
            nombre_mesa = limpiar_texto(data.cuenta_nueva, MAX_NOMBRE_CUENTA).upper()
            if not nombre_mesa:
                raise HTTPException(status_code=422, detail="Escriba el nombre de la cuenta.")
            maximo = (await conn.execute(text(
                "SELECT MAX(Imprimio_Precuenta) FROM temp_comanda WHERE Imprimio_Precuenta >= :b"),
                {"b": ID_CUENTA_NUEVA})).scalar()
            id_mesa = int(maximo) + 1 if maximo else ID_CUENTA_NUEVA

        await meseros.validar(conn, data.mesero)
        existente = (await conn.execute(text(f"SELECT {VISIBLE} AS visible FROM temp_comanda WHERE Mesa = :m LIMIT 1"),
                                        {"m": nombre_mesa})).scalar()
        if existente is not None:
            if int(existente or 0) == 1:
                raise HTTPException(status_code=409, detail=f"'{nombre_mesa.strip()}' ya tiene un pedido abierto. Agregue los {t('productos')} a ese pedido.")
            raise HTTPException(status_code=409, detail=f"'{nombre_mesa.strip()}' está en uso en caja.")
        otro = await bloqueos.quien_bloquea(conn, id_mesa, nombre_mesa, mesero)
        if otro:
            raise HTTPException(status_code=409, detail=f"'{nombre_mesa.strip()}' está en uso en {otro}.")

        for _ in range(3):
            ahora = datetime.now()
            nro = numero_pedido(mesero.nombre_dispositivo, fecha, ahora)
            if not (await conn.execute(text("SELECT COUNT(*) FROM temp_comanda WHERE Nro_Pedido = :n"),
                                       {"n": nro})).scalar():
                break
            await asyncio.sleep(1.1)
        else:
            raise HTTPException(status_code=503, detail="No fue posible numerar el pedido. Intente de nuevo.")

        await conn.execute(text("""
            INSERT INTO temp_comanda
                (Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora, Mesero, Cancelado, Valor, Salio, Cortesia,
                 Imprimio_Precuenta, Nro_Comenzales, Nro_Puestos, Domicilio, Id_Cliente, Movil)
            VALUES (:n, :f, '0', :mesa, :hora, :mesero, 0, 0, 0, 0, :id_mesa, :comensales, 1, 0, :cli, 1)
        """), {"n": nro, "f": fecha.strftime("%Y/%m/%d"), "mesa": nombre_mesa, "hora": ahora.strftime("%I:%M:%S %p"),
               "mesero": data.mesero, "id_mesa": id_mesa, "comensales": comensales, "cli": cliente["id"]})
        await insertar_lineas(conn, nro, fecha, ahora, lineas, 1)
        # Enviar_Pedido_Impresion: a la cola que el escritorio manda a las impresoras
        await impresion.enviar_pedido_impresion(conn, emp, nro, True, fecha, ahora, mesero.nombre_dispositivo)
        await bloqueos.liberar(conn, id_mesa, nombre_mesa, mesero)
        await conn.commit()

    await auditoria.registrar("pedido_nuevo", "ok", ip_cliente(request), mesero.usuario, mesero.cod_empleado,
                              mesero.id_dispositivo, detalle=f"{nro} · {nombre_mesa} · {t('mesero')} {data.mesero}")
    return {"nro_pedido": nro, "mesa": nombre_mesa, "id_mesa": id_mesa,
            "total": sum(valor_linea(L["valor"], L["cantidad"]) for L in lineas)}


@router.post("/pedido/agregar")
async def agregar_productos(data: AgregarIn, request: Request, mesero: Mesero = Depends(mesero_actual),
                            emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    fecha = await exigir_caja_abierta(emp)
    pedido = await _pedido_abierto(tmp, data.nro_pedido)
    # Los precios salen de la lista del cliente del pedido
    lineas = await preparar_lineas(emp, tmp, data.lineas, int(pedido["Id_Cliente"] or CLIENTE_CONSUMIDOR_FINAL))

    async with _escritura() as conn:
        pedido = await _pedido_abierto(conn, data.nro_pedido)
        otro = await bloqueos.quien_bloquea(conn, int(pedido["Imprimio_Precuenta"] or 0), pedido["Mesa"], mesero)
        if otro:
            raise HTTPException(status_code=409, detail=f"'{pedido['Mesa'].strip()}' está en uso en {otro}.")
        item = await siguiente_item(conn, data.nro_pedido)
        ahora = datetime.now()
        await insertar_lineas(conn, data.nro_pedido, fecha, ahora, lineas, item)
        await impresion.enviar_pedido_impresion(conn, emp, data.nro_pedido, False, fecha, ahora, mesero.nombre_dispositivo)
        await conn.commit()

    await auditoria.registrar("pedido_agregar", "ok", ip_cliente(request), mesero.usuario, mesero.cod_empleado,
                              mesero.id_dispositivo, detalle=data.nro_pedido)
    return {"ok": True, "agregado": sum(valor_linea(L["valor"], L["cantidad"]) for L in lineas)}


@router.post("/pedido/comensales")
async def cambiar_comensales(data: ComensalesIn, request: Request, mesero: Mesero = Depends(mesero_actual),
                             emp: AsyncSession = Depends(get_emp)):
    """Cambia el número de comensales de una cuenta abierta (temp_comanda.Nro_Comenzales); al registrar
    el recibo o la factura pasa a recibos_comanda / comanda."""
    await exigir_caja_abierta(emp)
    if not await pedir_comensales(emp):
        raise HTTPException(status_code=409, detail="Esta empresa no maneja el número de comensales.")
    async with _escritura() as conn:
        pedido = await _pedido_abierto(conn, data.nro_pedido)
        otro = await bloqueos.quien_bloquea(conn, int(pedido["Imprimio_Precuenta"] or 0), pedido["Mesa"], mesero)
        if otro:
            raise HTTPException(status_code=409, detail=f"'{pedido['Mesa'].strip()}' está en uso en {otro}.")
        await conn.execute(text("UPDATE temp_comanda SET Nro_Comenzales = :c WHERE Nro_Pedido = :n"),
                           {"c": data.comensales, "n": data.nro_pedido})
        await conn.commit()

    anterior = int(pedido["Nro_Comenzales"] or 0)
    await auditoria.registrar("pedido_comensales", "ok", ip_cliente(request), mesero.usuario, mesero.cod_empleado,
                              mesero.id_dispositivo, detalle=f"{data.nro_pedido} · {anterior} → {data.comensales}")
    return {"ok": True, "comensales": data.comensales}


@router.post("/pedido/quitar")
async def quitar_linea(data: QuitarIn, request: Request, mesero: Mesero = Depends(mesero_actual)):
    """Regla del negocio (2026-10-05): desde la toma de pedidos NO se elimina nada ya enviado (ni
    productos ni la cuenta), aunque no esté impreso; solo se quita del carrito mientras se monta.
    Eliminar lo enviado se hace únicamente en el escritorio."""
    await auditoria.registrar("pedido_quitar", "rechazado", ip_cliente(request), mesero.usuario,
                              mesero.cod_empleado, mesero.id_dispositivo, detalle=data.nro_pedido)
    raise HTTPException(status_code=403, detail="Lo enviado solo se elimina desde el escritorio (solicítelo en caja).")
