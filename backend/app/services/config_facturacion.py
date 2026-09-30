"""
Configuración de facturación por empresa — espejo de `configuracion_facturacion` del escritorio.

Es la fuente de la propina (liquidar_propina, porcentaje_propina, textos), de la impresora
general de recibos (impresora_facturas) y de los textos de pie del recibo. Al guardarla se
replican has_tip / tip_percentage en company_configs, que otras pantallas aún leen.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Campos editables: nombre → tipo ("bool", "int", "float", "str:<max>", "text")
CAMPOS = {
    "id_sede": "int",
    "impuesto_iva": "float",
    "impuesto_impoconsumo": "float",
    "impuesto_rete_fuente": "float",
    "liquidar_propina": "bool",
    "resolucion_propina": "text",
    "paga_impuesto": "bool",
    "precios_incluyen_impuesto": "bool",
    "imprimir_logo_factura": "bool",
    "nombre_logo_factura": "str:200",
    "tipo_moneda": "int",
    "texto_numeracion": "str:100",
    "nombre_cliente_facturacion_varia": "str:100",
    "codigo_cliente_facturacion_varia": "str:100",
    "id_cliente_facturacion_varia": "float",
    "usa_lector_barras": "bool",
    "imprimir_encabezado_factura": "bool",
    "impresora_facturas": "int",
    "mensaje_factura": "str:255",
    "longitud_factura_sistema": "int",
    "longitud_factura_manual": "int",
    "cantidad_impresiones_factura": "int",
    "porcentaje_propina": "float",
    "activar_precio_x_mayor": "bool",
    "usar_precuenta": "bool",
    "imprimir_resolucion_propina": "bool",
    "imprimir_datos_legales": "bool",
    "imprimir_datos_cliente": "bool",
    "imprimir_recibo_domiciliario": "bool",
    "preguntar_valor_propina": "bool",
    "usar_comanda_corta": "bool",
}

_COLS = ", ".join(CAMPOS)


def _normalizar(row: dict) -> dict:
    out = {}
    for k, tipo in CAMPOS.items():
        v = row.get(k)
        if tipo == "bool":
            out[k] = bool(v)
        elif tipo == "int":
            out[k] = int(v) if v is not None else None
        elif tipo == "float":
            out[k] = float(v) if v is not None else 0.0
        else:
            out[k] = v or ""
    return out


async def get_config(db: AsyncSession, cid: int) -> dict:
    """Configuración de la empresa; si no existe se crea con los valores por defecto
    (tomando la propina que hubiera en company_configs)."""
    row = (await db.execute(text(
        f"SELECT {_COLS} FROM configuracion_facturacion WHERE company_id = :cid"
    ), {"cid": cid})).mappings().first()
    if not row:
        await db.execute(text("""
            INSERT IGNORE INTO configuracion_facturacion (company_id, liquidar_propina, porcentaje_propina)
            SELECT :cid, COALESCE(MAX(has_tip), 0), COALESCE(MAX(tip_percentage), 0)
            FROM company_configs WHERE company_id = :cid
        """), {"cid": cid})
        row = (await db.execute(text(
            f"SELECT {_COLS} FROM configuracion_facturacion WHERE company_id = :cid"
        ), {"cid": cid})).mappings().first()
    return _normalizar(dict(row))


async def sync_company_configs(db: AsyncSession, cid: int, liquidar_propina: bool, porcentaje: float) -> None:
    """Replica la propina en company_configs (lo leen otras pantallas)."""
    existe = (await db.execute(text(
        "SELECT 1 FROM company_configs WHERE company_id = :cid"
    ), {"cid": cid})).scalar()
    if existe:
        await db.execute(text(
            "UPDATE company_configs SET has_tip = :t, tip_percentage = :p WHERE company_id = :cid"
        ), {"t": int(bool(liquidar_propina)), "p": float(porcentaje or 0), "cid": cid})
    else:
        await db.execute(text("""
            INSERT INTO company_configs (company_id, has_tip, tip_percentage,
                                         has_pos_electronico, has_parking, has_tv_cocina)
            VALUES (:cid, :t, :p, 0, 0, 0)
        """), {"t": int(bool(liquidar_propina)), "p": float(porcentaje or 0), "cid": cid})


async def guardar(db: AsyncSession, cid: int, datos: dict, synced: int = 0) -> None:
    """Upsert de la configuración (solo los campos de CAMPOS presentes en `datos`)."""
    await get_config(db, cid)   # garantiza la fila
    campos = [k for k in CAMPOS if k in datos]
    if campos:
        sets = ", ".join(f"{k} = :{k}" for k in campos)
        params = {k: datos[k] for k in campos}
        params.update({"cid": cid, "synced": synced})
        await db.execute(text(
            f"UPDATE configuracion_facturacion SET {sets}, synced = :synced WHERE company_id = :cid"
        ), params)
    cfg = await get_config(db, cid)
    await sync_company_configs(db, cid, cfg["liquidar_propina"], cfg["porcentaje_propina"])
