import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task_evidence_model import TaskEvidence
from app.models.task_model import Task
from app.models.user_model import User
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession

router = APIRouter(prefix="/task-evidence", tags=["TaskEvidence"])

UPLOADS_BASE = Path(__file__).resolve().parent.parent / "uploads"
ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_VIDEO = {".mp4", ".mov", ".avi", ".webm"}
ALLOWED_AUDIO = {".mp3", ".m4a", ".ogg", ".wav", ".aac"}
MAX_SIZE_MB   = 50


def _get_user(authorization: str, db: Session):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token   = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    session = db.query(UserSession).filter(
        UserSession.token == token, UserSession.is_active == True
    ).first()
    if not session or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# ── GET: evidencias de una tarea ────────────────────────────────
@router.get("/{task_id}")
def get_evidence(task_id: int, db: Session = Depends(get_db)):
    items = db.query(TaskEvidence).filter(
        TaskEvidence.task_id == task_id
    ).order_by(TaskEvidence.created_at.asc()).all()

    return [_serialize(e) for e in items]


# ── POST: subir nueva evidencia ─────────────────────────────────
@router.post("/{task_id}")
async def add_evidence(
    task_id:     int,
    file_type:   str  = Form(...),          # image | video | audio | text
    description: str  = Form(""),
    file:        UploadFile = File(None),   # None si es tipo text
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    file_path = ""

    if file_type == "text":
        if not description.strip():
            raise HTTPException(status_code=400, detail="El texto no puede estar vacío")

    else:
        if not file:
            raise HTTPException(status_code=400, detail="Se requiere un archivo")

        content  = await file.read()
        size_mb  = len(content) / (1024 * 1024)
        if size_mb > MAX_SIZE_MB:
            raise HTTPException(status_code=413, detail=f"El archivo supera los {MAX_SIZE_MB} MB")

        ext = Path(file.filename).suffix.lower()

        if file_type == "image" and ext not in ALLOWED_IMAGE:
            raise HTTPException(status_code=400, detail="Formato de imagen no permitido (jpg, png, webp)")
        if file_type == "video" and ext not in ALLOWED_VIDEO:
            raise HTTPException(status_code=400, detail="Formato de video no permitido (mp4, mov, webm)")
        if file_type == "audio" and ext not in ALLOWED_AUDIO:
            raise HTTPException(status_code=400, detail="Formato de audio no permitido (mp3, m4a, wav)")

        folder = UPLOADS_BASE / f"{file_type}s"
        folder.mkdir(parents=True, exist_ok=True)

        filename  = f"{task_id}_{uuid.uuid4().hex[:8]}{ext}"
        full_path = folder / filename
        full_path.write_bytes(content)

        file_path = f"/uploads/{file_type}s/{filename}"

    evidence = TaskEvidence(
        task_id=     task_id,
        file_type=   file_type,
        file_path=   file_path,
        description= description,
        created_by=  user.id
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return _serialize(evidence)


# ── DELETE ──────────────────────────────────────────────────────
@router.delete("/{evidence_id}")
def delete_evidence(
    evidence_id:   int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_user(authorization, db)
    ev = db.query(TaskEvidence).filter(TaskEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    # Eliminar archivo del disco si existe
    if ev.file_path:
        file_on_disk = UPLOADS_BASE.parent / ev.file_path.lstrip("/")
        if file_on_disk.exists():
            file_on_disk.unlink()

    db.delete(ev)
    db.commit()
    return {"message": "Evidencia eliminada"}


def _serialize(e: TaskEvidence):
    return {
        "id":          e.id,
        "task_id":     e.task_id,
        "file_type":   e.file_type,
        "file_path":   e.file_path,
        "description": e.description,
        "created_by":  e.created_by,
        "created_at":  e.created_at.isoformat() if e.created_at else None,
    }
