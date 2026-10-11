"""
S3 — Tablas maestras de la web hacia el escritorio. NO es automático: lo ejecuta el admin desde el
panel de la mini-app ("Catálogo de la web") o desde el escritorio (form VB6: deja la solicitud en
ag_config y el ciclo del agente la atiende). La web manda (decisión del usuario 2026-10-10).

  Qué baja (lo que la web tiene pendiente, synced = 0):
    · platos → platos (BD de la empresa): nuevos, editados o desactivados (Activo = 1 inactivo, VB6),
      con sus impresoras → plato_impresoras (solo impresoras que existan en el escritorio).
    · datos de la sede → configuracion_sede (la única fila; Id_Sede y rutas de fotos no se tocan).
    · fotos de los platos (fotos_web.sincronizar).

  Plato nuevo de la web (id provisional): se crea con el siguiente Id_Plato (mayor entre el escritorio y la
  web) y queda ACTIVO; la web lo renumera y lo activa. ag_maestros_mapa guarda id provisional → Id_Plato
  real ANTES de avisar a la web: si el agente se cae, el reintento no duplica el plato.
  platos es MyISAM (sin rollback): cada plato se escribe completo antes del siguiente.
"""
import logging
from datetime import datetime

from sqlalchemy import text

from .. import nube
from ..db import SesionEmpresa, SesionTemp, motor_empresa

log = logging.getLogger("agente_local")

COLUMNAS_TEXTO = {"Nombre": 250, "Codigo_Producto": 250, "Comentario": 255, "Impresion_Extra": 255}
COLUMNAS_LARGAS = ("Procedimiento", "Descripcion_Plato")
COLUMNAS_SEDE = {"Nombre_Almacen": 250, "Nombre_Autorizado": 250, "Nit_Autorizado": 250, "Razon_Social": 255,
                 "Direccion_Sede": 255, "Mail_Uno": 100, "Mail_Dos": 100, "Nombre_Logo_Empresa": 200}
COLUMNAS_PLATO = ("Nombre", "Codigo_Producto", "Valor", "Tiempo", "Activo", "Cod_Categoria", "Procedimiento",
                  "Descripcion_Plato", "Comentario", "Impresion_Extra", "Preparacion_Previa", "Ofrecer",
                  "Prioridad_Ofrecer", "Impuesto", "Precio_x_Mayor", "Costo_Producto", "Stock_Minimo",
                  "Pedir_Valor_Venta_Producto", "Pedir_Descripcion_Producto")

estado = {"ultimo": None}


def _limpio(valor, largo: int | None):
    if valor is None:
        return None
    v = str(valor).replace("\x00", "")
    return v[:largo] if largo else v[:65000]


def _numero(valor, entero: bool = False, minimo: float = 0, maximo: float = 1e12):
    try:
        n = float(valor or 0)
    except (TypeError, ValueError):
        return 0
    n = min(max(n, minimo), maximo)
    return int(round(n)) if entero else n


def _datos_plato(d: dict) -> dict:
    """Valores de la web listos para platos (tipos y largos del escritorio)."""
    out = {}
    for col in COLUMNAS_PLATO:
        v = d.get(col)
        if col in COLUMNAS_TEXTO:
            out[col] = _limpio(v, COLUMNAS_TEXTO[col]) or ""
        elif col in COLUMNAS_LARGAS:
            out[col] = _limpio(v, None) or ""
        elif col in ("Precio_x_Mayor", "Costo_Producto", "Stock_Minimo"):
            out[col] = _numero(v)
        elif col in ("Activo", "Preparacion_Previa", "Ofrecer", "Pedir_Valor_Venta_Producto", "Pedir_Descripcion_Producto"):
            out[col] = 1 if _numero(v, True) else 0
        else:
            out[col] = _numero(v, True, 0, 2_000_000_000)
    return out


async def resumen() -> dict:
    """Lo que la web tiene pendiente de bajar (para mostrarlo antes de aplicar)."""
    r = await nube.pedir("GET", "/api/agente/maestros/pendientes") or {}
    platos = r.get("platos") or []
    return {
        "nuevos": [{"id": p["id"], "nombre": (p["datos"].get("Nombre") or "").strip()} for p in platos if p.get("provisional")],
        "modificados": [{"id": p["id"], "nombre": (p["datos"].get("Nombre") or "").strip(),
                         "inactivo": bool(p["datos"].get("Activo"))} for p in platos if not p.get("provisional")],
        "sede": bool(r.get("sede")),
        "total": len(platos) + (1 if r.get("sede") else 0),
    }


async def sincronizar(quien: str = "panel") -> dict:
    """Baja todo lo pendiente y lo aplica en el escritorio. Devuelve el resumen del resultado."""
    resultado = {"fecha": datetime.now().isoformat(timespec="seconds"), "quien": quien[:60], "nuevos": 0,
                 "actualizados": 0, "sede": False, "avisos": [], "error": None, "fotos": None}
    r = await nube.pedir("GET", "/api/agente/maestros/pendientes", timeout=60) or {}
    platos = r.get("platos") or []
    max_web = int(r.get("max_id_web") or 0)
    aplicados = []
    async with motor_empresa.connect() as conn:
        lock = (await conn.execute(text("SELECT GET_LOCK('ag_maestros', 10)"))).scalar()
        await conn.commit()
        if lock != 1:
            raise RuntimeError("Ya hay una sincronización de catálogo en curso.")
        try:
            impresoras_locales = {int(i) for (i,) in (await conn.execute(text("SELECT Id_Impresora FROM impresoras"))).all()}
            categorias_locales = {int(c) for (c,) in (await conn.execute(text("SELECT Cod_Categoria FROM categoria_platos"))).all()}
            for p in platos:
                id_web = int(p["id"])
                datos = _datos_plato(p.get("datos") or {})
                id_real = id_web
                if p.get("provisional"):
                    async with SesionTemp() as tmp:
                        ya = (await tmp.execute(text("SELECT id_real FROM ag_maestros_mapa WHERE id_web = :w"), {"w": id_web})).scalar()
                    if ya:
                        id_real = int(ya)
                    else:
                        maximo = (await conn.execute(text("SELECT COALESCE(MAX(Id_Plato), 0) FROM platos"))).scalar() or 0
                        id_real = max(int(maximo), max_web) + 1
                        async with SesionTemp() as tmp:          # el mapa primero: un reintento no duplica
                            await tmp.execute(text("INSERT INTO ag_maestros_mapa (id_web, id_real, creado) VALUES (:w, :r, NOW())"),
                                              {"w": id_web, "r": id_real})
                            await tmp.commit()
                    datos["Activo"] = 0                       # se activa al tener Id_Plato real
                existe = (await conn.execute(text("SELECT COUNT(*) FROM platos WHERE Id_Plato = :i"), {"i": id_real})).scalar()
                if datos["Cod_Categoria"] and datos["Cod_Categoria"] not in categorias_locales:
                    resultado["avisos"].append(f"'{datos['Nombre'].strip()}': la categoría {datos['Cod_Categoria']} no existe en el escritorio.")
                if existe:
                    await conn.execute(text(f"UPDATE platos SET {', '.join(f'{c} = :{c}' for c in COLUMNAS_PLATO)} WHERE Id_Plato = :id"),
                                       {**datos, "id": id_real})
                    resultado["actualizados"] += 1
                else:
                    await conn.execute(text(f"INSERT INTO platos (Id_Plato, {', '.join(COLUMNAS_PLATO)}, Enviada_MySql) "
                                            f"VALUES (:id, {', '.join(':' + c for c in COLUMNAS_PLATO)}, 0)"), {**datos, "id": id_real})
                    resultado["nuevos"] += 1
                # Impresoras del plato (las de la web que existan en el escritorio)
                imps = [i for i in (p.get("impresoras") or []) if int(i.get("id") or 0) in impresoras_locales]
                omitidas = len(p.get("impresoras") or []) - len(imps)
                if omitidas:
                    resultado["avisos"].append(f"'{datos['Nombre'].strip()}': {omitidas} impresora(s) de la web no existen en el escritorio.")
                # Sin impresoras válidas en la web no se tocan las del escritorio (un plato sin impresora no
                # imprime: lo más probable es que la web nunca las tuvo, no que se quieran quitar)
                if imps:
                    await conn.execute(text("DELETE FROM plato_impresoras WHERE Id_Plato = :i"), {"i": id_real})
                elif not existe:
                    resultado["avisos"].append(f"'{datos['Nombre'].strip()}': sin impresora asignada (no imprimirá comanda).")
                for i in imps:
                    await conn.execute(text("""
                        INSERT INTO plato_impresoras (Id_Plato, Id_Impresora, Cant_Impresiones, Enviada_MySql)
                        VALUES (:p, :i, :c, 0)
                    """), {"p": id_real, "i": int(i["id"]), "c": max(1, min(int(i.get("copias") or 1), 5))})
                await conn.commit()
                aplicados.append({"id_web": id_web, "id_real": id_real, "actualizado": p.get("actualizado")})

            sede = r.get("sede")
            if sede:
                valores = {c: _limpio(sede.get(c), n) or "" for c, n in COLUMNAS_SEDE.items()}
                hay = (await conn.execute(text("SELECT COUNT(*) FROM configuracion_sede"))).scalar()
                if hay:
                    await conn.execute(text(f"UPDATE configuracion_sede SET {', '.join(f'{c} = :{c}' for c in COLUMNAS_SEDE)}"), valores)
                else:
                    await conn.execute(text(f"INSERT INTO configuracion_sede ({', '.join(COLUMNAS_SEDE)}) "
                                            f"VALUES ({', '.join(':' + c for c in COLUMNAS_SEDE)})"), valores)
                await conn.commit()
                resultado["sede"] = True
        finally:
            await conn.execute(text("SELECT RELEASE_LOCK('ag_maestros')"))
            await conn.commit()

    if aplicados or resultado["sede"]:
        conf = await nube.pedir("POST", "/api/agente/maestros/aplicados", {
            "platos": aplicados, "sede_actualizado": (r.get("sede") or {}).get("actualizado")}, timeout=60) or {}
        for e in conf.get("errores") or []:
            resultado["avisos"].append(f"Plato {e.get('id_web')}: {e.get('error')}")
        if conf.get("renumerados"):
            async with SesionTemp() as tmp:
                for x in conf["renumerados"]:
                    await tmp.execute(text("UPDATE ag_maestros_mapa SET confirmado = NOW() WHERE id_web = :w"), {"w": x["id_web"]})
                await tmp.commit()

    # Fotos de la web (mismo botón)
    try:
        from . import fotos_web
        resultado["fotos"] = await fotos_web.sincronizar()
        nube.estado["fotos"] = resultado["fotos"]
    except Exception as e:                       # las fotos no deshacen lo anterior
        resultado["avisos"].append(f"Fotos: {e}")
    estado["ultimo"] = resultado
    async with SesionTemp() as tmp:
        await tmp.execute(text("""
            INSERT INTO ag_config (clave, valor) VALUES ('maestros_resultado', :v) ON DUPLICATE KEY UPDATE valor = :v
        """), {"v": (f"{resultado['fecha']} · {resultado['nuevos']} nuevos · {resultado['actualizados']} actualizados"
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
