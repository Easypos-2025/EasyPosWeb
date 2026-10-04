"""
Zonas y mesas de la BD de la empresa: los cambios del escritorio se ven al instante, sin abrir turno.
Como el escritorio: se muestran las zonas activas (zonas_asientos.Activa = 1) con TODAS sus mesas
(mesas.Activa no se usa para esto). Cada zona trae su color, y el alto de los botones es el de la
primera zona en orden alfabético (aplica a todas).
Estado de cada mesa (datatemppos):
  libre · mia (tiene un pedido mío) · ocupada (pedido de otro mesero) · abierta (en otro equipo)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_emp, get_tmp
from ..servicios import bloqueos
from ..servicios.catalogo import color_vb
from ..sesion import Mesero, mesero_actual
from ..textos import t

router = APIRouter(prefix="/api/ag", tags=["mesas"])


class MesaIn(BaseModel):
    id_mesa: int = Field(ge=0)
    mesa: str = Field(min_length=1, max_length=200)


@router.get("/mesas")
async def listar_mesas(mesero: Mesero = Depends(mesero_actual),
                       emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    zonas = (await emp.execute(text("""
        SELECT Id_Zona, Ubicacion, Zona_Dinamica, Color FROM zonas_asientos WHERE Activa = 1 ORDER BY Ubicacion
    """))).mappings().all()
    mesas = (await emp.execute(text("""
        SELECT m.Id_Mesa, m.Mesa, m.Id_Zona FROM mesas m
        JOIN zonas_asientos z ON z.Id_Zona = m.Id_Zona AND z.Activa = 1
        ORDER BY m.Mesa
    """))).mappings().all()
    # Alto de los botones: el de la primera zona en orden alfabético (en twips de VB6)
    altura = (await emp.execute(text(
        "SELECT Altura FROM zonas_asientos ORDER BY Ubicacion LIMIT 1"))).scalar()
    pedidos = {r["Mesa"]: r for r in (await tmp.execute(text(
        "SELECT Mesa, Mesero, Nro_Pedido FROM temp_comanda"))).mappings().all()}
    abiertas = {int(r[0]) for r in (await tmp.execute(text(
        "SELECT Id_Mesa FROM temp_mesa_abierta WHERE Abierta = 1"))).all()}
    mias = {int(r[0]) for r in (await tmp.execute(text(
        "SELECT id_mesa FROM ag_bloqueo_mesa WHERE id_dispositivo = :d"), {"d": mesero.id_dispositivo})).all()}

    def estado(m) -> dict:
        p = pedidos.get(m["Mesa"])
        if p:
            if int(p["Mesero"] or 0) == mesero.cod_empleado:
                return {"estado": "mia", "nro_pedido": p["Nro_Pedido"]}
            return {"estado": "ocupada"}
        if int(m["Id_Mesa"]) in abiertas and int(m["Id_Mesa"]) not in mias:
            return {"estado": "abierta"}
        return {"estado": "libre"}

    salida = []
    for z in zonas:
        salida.append({
            "id": int(z["Id_Zona"]), "nombre": (z["Ubicacion"] or "").strip(),
            "dinamica": int(z["Zona_Dinamica"] or 0), "color": color_vb(z["Color"]),
            "mesas": [{"id": int(m["Id_Mesa"]), "nombre": m["Mesa"], **estado(m)}
                      for m in mesas if int(m["Id_Zona"] or 0) == int(z["Id_Zona"])],
        })
    return {"zonas": salida, "alto": round(int(altura or 0) / 15)}     # twips → px


async def mesa_existe(emp: AsyncSession, id_mesa: int, mesa: str) -> bool:
    """Mesa de una zona activa."""
    return bool((await emp.execute(text("""
        SELECT COUNT(*) FROM mesas m JOIN zonas_asientos z ON z.Id_Zona = m.Id_Zona AND z.Activa = 1
        WHERE m.Id_Mesa = :i AND m.Mesa = :m
    """), {"i": id_mesa, "m": mesa})).scalar())


async def _mesa_permitida(emp: AsyncSession, tmp: AsyncSession, data: MesaIn, mesero: Mesero) -> None:
    """Mesa de una zona activa, o cuenta (Id >= 1000) de un pedido mío."""
    existe = await mesa_existe(emp, data.id_mesa, data.mesa)
    if not existe:
        existe = (await tmp.execute(text("""
            SELECT COUNT(*) FROM temp_comanda WHERE Imprimio_Precuenta = :i AND Mesa = :m AND Mesero = :c
        """), {"i": data.id_mesa, "m": data.mesa, "c": mesero.cod_empleado})).scalar()
    if not existe:
        raise HTTPException(status_code=404, detail=f"'{data.mesa.strip()}' no existe.")
    otro = (await tmp.execute(text("""
        SELECT COUNT(*) FROM temp_comanda WHERE Mesa = :m AND Mesero <> :c
    """), {"m": data.mesa, "c": mesero.cod_empleado})).scalar()
    if otro:
        raise HTTPException(status_code=409, detail=f"'{data.mesa.strip()}' tiene un pedido de otro {t('mesero')}.")


@router.post("/mesas/bloquear")
async def bloquear_mesa(data: MesaIn, mesero: Mesero = Depends(mesero_actual),
                        emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    await _mesa_permitida(emp, tmp, data, mesero)
    await bloqueos.bloquear(tmp, data.id_mesa, data.mesa, mesero)
    await tmp.commit()
    return {"ok": True, "minutos": bloqueos.MINUTOS_BLOQUEO}


@router.post("/mesas/liberar")
async def liberar_mesa(data: MesaIn, mesero: Mesero = Depends(mesero_actual),
                       tmp: AsyncSession = Depends(get_tmp)):
    await bloqueos.liberar(tmp, data.id_mesa, data.mesa, mesero)
    await tmp.commit()
    return {"ok": True}
