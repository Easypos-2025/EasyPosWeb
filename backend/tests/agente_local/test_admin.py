"""Panel de administración local, errores de dispositivos y comunicación con la nube (simulada)."""
import pytest
from conftest import BD_EMP, BD_TMP, activar_en_escritorio

E, T = BD_EMP, BD_TMP


def _sql(db, *sentencias):
    with db.cursor() as c:
        for s in sentencias:
            c.execute(s)


def _filas(db, sql, *p):
    with db.cursor() as c:
        c.execute(sql, p)
        return c.fetchall()


@pytest.fixture
def admin(cliente, db):
    """Fija la clave de administrador como lo hace el instalador y devuelve el encabezado."""
    from agente_local.seguridad import cifrar_clave
    _sql(db, f"INSERT INTO {T}.ag_config (clave, valor) VALUES ('clave_admin', '{cifrar_clave('Admin123')}'), ('admin_version', '1')")
    token = cliente.post("/api/ag/admin/ingresar", json={"clave": "Admin123"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mesero(cliente, db):
    cliente.post("/api/ag/dispositivos/registro", json={"nombre_dispositivo": "Cel Ana", "usuario": "ana", "clave": "4321"})
    activar_en_escritorio(db, "ana")
    t = cliente.post("/api/ag/sesion/ingresar", json={"usuario": "ana", "clave": "4321"}).json()["token"]
    return {"Authorization": f"Bearer {t}"}


# ───────────── clave y sesión de administrador ─────────────

def test_sin_clave_configurada(cliente):
    r = cliente.post("/api/ag/admin/ingresar", json={"clave": "x"})
    assert r.status_code == 409 and "instalador" in r.json()["detail"]


def test_ingreso_admin_y_limite(cliente, db, admin):
    assert cliente.get("/api/ag/admin/resumen", headers=admin).status_code == 200
    assert cliente.get("/api/ag/admin/resumen").status_code == 401
    for _ in range(5):
        assert cliente.post("/api/ag/admin/ingresar", json={"clave": "mala"}).status_code == 401
    assert cliente.post("/api/ag/admin/ingresar", json={"clave": "Admin123"}).status_code == 429


def test_token_de_mesero_no_sirve_en_admin(cliente, admin, mesero):
    assert cliente.get("/api/ag/admin/resumen", headers=mesero).status_code == 401


def test_admin_no_sirve_como_mesero(cliente, admin):
    assert cliente.get("/api/ag/pedidos", headers=admin).status_code == 401


def test_cambiar_clave_invalida_sesiones(cliente, admin):
    assert cliente.post("/api/ag/admin/clave", headers=admin, json={"actual": "mala", "nueva": "Nueva123"}).status_code == 400
    r = cliente.post("/api/ag/admin/clave", headers=admin, json={"actual": "Admin123", "nueva": "Nueva123"})
    assert r.status_code == 200
    assert cliente.get("/api/ag/admin/resumen", headers=admin).status_code == 401          # la sesión vieja cae
    assert cliente.get("/api/ag/admin/resumen", headers={"Authorization": f"Bearer {r.json()['token']}"}).status_code == 200
    assert cliente.post("/api/ag/admin/ingresar", json={"clave": "Nueva123"}).status_code == 200


# ───────────── dispositivos ─────────────

def test_latido_y_estado_de_dispositivos(cliente, db, admin, mesero):
    r = cliente.post("/api/ag/sesion/latido", headers=mesero)
    assert r.status_code == 200 and r.json()["pc"].startswith("http://")
    assert r.json()["actualizacion"]["lista"] is False                     # sin versión nueva, sin aviso
    # Actualizar desde un dispositivo: solo la versión vigente publicada (aquí no hay ninguna)
    assert cliente.post("/api/ag/actualizar", headers=mesero).status_code == 409
    assert cliente.post("/api/ag/actualizar").status_code == 401
    d = cliente.get("/api/ag/admin/dispositivos", headers=admin).json()["dispositivos"]
    assert d[0]["nombre_dispositivo"] == "Cel Ana" and d[0]["conectado"] is True and d[0]["activo_escritorio"] is True
    _sql(db, f"UPDATE {T}.ag_dispositivos SET ultimo_acceso = NOW() - INTERVAL 5 MINUTE")
    assert cliente.get("/api/ag/admin/dispositivos", headers=admin).json()["dispositivos"][0]["conectado"] is False
    r = cliente.get("/api/ag/admin/resumen", headers=admin).json()
    assert r["dispositivos"]["total"] == 1 and r["dispositivos"]["conectados"] == 0


def test_bloquear_dispositivo_corta_su_sesion(cliente, admin, mesero):
    id_disp = cliente.get("/api/ag/admin/dispositivos", headers=admin).json()["dispositivos"][0]["id"]
    assert cliente.post(f"/api/ag/admin/dispositivos/{id_disp}/bloquear", headers=admin).status_code == 200
    assert cliente.get("/api/ag/pedidos", headers=mesero).status_code == 401
    assert cliente.post("/api/ag/sesion/ingresar", json={"usuario": "ana", "clave": "4321"}).status_code == 403
    cliente.post(f"/api/ag/admin/dispositivos/{id_disp}/habilitar", headers=admin)
    assert cliente.post("/api/ag/sesion/ingresar", json={"usuario": "ana", "clave": "4321"}).json()["estado"] == "activo"


# ───────────── errores ─────────────

def test_errores_del_dispositivo_se_agrupan(cliente, db, admin, mesero):
    ev = {"tipo": "RED", "nivel": "ADVERTENCIA", "titulo": "Sin conexión con la caja", "vista": "/pedido", "cuando": "10:42"}
    for _ in range(3):
        assert cliente.post("/api/ag/errores", headers=mesero, json={"eventos": [ev]}).status_code == 200
    # sin sesión también se acepta (la sesión pudo vencerse mientras no había conexión)
    assert cliente.post("/api/ag/errores", json={"eventos": [ev]}).status_code == 200
    errs = cliente.get("/api/ag/admin/errores", headers=admin).json()
    assert len(errs) == 1 and errs[0]["ocurrencias"] == 4 and errs[0]["origen"] == "dispositivo"
    assert "Cel Ana" in errs[0]["dispositivo"] or "IP" in errs[0]["dispositivo"]
    r = cliente.get("/api/ag/admin/resumen", headers=admin).json()["errores"]
    assert r["sin_resolver"] == 1 and r["conexion"] == 1


def test_errores_dispositivo_validacion_y_limite(cliente):
    assert cliente.post("/api/ag/errores", json={"eventos": [{"tipo": "SEGURIDAD", "titulo": "x"}]}).status_code == 422
    assert cliente.post("/api/ag/errores", json={"eventos": []}).status_code == 422
    for _ in range(30):
        cliente.post("/api/ag/errores", json={"eventos": [{"titulo": "spam"}]})
    assert cliente.post("/api/ag/errores", json={"eventos": [{"titulo": "spam"}]}).json()["registrados"] == 0


def test_resolver_y_regresion(cliente, admin):
    cliente.post("/api/ag/errores", json={"eventos": [{"titulo": "Falla en carta", "vista": "/pedido"}]})
    e = cliente.get("/api/ag/admin/errores", headers=admin).json()[0]
    assert cliente.post(f"/api/ag/admin/errores/{e['id']}/resolver", headers=admin, json={"nota": "x"}).status_code == 422
    assert cliente.post(f"/api/ag/admin/errores/{e['id']}/resolver", headers=admin, json={"nota": "Se reinició el router"}).status_code == 200
    assert cliente.get("/api/ag/admin/errores", headers=admin).json() == []
    assert cliente.get("/api/ag/admin/errores?estado=resueltos", headers=admin).json()[0]["nota"] == "Se reinició el router"
    # vuelve a ocurrir → se reabre como regresión
    cliente.post("/api/ag/errores", json={"eventos": [{"titulo": "Falla en carta", "vista": "/pedido"}]})
    e2 = cliente.get("/api/ag/admin/errores", headers=admin).json()[0]
    assert e2["id"] == e["id"] and e2["estado"] == "NUEVO" and e2["regresiones"] == 1


def test_error_interno_queda_registrado(cliente, db, admin, monkeypatch):
    from agente_local.routers import catalogo as rc

    async def falla(*a, **k):
        raise RuntimeError("fallo de prueba 123")
    monkeypatch.setattr(rc.catalogo, "categorias", falla)
    monkeypatch.setattr(cliente._transport, "raise_server_exceptions", False)   # ver el 500 como lo ve el celular
    cliente.post("/api/ag/dispositivos/registro", json={"nombre_dispositivo": "Cel Beto", "usuario": "beto", "clave": "9999"})
    activar_en_escritorio(db, "beto")
    t = cliente.post("/api/ag/sesion/ingresar", json={"usuario": "beto", "clave": "9999"}).json()["token"]
    r = cliente.get("/api/ag/catalogo", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 500 and "fallo de prueba" not in r.text            # sin detalles internos al cliente
    errs = cliente.get("/api/ag/admin/errores", headers=admin).json()
    assert errs[0]["origen"] == "agente" and "RuntimeError" in errs[0]["titulo"] and "Traceback" in errs[0]["detalle"]


# ───────────── nube (simulada) ─────────────

def test_enviar_errores_a_la_nube(cliente, db, admin, monkeypatch):
    from agente_local import nube
    enviados = []
    monkeypatch.setattr(nube, "_pedir", lambda metodo, ruta, cuerpo=None, timeout=15: enviados.append((ruta, cuerpo)) or {"ok": True})
    cliente.post("/api/ag/errores", json={"eventos": [{"titulo": "Uno"}, {"titulo": "Dos"}]})
    cliente.post("/api/ag/errores", json={"eventos": [{"titulo": "Uno"}]})
    n = cliente.portal.call(nube.enviar_errores)
    assert n == 2 and enviados[0][0] == "/api/agente/errores"
    ocurr = {e["titulo"]: e["ocurrencias"] for e in enviados[0][1]["eventos"]}
    assert ocurr == {"Uno": 2, "Dos": 1}
    assert cliente.portal.call(nube.enviar_errores) == 0                          # ya no hay pendientes


def test_sincronizar_fotos_de_la_web(cliente, db, admin, tmp_path, monkeypatch):
    from PIL import Image
    from agente_local import config, nube
    from agente_local.servicios import fotos_web
    _sql(db, f"INSERT INTO {E}.configuracion_sede (Id_Sede, Ruta_Foto_Productos) VALUES (1, '{str(tmp_path).replace(chr(92), chr(92) * 2)}')",
         f"INSERT INTO {E}.platos (Id_Plato, Nombre, Valor, Cod_Categoria, Activo, Ruta_Foto) VALUES "
         f"(700,'SIN FOTO',1000,1,0,''),(701,'CON FOTO LOCAL',1000,1,0,'propia.jpg')")
    monkeypatch.setattr(config, "NUBE_CLAVE", "ag_prueba")
    monkeypatch.setattr(nube, "_pedir", lambda *a, **k: [
        {"id_plato": 700, "url": "https://cdn/700.webp", "actualizado": "2026-10-04T10:00:00"},
        {"id_plato": 701, "url": "https://cdn/701.webp", "actualizado": "2026-10-04T10:00:00"},
        {"id_plato": 999, "url": "https://cdn/999.webp", "actualizado": None},              # no existe en el escritorio
        {"id_plato": 700, "url": "http://inseguro/700.webp", "actualizado": None}])
    monkeypatch.setattr(fotos_web, "_descargar_jpg",
                        lambda url, destino: (url.startswith("https://") or (_ for _ in ()).throw(ValueError()))
                        and Image.new("RGB", (50, 50), "green").save(destino, "JPEG"))
    r = cliente.post("/api/ag/admin/fotos/sincronizar", headers=admin).json()
    assert r["descargadas"] == 2 and r["asignadas"] == 2 and r["fallidas"] == 1
    fotos = {f["Id_Plato"]: f["Ruta_Foto"] for f in _filas(db, f"SELECT Id_Plato, Ruta_Foto FROM {E}.platos WHERE Id_Plato IN (700,701)")}
    assert fotos == {700: "web_700.jpg", 701: "web_701.jpg"}                     # la web manda
    # Sin cambios en la web: no se vuelve a descargar ni a asignar
    r2 = cliente.post("/api/ag/admin/fotos/sincronizar", headers=admin).json()
    assert r2["asignadas"] == 0
    assert (tmp_path / "web_700.jpg").exists() and (tmp_path / "web_701.jpg").exists()


def test_sincronizar_fotos_sin_clave(cliente, admin):
    assert cliente.post("/api/ag/admin/fotos/sincronizar", headers=admin).status_code == 409


# ───────────── cupo de dispositivos y eliminar ─────────────

def test_eliminar_dispositivo_libera_cupo(cliente, db, admin, mesero):
    _sql(db, f"CREATE TABLE IF NOT EXISTS {E}.configuracion_conexion LIKE maduritos.configuracion_conexion",
         f"DELETE FROM {E}.configuracion_conexion",
         f"INSERT INTO {E}.configuracion_conexion (Id_Sede, Dispositivos_Autorizados) VALUES (1, 1)")
    r = cliente.get("/api/ag/admin/dispositivos", headers=admin).json()
    assert (r["limite"], r["registrados"]) == (1, 1)
    # Cupo lleno: no se registran dispositivos nuevos
    nuevo = cliente.post("/api/ag/dispositivos/registro", json={"nombre_dispositivo": "Cel Nuevo", "usuario": "nuevo", "clave": "1234"})
    assert nuevo.status_code == 409 and "límite de 1" in nuevo.json()["detail"]
    # Eliminar el de Ana: sale del escritorio y del agente, su sesión cae, el mesero se conserva
    id_disp = r["dispositivos"][0]["id"]
    _sql(db, f"INSERT INTO {T}.temp_mesa_abierta (Id_Mesa, Mesa, Abierta, Abierta_Desde) VALUES (1,'S-01',1,'Cel Ana')",
         f"INSERT INTO {T}.ag_bloqueo_mesa (id_mesa, mesa, cod_empleado, id_dispositivo, desde, vence) "
         f"VALUES (1,'S-01',1,{id_disp},NOW(),NOW() + INTERVAL 5 MINUTE)")
    assert cliente.post(f"/api/ag/admin/dispositivos/{id_disp}/eliminar", headers=admin).status_code == 200
    assert _filas(db, f"SELECT * FROM {E}.registro_dispositivos WHERE Usuario='ana'") == ()
    assert _filas(db, f"SELECT * FROM {T}.temp_registro_dispositivos WHERE Usuario='ana'") == ()
    assert _filas(db, f"SELECT * FROM {T}.temp_mesa_abierta") == () and _filas(db, f"SELECT * FROM {T}.ag_bloqueo_mesa") == ()
    assert len(_filas(db, f"SELECT * FROM {E}.meseros WHERE nombres='ANA'")) == 1
    assert cliente.get("/api/ag/pedidos", headers=mesero).status_code == 401
    assert cliente.post("/api/ag/dispositivos/registro", json={"nombre_dispositivo": "Cel Nuevo", "usuario": "nuevo",
                                                                "clave": "1234"}).status_code == 200
    assert cliente.post("/api/ag/admin/dispositivos/999/eliminar", headers=admin).status_code == 404
    _sql(db, f"DROP TABLE {E}.configuracion_conexion")


def test_aviso_para_el_escritorio(cliente, db, monkeypatch):
    from agente_local import actualizador, config
    monkeypatch.setattr(config, "EMPAQUETADO", True)
    monkeypatch.setitem(actualizador.estado, "vigente", {"version": "26.10.09-zzz"})
    monkeypatch.setitem(actualizador.estado, "descargada", "26.10.09-zzz")
    cliente.portal.call(actualizador.publicar_aviso)
    avisos = {f["clave"]: f["valor"] for f in _filas(db, f"SELECT clave, valor FROM {T}.ag_config")}
    assert "26.10.09-zzz" in avisos["aviso_escritorio"] and "abrir turno" in avisos["aviso_escritorio"]
    monkeypatch.setitem(actualizador.estado, "vigente", None)
    cliente.portal.call(actualizador.publicar_aviso)
    assert _filas(db, f"SELECT valor FROM {T}.ag_config WHERE clave='aviso_escritorio'")[0]["valor"] == ""
