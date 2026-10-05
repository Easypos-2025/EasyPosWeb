"""
Agentes Locales en la nube (app/routers/agentes_locales_router.py) contra la BD local de
desarrollo (easyposweb). Usa empresas de prueba temporales y las borra al terminar.
Correr desde backend/:  ..\\venv\\Scripts\\python -m pytest tests/nube -q
"""
import hashlib

import pymysql
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user, require_sysadmin
from app.auth.tenant import tenant_guard
from app.routers.agentes_locales_router import router_admin, router_agente, router_empresa

BD = dict(host="localhost", user="root", password="123456", database="easyposweb", autocommit=True,
          init_command="SET SESSION sql_mode='NO_ENGINE_SUBSTITUTION'")   # datos de prueba mínimos
EMP_A, EMP_B = 990001, 990002


class _Sysadmin:
    id = 1


class _Usuario:
    """Usuario de la empresa efectiva (la resuelve el servidor; aquí se fija para la prueba)."""
    id = 2
    company_id = EMP_A


@pytest.fixture(scope="module")
def db():
    con = pymysql.connect(**BD, cursorclass=pymysql.cursors.DictCursor)
    with con.cursor() as c:
        for e in (EMP_A, EMP_B):
            c.execute("DELETE FROM company_local_agents WHERE company_id=%s", (e,))
            c.execute("DELETE FROM pos_dishes WHERE company_id=%s", (e,))
            c.execute("DELETE FROM companies WHERE id_company=%s", (e,))
            c.execute("INSERT INTO companies (id_company, name, identification_number) VALUES (%s, %s, %s)",
                      (e, f"PRUEBA AGENTE {e}", str(e)))
        c.execute("INSERT INTO pos_dishes (id, company_id, name, price, photo_path) VALUES "
                  "(501, %s, 'CON FOTO WEB', 1000, 'https://cdn.ejemplo.com/dishes/1/501.webp'),"
                  "(502, %s, 'FOTO DEL ESCRITORIO', 1000, 'aji.jpg'),"
                  "(504, %s, 'FOTO EN EL SERVIDOR', 1000, '/uploads/dishes/1/504_ab12.webp'),"
                  "(503, %s, 'DE OTRA EMPRESA', 1000, 'https://cdn.ejemplo.com/otra.webp')", (EMP_A, EMP_A, EMP_A, EMP_B))
    yield con
    with con.cursor() as c:
        for e in (EMP_A, EMP_B):
            c.execute("DELETE FROM company_local_agents WHERE company_id=%s", (e,))
            c.execute("DELETE FROM pos_dishes WHERE company_id=%s", (e,))
            c.execute("DELETE FROM companies WHERE id_company=%s", (e,))
    con.close()


@pytest.fixture(scope="module")
def cliente(db):
    app = FastAPI()
    app.include_router(router_admin)
    app.include_router(router_agente)
    app.include_router(router_empresa)
    app.dependency_overrides[require_sysadmin] = lambda: _Sysadmin()
    app.dependency_overrides[get_current_user] = lambda: _Usuario()
    app.dependency_overrides[tenant_guard] = lambda: None
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def claves(cliente):
    a = cliente.post("/api/agentes-locales", json={"company_id": EMP_A, "codigo": "T990001"}).json()["clave"]
    b = cliente.post("/api/agentes-locales", json={"company_id": EMP_B, "codigo": "T990002"}).json()["clave"]
    return a, b


def test_crear_guarda_solo_hash(cliente, db, claves):
    a, _ = claves
    assert a.startswith("ag_") and len(a) > 40
    with db.cursor() as c:
        c.execute("SELECT clave_hash, clave_prefijo FROM company_local_agents WHERE company_id=%s", (EMP_A,))
        fila = c.fetchone()
    assert fila["clave_hash"] == hashlib.sha256(a.encode()).hexdigest() and fila["clave_prefijo"] == a[:8]
    lista = {x["company_id"]: x for x in cliente.get("/api/agentes-locales").json()}
    assert "clave_hash" not in lista[EMP_A] and lista[EMP_A]["codigo"] == "T990001"


def test_no_duplica_empresa_ni_codigo(cliente, claves):
    assert cliente.post("/api/agentes-locales", json={"company_id": EMP_A, "codigo": "OTRO"}).status_code == 409
    assert cliente.post("/api/agentes-locales", json={"company_id": 123456789, "codigo": "X1"}).status_code == 404
    assert cliente.post("/api/agentes-locales", json={"company_id": EMP_A, "codigo": "a b"}).status_code == 422


def test_latido_actualiza_contacto(cliente, claves):
    a, _ = claves
    r = cliente.post("/api/agente/latido", headers={"X-Agente-Clave": a},
                     json={"url_local": "http://192.168.1.2:8090", "ip_local": "192.168.1.2", "version": "0.1.0"})
    assert r.status_code == 200 and r.json()["codigo"] == "T990001"
    ag = {x["company_id"]: x for x in cliente.get("/api/agentes-locales").json()}[EMP_A]
    assert ag["url_local"] == "http://192.168.1.2:8090" and ag["en_linea"] is True
    # Una URL con ruta o esquema raro no se guarda
    cliente.post("/api/agente/latido", headers={"X-Agente-Clave": a}, json={"url_local": "javascript:alert(1)"})
    assert {x["company_id"]: x for x in cliente.get("/api/agentes-locales").json()}[EMP_A]["url_local"] is None


def test_clave_invalida(cliente, claves):
    assert cliente.post("/api/agente/latido", json={}).status_code == 401
    assert cliente.post("/api/agente/latido", headers={"X-Agente-Clave": "ag_falsa"}, json={}).status_code == 401
    assert cliente.get("/api/agente/fotos-platos", headers={"X-Agente-Clave": "x" * 200}).status_code == 401


def test_fotos_solo_de_su_empresa(cliente, claves):
    a, b = claves
    fotos = cliente.get("/api/agente/fotos-platos", headers={"X-Agente-Clave": a}).json()
    # La de Spaces y la del servidor (/uploads, con el dominio público); ni la del escritorio ni la de otra empresa
    assert sorted(f["id_plato"] for f in fotos) == [501, 504]
    assert next(f for f in fotos if f["id_plato"] == 504)["url"] == "https://easyposweb.com/uploads/dishes/1/504_ab12.webp"
    assert [f["id_plato"] for f in cliente.get("/api/agente/fotos-platos", headers={"X-Agente-Clave": b}).json()] == [503]


def test_errores_al_monitor(cliente, claves):
    a, _ = claves
    r = cliente.post("/api/agente/errores", headers={"X-Agente-Clave": a}, json={"eventos": [
        {"origen": "dispositivo", "tipo": "RED", "nivel": "ADVERTENCIA", "titulo": "Sin conexión con la caja",
         "dispositivo": "Celular Ana", "ocurrencias": 3}]})
    assert r.status_code == 200 and r.json()["refs"][0].startswith("ERR-")
    assert cliente.post("/api/agente/errores", headers={"X-Agente-Clave": a},
                        json={"eventos": [{"titulo": "x", "tipo": "SEGURIDAD"}]}).status_code == 422


def test_regenerar_y_desactivar(cliente, claves):
    a, _ = claves
    ag = {x["company_id"]: x for x in cliente.get("/api/agentes-locales").json()}[EMP_A]
    nueva = cliente.post(f"/api/agentes-locales/{ag['id']}/clave").json()["clave"]
    assert cliente.post("/api/agente/latido", headers={"X-Agente-Clave": a}, json={}).status_code == 401
    assert cliente.post("/api/agente/latido", headers={"X-Agente-Clave": nueva}, json={}).status_code == 200
    cliente.patch(f"/api/agentes-locales/{ag['id']}", json={"activo": False})
    assert cliente.post("/api/agente/latido", headers={"X-Agente-Clave": nueva}, json={}).status_code == 401


def test_dashboard_empresa_ve_solo_su_agente(cliente, claves):
    a, _ = claves
    ag = {x["company_id"]: x for x in cliente.get("/api/agentes-locales").json()}[EMP_A]
    cliente.patch(f"/api/agentes-locales/{ag['id']}", json={"activo": True})
    nueva = cliente.post(f"/api/agentes-locales/{ag['id']}/clave").json()["clave"]
    cliente.post("/api/agente/latido", headers={"X-Agente-Clave": nueva}, json={})        # sin dirección aún
    assert cliente.get("/api/mi-agente-local/qr.png").status_code == 404
    cliente.post("/api/agente/latido", headers={"X-Agente-Clave": nueva},
                 json={"url_local": "http://192.168.1.50:8090", "version": "0.1.0"})
    d = cliente.get("/api/mi-agente-local").json()
    assert d["existe"] and d["url_local"] == "http://192.168.1.50:8090" and d["en_linea"]
    r = cliente.get("/api/mi-agente-local/qr.png")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    _Usuario.company_id = 123456789                     # empresa sin agente
    assert cliente.get("/api/mi-agente-local").json() == {"existe": False}
    _Usuario.company_id = EMP_A
    cliente.patch(f"/api/agentes-locales/{ag['id']}", json={"activo": False})
    assert cliente.get("/api/mi-agente-local").json() == {"existe": False}


# ───────────── versiones y actualización de las sedes ─────────────

def test_versiones_descarga_y_vigente(cliente, db, claves, tmp_path, monkeypatch):
    from app.routers import agentes_locales_router as r
    monkeypatch.setattr(r, "DIR_DESCARGAS", tmp_path)
    (tmp_path / "agente-v1.zip").write_bytes(b"version uno")
    (tmp_path / "agente-v2.zip").write_bytes(b"version dos")
    (tmp_path.parent / "secreto.txt").write_text("no")
    with db.cursor() as c:
        c.execute("DELETE FROM agente_versiones WHERE version IN ('t-v1','t-v2')")
        c.execute("INSERT INTO agente_versiones (version, archivo, sha256, tamano, vigente) VALUES "
                  "('t-v1','agente-v1.zip',%s,11,0),('t-v2','agente-v2.zip',%s,11,1)",
                  (hashlib.sha256(b"version uno").hexdigest(), hashlib.sha256(b"version dos").hexdigest()))
    _, b = claves
    h = {"X-Agente-Clave": b}
    d = cliente.post("/api/agente/latido", headers=h, json={"version": "t-v1", "actualizacion": "OK t-v0 → t-v1"}).json()
    assert d["version_vigente"]["version"] == "t-v2" and d["version_vigente"]["sha256"] == hashlib.sha256(b"version dos").hexdigest()
    ag = {x["company_id"]: x for x in cliente.get("/api/agentes-locales").json()}[EMP_B]
    assert ag["al_dia"] is False and ag["version_vigente"] == "t-v2" and ag["actualizacion"] == "OK t-v0 → t-v1"
    r2 = cliente.get("/api/agente/descarga/t-v2", headers=h)
    assert r2.status_code == 200 and r2.content == b"version dos"
    assert cliente.get("/api/agente/descarga/t-v2").status_code == 401                        # sin clave
    assert cliente.get("/api/agente/descarga/no-existe", headers=h).status_code == 404
    assert cliente.get("/api/agente/descarga/..%2Fsecreto.txt", headers=h).status_code == 404
    # Volver a la versión anterior
    v1 = next(v for v in cliente.get("/api/agentes-locales/versiones").json() if v["version"] == "t-v1")
    assert cliente.post(f"/api/agentes-locales/versiones/{v1['id']}/vigente").status_code == 200
    assert cliente.post("/api/agente/latido", headers=h, json={}).json()["version_vigente"]["version"] == "t-v1"
    with db.cursor() as c:
        c.execute("DELETE FROM agente_versiones WHERE version IN ('t-v1','t-v2')")
