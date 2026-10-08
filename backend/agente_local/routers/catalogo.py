"""
Carta (con precios de la lista del cliente), opciones de armado / menú del día y clientes.
"""
import hashlib
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_emp, get_tmp
from ..servicios import catalogo, fotos
from ..servicios.negocio import facturacion, fecha_negocio, opciones_toma
from ..servicios.precios import CLIENTE_CONSUMIDOR_FINAL, con_impuesto, lista_cliente, precio_plato
from ..sesion import Mesero, mesero_actual
from ..textos import textos

router = APIRouter(prefix="/api/ag", tags=["catalogo"])


async def cliente_valido(emp: AsyncSession, id_cliente: int) -> dict:
    fila = (await emp.execute(text("""
        SELECT Id_Cliente, cedula, nombres, Apellidos FROM clientes WHERE Id_Cliente = :c
    """), {"c": id_cliente})).mappings().first()
    if fila:
        nombre = " ".join(x for x in ((fila["nombres"] or "").strip(), (fila["Apellidos"] or "").strip()) if x)
        return {"id": int(fila["Id_Cliente"]), "nombre": nombre, "cedula": (fila["cedula"] or "").strip()}
    if id_cliente == CLIENTE_CONSUMIDOR_FINAL:
        return {"id": CLIENTE_CONSUMIDOR_FINAL, "nombre": "Consumidor Final", "cedula": "222222222222"}
    raise HTTPException(status_code=422, detail="El cliente no existe.")


@router.get("/config")
async def config_toma(mesero: Mesero = Depends(mesero_actual),
                      emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    return {"fecha_negocio": (await fecha_negocio(emp)).isoformat(),
            **await opciones_toma(emp), **await facturacion(emp),
            "cliente_default": await cliente_valido(emp, CLIENTE_CONSUMIDOR_FINAL),
            "textos": textos()}


@router.get("/catalogo")
async def carta(response: Response, cliente: int = Query(CLIENTE_CONSUMIDOR_FINAL, ge=0),
                if_none_match: str | None = Header(default=None),
                mesero: Mesero = Depends(mesero_actual),
                emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    await cliente_valido(emp, cliente)
    fact = await facturacion(emp)
    lista = await lista_cliente(emp, cliente)
    para_armar = await catalogo.platos_para_armar(emp)
    pres = await catalogo.presentaciones(emp)
    idx_prod = fotos.indice(await fotos.carpeta(emp, "productos"))
    idx_cat = fotos.indice(await fotos.carpeta(emp, "categorias"))

    def url_foto(tipo: str, ident: int, idx: dict, nombre) -> str | None:
        v = fotos.version(idx, nombre)
        return f"/api/ag/fotos/{tipo}/{ident}?v={v}" if v is not None else None

    platos = []
    for p in await catalogo.platos_visibles(emp):
        item = {
            "id": int(p["Id_Plato"]), "nombre": (p["Nombre"] or "").strip(),
            "categoria": int(p["Cod_Categoria"]), "precio": precio_plato(p, lista, fact),
            "pedir_precio": int(p["Pedir_Valor_Venta_Producto"] or 0),
            "pedir_descripcion": int(p["Pedir_Descripcion_Producto"] or 0),
            "armado": catalogo.tipo_armado(p, para_armar),
            "foto": url_foto("plato", int(p["Id_Plato"]), idx_prod, p["Ruta_Foto"]),
            # % que se suma al precio digitado (solo si la empresa cobra impuesto aparte)
            "impuesto_aparte": float(p["Impuesto"] or 0)
                if fact["paga_impuesto"] == 1 and fact["precios_incluyen_impuesto"] == 0 else 0,
        }
        if int(p["Id_Plato"]) in pres:
            # Varias presentaciones: el dispositivo muestra una grilla para escoger
            item["presentaciones"] = [{
                "id": int(x["Id_Forma_Medida"]), "nombre": (x["Descripcion"] or "").strip(),
                "precio": precio_plato(p, lista, fact, x), "unidades": float(x["Unidades_Minimas"] or 1),
            } for x in pres[int(p["Id_Plato"])]]
            item["precio"] = item["presentaciones"][0]["precio"]
        platos.append(item)
    cats = [{"id": c["id"], "nombre": c["nombre"], "foto": url_foto("categoria", c["id"], idx_cat, c["Nombre_foto"])}
            for c in await catalogo.categorias(emp)]
    datos = {"categorias": cats, "platos": platos, "colores": await catalogo.colores(emp),
             "novedades": {str(k): v for k, v in (await catalogo.novedades(emp)).items()}}

    # Versión de la carta: si no cambió, el dispositivo no la vuelve a descargar
    version = '"' + hashlib.sha1(json.dumps(datos, sort_keys=True).encode()).hexdigest() + '"'
    response.headers["ETag"] = version
    if if_none_match == version:
        return Response(status_code=304, headers={"ETag": version})
    return {"version": version, "cliente": cliente, **datos}


@router.get("/catalogo/plato/{id_plato}/opciones")
async def opciones_plato(id_plato: int, mesero: Mesero = Depends(mesero_actual),
                         emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    plato = await catalogo.plato_visible(emp, id_plato)
    if not plato:
        raise HTTPException(status_code=404, detail=f"{textos()['producto']} no disponible.")
    para_armar = await catalogo.platos_para_armar(emp)
    tipo = catalogo.tipo_armado(plato, para_armar)
    grupos = await catalogo.opciones(emp, plato, await fecha_negocio(emp), para_armar)
    fact = await facturacion(emp)
    if tipo == "menu" and not grupos:
        raise HTTPException(status_code=409, detail="El menú del día no está armado para hoy.")
    # Al dispositivo solo le sirve id, nombre y si viene marcada por defecto
    return {"tipo": tipo, "grupos": [{
        "grupo": g["grupo"], "nombre": g["nombre"], "max": g["max"], "exigir": g["exigir"],
        "opciones": [{"id": o["id"], "nombre": o["nombre"], "por_defecto": o["por_defecto"],
                      # adicional que suma al plato (con el impuesto si la empresa lo cobra aparte)
                      "precio": con_impuesto(o["precio"], plato["Impuesto"], fact)} for o in g["opciones"]],
    } for g in grupos]}


async def _foto(emp: AsyncSession, tipo: str, sql: str, ident: int) -> FileResponse:
    nombre = (await emp.execute(text(sql), {"i": ident})).scalar()
    ruta = fotos.archivo(await fotos.carpeta(emp, tipo), nombre)
    if not ruta:
        raise HTTPException(status_code=404, detail="Sin foto.")
    # La URL lleva la versión (?v=) del archivo: el navegador la puede guardar
    return FileResponse(fotos.miniatura(ruta), headers={"Cache-Control": "public, max-age=604800"})


# Las fotos se piden desde <img> (sin encabezado de sesión): solo por id de un plato o
# categoría visible, nunca por nombre de archivo, y solo dentro de la carpeta configurada.
@router.get("/fotos/plato/{id_plato}")
async def foto_plato(id_plato: int, emp: AsyncSession = Depends(get_emp)):
    return await _foto(emp, "productos", "SELECT Ruta_Foto FROM platos WHERE Id_Plato = :i AND Activo = 0", id_plato)


@router.get("/fotos/categoria/{cod}")
async def foto_categoria(cod: int, emp: AsyncSession = Depends(get_emp)):
    return await _foto(emp, "categorias", "SELECT Nombre_foto FROM categoria_platos WHERE Cod_Categoria = :i AND Activa = 1", cod)


@router.get("/clientes")
async def buscar_clientes(q: str = Query(min_length=3, max_length=50), mesero: Mesero = Depends(mesero_actual),
                          emp: AsyncSession = Depends(get_emp)):
    # Los comodines que escriba el usuario se buscan como texto
    patron = "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    filas = (await emp.execute(text("""
        SELECT Id_Cliente, cedula, nombres, Apellidos,
               EXISTS (SELECT 1 FROM lista_precios_cliente l WHERE l.Id_Cliente = c.Id_Cliente AND l.Activa = 1) AS lista
        FROM clientes c
        WHERE c.cedula LIKE :p OR c.nombres LIKE :p OR c.Apellidos LIKE :p
           OR CONCAT_WS(' ', c.nombres, c.Apellidos) LIKE :p
        ORDER BY c.nombres
        LIMIT 20
    """), {"p": patron})).mappings().all()
    return [{"id": int(f["Id_Cliente"]),
             "nombre": " ".join(x for x in ((f["nombres"] or "").strip(), (f["Apellidos"] or "").strip()) if x),
             "cedula": (f["cedula"] or "").strip(), "tiene_lista": bool(f["lista"])} for f in filas]
