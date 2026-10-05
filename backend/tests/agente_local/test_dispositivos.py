"""Registro, activación e ingreso de dispositivos del Agente Local."""
from conftest import BD_EMP, BD_TMP, activar_en_escritorio

REG = {"nombre_dispositivo": "Celular Ana", "usuario": "ana", "clave": "4321"}


def _registrar(cliente, **cambios):
    return cliente.post("/api/ag/dispositivos/registro", json={**REG, **cambios})


def _ingresar(cliente, usuario="ana", clave="4321"):
    return cliente.post("/api/ag/sesion/ingresar", json={"usuario": usuario, "clave": clave})


def _fila(db, sql, *p):
    with db.cursor() as c:
        c.execute(sql, p)
        return c.fetchone()


# ───────────── base ─────────────

def test_salud_y_encabezados(cliente):
    r = cliente.get("/api/ag/salud")
    assert r.status_code == 200 and r.json()["ok"] is True
    # Dirección por el nombre del PC (no cambia con la IP): http://NOMBRE:PUERTO
    import re, socket
    from agente_local import config
    assert r.json()["pc"] == f"http://{socket.gethostname().split('.')[0]}:{config.PUERTO}"
    assert re.fullmatch(r"http://[A-Za-z0-9_-]+:\d+", r.json()["pc"])
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Cache-Control"] == "no-store"
    assert "server" not in {k.lower() for k in r.headers}


def test_sin_documentacion_publica(cliente):
    for ruta in ("/docs", "/redoc", "/openapi.json"):
        assert cliente.get(ruta).status_code == 404


def test_cuerpo_demasiado_grande(cliente):
    r = cliente.post("/api/ag/sesion/ingresar", content=b"x" * 70_000,
                     headers={"content-type": "application/json"})
    assert r.status_code == 413


# ───────────── registro ─────────────

def test_registro_crea_filas_como_la_app_anterior(cliente, db):
    r = _registrar(cliente)
    assert r.status_code == 200
    d = r.json()
    assert d["estado"] == "pendiente" and len(d["secreto"]) >= 40

    t = _fila(db, f"SELECT * FROM {BD_TMP}.temp_registro_dispositivos WHERE Usuario='ana'")
    assert t["Activo"] == 0 and t["Nombre_Dispositivo"] == "Celular Ana"
    assert t["Cod_Empleado"] == d["cod_empleado"] and 10000 <= t["Cod_Empleado"] <= 99999
    # La clave real nunca queda en la tabla del escritorio
    assert t["Contrasena"] != "4321" and len(t["Contrasena"]) == 25

    a = _fila(db, f"SELECT * FROM {BD_TMP}.ag_dispositivos WHERE usuario='ana'")
    assert a["clave_hash"].startswith("$2") and "4321" not in a["clave_hash"]
    assert a["secreto_hash"] != d["secreto"]


def test_codigo_empleado_no_choca(cliente, db):
    with db.cursor() as c:
        c.execute(f"INSERT INTO {BD_EMP}.meseros (cod_empleado, nombres, estado) VALUES (55555,'X',1)")
    cod = _registrar(cliente).json()["cod_empleado"]
    assert cod != 55555


def test_registro_duplicado(cliente, db):
    assert _registrar(cliente).status_code == 200
    assert _registrar(cliente, nombre_dispositivo="Otro").status_code == 409          # mismo usuario
    assert _registrar(cliente, usuario="pedro").status_code == 409                     # mismo nombre
    activar_en_escritorio(db, "ana")
    with db.cursor() as c:
        c.execute(f"DELETE FROM {BD_TMP}.temp_registro_dispositivos")
        c.execute(f"DELETE FROM {BD_TMP}.ag_dispositivos")
    assert _registrar(cliente, nombre_dispositivo="Otro").status_code == 409          # ya en el escritorio


def test_registro_rechaza_comodines_y_basura(cliente):
    for malo in ({"usuario": "%"}, {"usuario": "a' OR 1=1 --"}, {"usuario": "ab"},
                 {"nombre_dispositivo": "<script>"}, {"nombre_dispositivo": "x/../y"}, {"clave": "12"}):
        r = _registrar(cliente, **malo)
        assert r.status_code == 422, malo
        assert "loc" not in r.text      # no expone el detalle de validación


def test_registro_limite_por_ip(cliente):
    for i in range(5):
        assert _registrar(cliente, usuario=f"user{i}", nombre_dispositivo=f"Cel {i}").status_code == 200
    assert _registrar(cliente, usuario="user9", nombre_dispositivo="Cel 9").status_code == 429


def test_registro_limite_pendientes(cliente, db):
    with db.cursor() as c:
        for i in range(20):
            c.execute(f"INSERT INTO {BD_TMP}.temp_registro_dispositivos (Nombre_Dispositivo, Usuario, Activo) "
                      f"VALUES (%s,%s,0)", (f"P{i}", f"p{i}"))
    assert _registrar(cliente).status_code == 429


# ───────────── activación ─────────────

def test_estado_pendiente_y_activo(cliente, db):
    secreto = _registrar(cliente).json()["secreto"]
    h = {"X-Ag-Dispositivo": secreto}
    assert cliente.get("/api/ag/dispositivos/estado", headers=h).json()["estado"] == "pendiente"
    activar_en_escritorio(db, "ana")
    assert cliente.get("/api/ag/dispositivos/estado", headers=h).json()["estado"] == "activo"


def test_estado_con_secreto_falso(cliente):
    _registrar(cliente)
    assert cliente.get("/api/ag/dispositivos/estado", headers={"X-Ag-Dispositivo": "falso"}).status_code == 401
    assert cliente.get("/api/ag/dispositivos/estado").status_code == 401


# ───────────── ingreso ─────────────

def test_ingreso_pendiente_no_da_token(cliente):
    _registrar(cliente)
    d = _ingresar(cliente).json()
    assert d["estado"] == "pendiente" and "token" not in d and d["secreto"]


def test_ingreso_activo(cliente, db):
    _registrar(cliente)
    activar_en_escritorio(db, "ana")
    d = _ingresar(cliente).json()
    assert d["estado"] == "activo" and d["token"]
    assert d["mesero"]["nombre"] == "ANA"
    yo = cliente.get("/api/ag/sesion/yo", headers={"Authorization": f"Bearer {d['token']}"})
    assert yo.status_code == 200 and yo.json()["cod_empleado"] == d["mesero"]["cod_empleado"]


def test_ingreso_clave_mala_y_limite(cliente, db):
    _registrar(cliente)
    activar_en_escritorio(db, "ana")
    for _ in range(5):
        assert _ingresar(cliente, clave="mala").status_code == 401
    # Bloqueado aunque ahora use la clave correcta
    assert _ingresar(cliente).status_code == 429


def test_ingreso_sin_like(cliente, db):
    _registrar(cliente)
    activar_en_escritorio(db, "ana")
    assert _ingresar(cliente, usuario="%", clave="%").status_code == 422
    assert _ingresar(cliente, usuario="an_", clave="4321").status_code == 401
    assert _ingresar(cliente, usuario="ana", clave="%").status_code == 401


def test_usuario_inexistente_misma_respuesta(cliente):
    r = _ingresar(cliente, usuario="nadie", clave="1234")
    assert r.status_code == 401 and r.json()["detail"] == "Usuario o clave incorrectos."


# ───────────── sesión ─────────────

def test_nuevo_ingreso_invalida_sesion_anterior(cliente, db):
    _registrar(cliente)
    activar_en_escritorio(db, "ana")
    t1 = _ingresar(cliente).json()["token"]
    t2 = _ingresar(cliente).json()["token"]
    assert cliente.get("/api/ag/sesion/yo", headers={"Authorization": f"Bearer {t1}"}).status_code == 401
    assert cliente.get("/api/ag/sesion/yo", headers={"Authorization": f"Bearer {t2}"}).status_code == 200


def test_salir_invalida_token(cliente, db):
    _registrar(cliente)
    activar_en_escritorio(db, "ana")
    h = {"Authorization": f"Bearer {_ingresar(cliente).json()['token']}"}
    assert cliente.post("/api/ag/sesion/salir", headers=h).status_code == 200
    assert cliente.get("/api/ag/sesion/yo", headers=h).status_code == 401


def test_desactivar_en_escritorio_corta_sesion(cliente, db):
    _registrar(cliente)
    activar_en_escritorio(db, "ana")
    h = {"Authorization": f"Bearer {_ingresar(cliente).json()['token']}"}
    with db.cursor() as c:
        c.execute(f"UPDATE {BD_EMP}.registro_dispositivos SET Activo=0 WHERE Usuario='ana'")
    assert cliente.get("/api/ag/sesion/yo", headers=h).status_code == 403


def test_token_alterado_o_ajeno(cliente, db):
    from jose import jwt
    _registrar(cliente)
    activar_en_escritorio(db, "ana")
    token = _ingresar(cliente).json()["token"]
    assert cliente.get("/api/ag/sesion/yo", headers={"Authorization": f"Bearer {token[:-3]}abc"}).status_code == 401
    falso = jwt.encode({"typ": "ag", "sub": "1", "dsp": 1, "ver": 1}, "otra-clave", algorithm="HS256")
    assert cliente.get("/api/ag/sesion/yo", headers={"Authorization": f"Bearer {falso}"}).status_code == 401
    assert cliente.get("/api/ag/sesion/yo").status_code == 401


def test_revocado(cliente, db):
    _registrar(cliente)
    activar_en_escritorio(db, "ana")
    with db.cursor() as c:
        c.execute(f"UPDATE {BD_TMP}.ag_dispositivos SET revocado=1")
    assert _ingresar(cliente).status_code == 403


# ───────────── dispositivos de la app anterior ─────────────

def test_adopcion_dispositivo_app_anterior(cliente, db):
    with db.cursor() as c:
        c.execute(f"""INSERT INTO {BD_EMP}.registro_dispositivos
                      (Nombre_Dispositivo, Usuario, Contrasena, Activo, Fecha_Activacion, Cod_Empleado)
                      VALUES ('M2102J20SG','essypos','1231',1,'2026-01-01',618)""")
        c.execute(f"INSERT INTO {BD_EMP}.meseros (cod_empleado, nombres, estado) VALUES (618,'essypos',1)")
    assert _ingresar(cliente, "essypos", "9999").status_code == 401
    d = _ingresar(cliente, "essypos", "1231").json()
    assert d["estado"] == "activo" and d["mesero"]["cod_empleado"] == 618
    # La fila del escritorio no se toca (la app anterior sigue funcionando)
    assert _fila(db, f"SELECT Contrasena FROM {BD_EMP}.registro_dispositivos WHERE Usuario='essypos'")["Contrasena"] == "1231"
    # Desde ahora vale la clave cifrada del agente
    assert _ingresar(cliente, "essypos", "1231").json()["estado"] == "activo"
