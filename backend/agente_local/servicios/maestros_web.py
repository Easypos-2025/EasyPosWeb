"""
S3 — Tablas maestras de la web hacia el escritorio. NO es automático: lo ejecuta el admin desde el
panel de la mini-app ("Catálogo de la web") o desde el escritorio (modCatalogoWeb.bas: deja la
solicitud en ag_config y el ciclo del agente la atiende). La web manda (decisión del usuario 2026-10-10).

  Qué baja (lo que la web tiene pendiente), en este orden:
    1. Catálogos con número propio: formas de medida → categorías de productos → categorías de platos
       → proveedores → insumos (con sus formas de medida y proveedores) → clientes.
    2. Platos, con lo que viaja con ellos: impresoras, receta (insumos fijos), armado y presentaciones.
    3. Listas de precios (y su cabecera, si la sede tiene esa tabla).
    4. Datos de la sede (configuracion_sede) y las fotos.

  Número provisional (lo creado en la web, ≥ ID_PROVISIONAL): se crea en el escritorio con el siguiente
  número (mayor entre el escritorio y la web) y ag_maestros_mapa2 guarda provisional → real ANTES de avisar
  a la web (un reintento no duplica). Las referencias a provisionales (insumo → forma de medida, armado →
  insumo, lista → cliente…) se traducen con ese mapa.

  Solo se escriben las columnas que existen en la tabla de esa sede, con sus tipos y largos.
  Lo que viaja con el plato o el insumo se reemplaza solo si la web tiene al menos una fila (una lista
  vacía casi siempre es "la web nunca lo tuvo", no "quitar todo"). Las tablas son MyISAM (sin rollback):
  cada registro se escribe completo antes del siguiente.
"""
import logging
from datetime import datetime

from sqlalchemy import text

from .. import nube
from ..db import SesionTemp, motor_empresa

log = logging.getLogger("agente_local")

ID_PROVISIONAL = 900_000_000
ORDEN = ("forma_medida", "categoria_productos", "categoria_platos", "proveedor", "insumo", "cliente")
NOMBRES = {"forma_medida": "formas de medida", "categoria_productos": "categorías de productos",
           "categoria_platos": "categorías de platos", "proveedor": "proveedores", "insumo": "insumos",
           "cliente": "clientes", "plato": "platos"}

# Tabla del escritorio y su número, por catálogo (las columnas y referencias las manda la web)
ESCRITORIO = {
    "forma_medida": ("forma_medida", "Id_Forma_Medida", "Descripcion"),
    "categoria_productos": ("categoria_productos", "Cod_Categoria", "Nombre"),
    "categoria_platos": ("categoria_platos", "Cod_Categoria", "Nombre"),
    "proveedor": ("proveedores", "Id_Proveedor", "Empresa"),
    "insumo": ("inventario_porciones", "Id_Item", "Descripcion"),
    "cliente": ("clientes", "Id_Cliente", "nombres"),
}
REFS = {
    "insumo": {"Und_Compra": "forma_medida", "Und_Uso": "forma_medida", "Agrupar": "categoria_productos"},
    "plato": {"Cod_Categoria": "categoria_platos"},
}
HIJOS_INSUMO = {
    "insumos_forma_medida": ("insumos_forma_medida", "Id_Insumo", {"Id_Forma_Medida": "forma_medida"}),
    "insumos_proveedor": ("insumos_proveedor", "Id_Insumo", {"Id_Proveedor": "proveedor", "Id_Forma_Medida": "forma_medida"}),
}
HIJOS_PLATO = {
    "receta": ("inventario_porciones_plato", "Id_Plato", {"Id_Item": "insumo", "Id_Grupo": "categoria_productos", "Posicion": "insumo"}),
    "armado": ("plato_armar", "Id_Plato", {"Cod_Categoria": "categoria_productos"}),
    "armado_detalle": ("plato_armar_detalle", "Id_Plato", {"Cod_Categoria": "categoria_productos", "Item": "insumo",
                                                          "Posicion": "insumo"}),
    "presentaciones": ("plato_producto", "Id_Plato", {"Id_Forma_Medida": "forma_medida", "id_proveedor": "proveedor"}),
}
REFS_LISTA = {"Id_Cliente": "cliente", "Id_Producto": "plato", "Id_Presentacion": "forma_medida"}

estado = {"ultimo": None}


def _provisional(v) -> bool:
    try:
        return int(v) >= ID_PROVISIONAL
    except (TypeError, ValueError):
        return False


class Escritorio:
    """Escritura en la BD de la empresa: columnas reales de cada tabla, mapa de provisionales."""

    def __init__(self, conn, resultado: dict):
        self.conn = conn
        self.res = resultado
        self.cols: dict[str, dict] = {}
        self.mapa: dict[str, dict[int, int]] = {}

    async def cargar_mapa(self) -> None:
        async with SesionTemp() as tmp:
            for ent, w, r in (await tmp.execute(text("SELECT entidad, id_web, id_real FROM ag_maestros_mapa2"))).all():
                self.mapa.setdefault(ent, {})[int(w)] = int(r)

    async def columnas(self, tabla: str) -> dict:
        """{nombre en minúscula: (nombre real, tipo, largo)} de la tabla de esta sede ({} si no existe)."""
        if tabla not in self.cols:
            filas = (await self.conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length FROM information_schema.columns
                WHERE table_schema = DATABASE() AND table_name = :t
            """), {"t": tabla})).all()
            self.cols[tabla] = {c.lower(): (c, (t or "").lower(), n) for c, t, n in filas}
        return self.cols[tabla]

    def _convertir(self, valor, tipo: str, largo):
        if valor is None:
            return None
        if tipo in ("varchar", "char", "text", "longtext", "mediumtext", "tinytext"):
            v = str(valor).replace("\x00", "")
            return v[: int(largo)] if largo else v[:65000]
        if tipo in ("int", "tinyint", "smallint", "mediumint", "bigint"):
            try:
                return int(round(float(valor)))
            except (TypeError, ValueError):
                return 0
        if tipo in ("decimal", "double", "float"):
            try:
                return float(valor)
            except (TypeError, ValueError):
                return 0
        if tipo in ("date", "datetime", "timestamp"):
            texto = str(valor).replace("T", " ")[:19]
            return texto if texto[:4].isdigit() else None
        return valor

    def traducir(self, entidad: str, valor):
        """Número provisional de la web → número real del escritorio (None si aún no lo tiene)."""
        if not _provisional(valor):
            return valor
        return self.mapa.get(entidad, {}).get(int(valor))

    async def preparar(self, tabla: str, datos: dict, refs: dict, nombre: str) -> dict:
        cols = await self.columnas(tabla)
        out = {}
        for k, v in datos.items():
            meta = cols.get(k.lower())
            if not meta:
                continue                                   # esa sede no tiene la columna
            if k in refs and v not in (None, ""):
                real = self.traducir(refs[k], v)
                if real is None:
                    self.res["avisos"].append(f"{nombre}: {k} apunta a un registro de la web que aún no está en el escritorio.")
                    real = 0
                v = real
            v = self._convertir(v, meta[1], meta[2])
            if v is None:
                continue          # sin dato en la web: la columna conserva su valor (o su valor por defecto al crear)
            out[meta[0]] = v
        return out

    async def existe(self, tabla: str, llave: str, valor) -> bool:
        return bool((await self.conn.execute(text(f"SELECT COUNT(*) FROM {tabla} WHERE {llave} = :v"), {"v": valor})).scalar())

    async def guardar(self, tabla: str, llave: str, id_real: int, datos: dict) -> bool:
        """Actualiza o crea. Devuelve True si fue nuevo."""
        datos = {k: v for k, v in datos.items() if k.lower() != llave.lower()}
        if await self.existe(tabla, llave, id_real):
            if datos:
                await self.conn.execute(text(f"UPDATE {tabla} SET {', '.join(f'`{c}` = :p{i}' for i, c in enumerate(datos))} "
                                             f"WHERE {llave} = :id"),
                                        {**{f"p{i}": v for i, v in enumerate(datos.values())}, "id": id_real})
            return False
        cols = [llave] + list(datos)
        valores = [id_real] + list(datos.values())
        cols_tabla = await self.columnas(tabla)
        if "enviada_mysql" in cols_tabla and "enviada_mysql" not in {c.lower() for c in cols}:
            cols.append(cols_tabla["enviada_mysql"][0])
            valores.append(0)
        await self.conn.execute(text(f"INSERT INTO {tabla} ({', '.join(f'`{c}`' for c in cols)}) "
                                     f"VALUES ({', '.join(f':p{i}' for i in range(len(cols)))})"),
                                {f"p{i}": v for i, v in enumerate(valores)})
        return True

    async def reemplazar_hijos(self, tabla: str, llave: str, id_padre: int, filas: list, refs: dict, nombre: str) -> None:
        if not filas or not await self.columnas(tabla):
            return
        await self.conn.execute(text(f"DELETE FROM {tabla} WHERE {llave} = :p"), {"p": id_padre})
        for f in filas:
            datos = await self.preparar(tabla, {**f, llave: id_padre}, refs, nombre)
            datos[(await self.columnas(tabla))[llave.lower()][0]] = id_padre
            await self.conn.execute(text(f"INSERT INTO {tabla} ({', '.join(f'`{c}`' for c in datos)}) "
                                         f"VALUES ({', '.join(f':p{i}' for i in range(len(datos)))})"),
                                    {f"p{i}": v for i, v in enumerate(datos.values())})

    async def numero_real(self, entidad: str, tabla: str, llave: str, id_web: int, max_web: int) -> int:
        """Provisional → real: el del mapa (reintento) o el siguiente número; queda en el mapa antes de escribir."""
        ya = self.mapa.get(entidad, {}).get(id_web)
        if ya:
            return ya
        maximo = (await self.conn.execute(text(f"SELECT COALESCE(MAX({llave}), 0) FROM {tabla} WHERE {llave} < :p"),
                                          {"p": ID_PROVISIONAL})).scalar() or 0
        usados = [v for v in self.mapa.get(entidad, {}).values()]
        real = max([int(maximo), int(max_web)] + usados) + 1
        async with SesionTemp() as tmp:
            await tmp.execute(text("INSERT INTO ag_maestros_mapa2 (entidad, id_web, id_real, creado) VALUES (:e, :w, :r, NOW())"),
                              {"e": entidad, "w": id_web, "r": real})
            await tmp.commit()
        self.mapa.setdefault(entidad, {})[id_web] = real
        return real


async def resumen() -> dict:
    """Lo que la web tiene pendiente de bajar (para mostrarlo antes de aplicar)."""
    r = await nube.pedir("GET", "/api/agente/maestros/pendientes") or {}
    platos = r.get("platos") or []
    catalogos = []
    for ent in ORDEN:
        filas = (r.get("entidades") or {}).get(ent) or []
        if filas:
            catalogos.append({"entidad": ent, "nombre": NOMBRES[ent], "nuevos": sum(1 for f in filas if f.get("provisional")),
                              "modificados": sum(1 for f in filas if not f.get("provisional"))})
    total = len(platos) + sum(c["nuevos"] + c["modificados"] for c in catalogos) + len(r.get("listas") or []) \
        + (1 if r.get("sede") else 0)
    return {
        "catalogos": catalogos,
        "nuevos": [{"id": p["id"], "nombre": (p["datos"].get("Nombre") or "").strip()} for p in platos if p.get("provisional")],
        "modificados": [{"id": p["id"], "nombre": (p["datos"].get("Nombre") or "").strip(),
                         "inactivo": bool(p["datos"].get("Activo"))} for p in platos if not p.get("provisional")],
        "listas": len(r.get("listas") or []),
        "sede": bool(r.get("sede")),
        "total": total,
    }


async def sincronizar(quien: str = "panel") -> dict:
    """Baja todo lo pendiente y lo aplica en el escritorio. Devuelve el resumen del resultado."""
    resultado = {"fecha": datetime.now().isoformat(timespec="seconds"), "quien": quien[:60], "nuevos": 0,
                 "actualizados": 0, "catalogos": {}, "listas": 0, "sede": False, "avisos": [], "error": None, "fotos": None}
    r = await nube.pedir("GET", "/api/agente/maestros/pendientes", timeout=90) or {}
    max_ids = r.get("max_ids") or {"plato": int(r.get("max_id_web") or 0)}
    confirmar = {"platos": [], "entidades": {}, "listas": [], "listas_cabecera": [], "sede_actualizado": None}

    async with motor_empresa.connect() as conn:
        lock = (await conn.execute(text("SELECT GET_LOCK('ag_maestros', 10)"))).scalar()
        await conn.commit()
        if lock != 1:
            raise RuntimeError("Ya hay una sincronización de catálogo en curso.")
        try:
            esc = Escritorio(conn, resultado)
            await esc.cargar_mapa()

            # 1. catálogos con número propio
            for ent in ORDEN:
                tabla, llave, campo_nombre = ESCRITORIO[ent]
                filas = (r.get("entidades") or {}).get(ent) or []
                if not filas:
                    continue
                if not await esc.columnas(tabla):
                    resultado["avisos"].append(f"La sede no tiene la tabla {tabla}: no se bajaron los {NOMBRES[ent]}.")
                    continue
                cuenta = {"nuevos": 0, "actualizados": 0}
                for f in filas:
                    id_web = int(f["id"])
                    nombre = str((f.get("datos") or {}).get(campo_nombre) or f"#{id_web}").strip()
                    id_real = await esc.numero_real(ent, tabla, llave, id_web, max_ids.get(ent, 0)) if f.get("provisional") else id_web
                    datos = await esc.preparar(tabla, f.get("datos") or {}, REFS.get(ent, {}), nombre)
                    if ent == "insumo":
                        # Id_Insumo y Posicion del insumo nuevo eran el mismo número provisional
                        for c in ("Id_Insumo", "Posicion"):
                            if _provisional((f.get("datos") or {}).get(c)):
                                datos[c] = id_real
                    nuevo = await esc.guardar(tabla, llave, id_real, datos)
                    cuenta["nuevos" if nuevo else "actualizados"] += 1
                    for h, (tabla_h, llave_h, refs_h) in (HIJOS_INSUMO.items() if ent == "insumo" else []):
                        await esc.reemplazar_hijos(tabla_h, llave_h, id_real, (f.get("hijos") or {}).get(h) or [], refs_h, nombre)
                    await conn.commit()
                    confirmar["entidades"].setdefault(ent, []).append(
                        {"id_web": id_web, "id_real": id_real, "actualizado": f.get("actualizado")})
                resultado["catalogos"][NOMBRES[ent]] = cuenta

            # 2. platos (con impresoras, receta, armado y presentaciones)
            impresoras_locales = {int(i) for (i,) in (await conn.execute(text("SELECT Id_Impresora FROM impresoras"))).all()}
            for p in r.get("platos") or []:
                id_web = int(p["id"])
                nombre = str((p.get("datos") or {}).get("Nombre") or f"#{id_web}").strip()
                id_real = await esc.numero_real("plato", "platos", "Id_Plato", id_web, max_ids.get("plato", 0)) \
                    if p.get("provisional") else id_web
                datos = await esc.preparar("platos", p.get("datos") or {}, REFS["plato"], f"'{nombre}'")
                if p.get("provisional"):
                    datos["Activo"] = 0                   # se activa al tener Id_Plato real
                nuevo = await esc.guardar("platos", "Id_Plato", id_real, datos)
                resultado["nuevos" if nuevo else "actualizados"] += 1
                imps = [i for i in (p.get("impresoras") or []) if int(i.get("id") or 0) in impresoras_locales]
                omitidas = len(p.get("impresoras") or []) - len(imps)
                if omitidas:
                    resultado["avisos"].append(f"'{nombre}': {omitidas} impresora(s) de la web no existen en el escritorio.")
                if imps:
                    await conn.execute(text("DELETE FROM plato_impresoras WHERE Id_Plato = :i"), {"i": id_real})
                    for i in imps:
                        await conn.execute(text("""
                            INSERT INTO plato_impresoras (Id_Plato, Id_Impresora, Cant_Impresiones, Enviada_MySql)
                            VALUES (:p, :i, :c, 0)
                        """), {"p": id_real, "i": int(i["id"]), "c": max(1, min(int(i.get("copias") or 1), 5))})
                elif nuevo:
                    resultado["avisos"].append(f"'{nombre}': sin impresora asignada (no imprimirá comanda).")
                for h, (tabla_h, llave_h, refs_h) in HIJOS_PLATO.items():
                    await esc.reemplazar_hijos(tabla_h, llave_h, id_real, (p.get("hijos") or {}).get(h) or [], refs_h, f"'{nombre}'")
                await conn.commit()
                confirmar["platos"].append({"id_web": id_web, "id_real": id_real, "actualizado": p.get("actualizado")})

            # 3. listas de precios
            if (r.get("listas") or r.get("listas_cabecera")) and await esc.columnas("lista_precios_cliente"):
                for x in r.get("listas_cabecera") or []:
                    if await esc.columnas("lista_precios_cliente_cabecera"):
                        d = await esc.preparar("lista_precios_cliente_cabecera", x["datos"], {"Id_Cliente": "cliente"}, "Lista de precios")
                        await esc.guardar("lista_precios_cliente_cabecera", "id_lista", int(x["datos"]["id_lista"]), d)
                    confirmar["listas_cabecera"].append({"id": x["id"], "actualizado": x.get("actualizado")})
                for x in r.get("listas") or []:
                    d = await esc.preparar("lista_precios_cliente", x["datos"], REFS_LISTA, "Lista de precios")
                    if not d.get("Id_Producto") or ("Id_Cliente" in d and not d["Id_Cliente"]):
                        continue                          # producto o cliente aún sin número real: queda pendiente
                    cols = list(d)
                    await conn.execute(text(f"""
                        INSERT INTO lista_precios_cliente ({', '.join(f'`{c}`' for c in cols)})
                        VALUES ({', '.join(f':p{i}' for i in range(len(cols)))})
                        ON DUPLICATE KEY UPDATE {', '.join(f'`{c}` = VALUES(`{c}`)' for c in cols if c in ('Precio_Producto', 'Fecha', 'Activa'))}
                    """), {f"p{i}": v for i, v in enumerate(d.values())})
                    resultado["listas"] += 1
                    confirmar["listas"].append({"id": x["id"], "actualizado": x.get("actualizado")})
                await conn.commit()

            # 4. datos de la sede
            sede = r.get("sede")
            if sede and await esc.columnas("configuracion_sede"):
                datos = await esc.preparar("configuracion_sede", {k: v for k, v in sede.items() if k != "actualizado"}, {}, "Sede")
                if (await conn.execute(text("SELECT COUNT(*) FROM configuracion_sede"))).scalar():
                    await conn.execute(text(f"UPDATE configuracion_sede SET {', '.join(f'`{c}` = :p{i}' for i, c in enumerate(datos))}"),
                                       {f"p{i}": v for i, v in enumerate(datos.values())})
                else:
                    await conn.execute(text(f"INSERT INTO configuracion_sede ({', '.join(f'`{c}`' for c in datos)}) "
                                            f"VALUES ({', '.join(f':p{i}' for i in range(len(datos)))})"),
                                       {f"p{i}": v for i, v in enumerate(datos.values())})
                await conn.commit()
                resultado["sede"] = True
                confirmar["sede_actualizado"] = sede.get("actualizado")
        finally:
            await conn.execute(text("SELECT RELEASE_LOCK('ag_maestros')"))
            await conn.commit()

    if confirmar["platos"] or confirmar["entidades"] or confirmar["listas"] or confirmar["listas_cabecera"] or resultado["sede"]:
        conf = await nube.pedir("POST", "/api/agente/maestros/aplicados", confirmar, timeout=90) or {}
        for e in conf.get("errores") or []:
            resultado["avisos"].append(f"{NOMBRES.get(e.get('entidad'), e.get('entidad'))} {e.get('id_web')}: {e.get('error')}")
        if conf.get("renumerados"):
            async with SesionTemp() as tmp:
                for x in conf["renumerados"]:
                    await tmp.execute(text("UPDATE ag_maestros_mapa2 SET confirmado = NOW() WHERE entidad = :e AND id_web = :w"),
                                      {"e": x.get("entidad") or "plato", "w": x["id_web"]})
                await tmp.commit()

    # Fotos de la web (mismo botón)
    try:
        from . import fotos_web
        resultado["fotos"] = await fotos_web.sincronizar()
        nube.estado["fotos"] = resultado["fotos"]
    except Exception as e:                       # las fotos no deshacen lo anterior
        resultado["avisos"].append(f"Fotos: {e}")
    estado["ultimo"] = resultado
    catalogos = sum(c["nuevos"] + c["actualizados"] for c in resultado["catalogos"].values())
    async with SesionTemp() as tmp:
        await tmp.execute(text("""
            INSERT INTO ag_config (clave, valor) VALUES ('maestros_resultado', :v) ON DUPLICATE KEY UPDATE valor = :v
        """), {"v": (f"{resultado['fecha']} · platos: {resultado['nuevos']} nuevos, {resultado['actualizados']} actualizados"
                     + (f" · catálogos: {catalogos}" if catalogos else "") + (f" · listas: {resultado['listas']}" if resultado["listas"] else "")
                     + (" · sede" if resultado["sede"] else "") + (f" · {len(resultado['avisos'])} avisos" if resultado["avisos"] else ""))[:255]})
        await tmp.commit()
    return resultado


async def atender_solicitud_escritorio() -> None:
    """El form del escritorio deja ag_config.maestros_solicitud = 'SOLICITADO|usuario'; el ciclo lo atiende."""
    async with SesionTemp() as tmp:
        valor = (await tmp.execute(text("SELECT valor FROM ag_config WHERE clave = 'maestros_solicitud'"))).scalar()
    if not valor or not str(valor).startswith("SOLICITADO"):
        return
    quien = (str(valor).split("|", 1) + ["escritorio"])[1] or "escritorio"
    async with SesionTemp() as tmp:
        await tmp.execute(text("UPDATE ag_config SET valor = 'EN CURSO' WHERE clave = 'maestros_solicitud'"))
        await tmp.commit()
    final = "LISTO"
    try:
        await sincronizar(f"escritorio: {quien}")
    except Exception as e:
        log.exception("Sincronización de catálogo pedida desde el escritorio")
        final = f"ERROR: {e}"[:255]
    async with SesionTemp() as tmp:
        await tmp.execute(text("UPDATE ag_config SET valor = :v WHERE clave = 'maestros_solicitud'"), {"v": final})
        await tmp.commit()
