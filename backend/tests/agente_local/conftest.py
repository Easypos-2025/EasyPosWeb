"""
Pruebas del Agente Local contra BD de prueba propias (nunca contra los datos reales):
  ag_test_emp  ← estructura de la BD de empresa (maduritos)
  ag_test_tmp  ← estructura de datatemppos
Requiere el MySQL/MariaDB local con maduritos y datatemppos.
Correr desde backend/:  ..\\venv\\Scripts\\python -m pytest tests/agente_local -q
"""
import os

import pymysql
import pytest

MYSQL = dict(host="localhost", user="root", password="123456", autocommit=True,
             init_command="SET SESSION sql_mode='NO_ENGINE_SUBSTITUTION'")
ORIGEN_EMP, ORIGEN_TMP = "maduritos", "datatemppos"
BD_EMP, BD_TMP = "ag_test_emp", "ag_test_tmp"

TABLAS_EMP = ["registro_dispositivos", "empleados", "meseros",
              "platos", "categoria_platos", "plato_impresoras", "impresoras", "novedades_categorias",
              "lista_precios_cliente", "clientes", "mesas", "zonas_asientos", "configuracion_facturacion",
              "variables_del_sistema", "inventario_porciones_plato", "plato_producto",
              "plato_armar", "plato_armar_detalle", "menu_diario", "inventario_porciones", "categoria_productos",
              "configuracion_sede", "configuracion_tamano_letra"]
TABLAS_TMP = ["temp_registro_dispositivos", "temp_empleados", "temp_meseros",
              "temp_variables_del_sistema", "temp_comanda", "temp_detalle_comanda", "temp_detalle_comanda_parcial",
              "temp_plato_producto", "temp_plato_producto_parcial", "temp_novedades_plato_pedido", "temp_mesa_abierta",
              "temp_plato_armar_menu", "temp_menu_diario", "temp_plato_armar_origen",
              "temp_plato_armar_detalle_origen", "temp_inventario_porciones", "temp_categoria_productos",
              "temp_mesas", "temp_zonas_asientos"]

os.environ["AG_DB_EMPRESA_URL"] = f"mysql+aiomysql://root:123456@localhost/{BD_EMP}"
os.environ["AG_DB_TEMP_URL"] = f"mysql+aiomysql://root:123456@localhost/{BD_TMP}"
os.environ["AG_SECRETO"] = "secreto-de-pruebas-del-agente-local-0123456789"


def _preparar_bds():
    con = pymysql.connect(**MYSQL)
    with con.cursor() as c:
        for bd, origen, tablas in ((BD_EMP, ORIGEN_EMP, TABLAS_EMP), (BD_TMP, ORIGEN_TMP, TABLAS_TMP)):
            c.execute(f"DROP DATABASE IF EXISTS {bd}")
            c.execute(f"CREATE DATABASE {bd} CHARACTER SET latin1")
            for t in tablas:
                c.execute(f"CREATE TABLE {bd}.{t} LIKE {origen}.{t}")
    con.close()


_preparar_bds()


@pytest.fixture(scope="session")
def db():
    con = pymysql.connect(**MYSQL, cursorclass=pymysql.cursors.DictCursor)
    yield con
    con.close()


@pytest.fixture(scope="session")
def cliente():
    from fastapi.testclient import TestClient

    from agente_local.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def limpiar(db, cliente):
    with db.cursor() as c:
        for t in TABLAS_EMP:
            c.execute(f"DELETE FROM {BD_EMP}.{t}")
        for t in TABLAS_TMP + ["ag_dispositivos", "ag_auditoria", "ag_bloqueo_mesa"]:
            c.execute(f"DELETE FROM {BD_TMP}.{t}")
    yield


def activar_en_escritorio(db, usuario: str, activo: int = 1):
    """Simula el botón del escritorio: pasa el dispositivo a registro_dispositivos de la
    empresa y crea el mesero, tal como hace el programa VB6."""
    with db.cursor() as c:
        c.execute(f"SELECT * FROM {BD_TMP}.temp_registro_dispositivos WHERE Usuario=%s", (usuario,))
        t = c.fetchone()
        c.execute(f"DELETE FROM {BD_EMP}.registro_dispositivos WHERE Usuario=%s", (usuario,))
        c.execute(f"""INSERT INTO {BD_EMP}.registro_dispositivos
                      (Nombre_Dispositivo, Usuario, Contrasena, Activo, Fecha_Activacion, Cod_Empleado)
                      VALUES (%s,%s,%s,%s,%s,%s)""",
                  (t["Nombre_Dispositivo"], usuario, t["Contrasena"], activo, t["Fecha_Activacion"], t["Cod_Empleado"]))
        c.execute(f"REPLACE INTO {BD_EMP}.meseros (cod_empleado, nombres, clave, estado, tipo_empleado) "
                  f"VALUES (%s,%s,%s,%s,2)", (t["Cod_Empleado"], usuario.upper(), t["Contrasena"], activo))
