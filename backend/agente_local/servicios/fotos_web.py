"""
Fotos de los platos subidas en la web → carpeta de fotos del escritorio.

  · La nube entrega las fotos de SU empresa (pos_dishes.id = Id_Plato del escritorio).
  · Se guardan como "web_<Id_Plato>.jpg" (el VB6 no muestra .webp) en
    configuracion_sede.Ruta_Foto_Productos.
  · platos.Ruta_Foto se llena SOLO en los platos que no tienen foto (no pisa las del escritorio).
  · Solo HTTPS, máximo 10 MB y debe ser una imagen válida.
"""
import io
import urllib.request
from datetime import datetime

from sqlalchemy import text

from .. import nube
from ..db import SesionEmpresa
from . import fotos

MAX_BYTES = 10 * 1024 * 1024
LADO_MAX = 800


def _descargar_jpg(url: str, destino) -> None:
    if not url.lower().startswith("https://"):
        raise ValueError("Solo se descargan fotos por HTTPS")
    req = urllib.request.Request(url, headers={"User-Agent": "EasyPosAgenteLocal"})
    with urllib.request.urlopen(req, timeout=30) as r:
        datos = r.read(MAX_BYTES + 1)
    if len(datos) > MAX_BYTES:
        raise ValueError("Foto demasiado grande")
    from PIL import Image
    with Image.open(io.BytesIO(datos)) as img:
        img.thumbnail((LADO_MAX, LADO_MAX))
        img.convert("RGB").save(destino, "JPEG", quality=85, optimize=True)


async def sincronizar() -> dict:
    import asyncio
    resumen = {"fecha": datetime.now().isoformat(timespec="seconds"), "descargadas": 0, "asignadas": 0,
               "sin_cambios": 0, "fallidas": 0, "error": None}
    lista = await nube.pedir("GET", "/api/agente/fotos-platos") or []
    async with SesionEmpresa() as emp:
        carpeta = await fotos.carpeta(emp, "productos")
        if not carpeta:
            resumen["error"] = "No existe la carpeta de fotos de productos (configuracion_sede.Ruta_Foto_Productos)."
            return resumen
        for f in lista:
            try:
                id_plato = int(f["id_plato"])
                existe = (await emp.execute(text("SELECT COUNT(*) FROM platos WHERE Id_Plato = :i"),
                                            {"i": id_plato})).scalar()
                if not existe:
                    continue
                nombre = f"web_{id_plato}.jpg"
                destino = carpeta / nombre
                actualizado = datetime.fromisoformat(f["actualizado"]) if f.get("actualizado") else None
                if destino.exists() and actualizado and datetime.fromtimestamp(destino.stat().st_mtime) >= actualizado:
                    resumen["sin_cambios"] += 1
                else:
                    await asyncio.to_thread(_descargar_jpg, str(f["url"]), destino)
                    resumen["descargadas"] += 1
                n = (await emp.execute(text("""
                    UPDATE platos SET Ruta_Foto = :n
                    WHERE Id_Plato = :i AND (Ruta_Foto IS NULL OR TRIM(Ruta_Foto) = '')
                """), {"n": nombre, "i": id_plato})).rowcount
                resumen["asignadas"] += n
            except Exception:
                resumen["fallidas"] += 1
        await emp.commit()
    return resumen
