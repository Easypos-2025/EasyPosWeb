"""
Configuración de Facturación (espejo de `configuracion_facturacion` del escritorio).

  GET /api/config-facturacion   configuración de la empresa + impresoras para el selector
  PUT /api/config-facturacion   guarda (solo ADMIN / SYSADMIN)

La empresa sale de la sesión (empresa seleccionada en el topbar, validada por tenant).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.models.role_model import Role
from app.models.user_model import User
from app.services import config_facturacion as cfg_svc

router = APIRouter(prefix="/api/config-facturacion", tags=["Configuración Facturación"],
                   dependencies=[Depends(tenant_guard)])

Pct   = Annotated[float, Field(ge=0, le=100)]
Small = Annotated[int, Field(ge=0, le=99)]


def _s(n: int):
    return Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=n)]]


class ConfigIn(BaseModel):
    impuesto_iva: Pct = 0
    impuesto_impoconsumo: Pct = 0
    impuesto_rete_fuente: Pct = 0
    liquidar_propina: bool = False
    porcentaje_propina: Pct = 0
    preguntar_valor_propina: bool = False
    imprimir_resolucion_propina: bool = False
    resolucion_propina: _s(3000) = ""
    paga_impuesto: bool = False
    precios_incluyen_impuesto: bool = False
    imprimir_logo_factura: bool = False
    nombre_logo_factura: _s(200) = ""
    tipo_moneda: Annotated[int, Field(ge=0, le=9)] = 1
    texto_numeracion: _s(100) = ""
    nombre_cliente_facturacion_varia: _s(100) = ""
    codigo_cliente_facturacion_varia: _s(100) = ""
    id_cliente_facturacion_varia: Annotated[float, Field(ge=0, le=1e12)] = 1
    usa_lector_barras: bool = False
    imprimir_encabezado_factura: bool = True
    impresora_facturas: Optional[Annotated[int, Field(ge=0)]] = None
    mensaje_factura: _s(255) = ""
    longitud_factura_sistema: Small = 1
    longitud_factura_manual: Small = 1
    cantidad_impresiones_factura: Annotated[int, Field(ge=0, le=5)] = 1
    activar_precio_x_mayor: bool = False
    usar_precuenta: bool = False
    imprimir_datos_legales: bool = False
    imprimir_datos_cliente: bool = False
    imprimir_recibo_domiciliario: bool = False
    usar_comanda_corta: bool = False
    company_id: Optional[int] = None     # lo valida tenant_guard; no se usa


async def _exigir_admin(db: AsyncSession, user: User) -> None:
    role = await db.get(Role, user.role_id) if user.role_id else None
    if not role or not (role.is_system or "ADMIN" in (role.name or "").upper()):
        raise HTTPException(status_code=403, detail="Solo un administrador puede modificar la configuración de facturación")


async def _impresoras(db: AsyncSession, cid: int) -> list:
    rows = (await db.execute(text(
        "SELECT id, name, connection_type FROM pos_printers WHERE company_id=:cid AND is_active=1 ORDER BY name"
    ), {"cid": cid})).mappings().all()
    return [dict(r) for r in rows]


@router.get("")
async def obtener(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    cid = current_user.company_id
    cfg = await cfg_svc.get_config(db, cid)
    await db.commit()
    return {"config": cfg, "printers": await _impresoras(db, cid)}


@router.put("")
async def guardar(body: ConfigIn, db: AsyncSession = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    await _exigir_admin(db, current_user)
    cid = current_user.company_id
    datos = body.model_dump(exclude={"company_id"})
    if datos["impresora_facturas"]:
        ok = (await db.execute(text(
            "SELECT 1 FROM pos_printers WHERE company_id=:cid AND id=:pid"
        ), {"cid": cid, "pid": datos["impresora_facturas"]})).scalar()
        if not ok:
            raise HTTPException(status_code=422, detail="Impresora no válida para esta empresa")
    for k, tipo in cfg_svc.CAMPOS.items():
        if tipo == "bool" and k in datos:
            datos[k] = int(datos[k])
    await cfg_svc.guardar(db, cid, datos)
    await db.commit()
    return {"ok": True, "config": await cfg_svc.get_config(db, cid)}
