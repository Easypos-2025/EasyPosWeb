"""
Permisos del usuario de BD del agente en la BD de la EMPRESA (se revisan al arrancar).

El instalador crea el usuario con lectura en la BD de la empresa y solo los permisos de escritura de
PERMISOS_EMPRESA (misma lista en instalador_agente/instalador.py). El agente no se puede dar permisos a
sí mismo: si una sede se instaló con un instalador anterior, le faltan y lo que los usa (S2 eliminar /
cancelar desde la web, S3 catálogo de la web) fallaría sin aviso. Aquí se avisa en el panel del agente
y en el Monitor de Errores de la nube; se repara ejecutando de nuevo el instalador.
"""
import logging

from sqlalchemy import text

from . import errores
from .db import motor_empresa

log = logging.getLogger("agente_local")

# Tabla de la BD de la empresa → permisos de escritura que necesita el agente
PERMISOS_EMPRESA = {
    "registro_dispositivos": ("DELETE",),                    # eliminar dispositivos (cupo)
    "historico_comandas_eliminadas": ("INSERT", "UPDATE"),   # S2 cancelar cuenta
    "historico_detalle_comanda_eliminadas": ("INSERT",),     # S2 eliminar producto / cancelar
    "platos": ("INSERT", "UPDATE"),                          # S3 catálogo de la web (y fotos)
    "plato_impresoras": ("INSERT", "DELETE"),                # S3
    "configuracion_sede": ("INSERT", "UPDATE"),              # S3
}


async def faltantes() -> list[str]:
    """Permisos de PERMISOS_EMPRESA que el usuario no tiene (solo de tablas que existen)."""
    async with motor_empresa.connect() as conn:
        bd = (await conn.execute(text("SELECT DATABASE()"))).scalar()
        existen = {t for (t,) in (await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()"))).all()}
        # information_schema solo muestra los privilegios del usuario actual
        globales = {p for (p,) in (await conn.execute(text(
            "SELECT privilege_type FROM information_schema.user_privileges"))).all()}
        de_bd = {p for (s, p) in (await conn.execute(text(
            "SELECT table_schema, privilege_type FROM information_schema.schema_privileges"))).all()
            if s.replace("\\", "") == bd}
        de_tabla = {(t, p) for (t, p) in (await conn.execute(text(
            "SELECT table_name, privilege_type FROM information_schema.table_privileges WHERE table_schema = :b"),
            {"b": bd})).all()}
    falta = []
    for tabla, privilegios in PERMISOS_EMPRESA.items():
        if tabla not in existen:
            continue
        for p in privilegios:
            if p not in globales and p not in de_bd and (tabla, p) not in de_tabla:
                falta.append(f"{p} en {tabla}")
    return falta


async def revisar() -> None:
    """Al arrancar: avisa si faltan permisos. Nunca impide que el agente arranque."""
    try:
        falta = await faltantes()
    except Exception:
        log.exception("No se pudieron revisar los permisos de la base de datos")
        return
    if falta:
        log.warning("Faltan permisos de BD: %s", ", ".join(falta))
        await errores.registrar(
            origen="agente", tipo="BASE_DATOS", nivel="ADVERTENCIA",
            titulo="Faltan permisos de base de datos para la sincronización con la web",
            mensaje="Ejecute de nuevo el instalador del agente (EasyPosAgente-Setup.exe) en este PC para "
                    "actualizar los permisos. La toma de pedidos funciona normal.",
            detalle="Faltan: " + ", ".join(falta))
