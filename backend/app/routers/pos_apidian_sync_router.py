import os
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db

router = APIRouter(prefix="/api/pos", tags=["POS Apidian Sync"])

POS_API_KEY = os.getenv("POS_API_KEY", "easypos-sync-key-2024")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != POS_API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")


# ─────────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────────

class ApidianCajaFacturaIn(BaseModel):
    company_id:           int
    Nro_Caja:             int           = 0
    Nro_Factura:          str
    Fecha:                Optional[str] = None
    Nro_Pedido:           Optional[str] = None
    Valor:                Optional[float] = 0
    Base:                 Optional[float] = 0
    Impuesto_Iva:         Optional[float] = 0
    Impuesto_Impoconsumo: Optional[float] = 0
    Empleado:             Optional[int]   = 0
    Turno:                Optional[int]   = 0
    Pc_Desde:             Optional[str]  = None
    Cod_Domiciliario:     Optional[int]  = 0
    Observacion_Factura:  Optional[str]  = None
    Prefix:               Optional[str]  = None
    Fac_PE:               Optional[str]  = None
    Enviada_MySql:        Optional[int]  = 1


class ApidianClienteAdquirienteIn(BaseModel):
    company_id:      int
    Id_Cliente:      int
    cedula:          Optional[str] = None
    PersonaJuridica: Optional[int] = 0
    Tipo_Documento:  Optional[str] = None
    DV:              Optional[str] = None
    RegContributivo: Optional[str] = None
    nombres:         Optional[str] = None
    direccion:       Optional[str] = None
    telefono:        Optional[str] = None
    Mail:            Optional[str] = None
    Observaciones:   Optional[str] = None
    Enviada_MySql:   Optional[int] = 1
    Referencia:      Optional[str] = None
    Cod_Municipio:   Optional[int] = 0
    Ciudad:          Optional[int] = 0
    Departamento:    Optional[int] = 0
    CodPais:         Optional[int] = 0


class ApidianFacturaCufeIn(BaseModel):
    company_id:          int
    Nro_Caja:            int          = 0
    Prefix:              Optional[str] = ''
    Nro_Factura:         str
    Tipo_Pago:           Optional[str]   = None
    Cedula:              Optional[str]   = None
    Fecha:               Optional[str]   = None
    Nro_Pedido:          Optional[str]   = None
    cufe:                Optional[str]   = None
    FEExitosa:           Optional[int]   = 0
    Valor:               Optional[float] = 0
    Descuento:           Optional[float] = 0
    Empleado:            Optional[int]   = 0
    Pc_Desde:            Optional[str]   = None
    Estado:              Optional[str]   = None
    VentaCerrada:        Optional[int]   = 0
    Observacion_Factura: Optional[str]   = None
    Hora:                Optional[str]   = None
    Enviada_MySql:       Optional[int]   = 1


class ConsecutivoFacturaIn(BaseModel):
    company_id:     int
    Id_Consecutivo: int
    Nro_Pedido:     Optional[str] = None
    Fecha:          Optional[str] = None
    Id_Resolucion:  Optional[int] = 0
    Enviada_MySql:  Optional[int] = 1


# ═════════════════════════════════════════════════════════════════
# PUSH  apidian_caja_facturas
# ═════════════════════════════════════════════════════════════════
@router.post("/sync/push/apidian-caja-facturas")
async def push_apidian_caja_facturas(
    records: List[ApidianCajaFacturaIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        key = f"{r.company_id}|{r.Nro_Caja}|{r.Nro_Factura}"
        try:
            await db.execute(text("""
                INSERT INTO apidian_caja_facturas
                    (company_id, Nro_Caja, Nro_Factura, Fecha, Nro_Pedido,
                     Valor, Base, Impuesto_Iva, Impuesto_Impoconsumo,
                     Empleado, Turno, Pc_Desde, Cod_Domiciliario,
                     Observacion_Factura, Prefix, Fac_PE, Enviada_MySql, updated_at)
                VALUES
                    (:company_id, :Nro_Caja, :Nro_Factura, :Fecha, :Nro_Pedido,
                     :Valor, :Base, :Impuesto_Iva, :Impuesto_Impoconsumo,
                     :Empleado, :Turno, :Pc_Desde, :Cod_Domiciliario,
                     :Observacion_Factura, :Prefix, :Fac_PE, :Enviada_MySql, NOW())
                ON DUPLICATE KEY UPDATE
                    Fecha                = VALUES(Fecha),
                    Valor                = VALUES(Valor),
                    Base                 = VALUES(Base),
                    Impuesto_Iva         = VALUES(Impuesto_Iva),
                    Impuesto_Impoconsumo = VALUES(Impuesto_Impoconsumo),
                    Empleado             = VALUES(Empleado),
                    Turno                = VALUES(Turno),
                    Pc_Desde             = VALUES(Pc_Desde),
                    Cod_Domiciliario     = VALUES(Cod_Domiciliario),
                    Observacion_Factura  = VALUES(Observacion_Factura),
                    Prefix               = VALUES(Prefix),
                    Fac_PE               = VALUES(Fac_PE),
                    Enviada_MySql        = VALUES(Enviada_MySql),
                    updated_at           = NOW()
            """), r.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


# ═════════════════════════════════════════════════════════════════
# PUSH  apidian_clientes_adquiriente
# ═════════════════════════════════════════════════════════════════
@router.post("/sync/push/apidian-clientes")
async def push_apidian_clientes(
    records: List[ApidianClienteAdquirienteIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        key = f"{r.company_id}|{r.Id_Cliente}"
        try:
            await db.execute(text("""
                INSERT INTO apidian_clientes_adquiriente
                    (company_id, Id_Cliente, cedula, PersonaJuridica, Tipo_Documento,
                     DV, RegContributivo, nombres, direccion, telefono, Mail,
                     Observaciones, Enviada_MySql, Referencia,
                     Cod_Municipio, Ciudad, Departamento, CodPais, updated_at)
                VALUES
                    (:company_id, :Id_Cliente, :cedula, :PersonaJuridica, :Tipo_Documento,
                     :DV, :RegContributivo, :nombres, :direccion, :telefono, :Mail,
                     :Observaciones, :Enviada_MySql, :Referencia,
                     :Cod_Municipio, :Ciudad, :Departamento, :CodPais, NOW())
                ON DUPLICATE KEY UPDATE
                    cedula          = VALUES(cedula),
                    PersonaJuridica = VALUES(PersonaJuridica),
                    Tipo_Documento  = VALUES(Tipo_Documento),
                    DV              = VALUES(DV),
                    RegContributivo = VALUES(RegContributivo),
                    nombres         = VALUES(nombres),
                    direccion       = VALUES(direccion),
                    telefono        = VALUES(telefono),
                    Mail            = VALUES(Mail),
                    Observaciones   = VALUES(Observaciones),
                    Referencia      = VALUES(Referencia),
                    Cod_Municipio   = VALUES(Cod_Municipio),
                    Ciudad          = VALUES(Ciudad),
                    Departamento    = VALUES(Departamento),
                    CodPais         = VALUES(CodPais),
                    Enviada_MySql   = VALUES(Enviada_MySql),
                    updated_at      = NOW()
            """), r.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


# ═════════════════════════════════════════════════════════════════
# PUSH  apidian_facturas_cufe
# ═════════════════════════════════════════════════════════════════
@router.post("/sync/push/apidian-facturas-cufe")
async def push_apidian_facturas_cufe(
    records: List[ApidianFacturaCufeIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        key = f"{r.company_id}|{r.Nro_Caja}|{r.Prefix or ''}|{r.Nro_Factura}"
        try:
            await db.execute(text("""
                INSERT INTO apidian_facturas_cufe
                    (company_id, Nro_Caja, Prefix, Nro_Factura, Tipo_Pago,
                     Cedula, Fecha, Nro_Pedido, cufe, FEExitosa,
                     Valor, Descuento, Empleado, Pc_Desde, Estado,
                     VentaCerrada, Observacion_Factura, Hora, Enviada_MySql, updated_at)
                VALUES
                    (:company_id, :Nro_Caja, :Prefix, :Nro_Factura, :Tipo_Pago,
                     :Cedula, :Fecha, :Nro_Pedido, :cufe, :FEExitosa,
                     :Valor, :Descuento, :Empleado, :Pc_Desde, :Estado,
                     :VentaCerrada, :Observacion_Factura, :Hora, :Enviada_MySql, NOW())
                ON DUPLICATE KEY UPDATE
                    Tipo_Pago           = VALUES(Tipo_Pago),
                    Cedula              = VALUES(Cedula),
                    Fecha               = VALUES(Fecha),
                    cufe                = VALUES(cufe),
                    FEExitosa           = VALUES(FEExitosa),
                    Valor               = VALUES(Valor),
                    Descuento           = VALUES(Descuento),
                    Empleado            = VALUES(Empleado),
                    Pc_Desde            = VALUES(Pc_Desde),
                    Estado              = VALUES(Estado),
                    VentaCerrada        = VALUES(VentaCerrada),
                    Observacion_Factura = VALUES(Observacion_Factura),
                    Hora                = VALUES(Hora),
                    Enviada_MySql       = VALUES(Enviada_MySql),
                    updated_at          = NOW()
            """), r.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


# ═════════════════════════════════════════════════════════════════
# PUSH  consecutivo_factura_manual
# ═════════════════════════════════════════════════════════════════
@router.post("/sync/push/consecutivo-factura-manual")
async def push_consecutivo_factura_manual(
    records: List[ConsecutivoFacturaIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        key = f"{r.company_id}|{r.Id_Consecutivo}"
        try:
            await db.execute(text("""
                INSERT INTO consecutivo_factura_manual
                    (company_id, Id_Consecutivo, Nro_Pedido, Fecha,
                     Id_Resolucion, Enviada_MySql, updated_at)
                VALUES
                    (:company_id, :Id_Consecutivo, :Nro_Pedido, :Fecha,
                     :Id_Resolucion, :Enviada_MySql, NOW())
                ON DUPLICATE KEY UPDATE
                    Nro_Pedido    = VALUES(Nro_Pedido),
                    Fecha         = VALUES(Fecha),
                    Id_Resolucion = VALUES(Id_Resolucion),
                    Enviada_MySql = VALUES(Enviada_MySql),
                    updated_at    = NOW()
            """), r.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


# ═════════════════════════════════════════════════════════════════
# PUSH  consecutivo_factura_sistema
# ═════════════════════════════════════════════════════════════════
@router.post("/sync/push/consecutivo-factura-sistema")
async def push_consecutivo_factura_sistema(
    records: List[ConsecutivoFacturaIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        key = f"{r.company_id}|{r.Id_Consecutivo}"
        try:
            await db.execute(text("""
                INSERT INTO consecutivo_factura_sistema
                    (company_id, Id_Consecutivo, Nro_Pedido, Fecha,
                     Id_Resolucion, Enviada_MySql, updated_at)
                VALUES
                    (:company_id, :Id_Consecutivo, :Nro_Pedido, :Fecha,
                     :Id_Resolucion, :Enviada_MySql, NOW())
                ON DUPLICATE KEY UPDATE
                    Nro_Pedido    = VALUES(Nro_Pedido),
                    Fecha         = VALUES(Fecha),
                    Id_Resolucion = VALUES(Id_Resolucion),
                    Enviada_MySql = VALUES(Enviada_MySql),
                    updated_at    = NOW()
            """), r.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}
