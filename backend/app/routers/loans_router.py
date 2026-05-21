import secrets
from datetime import datetime, timedelta
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.loan_model import Loan
from app.models.bodega_item_model import BodegaItem
from app.models.external_collaborator_model import ExternalCollaborator
from app.auth.dependencies import get_current_user
from app.models.user_model import User
from app.models.role_model import Role
from app.models.role_module_model import RoleModule
from app.models.system_module_model import SystemModule

router = APIRouter(prefix="/loans", tags=["Loans"])
QR_EXPIRY_HOURS = 72
LOANS_ROUTE = "/loans/prestamos"


async def _get_loan_perms(user: User, db: AsyncSession):
    """Devuelve (is_sys, can_view_all, can_create, can_edit) para el usuario en el módulo de préstamos."""
    role = await db.get(Role, user.role_id)
    if role and role.is_system:
        return True, True, True, True

    result = await db.execute(
        select(RoleModule)
        .join(SystemModule, SystemModule.id == RoleModule.module_id)
        .where(RoleModule.role_id == user.role_id, SystemModule.route == LOANS_ROUTE)
    )
    perm = result.scalar_one_or_none()
    if not perm:
        return False, False, False, False
    return False, bool(perm.can_view_all), bool(perm.can_create), bool(perm.can_edit)


async def _ser(loan: Loan, db: AsyncSession):
    item   = await db.get(BodegaItem, loan.bodega_item_id)
    collab = await db.get(ExternalCollaborator, loan.external_collaborator_id) if loan.external_collaborator_id else None
    creator = await db.get(User, loan.created_by)
    leader  = await db.get(User, loan.task_leader_id) if loan.task_leader_id else None
    return {"id": loan.id, "company_id": loan.company_id,
            "bodega_item_id": loan.bodega_item_id, "bodega_item_nombre": item.nombre if item else "—",
            "bodega_item_codigo": item.codigo if item else None, "cantidad": loan.cantidad,
            "task_leader_id": loan.task_leader_id,
            "task_leader_nombre": leader.nombre if leader else None,
            "external_collaborator_id": loan.external_collaborator_id,
            "colaborador_nombre": collab.nombre if collab else None,
            "colaborador_dni": collab.dni if collab else None,
            "colaborador_empresa": collab.empresa if collab else None,
            "created_by_nombre": creator.nombre if creator else "—",
            "estado": loan.estado,
            "qr_token": loan.qr_token,
            "qr_signed_by": loan.qr_signed_by,
            "qr_expires_at": loan.qr_expires_at.isoformat() if loan.qr_expires_at else None,
            "fecha_salida_confirmada": loan.fecha_salida_confirmada.isoformat() if loan.fecha_salida_confirmada else None,
            "fecha_retorno_esperada": loan.fecha_retorno_esperada.isoformat() if loan.fecha_retorno_esperada else None,
            "fecha_retorno_confirmada": loan.fecha_retorno_confirmada.isoformat() if loan.fecha_retorno_confirmada else None,
            "estado_fisico_retorno": loan.estado_fisico_retorno, "notas": loan.notas,
            "created_at": loan.created_at.isoformat() if loan.created_at else None}


@router.get("/")
async def list_loans(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    is_sys, can_view_all, _, _ = await _get_loan_perms(current_user, db)

    conds = [] if is_sys else [Loan.company_id == current_user.company_id]
    if not is_sys and not can_view_all:
        conds.append(Loan.task_leader_id == current_user.id)

    result = await db.execute(select(Loan).where(*conds).order_by(Loan.created_at.desc()))
    return [await _ser(l, db) for l in result.scalars().all()]


@router.get("/stats")
async def loan_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    is_sys, can_view_all, _, _ = await _get_loan_perms(current_user, db)

    base_conds = [] if is_sys else [Loan.company_id == current_user.company_id]
    if not is_sys and not can_view_all:
        base_conds.append(Loan.task_leader_id == current_user.id)

    async def cnt(*extra):
        return (await db.execute(select(func.count()).select_from(Loan).where(*base_conds, *extra))).scalar()

    return {"total": await cnt(),
            "pendiente_confirmacion": await cnt(Loan.estado == "pendiente_confirmacion"),
            "activo": await cnt(Loan.estado == "activo"),
            "retorno_pendiente": await cnt(Loan.estado == "retorno_pendiente"),
            "devuelto": await cnt(Loan.estado.in_(["devuelto", "devuelto_con_dano"]))}


@router.post("/")
async def create_loan(data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _, _, can_create, _ = await _get_loan_perms(current_user, db)
    if not can_create:
        raise HTTPException(status_code=403, detail="Sin permiso para crear préstamos")

    result = await db.execute(select(BodegaItem).where(BodegaItem.id == data.get("bodega_item_id"), BodegaItem.company_id == current_user.company_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    cantidad = int(data.get("cantidad", 1))
    if cantidad < 1:
        raise HTTPException(status_code=400, detail="La cantidad debe ser al menos 1")
    if item.cantidad_disponible < cantidad:
        raise HTTPException(status_code=409, detail=f"Stock insuficiente. Disponible: {item.cantidad_disponible}")

    task_leader_id = data.get("task_leader_id")
    if not task_leader_id:
        raise HTTPException(status_code=400, detail="El líder de tarea es obligatorio")
    leader = await db.get(User, task_leader_id)
    if not leader or leader.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Líder de tarea no encontrado en esta empresa")

    collab = None
    if data.get("external_collaborator_id"):
        result = await db.execute(select(ExternalCollaborator).where(ExternalCollaborator.id == data["external_collaborator_id"], ExternalCollaborator.company_id == current_user.company_id))
        collab = result.scalar_one_or_none()
        if not collab:
            raise HTTPException(status_code=404, detail="Colaborador no encontrado")

    fecha_retorno = None
    if data.get("fecha_retorno_esperada"):
        from datetime import date
        try:
            fecha_retorno = date.fromisoformat(data["fecha_retorno_esperada"])
        except ValueError:
            pass
    loan = Loan(company_id=current_user.company_id, bodega_item_id=item.id, cantidad=cantidad,
                task_leader_id=task_leader_id,
                external_collaborator_id=collab.id if collab else None,
                created_by=current_user.id,
                estado="pendiente_confirmacion", qr_token=secrets.token_urlsafe(32),
                qr_expires_at=datetime.utcnow() + timedelta(hours=QR_EXPIRY_HOURS),
                fecha_retorno_esperada=fecha_retorno, notas=(data.get("notas") or "").strip() or None)
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    return await _ser(loan, db)


@router.get("/{loan_id}/qr")
async def get_qr_image(loan_id: int, request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    is_sys, can_view_all, _, _ = await _get_loan_perms(current_user, db)

    conds = [Loan.id == loan_id, Loan.company_id == current_user.company_id]
    if not is_sys and not can_view_all:
        conds.append(Loan.task_leader_id == current_user.id)

    result = await db.execute(select(Loan).where(*conds))
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    if not loan.qr_token:
        raise HTTPException(status_code=400, detail="Sin QR generado")
    try:
        import qrcode
        base = str(request.base_url).rstrip("/")
        url = f"{base}/prestamo-qr/{loan.qr_token}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png",
                                 headers={"Content-Disposition": f"inline; filename=qr-prestamo-{loan_id}.png"})
    except ImportError:
        raise HTTPException(status_code=500, detail="Librería qrcode no instalada en el servidor")


@router.post("/{loan_id}/activar-retorno")
async def activar_retorno(loan_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _, _, _, can_edit = await _get_loan_perms(current_user, db)
    if not can_edit:
        raise HTTPException(status_code=403, detail="Sin permiso para modificar préstamos")

    result = await db.execute(select(Loan).where(Loan.id == loan_id, Loan.company_id == current_user.company_id))
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    if loan.estado != "activo":
        raise HTTPException(status_code=409, detail=f"Estado actual: {loan.estado}. Solo se puede activar retorno desde 'activo'")
    loan.estado = "retorno_pendiente"
    loan.qr_expires_at = datetime.utcnow() + timedelta(hours=QR_EXPIRY_HOURS)
    await db.commit()
    await db.refresh(loan)
    return await _ser(loan, db)


@router.patch("/{loan_id}/cerrar")
async def cerrar_loan(loan_id: int, data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _, _, _, can_edit = await _get_loan_perms(current_user, db)
    if not can_edit:
        raise HTTPException(status_code=403, detail="Sin permiso para modificar préstamos")

    result = await db.execute(select(Loan).where(Loan.id == loan_id, Loan.company_id == current_user.company_id))
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    if loan.estado not in ("devuelto", "devuelto_con_dano", "retorno_pendiente", "activo"):
        raise HTTPException(status_code=409, detail="No se puede cerrar en este estado")
    estado_fisico = data.get("estado_fisico_retorno", "perfecto")
    loan.estado_fisico_retorno = estado_fisico
    loan.notas = (data.get("notas") or "").strip() or loan.notas
    loan.estado = "devuelto_con_dano" if estado_fisico in ("dano_leve", "dano_grave") else "devuelto"
    if not loan.fecha_retorno_confirmada:
        loan.fecha_retorno_confirmada = datetime.utcnow()
        item = await db.get(BodegaItem, loan.bodega_item_id)
        if item:
            item.cantidad_disponible = min(item.cantidad_total, item.cantidad_disponible + loan.cantidad)
    await db.commit()
    await db.refresh(loan)
    return await _ser(loan, db)
