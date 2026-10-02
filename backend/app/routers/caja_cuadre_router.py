"""
Cuadre de Caja (Transaccional → Cuadre Caja).

  GET  /api/caja/cuadre/opciones?fecha=      turnos y usuarios de la fecha, turno abierto propio,
                                             si la empresa tiene POS electrónico
  GET  /api/caja/cuadre?fecha&modo&...       cuadre (modo: todos | usuario | caja)
  GET  /api/caja/cuadre/articulos?...        artículos vendidos agrupados por categoría
  POST /api/caja/cuadre/cerrar               cierra el turno (dueño o Admin) guardando el cuadre
  POST /api/caja/cuadre/vista-previa         documentos para la vista previa de impresión
  POST /api/caja/cuadre/imprimir             tirilla ESC/POS: un corte por documento

La empresa sale SIEMPRE de la sesión (tenant); todo se filtra por ella y el cálculo lo hace el
servidor. Del navegador solo se aceptan filtros y las dos bases (únicos valores editables).
"""
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.models.user_model import User
from app.routers.pos_shift_router import (_BOG, _es_admin, _es_escritorio, _hoy, _id_caja_header,
                                          _turno_abierto, cerrar_y_liberar)
from app.services import cuadre_caja as svc

router = APIRouter(prefix="/api/caja/cuadre", tags=["Caja Cuadre"], dependencies=[Depends(tenant_guard)])

Fecha = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}$")]
Modo = Literal["todos", "usuario", "caja"]
Origen = Literal["recibos", "facturas", "ambos"]
Base = Annotated[float, Field(ge=0, le=1e12)]


def _fecha(f: str) -> str:
    try:
        datetime.strptime(f, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="Fecha no válida")
    return f


async def _pos_electronico(db: AsyncSession, cid: int) -> bool:
    v = (await db.execute(text(
        "SELECT COALESCE(has_pos_electronico, 0) FROM company_configs WHERE company_id = :cid"
    ), {"cid": cid})).scalar()
    return bool(v)


async def _origen(db: AsyncSession, cid: int, origen: Optional[str]) -> str:
    # Sin POS electrónico solo hay recibos
    if not await _pos_electronico(db, cid):
        return "recibos"
    return origen or "facturas"


class Filtros(BaseModel):
    fecha: Fecha
    modo: Modo = "todos"
    user_id: Optional[Annotated[int, Field(ge=1)]] = None
    closing_id: Optional[Annotated[int, Field(ge=1)]] = None
    origen: Optional[Origen] = None
    base_inicial: Optional[Base] = None
    base_final: Optional[Base] = None
    company_id: Optional[int] = None          # lo valida tenant_guard; no se usa para consultar


def _validar_modo(f) -> None:
    if f.modo == "usuario" and not f.user_id:
        raise HTTPException(status_code=422, detail="Seleccione el usuario")
    if f.modo == "caja" and not f.closing_id:
        raise HTTPException(status_code=422, detail="Seleccione el Id_Caja")


async def _cuadre(db: AsyncSession, cid: int, f) -> dict:
    _fecha(f.fecha)
    _validar_modo(f)
    return await svc.calcular(db, cid, f.fecha, f.modo, await _origen(db, cid, f.origen),
                              user_id=f.user_id, closing_id=f.closing_id,
                              base_inicial=f.base_inicial, base_final=f.base_final)


@router.get("/opciones")
async def opciones(
    request: Request,
    fecha: Optional[Fecha] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    f = _fecha(fecha or _hoy())
    ts = await svc.turnos(db, cid, f, "todos")
    usuarios = {}
    for t in ts:
        if t["user_id"]:
            usuarios.setdefault(int(t["user_id"]), t["usuario"] or f"Usuario {t['user_id']}")
    pe = await _pos_electronico(db, cid)
    return {
        "fecha": f, "hoy": _hoy(),
        "pos_electronico": pe, "origen_default": "facturas" if pe else "recibos",
        "turnos": [{"id": t["id"], "caja": t["caja_nombre"], "usuario": t["usuario"], "user_id": t["user_id"],
                    "cerrado": bool(int(t["closed"] or 0)), "apertura": t["opening_datetime"],
                    "cierre": t["closing_datetime"], "origen": t["origen"]} for t in ts],
        "usuarios": [{"id": k, "nombre": v} for k, v in sorted(usuarios.items(), key=lambda x: x[1])],
        "turno_actual": await _turno_abierto(db, cid, current_user.id, _id_caja_header(request)),
        "escritorio": await _es_escritorio(db, cid),
        "es_admin": await _es_admin(db, current_user),
        "user_id": current_user.id,
    }


@router.get("")
async def cuadre(
    f: Filtros = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _cuadre(db, current_user.company_id, f)


@router.get("/articulos")
async def articulos(
    f: Filtros = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    c = await _cuadre(db, cid, f)
    cats = await svc.ventas_por_categoria(db, cid, c["documentos"], detalle=True)
    return {"categorias": cats, "total": sum(x["valor"] for x in cats)}


class CerrarIn(BaseModel):
    closing_id: Annotated[int, Field(ge=1)]
    base_inicial: Base
    base_final: Base
    company_id: Optional[int] = None


@router.post("/cerrar")
async def cerrar(
    body: CerrarIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    turno = (await db.execute(text("""
        SELECT id_registro AS id, register_number, date, closed, synced, CAST(customer_sales AS SIGNED) user_id
        FROM pos_cash_register_closings WHERE id_registro = :id AND company_id = :cid
    """), {"id": body.closing_id, "cid": cid})).mappings().first()
    if not turno:
        raise HTTPException(status_code=404, detail="Id_Caja no encontrado")
    if int(turno["synced"] or 0):
        raise HTTPException(status_code=409, detail="Este Id_Caja se cierra desde el programa de escritorio")
    if int(turno["closed"] or 0):
        raise HTTPException(status_code=409, detail="Este Id_Caja ya está cerrado")
    if int(turno["user_id"] or 0) != current_user.id and not await _es_admin(db, current_user):
        raise HTTPException(status_code=403, detail="Solo el usuario que abrió la caja o un administrador pueden cerrarla")

    # Foto del cuadre del Id_Caja con TODO el dinero (recibos y facturas)
    c = await svc.calcular(db, cid, str(turno["date"]), "caja", "ambos", closing_id=int(turno["id"]),
                           base_inicial=body.base_inicial, base_final=body.base_final)
    total = lambda k: sum(m["valor"] for m in c["movimientos"][k])
    await cerrar_y_liberar(db, cid, int(turno["id"]), int(turno["register_number"] or 0), {
        "base_amount": c["bases"]["inicial"], "final_base": c["bases"]["final"],
        "total_sales": c["venta"]["total"], "cash_sales": c["venta"]["efectivo"], "voucher_sales": c["venta"]["otros"],
        "tips": c["propinas"]["total"], "expenses": total("gastos"), "purchases": total("compras"),
        "vouchers": total("vales"), "total_invoices": c["conteos"]["cuentas"],
        "voucher_invoices": c["conteos"]["otros"], "voided_invoices": c["conteos"]["anuladas"],
        "invoice_start": str(c["conteos"]["inicial"])[:50], "invoice_end": str(c["conteos"]["final"])[:50],
        "delivery_income": c["domicilios"]["total"], "delivery_expense": c["domicilios"]["total"],
    })
    await db.commit()
    return {"ok": True, "dinero_entregar": c["dinero_entregar"]}


# ═══════════════════════════════════════════════════════════════════════════
# IMPRESIÓN — el cuadre lleva solo totales; los checks agregan el detalle,
# cada uno como un documento aparte (en tirilla: un corte de papel por documento)
# ═══════════════════════════════════════════════════════════════════════════
class Incluir(BaseModel):
    movimientos: bool = False      # detalle de gastos, compras, vales, otros ingresos/egresos
    articulos: bool = False        # lista de artículos vendidos
    categorias: bool = False       # venta por categoría


class ImpresionIn(Filtros):
    incluir: Incluir = Incluir()


class ImprimirIn(ImpresionIn):
    printer_id: Annotated[int, Field(ge=1)]
    raw: bool = False
    receipt_number: Optional[str] = None      # lo envía el componente de impresión; no se usa


def _fmt_fecha(f: str) -> str:
    return datetime.strptime(f, "%Y-%m-%d").strftime("%d/%m/%Y")


async def _documentos(db: AsyncSession, cid: int, f: ImpresionIn) -> dict:
    c = await _cuadre(db, cid, f)
    ts = c["turnos"]
    if f.modo == "caja" and ts:
        alcance = f"{ts[0]['caja_nombre']} · Id_Caja {ts[0]['id']} · {ts[0]['usuario']}"
    elif f.modo == "usuario":
        alcance = f"Usuario: {ts[0]['usuario'] if ts else f.user_id}"
    else:
        alcance = "Todas las cajas"
    origen = {"recibos": "Recibos", "facturas": "Facturas", "ambos": "Facturas y Recibos"}[c["origen"]]
    fila = lambda label, valor, bold=False, cant=None: {"label": label, "valor": valor, "bold": bold, "cant": cant}

    secs = [
        {"titulo": "DESGLOSE VENTA", "filas": [fila("Venta del Día", c["venta"]["total"], True),
                                               fila("Efectivo", c["venta"]["efectivo"]), fila("Otros", c["venta"]["otros"])]},
    ]
    if c["domicilios"]["total"]:
        secs.append({"titulo": "DOMICILIOS", "filas": [fila("Valor Domicilios", c["domicilios"]["total"], True),
                     fila("Efectivo", c["domicilios"]["efectivo"]), fila("Otros", c["domicilios"]["otros"])]})
    if c["propinas"]["total"]:
        secs.append({"titulo": "PROPINAS", "filas": [fila("Propinas", c["propinas"]["total"], True),
                     fila("Efectivo", c["propinas"]["efectivo"]), fila("Otros", c["propinas"]["otros"])]})
    k = c["conteos"]
    secs.append({"titulo": "CUENTAS", "texto": True, "filas": [
        fila("Cuentas", None, cant=k["cuentas"]), fila("Otros (no efectivo)", None, cant=k["otros"]),
        fila("Anuladas", None, cant=k["anuladas"]),
        fila("Inicial", None, cant=k["inicial"] or "-"), fila("Final", None, cant=k["final"] or "-")]})
    secs.append({"titulo": "ENTRAN EFECTIVO", "filas": [fila(e["label"], e["valor"]) for e in c["entran"]]
                 + [fila("Total Ingresos", c["total_entran"], True)]})
    secs.append({"titulo": "SALEN EFECTIVO", "filas": [fila(s["label"], s["valor"]) for s in c["salen"]]
                 + [fila("Total Egresos", c["total_salen"], True)]})
    secs.append({"titulo": "DINERO A ENTREGAR", "filas": [fila("Dinero a Entregar", c["dinero_entregar"], True)]})
    if c["formas_pago"]:
        secs.append({"titulo": "FORMAS DE PAGO", "filas": [fila(p["name"], p["valor"]) for p in c["formas_pago"]]})
    docs = [{"titulo": "CUADRE DE CAJA", "secciones": secs}]

    if f.incluir.movimientos:
        for clave, _t, titulo, _tipo, _s in svc.MOVIMIENTOS:
            movs = c["movimientos"][clave]
            if not movs:
                continue
            docs.append({"titulo": titulo.upper(), "secciones": [{"titulo": f"Detalle de {titulo}", "filas":
                [fila(" - ".join(x for x in (m["concepto"], m["detalle"]) if x) or titulo, m["valor"]) for m in movs]
                + [fila(f"Total {titulo}", sum(m["valor"] for m in movs), True)]}]})
    if f.incluir.categorias and c["categorias"]:
        docs.append({"titulo": "VENTA POR CATEGORIA", "secciones": [{"titulo": "Categorías", "filas":
            [fila(x["categoria"], x["valor"], cant=x["cantidad"]) for x in c["categorias"]]
            + [fila("Total", sum(x["valor"] for x in c["categorias"]), True)]}]})
    if f.incluir.articulos:
        cats = await svc.ventas_por_categoria(db, cid, c["documentos"], detalle=True)
        if cats:
            docs.append({"titulo": "ARTICULOS VENDIDOS", "secciones": [
                {"titulo": x["categoria"], "filas": [fila(i["producto"], i["valor"], cant=i["cantidad"]) for i in x["items"]]
                 + [fila(f"Total {x['categoria']}", x["valor"], True, cant=x["cantidad"])]} for x in cats]})

    empresa = (await db.execute(text("SELECT name FROM companies WHERE id_company = :cid"), {"cid": cid})).scalar() or ""
    return {"empresa": empresa, "fecha": _fmt_fecha(c["fecha"]), "alcance": alcance, "origen": origen,
            "impreso": datetime.now(_BOG).strftime("%d/%m/%Y %H:%M"), "documentos": docs}


def _tirilla_cuadre(d: dict, width: int = 32) -> bytes:
    from app.routers.pos_recibo_impresion_router import _ascii, _money
    ESC = b"\x1b"
    INIT, BOLD_ON, BOLD_OFF = ESC + b"@", ESC + b"E\x01", ESC + b"E\x00"
    CENTER, LEFT, CUT, LF = ESC + b"a\x01", ESC + b"a\x00", b"\x1dV\x42\x00", b"\n"
    buf = bytearray()

    def line(t="", bold=False, center=False):
        buf.extend((BOLD_ON if bold else b"") + (CENTER if center else LEFT) + _ascii(t) + LF + (BOLD_OFF if bold else b""))

    def dl(a, b, bold=False):
        a = str(a)[: max(1, width - len(b) - 1)]
        line(a + " " * max(1, width - len(a) - len(b)) + b, bold=bold)

    for doc in d["documentos"]:
        buf.extend(INIT)
        line(d["empresa"], bold=True, center=True)
        line(doc["titulo"], bold=True, center=True)
        line(f"Fecha: {d['fecha']}", center=True)
        line(d["alcance"][:width], center=True)
        line(d["origen"], center=True)
        line("-" * width)
        for s in doc["secciones"]:
            line(s["titulo"], bold=True)
            for r in s["filas"]:
                if r["valor"] is None:
                    dl(r["label"], str(r["cant"]), r["bold"])
                else:
                    lab = f"{r['cant']} {r['label']}" if r.get("cant") not in (None, "") else r["label"]
                    dl(lab, _money(r["valor"]), r["bold"])
            line()
        line(f"Impreso: {d['impreso']}", center=True)
        buf.extend(LF * 4 + CUT)
    return bytes(buf)


@router.post("/vista-previa")
async def vista_previa(
    body: ImpresionIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _documentos(db, current_user.company_id, body)


@router.post("/imprimir")
async def imprimir(
    body: ImprimirIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.routers.pos_recibo_impresion_router import enviar_tirilla
    cid = current_user.company_id
    return await enviar_tirilla(db, cid, body.printer_id, body.raw,
                                lambda: _documentos(db, cid, body), armar=_tirilla_cuadre)
