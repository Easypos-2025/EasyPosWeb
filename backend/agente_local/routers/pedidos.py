"""
Pedidos del mesero: solo ve y modifica los suyos (temp_comanda.Mesero = su código).

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
from ..servicios import bloqueos
from ..servicios.negocio import fecha_negocio
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
    lineas: list[LineaIn] = Field(max_length=60)


class AgregarIn(BaseModel):
    nro_pedido: str = Field(min_length=1, max_length=255)
    lineas: list[LineaIn] = Field(max_length=60)


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


async def _pedido_mio(db, nro: str, mesero: Mesero):
    fila = (await db.execute(text("""
        SELECT Nro_Pedido, Mesa, Imprimio_Precuenta, Id_Cliente, Hora, Salio
        FROM temp_comanda WHERE Nro_Pedido = :n AND Mesero = :c
    """), {"n": nro, "c": mesero.cod_empleado})).mappings().first()
    if not fila or int(fila["Salio"] or 0) != 0:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    return fila


# ───────────────────────────── consultas ─────────────────────────────

@router.get("/pedidos")
async def mis_pedidos(mesero: Mesero = Depends(mesero_actual), tmp: AsyncSession = Depends(get_tmp)):
    filas = (await tmp.execute(text("""
        SELECT c.Nro_Pedido, c.Mesa, c.Imprimio_Precuenta, c.Hora, c.Id_Cliente,
               COALESCE(SUM(CASE WHEN d.Mostrar = 1 THEN d.Valor END), 0) AS total,
               COALESCE(SUM(CASE WHEN d.Mostrar = 1 THEN d.Cantidad END), 0) AS unidades
        FROM temp_comanda c
        LEFT JOIN temp_detalle_comanda d ON d.Nro_pedido = c.Nro_Pedido
        WHERE c.Mesero = :c AND c.Salio = 0
        GROUP BY c.Nro_Pedido, c.Mesa, c.Imprimio_Precuenta, c.Hora, c.Id_Cliente
        ORDER BY c.Mesa
    """), {"c": mesero.cod_empleado})).mappings().all()
    return [{"nro_pedido": f["Nro_Pedido"], "mesa": f["Mesa"], "id_mesa": int(f["Imprimio_Precuenta"] or 0),
             "hora": f["Hora"], "id_cliente": int(f["Id_Cliente"] or 0),
             "total": int(f["total"] or 0), "unidades": round(float(f["unidades"] or 0), 3)} for f in filas]


@router.get("/pedido")
async def ver_pedido(nro: str = Query(min_length=1, max_length=255), mesero: Mesero = Depends(mesero_actual),
                     emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    pedido = await _pedido_mio(tmp, nro, mesero)
    filas = (await tmp.execute(text("""
        SELECT Item, Depende, Id_Plato, Descripcion, Producto_Personalizado, Cantidad, Valor, Novedad,
               Impreso, Salio, Mostrar
        FROM temp_detalle_comanda WHERE Nro_pedido = :n ORDER BY Item
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
    return {"nro_pedido": pedido["Nro_Pedido"], "mesa": pedido["Mesa"],
            "id_mesa": int(pedido["Imprimio_Precuenta"] or 0), "hora": pedido["Hora"],
            "cliente": await cliente_valido(emp, int(pedido["Id_Cliente"] or CLIENTE_CONSUMIDOR_FINAL)),
            "lineas": lista, "total": sum(L["subtotal"] for L in lista)}


# ───────────────────────────── escrituras ─────────────────────────────

@router.post("/pedidos")
async def crear_pedido(data: PedidoNuevoIn, request: Request, mesero: Mesero = Depends(mesero_actual),
                       emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    if bool(data.mesa) == bool(data.cuenta_nueva):
        raise HTTPException(status_code=422, detail=f"Escoja dónde montar el pedido: una opción de {t('cuentas')} o un nombre nuevo.")
    cliente = await cliente_valido(emp, data.id_cliente)
    lineas = await preparar_lineas(emp, tmp, data.lineas, cliente["id"])
    fecha = await fecha_negocio(tmp)

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

        dueno = (await conn.execute(text("SELECT Mesero FROM temp_comanda WHERE Mesa = :m LIMIT 1"),
                                    {"m": nombre_mesa})).scalar()
        if dueno is not None:
            if int(dueno or 0) == mesero.cod_empleado:
                raise HTTPException(status_code=409, detail=f"'{nombre_mesa.strip()}' ya tiene un pedido suyo. Agregue los {t('productos')} a ese pedido.")
            raise HTTPException(status_code=409, detail=f"'{nombre_mesa.strip()}' ya tiene un pedido abierto.")
        otro = await bloqueos.quien_bloquea(conn, id_mesa, nombre_mesa, mesero)
        if otro:
            raise HTTPException(status_code=409, detail=f"'{nombre_mesa.strip()}' está en uso en {otro}.")

        for _ in range(3):
            ahora = datetime.now()
            nro = numero_pedido(mesero.nombre_dispositivo, ahora)
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
            VALUES (:n, :f, '0', :mesa, :hora, :mesero, 0, 0, 0, 0, :id_mesa, 1, 1, 0, :cli, 1)
        """), {"n": nro, "f": fecha.strftime("%Y/%m/%d"), "mesa": nombre_mesa, "hora": ahora.strftime("%I:%M:%S %p"),
               "mesero": mesero.cod_empleado, "id_mesa": id_mesa, "cli": cliente["id"]})
        await insertar_lineas(conn, nro, fecha, ahora, lineas, 1)
        await bloqueos.liberar(conn, id_mesa, nombre_mesa, mesero)
        await conn.commit()

    await auditoria.registrar("pedido_nuevo", "ok", ip_cliente(request), mesero.usuario, mesero.cod_empleado,
                              mesero.id_dispositivo, detalle=f"{nro} · {nombre_mesa}")
    return {"nro_pedido": nro, "mesa": nombre_mesa, "id_mesa": id_mesa,
            "total": sum(valor_linea(L["valor"], L["cantidad"]) for L in lineas)}


@router.post("/pedido/agregar")
async def agregar_productos(data: AgregarIn, request: Request, mesero: Mesero = Depends(mesero_actual),
                            emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    pedido = await _pedido_mio(tmp, data.nro_pedido, mesero)
    # Los precios salen de la lista del cliente del pedido
    lineas = await preparar_lineas(emp, tmp, data.lineas, int(pedido["Id_Cliente"] or CLIENTE_CONSUMIDOR_FINAL))
    fecha = await fecha_negocio(tmp)

    async with _escritura() as conn:
        pedido = await _pedido_mio(conn, data.nro_pedido, mesero)
        otro = await bloqueos.quien_bloquea(conn, int(pedido["Imprimio_Precuenta"] or 0), pedido["Mesa"], mesero)
        if otro:
            raise HTTPException(status_code=409, detail=f"'{pedido['Mesa'].strip()}' está en uso en {otro}.")
        item = await siguiente_item(conn, data.nro_pedido)
        await insertar_lineas(conn, data.nro_pedido, fecha, datetime.now(), lineas, item)
        await conn.commit()

    await auditoria.registrar("pedido_agregar", "ok", ip_cliente(request), mesero.usuario, mesero.cod_empleado,
                              mesero.id_dispositivo, detalle=data.nro_pedido)
    return {"ok": True, "agregado": sum(valor_linea(L["valor"], L["cantidad"]) for L in lineas)}


@router.post("/pedido/quitar")
async def quitar_linea(data: QuitarIn, request: Request, mesero: Mesero = Depends(mesero_actual)):
    """Quita una línea completa (todas sus unidades e impresoras) si nada de ella se ha impreso."""
    async with _escritura() as conn:
        pedido = await _pedido_mio(conn, data.nro_pedido, mesero)
        p = {"n": data.nro_pedido, "d": str(data.depende)}
        filas = (await conn.execute(text("""
            SELECT Item, Impreso, Salio FROM temp_detalle_comanda WHERE Nro_pedido = :n AND Depende = :d
            UNION ALL
            SELECT Item, Impreso, Salio FROM temp_detalle_comanda_parcial WHERE Nro_pedido = :n AND Depende = :d
        """), p)).mappings().all()
        if not filas:
            raise HTTPException(status_code=404, detail="Producto no encontrado en el pedido.")
        if any(int(f["Impreso"] or 0) or int(f["Salio"] or 0) for f in filas):
            raise HTTPException(status_code=409, detail="Ese producto ya se imprimió; no se puede quitar desde aquí.")

        items = sorted({int(f["Item"]) for f in filas})
        await conn.execute(text("DELETE FROM temp_detalle_comanda WHERE Nro_pedido = :n AND Depende = :d"), p)
        await conn.execute(text("DELETE FROM temp_detalle_comanda_parcial WHERE Nro_pedido = :n AND Depende = :d"), p)
        for item in items:
            for tabla in ("temp_plato_producto", "temp_plato_producto_parcial"):
                await conn.execute(text(f"DELETE FROM {tabla} WHERE Nro_Pedido = :n AND Item = :i"),
                                   {"n": data.nro_pedido, "i": item})
        await conn.execute(text("""
            DELETE FROM temp_novedades_plato_pedido WHERE Nro_Pedido = :n AND Item = :d AND Depende = :d
        """), {"n": data.nro_pedido, "d": data.depende})

        # Pedido sin productos: se retira para liberar la mesa
        vacio = not (await conn.execute(text("SELECT COUNT(*) FROM temp_detalle_comanda WHERE Nro_pedido = :n"),
                                        {"n": data.nro_pedido})).scalar()
        if vacio:
            await conn.execute(text("DELETE FROM temp_comanda WHERE Nro_Pedido = :n AND Mesero = :c"),
                               {"n": data.nro_pedido, "c": mesero.cod_empleado})
            await bloqueos.liberar(conn, int(pedido["Imprimio_Precuenta"] or 0), pedido["Mesa"], mesero)
        await conn.commit()

    await auditoria.registrar("pedido_quitar", "ok", ip_cliente(request), mesero.usuario, mesero.cod_empleado,
                              mesero.id_dispositivo, detalle=f"{data.nro_pedido} · línea {data.depende}")
    return {"ok": True, "pedido_eliminado": vacio}
