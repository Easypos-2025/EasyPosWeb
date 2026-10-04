"""
Fotos de platos y categorías del escritorio.

  Carpeta: configuracion_sede.Ruta_Foto_Productos / Ruta_Foto_Categorias (BD de la empresa).
           Si en este PC no existe, se usa AG_DIR_FOTOS_PRODUCTOS / AG_DIR_FOTOS_CATEGORIAS del .env.
  Archivo: platos.Ruta_Foto / categoria_platos.Nombre_foto (solo el nombre, ej. "aji.jpg").

Seguridad: nunca se recibe una ruta del navegador; se sirve por id y el nombre guardado en la
BD se reduce a un nombre simple con extensión de imagen, siempre dentro de la carpeta.
Se envía una miniatura (máx. 400 px) guardada en caché para que la carta cargue rápido.
"""
import hashlib
import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .. import config

EXTENSIONES = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
LADO_MAX = 400
DIR_CACHE = config.BASE / "cache_fotos"

_ENV = {"productos": "AG_DIR_FOTOS_PRODUCTOS", "categorias": "AG_DIR_FOTOS_CATEGORIAS"}
_COLUMNA = {"productos": "Ruta_Foto_Productos", "categorias": "Ruta_Foto_Categorias"}


async def carpeta(emp: AsyncSession, tipo: str) -> Path | None:
    candidatas = []
    try:
        ruta = (await emp.execute(text(f"SELECT {_COLUMNA[tipo]} FROM configuracion_sede LIMIT 1"))).scalar()
        if ruta:
            candidatas.append(str(ruta).strip())
    except Exception:
        pass
    if os.getenv(_ENV[tipo]):
        candidatas.append(os.getenv(_ENV[tipo]).strip())
    for c in candidatas:
        p = Path(c)
        if c and p.is_dir():
            return p
    return None


def nombre_seguro(nombre: str | None) -> str | None:
    """'aji.jpg' → 'aji.jpg'; '..\\..\\x.key', 'C:/a/b.jpg', 'x.exe' → None o solo el nombre válido."""
    limpio = (nombre or "").strip().replace("\\", "/").split("/")[-1]
    if not limpio or limpio.startswith(".") or Path(limpio).suffix.lower() not in EXTENSIONES:
        return None
    return limpio


def indice(dir_fotos: Path | None) -> dict[str, tuple[str, int]]:
    """{nombre en minúscula: (nombre real, versión)} de la carpeta (Windows no distingue mayúsculas)."""
    if not dir_fotos:
        return {}
    salida = {}
    try:
        with os.scandir(dir_fotos) as it:
            for e in it:
                if e.is_file() and Path(e.name).suffix.lower() in EXTENSIONES:
                    salida[e.name.lower()] = (e.name, int(e.stat().st_mtime))
    except OSError:
        return {}
    return salida


def version(idx: dict, nombre: str | None) -> int | None:
    n = nombre_seguro(nombre)
    return idx[n.lower()][1] if n and n.lower() in idx else None


def archivo(dir_fotos: Path | None, nombre: str | None) -> Path | None:
    n = nombre_seguro(nombre)
    if not dir_fotos or not n:
        return None
    real = indice(dir_fotos).get(n.lower())
    if not real:
        return None
    ruta = (dir_fotos / real[0]).resolve()
    if ruta.parent != dir_fotos.resolve():
        return None
    return ruta


def miniatura(ruta: Path) -> Path:
    """Miniatura JPEG en caché (se regenera si la foto original cambia). Si falla, la original."""
    try:
        from PIL import Image
        marca = f"{ruta}|{int(ruta.stat().st_mtime)}|{LADO_MAX}"
        destino = DIR_CACHE / (hashlib.sha1(marca.encode()).hexdigest() + ".jpg")
        if destino.exists():
            return destino
        DIR_CACHE.mkdir(exist_ok=True)
        with Image.open(ruta) as img:
            img.thumbnail((LADO_MAX, LADO_MAX))
            img.convert("RGB").save(destino, "JPEG", quality=80, optimize=True)
        return destino
    except Exception:
        return ruta
