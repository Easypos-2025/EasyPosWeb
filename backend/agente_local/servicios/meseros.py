"""
Meseros del día: datatemppos.temp_meseros_dia. La caja los registra cada día (entre ellos se
liquida la propina). Al montar un pedido se escoge a quién se le asigna: un mismo dispositivo
lo pueden usar varios meseros, así que el pedido NO se asigna al usuario del dispositivo.
Sin meseros del día no se pueden montar pedidos.
"""
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..textos import t


async def del_dia(tmp: AsyncSession) -> list[dict]:
    filas = (await tmp.execute(text(
        "SELECT cod_empleado, nombres FROM temp_meseros_dia ORDER BY nombres"))).all()
    return [{"cod": int(c), "nombre": (n or "").strip() or f"Código {c}"} for c, n in filas]


async def validar(tmp: AsyncSession, cod: int) -> None:
    """El mesero escogido debe estar en los meseros del día (no se confía en el dispositivo)."""
    hay = (await tmp.execute(text("SELECT COUNT(*) FROM temp_meseros_dia"))).scalar()
    if not hay:
        raise HTTPException(status_code=409, detail=sin_meseros())
    if not (await tmp.execute(text("SELECT COUNT(*) FROM temp_meseros_dia WHERE cod_empleado = :c"),
                              {"c": cod})).scalar():
        raise HTTPException(status_code=422, detail=f"Ese {t('mesero')} no está en los {t('meseros')} del día. Actualice la lista.")


def sin_meseros() -> str:
    return f"En caja no han registrado los {t('meseros')} del día. Pida que los agreguen para poder montar pedidos."


async def nombres(emp: AsyncSession, tmp: AsyncSession, codigos: set[int]) -> dict[int, str]:
    """Nombre de cada código: primero los del día; si ya no está (pedido de ayer, usuario del
    dispositivo en pedidos anteriores) se busca en meseros de la empresa."""
    codigos = {int(c) for c in codigos if c}
    if not codigos:
        return {}
    lista = ", ".join(str(c) for c in codigos)          # enteros: sin riesgo de inyección
    salida = {int(c): (n or "").strip() for c, n in (await tmp.execute(text(
        f"SELECT cod_empleado, nombres FROM temp_meseros_dia WHERE cod_empleado IN ({lista})"))).all()}
    faltan = codigos - set(salida)
    if faltan:
        lista = ", ".join(str(c) for c in faltan)
        salida.update({int(c): (n or "").strip() for c, n in (await emp.execute(text(
            f"SELECT cod_empleado, nombres FROM meseros WHERE cod_empleado IN ({lista})"))).all()})
    return salida
