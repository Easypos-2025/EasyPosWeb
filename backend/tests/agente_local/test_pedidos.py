"""Carta, mesas y pedidos del Agente Local contra datos de prueba con la forma del escritorio."""
import pytest
from conftest import BD_EMP, BD_TMP, activar_en_escritorio

E, T = BD_EMP, BD_TMP
FECHA_TURNO = "2026/10/03"      # fecha de negocio del turno (distinta a la del calendario)
LAURA, PEDRO = 601, 602         # meseros del día (temp_meseros_dia)


def _sql(db, *sentencias):
    with db.cursor() as c:
        for s in sentencias:
            c.execute(s)


def _filas(db, sql, *p):
    with db.cursor() as c:
        c.execute(sql, p)
        return c.fetchall()


@pytest.fixture
def datos(db):
    _sql(db,
         f"INSERT INTO {E}.configuracion_facturacion (Id_Sede, Paga_Impuesto, Precios_Incluyen_Impuesto) VALUES (1,0,0)",
         f"INSERT INTO {E}.variables_del_sistema (Id_Sede, Fecha, Pedir_Cantidad_Mod_Mesas) VALUES (1,'2026-10-04',1)",
         f"INSERT INTO {T}.temp_variables_del_sistema (Id_Sede, Fecha) VALUES (1,'{FECHA_TURNO}')",
         f"INSERT INTO {T}.temp_meseros_dia (cod_empleado, nombres, estado) VALUES ({LAURA},'LAURA',1),({PEDRO},'PEDRO',1)",
         f"INSERT INTO {E}.categoria_platos (Cod_Categoria, Nombre, Activa) VALUES (1,'COMIDAS',1),(2,'BEBIDAS',1),(3,'OCULTA',0)",
         # Activo = 0 es visible (invertido en el escritorio)
         f"""INSERT INTO {E}.platos (Id_Plato, Nombre, Valor, Cod_Categoria, Activo, Impuesto, Prioridad_Ofrecer,
                 Pedir_Valor_Venta_Producto, Pedir_Descripcion_Producto, Impresora) VALUES
             (10,'HAMBURGUESA',20000,1,0,8,0,0,0,''),
             (11,'GASEOSA',4000,2,0,0,0,0,0,''),
             (12,'PLATO OCULTO',1000,1,1,0,0,0,0,''),
             (13,'EN CATEGORIA INACTIVA',1000,3,0,0,0,0,0,''),
             (14,'VARIOS',0,1,0,0,0,1,1,''),
             (15,'ALMUERZO',15000,1,0,0,1,0,0,''),
             (16,'BOWL',18000,1,0,0,0,0,0,'COCINA'),
             (17,'DOLEX',2000,1,0,0,0,0,0,'')""",
         # Presentaciones: solo cuentan los productos con 2 o más (Activo = 0 es vigente)
         f"""INSERT INTO {E}.plato_producto (Id_Plato, Id_Forma_Medida, Unidades_Minimas, Valor_Presentacion, Descripcion, Activo) VALUES
             (17,2,1,2000,'UNIDAD',0),(17,57,10,18000,'BLISTER',0),(17,9,100,175000,'CAJA',0),(10,2,2,99999,'Unidad',0)""",
         f"INSERT INTO {E}.inventario_porciones_plato (Id_Plato, Id_Grupo, Id_Item, Cantidad, Porciones_A_Desccontar, Posicion, Opcion_Cambiar) VALUES (17,1,700,1,1,700,0)",
         f"INSERT INTO {E}.impresoras (Id_Impresora, Nombre, Activa) VALUES (1,'COCINA',1),(2,'BARRA',1)",
         f"INSERT INTO {E}.plato_impresoras (Id_Plato, Id_Impresora, Cant_Impresiones) VALUES (10,1,1),(10,2,1),(11,2,1),(14,1,1),(15,1,1)",
         f"INSERT INTO {E}.novedades_categorias (Id_Consecutivo, Cod_Categoria, Id_Novedad, Novedad) VALUES (1,1,1,'SIN CEBOLLA'),(2,1,2,'BIEN ASADA'),(3,2,3,'SIN HIELO')",
         f"INSERT INTO {E}.inventario_porciones_plato (Id_Plato, Id_Grupo, Id_Item, Cantidad, Porciones_A_Desccontar, Posicion, Opcion_Cambiar) VALUES (10,1,36,1,1,36,0),(10,1,1,1,20,1,0)",
         f"INSERT INTO {E}.clientes (Id_Cliente, cedula, nombres, Apellidos) VALUES (1,'222222222222','Consumidor','Final'),(194,'900123','DISTRIBUIDORA','CENTRO'),(195,'800_%','CLIENTE','RARO')",
         f"INSERT INTO {E}.lista_precios_cliente (id_lista, Id_Cliente, Id_Producto, Id_Presentacion, Precio_Producto, Activa) VALUES (3,194,10,1,15600,1),(3,194,11,1,3000,0)",
         # Zonas activas con TODAS sus mesas (mesas.Activa no filtra); TERRAZA está inactiva
         f"""INSERT INTO {E}.zonas_asientos (Id_Sede, Id_Zona, Ubicacion, Activa, Zona_Dinamica, Color, Altura) VALUES
             (1,1,'SALON',1,0,12648384,1200),(1,2,'CLIENTES',1,1,0,700),(1,3,'TERRAZA',0,0,0,700)""",
         f"""INSERT INTO {E}.mesas (Id_Mesa, Mesa, Ubicacion, Activa, Id_Zona) VALUES
             (1,'S-01','SALON',1,1),(2,'S-02','SALON',1,1),(3,'S-99','SALON',0,1),(5,'T-01','TERRAZA',1,3)""",
         # Menú del día (BD de la empresa): grupos en plato_armar, menú de la fecha del turno con Seleccionado = 1
         f"INSERT INTO {E}.plato_armar (Id_Plato, Cod_Categoria, Cantidad_Elegir, Activa, Exgir_Seleccion) VALUES (15,19,1,1,1),(16,7,2,1,0)",
         f"""INSERT INTO {E}.menu_diario (Id_Menu, Id_Item, Fecha, Categoria, Descripcion, Agrupar, Seleccionado) VALUES
             (52,146,'2026-10-03','01 SOPAS','FRIJOLADA',19,1),(52,151,'2026-10-03','01 SOPAS','SANCOCHO',19,1),
             (52,160,'2026-10-03','01 SOPAS','NO ESCOGIDA HOY',19,0),(51,999,'2026-10-02','01 SOPAS','DE AYER',19,1)""",
         f"INSERT INTO {E}.categoria_productos (Cod_Categoria, Nombre, Activa) VALUES (7,'PROTEINA',1)",
         f"INSERT INTO {E}.plato_armar_detalle (Id_Plato, Cod_Categoria, Item, Posicion, Cantidad_Descontar, Por_Default, Precio_Insumo) VALUES (16,7,1,501,1.5,1,0),(16,7,2,502,2,0,3000)",
         f"""INSERT INTO {E}.inventario_porciones (Id_Grupo, Id_Item, Descripcion, Posicion, Agrupar) VALUES
             (4,501,'POLLO',501,7),(4,502,'RES',502,7),(1,146,'FRIJOLADA',146,19),(1,151,'SANCOCHO',151,19)""",
         )
    yield


@pytest.fixture
def h(cliente, db, datos):
    """Encabezado de un mesero activo (usuario ana)."""
    r = cliente.post("/api/ag/dispositivos/registro", json={"nombre_dispositivo": "Cel Ana", "usuario": "ana", "clave": "4321"})
    activar_en_escritorio(db, "ana")
    token = cliente.post("/api/ag/sesion/ingresar", json={"usuario": "ana", "clave": "4321"}).json()["token"]
    return {"Authorization": f"Bearer {token}", "_cod": r.json()["cod_empleado"]}


def _hdr(h):
    return {"Authorization": h["Authorization"]}


def _otro_mesero(cliente, db):
    cliente.post("/api/ag/dispositivos/registro", json={"nombre_dispositivo": "Cel Beto", "usuario": "beto", "clave": "9999"})
    activar_en_escritorio(db, "beto")
    t = cliente.post("/api/ag/sesion/ingresar", json={"usuario": "beto", "clave": "9999"}).json()["token"]
    return {"Authorization": f"Bearer {t}"}


def _crear(cliente, h, lineas, **extra):
    cuerpo = {"mesa": {"id": 1, "nombre": "S-01"}, "mesero": LAURA, "lineas": lineas, **extra}
    return cliente.post("/api/ag/pedidos", json=cuerpo, headers=_hdr(h))


# ───────────── carta ─────────────

def test_todo_exige_sesion(cliente, datos):
    for ruta in ("/api/ag/catalogo", "/api/ag/mesas", "/api/ag/pedidos", "/api/ag/config"):
        assert cliente.get(ruta).status_code == 401


def test_carta_visibles_y_precios(cliente, h):
    d = cliente.get("/api/ag/catalogo", headers=_hdr(h)).json()
    ids = {p["id"] for p in d["platos"]}
    assert ids == {10, 11, 14, 15, 16, 17}                     # sin ocultos ni categoría inactiva
    precio = {p["id"]: p["precio"] for p in d["platos"]}
    assert precio[10] == 20000                              # consumidor final: platos.Valor
    armado = {p["id"]: p["armado"] for p in d["platos"]}
    assert armado[15] == "menu" and armado[16] == "armado" and armado[10] is None
    assert d["novedades"]["1"][0]["nombre"] == "BIEN ASADA"


def test_carta_lista_del_cliente(cliente, h):
    d = cliente.get("/api/ag/catalogo?cliente=194", headers=_hdr(h)).json()
    precio = {p["id"]: p["precio"] for p in d["platos"]}
    assert precio[10] == 15600                              # lista del cliente
    assert precio[11] == 4000                               # precio inactivo en la lista → platos.Valor


def test_carta_impuesto_no_incluido(cliente, db, h):
    _sql(db, f"UPDATE {E}.configuracion_facturacion SET Paga_Impuesto=1, Precios_Incluyen_Impuesto=0")
    precio = {p["id"]: p["precio"] for p in cliente.get("/api/ag/catalogo", headers=_hdr(h)).json()["platos"]}
    assert precio[10] == 21600                              # 20000 + 8 %


def test_carta_version_304(cliente, db, h):
    r = cliente.get("/api/ag/catalogo", headers=_hdr(h))
    etag = r.headers["ETag"]
    assert cliente.get("/api/ag/catalogo", headers={**_hdr(h), "If-None-Match": etag}).status_code == 304
    _sql(db, f"UPDATE {E}.platos SET Valor=21000 WHERE Id_Plato=10")    # cambio en el escritorio
    assert cliente.get("/api/ag/catalogo", headers={**_hdr(h), "If-None-Match": etag}).status_code == 200


def test_cliente_inexistente(cliente, h):
    assert cliente.get("/api/ag/catalogo?cliente=777", headers=_hdr(h)).status_code == 422


def test_opciones_menu_del_dia_fecha_turno(cliente, h):
    d = cliente.get("/api/ag/catalogo/plato/15/opciones", headers=_hdr(h)).json()
    nombres = [o["nombre"] for o in d["grupos"][0]["opciones"]]
    assert d["tipo"] == "menu" and nombres == ["FRIJOLADA", "SANCOCHO"]      # sin el de ayer


def test_menu_no_armado_bloquea(cliente, db, h):
    _sql(db, f"DELETE FROM {E}.menu_diario")
    assert cliente.get("/api/ag/catalogo/plato/15/opciones", headers=_hdr(h)).status_code == 409
    r = _crear(cliente, h, [{"id_plato": 15, "cantidad": 1}])
    assert r.status_code == 409


def test_buscar_clientes_sin_comodines(cliente, h):
    assert [c["id"] for c in cliente.get("/api/ag/clientes?q=DISTRI", headers=_hdr(h)).json()] == [194]
    assert cliente.get("/api/ag/clientes?q=DISTRI", headers=_hdr(h)).json()[0]["tiene_lista"] is True
    assert [c["id"] for c in cliente.get("/api/ag/clientes?q=0_%", headers=_hdr(h)).json()] == [195]
    assert cliente.get("/api/ag/clientes?q=%%%", headers=_hdr(h)).json() == []
    assert cliente.get("/api/ag/clientes?q=ab", headers=_hdr(h)).status_code == 422


# ───────────── pedido nuevo: forma del escritorio ─────────────

def test_pedido_forma_escritorio(cliente, db, h):
    r = _crear(cliente, h, [{"id_plato": 10, "cantidad": 2, "novedades": [1]}, {"id_plato": 11, "cantidad": 1}])
    assert r.status_code == 200, r.text
    nro = r.json()["nro_pedido"]
    assert nro.startswith("Cel Ana-2026/") and r.json()["total"] == 44000

    c = _filas(db, f"SELECT * FROM {T}.temp_comanda WHERE Nro_Pedido=%s", nro)[0]
    assert (c["Mesa"], c["Imprimio_Precuenta"], c["Mesero"], c["Movil"], c["Salio"], c["Id_Cliente"]) == \
           ("S-01", 1, LAURA, 1, 0, 1)
    assert c["Fecha"] == FECHA_TURNO

    det = _filas(db, f"SELECT Item, Id_Plato, Mostrar, Impresora, Depende, Valor, Novedad, Impreso, Fecha, Producto_Personalizado "
                     f"FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s ORDER BY Item", nro)
    # HAMBURGUESA x2 con 2 impresoras = 4 filas; GASEOSA x1 con 1 impresora = 1 fila
    resumen = [(d["Item"], d["Id_Plato"], d["Mostrar"], d["Impresora"], d["Depende"]) for d in det]
    assert resumen == [(1, 10, 1, "COCINA", "1"), (2, 10, 0, "BARRA", "1"),
                       (3, 10, 1, "COCINA", "1"), (4, 10, 0, "BARRA", "1"),
                       (5, 11, 1, "BARRA", "5")]
    assert all(d["Impreso"] == 0 for d in det)
    assert str(det[0]["Fecha"]) == "2026-10-03"                        # fecha de negocio
    assert det[0]["Novedad"] == "SIN CEBOLLA" and det[0]["Producto_Personalizado"] == "HAMBURGUESA"
    assert len(_filas(db, f"SELECT * FROM {T}.temp_detalle_comanda_parcial WHERE Nro_pedido=%s", nro)) == 5

    # Inventario por UNIDAD (como el VB6) con la columna Cantidad de la receta
    inv = _filas(db, f"SELECT Item, Id_Item, Cantidad FROM {T}.temp_plato_producto WHERE Nro_Pedido=%s ORDER BY Item, Id_Item", nro)
    assert [(i["Item"], i["Id_Item"], i["Cantidad"]) for i in inv] == [(1, 1, 1.0), (1, 36, 1.0), (3, 1, 1.0), (3, 36, 1.0)]

    nov = _filas(db, f"SELECT Item, Depende, Id_Novedad, Novedad FROM {T}.temp_novedades_plato_pedido WHERE Nro_Pedido=%s", nro)
    assert [(n["Item"], n["Depende"], n["Id_Novedad"]) for n in nov] == [(1, 1, 1)]


def test_novedad_libre(cliente, db, h):
    """Lo que no está en la lista: Id_Novedad = 0 con la categoría del producto (como el escritorio)."""
    r = _crear(cliente, h, [{"id_plato": 10, "cantidad": 1, "novedades": [1], "nota": "  salsa\x00   aparte "}])
    assert r.status_code == 200, r.text
    nro = r.json()["nro_pedido"]
    nov = _filas(db, f"SELECT Id_Consecutivo, Cod_Categoria, Id_Novedad, Novedad FROM {T}.temp_novedades_plato_pedido "
                     f"WHERE Nro_Pedido=%s ORDER BY Id_Consecutivo", nro)
    cat = _filas(db, f"SELECT Cod_Categoria FROM {E}.platos WHERE Id_Plato=10")[0]["Cod_Categoria"]
    assert [(n["Id_Novedad"], n["Novedad"].strip()) for n in nov] == [(1, "SIN CEBOLLA"), (0, "SALSA APARTE")]
    assert nov[1]["Cod_Categoria"] == cat
    det = _filas(db, f"SELECT Novedad FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s AND Mostrar=1", nro)[0]
    assert det["Novedad"] == "SIN CEBOLLA - SALSA APARTE"
    # Tope de largo; vacía o solo espacios no guarda nada
    assert _crear(cliente, h, [{"id_plato": 10, "cantidad": 1, "nota": "x" * 101}]).status_code == 422
    r = _crear(cliente, h, [{"id_plato": 11, "cantidad": 1, "nota": "   "}], mesa=None, cuenta_nueva="NOTA VACIA")
    assert r.status_code == 200, r.text
    nro = r.json()["nro_pedido"]
    assert not _filas(db, f"SELECT * FROM {T}.temp_novedades_plato_pedido WHERE Nro_Pedido=%s", nro)


def test_precio_de_lista_al_guardar(cliente, db, h):
    r = _crear(cliente, h, [{"id_plato": 10, "cantidad": 1}], id_cliente=194)
    nro = r.json()["nro_pedido"]
    assert _filas(db, f"SELECT Valor FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s AND Mostrar=1", nro)[0]["Valor"] == 15600
    assert _filas(db, f"SELECT Id_Cliente FROM {T}.temp_comanda WHERE Nro_Pedido=%s", nro)[0]["Id_Cliente"] == 194


def test_precio_enviado_se_ignora(cliente, db, h):
    nro = _crear(cliente, h, [{"id_plato": 10, "cantidad": 1, "precio": 100,
                               "descripcion": "GRATIS"}]).json()["nro_pedido"]
    fila = _filas(db, f"SELECT Valor, Producto_Personalizado FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s AND Mostrar=1", nro)[0]
    assert fila["Valor"] == 20000 and fila["Producto_Personalizado"] == "HAMBURGUESA"


def test_pedir_precio_y_descripcion(cliente, db, h):
    assert _crear(cliente, h, [{"id_plato": 14, "cantidad": 1}]).status_code == 422
    assert _crear(cliente, h, [{"id_plato": 14, "cantidad": 1, "precio": 7500}]).status_code == 422
    r = _crear(cliente, h, [{"id_plato": 14, "cantidad": 1, "precio": 7500, "descripcion": "  Tornillo\x00 3/8  "}])
    assert r.status_code == 200, r.text
    fila = _filas(db, f"SELECT Valor, Descripcion, Producto_Personalizado FROM {T}.temp_detalle_comanda "
                      f"WHERE Nro_pedido=%s", r.json()["nro_pedido"])[0]
    assert (fila["Valor"], fila["Descripcion"], fila["Producto_Personalizado"]) == (7500, "VARIOS", "Tornillo 3/8")


def test_menu_del_dia_y_armado(cliente, db, h):
    r = _crear(cliente, h, [{"id_plato": 15, "cantidad": 1, "opciones": [{"grupo": 19, "id": 146}]},
                            {"id_plato": 16, "cantidad": 1, "opciones": [{"grupo": 7, "id": 501}, {"grupo": 7, "id": 502}]}])
    assert r.status_code == 200, r.text
    nro = r.json()["nro_pedido"]
    inv = _filas(db, f"SELECT Id_Plato, Id_Grupo, Id_Item, Cantidad FROM {T}.temp_plato_producto WHERE Nro_Pedido=%s ORDER BY Id_Plato, Id_Item", nro)
    assert [(i["Id_Plato"], i["Id_Grupo"], i["Id_Item"], i["Cantidad"]) for i in inv] == \
           [(15, 1, 146, 1.0), (16, 4, 501, 1.5), (16, 4, 502, 2.0)]
    nov = _filas(db, f"SELECT Id_Novedad, Novedad FROM {T}.temp_novedades_plato_pedido WHERE Nro_Pedido=%s ORDER BY Id_Novedad", nro)
    assert [n["Novedad"] for n in nov] == ["FRIJOLADA", "POLLO - RES"]
    # BOWL sin plato_impresoras usa platos.Impresora
    assert _filas(db, f"SELECT Impresora FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s AND Id_Plato=16", nro)[0]["Impresora"] == "COCINA"


def test_opciones_invalidas(cliente, h):
    assert _crear(cliente, h, [{"id_plato": 15, "cantidad": 1}]).status_code == 422                       # exige selección
    assert _crear(cliente, h, [{"id_plato": 15, "cantidad": 1, "opciones": [{"grupo": 19, "id": 999}]}]).status_code == 422   # de otro día
    assert _crear(cliente, h, [{"id_plato": 15, "cantidad": 1,
                                "opciones": [{"grupo": 19, "id": 146}, {"grupo": 19, "id": 151}]}]).status_code == 422   # máximo 1
    assert _crear(cliente, h, [{"id_plato": 10, "cantidad": 1, "opciones": [{"grupo": 7, "id": 501}]}]).status_code == 422
    assert _crear(cliente, h, [{"id_plato": 10, "cantidad": 1, "novedades": [3]}]).status_code == 422     # novedad de otra categoría


def test_productos_no_disponibles_y_topes(cliente, h):
    for malo in ([{"id_plato": 12, "cantidad": 1}], [{"id_plato": 13, "cantidad": 1}], [{"id_plato": 999, "cantidad": 1}],
                 [{"id_plato": 10, "cantidad": 0}], [{"id_plato": 10, "cantidad": 51}], [{"id_plato": 10, "cantidad": 0.0001}],
                 [{"id_plato": 10, "cantidad": -1}], []):
        assert _crear(cliente, h, malo).status_code == 422, malo
    assert _crear(cliente, h, [{"id_plato": 10, "cantidad": 50}] * 5).status_code == 422             # > 200 unidades


def test_mesa_invalida_u_ocupada(cliente, db, h):
    assert _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}], mesa={"id": 5, "nombre": "T-01"}).status_code == 404
    assert _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}]).status_code == 200
    assert _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}]).status_code == 409                   # ya tiene pedido
    otro = _otro_mesero(cliente, db)
    r = cliente.post("/api/ag/pedidos", json={"mesa": {"id": 1, "nombre": "S-01"}, "mesero": PEDRO,
                                             "lineas": [{"id_plato": 11, "cantidad": 1}]}, headers=otro)
    assert r.status_code == 409 and "Agregue" in r.json()["detail"]


def test_cuenta_nueva(cliente, db, h):
    r1 = _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}], mesa=None, cuenta_nueva="juan perez")
    r2 = _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}], mesa=None, cuenta_nueva="llevar 2")
    assert (r1.json()["id_mesa"], r1.json()["mesa"]) == (1000, "JUAN PEREZ")
    assert r2.json()["id_mesa"] == 1001
    dup = _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}], mesa=None, cuenta_nueva="Juan Perez")
    assert dup.status_code == 409


# ───────────── mesas y bloqueo ─────────────

def test_mesas_estados(cliente, db, h):
    _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}])
    _sql(db, f"INSERT INTO {T}.temp_mesa_abierta (Id_Mesa, Mesa, Abierta, Abierta_Desde) VALUES (2,'S-02',1,'CAJA01')")
    d = cliente.get("/api/ag/mesas", headers=_hdr(h)).json()
    zonas = {z["nombre"]: z for z in d["zonas"]}
    assert list(zonas) == ["CLIENTES", "SALON"]                  # orden alfabético, sin la zona inactiva
    salon = {m["nombre"]: m["estado"] for m in zonas["SALON"]["mesas"]}
    assert salon == {"S-01": "pedido", "S-02": "abierta", "S-99": "libre"}    # mesas.Activa no filtra
    assert zonas["SALON"]["mesas"][0]["mesero"] == "LAURA"                    # nombre del mesero asignado
    assert zonas["CLIENTES"]["dinamica"] == 1
    assert zonas["SALON"]["color"] == "#c0ffc0" and zonas["CLIENTES"]["color"] is None
    assert d["alto"] == 47                                       # 700 twips de CLIENTES (primera alfabética)


def test_bloqueo_entre_dispositivos_y_escritorio(cliente, db, h):
    otro = _otro_mesero(cliente, db)
    m = {"id_mesa": 1, "mesa": "S-01"}
    assert cliente.post("/api/ag/mesas/bloquear", json=m, headers=_hdr(h)).status_code == 200
    assert cliente.post("/api/ag/mesas/bloquear", json=m, headers=_hdr(h)).status_code == 200      # renueva
    assert cliente.post("/api/ag/mesas/bloquear", json=m, headers=otro).status_code == 409
    assert cliente.post("/api/ag/mesas/liberar", json=m, headers=otro).status_code == 200          # no libera lo ajeno
    assert cliente.post("/api/ag/mesas/bloquear", json=m, headers=otro).status_code == 409
    assert cliente.post("/api/ag/mesas/liberar", json=m, headers=_hdr(h)).status_code == 200
    assert cliente.post("/api/ag/mesas/bloquear", json=m, headers=otro).status_code == 200
    # Bloqueo hecho por el escritorio (sin vencimiento): se respeta
    _sql(db, f"INSERT INTO {T}.temp_mesa_abierta (Id_Mesa, Mesa, Abierta, Abierta_Desde) VALUES (2,'S-02',1,'CAJA01')")
    r = cliente.post("/api/ag/mesas/bloquear", json={"id_mesa": 2, "mesa": "S-02"}, headers=_hdr(h))
    assert r.status_code == 409 and "CAJA01" in r.json()["detail"]


def test_bloqueo_vencido_se_limpia(cliente, db, h):
    otro = _otro_mesero(cliente, db)
    m = {"id_mesa": 1, "mesa": "S-01"}
    cliente.post("/api/ag/mesas/bloquear", json=m, headers=_hdr(h))
    _sql(db, f"UPDATE {T}.ag_bloqueo_mesa SET vence = NOW() - INTERVAL 1 MINUTE")
    assert cliente.post("/api/ag/mesas/bloquear", json=m, headers=otro).status_code == 200


def test_pedido_libera_bloqueo_propio(cliente, db, h):
    cliente.post("/api/ag/mesas/bloquear", json={"id_mesa": 1, "mesa": "S-01"}, headers=_hdr(h))
    assert _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}]).status_code == 200
    assert _filas(db, f"SELECT * FROM {T}.temp_mesa_abierta") == ()


# ───────────── pedidos del mesero ─────────────

def test_todos_ven_todos_los_pedidos(cliente, db, h):
    """Un dispositivo lo usan varios meseros: todos ven y agregan a todos los pedidos abiertos (de la
    toma de pedidos o de caja), con el nombre del mesero. No se muestran los domicilios ni lo que se
    está montando en el escritorio (Salio = 1, en encabezado o detalle)."""
    nro = _crear(cliente, h, [{"id_plato": 10, "cantidad": 2}]).json()["nro_pedido"]
    _sql(db,
         f"""INSERT INTO {T}.temp_comanda (Nro_Pedido, Fecha, Mesa, Mesero, Salio, Movil, Domicilio, Imprimio_Precuenta, Id_Cliente) VALUES
             ('CAJA-1','{FECHA_TURNO}','S-02',{PEDRO},0,0,0,2,1),
             ('DOMI-1','{FECHA_TURNO}','DOMICILIO 1',{PEDRO},0,0,1,0,1),
             ('MONTANDO','{FECHA_TURNO}','S-99',{PEDRO},1,0,0,3,1)""",
         # Caja: una fila enviada (Salio = 0) y otra que aún se está montando (Salio = 1)
         f"""INSERT INTO {T}.temp_detalle_comanda (Nro_pedido, Fecha, Id_Plato, Item, Descripcion, Cantidad, Valor, Salio, Mostrar, Depende, Impreso) VALUES
             ('CAJA-1','2026-10-03',11,1,'GASEOSA',1,4000,0,1,'1',1),
             ('CAJA-1','2026-10-03',10,2,'HAMBURGUESA',1,20000,1,1,'2',0)""")
    otro = _otro_mesero(cliente, db)
    for quien in (_hdr(h), otro):
        todos = cliente.get("/api/ag/pedidos", headers=quien).json()
        assert sorted((p["nro_pedido"], p["mesero"], p["total"], p["unidades"]) for p in todos) == \
               sorted([(nro, "LAURA", 40000, 2), ("CAJA-1", "PEDRO", 4000, 1)])
    caja = cliente.get("/api/ag/pedido", params={"nro": "CAJA-1"}, headers=otro).json()
    assert [L["nombre"] for L in caja["lineas"]] == ["GASEOSA"] and caja["total"] == 4000
    for oculto in ("DOMI-1", "MONTANDO"):
        assert cliente.get("/api/ag/pedido", params={"nro": oculto}, headers=otro).status_code == 404
    d = cliente.get("/api/ag/pedido", params={"nro": nro}, headers=otro).json()
    assert d["lineas"][0]["cantidad"] == 2 and d["total"] == 40000 and d["cliente"]["id"] == 1 and d["mesero"] == "LAURA"
    r = cliente.post("/api/ag/pedido/agregar", json={"nro_pedido": nro, "lineas": [{"id_plato": 11, "cantidad": 1}]}, headers=otro)
    assert r.status_code == 200
    # Agregar no cambia el mesero del pedido
    assert _filas(db, f"SELECT Mesero FROM {T}.temp_comanda WHERE Nro_Pedido=%s", nro)[0]["Mesero"] == LAURA
    # Al de caja también se le agrega; a lo que se está montando en caja, no
    assert cliente.post("/api/ag/pedido/agregar", json={"nro_pedido": "CAJA-1", "lineas": [{"id_plato": 11, "cantidad": 1}]},
                        headers=otro).status_code == 200
    assert cliente.post("/api/ag/pedido/agregar", json={"nro_pedido": "MONTANDO", "lineas": [{"id_plato": 11, "cantidad": 1}]},
                        headers=otro).status_code == 404
    assert cliente.post("/api/ag/mesas/bloquear", json={"id_mesa": 3, "mesa": "S-99"}, headers=otro).status_code == 409
    estados = {m["nombre"]: (m["estado"], m.get("mesero")) for z in cliente.get("/api/ag/mesas", headers=otro).json()["zonas"]
               for m in z["mesas"]}
    assert estados["S-02"] == ("pedido", "PEDRO") and estados["S-99"][0] == "ocupada"


def test_meseros_del_dia(cliente, db, h):
    r = cliente.get("/api/ag/meseros-dia", headers=_hdr(h)).json()
    assert r["meseros"] == [{"cod": LAURA, "nombre": "LAURA"}, {"cod": PEDRO, "nombre": "PEDRO"}] and r["aviso"] is None
    assert cliente.get("/api/ag/meseros-dia").status_code == 401
    # Mesero que no está en los del día (o inventado por el dispositivo): rechazado
    assert _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}], mesero=h["_cod"]).status_code == 422
    assert _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}], mesero=None).status_code == 422
    # Sin meseros del día no se monta el pedido
    _sql(db, f"DELETE FROM {T}.temp_meseros_dia")
    r = cliente.get("/api/ag/meseros-dia", headers=_hdr(h)).json()
    assert r["meseros"] == [] and "meseros del día" in r["aviso"]
    r = _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}])
    assert r.status_code == 409 and "meseros del día" in r.json()["detail"]
    assert not _filas(db, f"SELECT * FROM {T}.temp_comanda")


def test_agregar_productos_continua_items(cliente, db, h):
    nro = _crear(cliente, h, [{"id_plato": 10, "cantidad": 1}], id_cliente=194).json()["nro_pedido"]
    r = cliente.post("/api/ag/pedido/agregar", json={"nro_pedido": nro, "lineas": [{"id_plato": 10, "cantidad": 1}]}, headers=_hdr(h))
    assert r.status_code == 200 and r.json()["agregado"] == 15600          # lista del cliente del pedido
    items = [f["Item"] for f in _filas(db, f"SELECT Item FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s ORDER BY Item", nro)]
    assert items == [1, 2, 3, 4]
    assert [f["Depende"] for f in _filas(db, f"SELECT Depende FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s AND Item=3", nro)] == ["3"]


def test_agregar_con_mesa_abierta_en_otro_equipo(cliente, db, h):
    nro = _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}]).json()["nro_pedido"]
    _sql(db, f"INSERT INTO {T}.temp_mesa_abierta (Id_Mesa, Mesa, Abierta, Abierta_Desde) VALUES (1,'S-01',1,'CAJA01')")
    r = cliente.post("/api/ag/pedido/agregar", json={"nro_pedido": nro, "lineas": [{"id_plato": 11, "cantidad": 1}]}, headers=_hdr(h))
    assert r.status_code == 409






def test_auditoria_de_pedidos(cliente, db, h):
    _crear(cliente, h, [{"id_plato": 11, "cantidad": 1}])
    eventos = [f["evento"] for f in _filas(db, f"SELECT evento FROM {T}.ag_auditoria ORDER BY id")]
    assert "pedido_nuevo" in eventos


# ───────────── presentaciones, adicionales y tabla parcial ─────────────

def test_carta_presentaciones(cliente, h):
    platos = {p["id"]: p for p in cliente.get("/api/ag/catalogo", headers=_hdr(h)).json()["platos"]}
    assert [(x["nombre"], x["precio"], x["unidades"]) for x in platos[17]["presentaciones"]] ==            [("UNIDAD", 2000, 1.0), ("BLISTER", 18000, 10.0), ("CAJA", 175000, 100.0)]
    assert "presentaciones" not in platos[10] and platos[10]["precio"] == 20000      # una sola: platos.Valor


def test_pedido_con_presentacion(cliente, db, h):
    assert _crear(cliente, h, [{"id_plato": 17, "cantidad": 1}]).status_code == 422          # debe escoger
    assert _crear(cliente, h, [{"id_plato": 17, "cantidad": 1, "presentacion": 99}]).status_code == 422
    assert _crear(cliente, h, [{"id_plato": 11, "cantidad": 1, "presentacion": 2}]).status_code == 422
    r = _crear(cliente, h, [{"id_plato": 17, "cantidad": 2, "presentacion": 57}])
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 36000
    nro = r.json()["nro_pedido"]
    det = _filas(db, f"SELECT Valor, Producto_Personalizado FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s AND Mostrar=1", nro)
    assert [(d["Valor"], d["Producto_Personalizado"]) for d in det] == [(18000, "DOLEX - BLISTER")] * 2
    for tabla in ("temp_plato_producto", "temp_plato_producto_parcial"):    # descarga 10 por blister
        inv = _filas(db, f"SELECT Item, Id_Item, Cantidad FROM {T}.{tabla} WHERE Nro_Pedido=%s ORDER BY Item", nro)
        assert [(i["Item"], i["Id_Item"], i["Cantidad"]) for i in inv] == [(1, 700, 10.0), (2, 700, 10.0)]


def test_lista_por_presentacion(cliente, db, h):
    _sql(db, f"INSERT INTO {E}.lista_precios_cliente (id_lista, Id_Cliente, Id_Producto, Id_Presentacion, Precio_Producto, Activa) "
             f"VALUES (3,194,17,57,15000,1)")
    platos = {p["id"]: p for p in cliente.get("/api/ag/catalogo?cliente=194", headers=_hdr(h)).json()["platos"]}
    assert [x["precio"] for x in platos[17]["presentaciones"]] == [2000, 15000, 175000]
    nro = _crear(cliente, h, [{"id_plato": 17, "cantidad": 1, "presentacion": 57}], id_cliente=194).json()["nro_pedido"]
    assert _filas(db, f"SELECT Valor FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s", nro)[0]["Valor"] == 15000


def test_adicional_del_armado_suma(cliente, db, h):
    op = cliente.get("/api/ag/catalogo/plato/16/opciones", headers=_hdr(h)).json()
    assert {o["nombre"]: o["precio"] for o in op["grupos"][0]["opciones"]} == {"POLLO": 0, "RES": 3000}
    nro = _crear(cliente, h, [{"id_plato": 16, "cantidad": 1, "opciones": [{"grupo": 7, "id": 502}]}]).json()["nro_pedido"]
    assert _filas(db, f"SELECT Valor FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s", nro)[0]["Valor"] == 21000
    fila = _filas(db, f"SELECT Valor_Adicional_Armar FROM {T}.temp_plato_producto_parcial WHERE Nro_Pedido=%s AND Id_Item=502", nro)[0]
    assert fila["Valor_Adicional_Armar"] == 3000


def test_impuesto_incluido_no_suma(cliente, db, h):
    _sql(db, f"UPDATE {E}.configuracion_facturacion SET Paga_Impuesto=1, Precios_Incluyen_Impuesto=1")
    nro = _crear(cliente, h, [{"id_plato": 10, "cantidad": 1}]).json()["nro_pedido"]
    fila = _filas(db, f"SELECT Valor, Impuesto, Paga_Impuesto FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s AND Mostrar=1", nro)[0]
    assert (fila["Valor"], fila["Impuesto"], fila["Paga_Impuesto"]) == (20000, 8, 1)


def test_precio_digitado_con_impuesto_aparte(cliente, db, h):
    _sql(db, f"UPDATE {E}.configuracion_facturacion SET Paga_Impuesto=1, Precios_Incluyen_Impuesto=0",
             f"UPDATE {E}.platos SET Impuesto=8 WHERE Id_Plato=14")
    nro = _crear(cliente, h, [{"id_plato": 14, "cantidad": 1, "precio": 1000, "descripcion": "X"}]).json()["nro_pedido"]
    assert _filas(db, f"SELECT Valor FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s", nro)[0]["Valor"] == 1080




def test_cantidad_decimal_como_escritorio(cliente, db, h):
    r = _crear(cliente, h, [{"id_plato": 10, "cantidad": 1.5}])
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 30000
    nro = r.json()["nro_pedido"]
    det = _filas(db, f"SELECT Item, Cantidad, Valor, Mostrar, Impresora, Depende FROM {T}.temp_detalle_comanda "
                     f"WHERE Nro_pedido=%s ORDER BY Item", nro)
    # La fracción primero (como el VB6), cada unidad en sus 2 impresoras
    assert [(d["Item"], d["Cantidad"], d["Valor"], d["Mostrar"], d["Impresora"], d["Depende"]) for d in det] == [
        (1, 0.5, 10000, 1, "COCINA", "1"), (2, 0.5, 10000, 0, "BARRA", "1"),
        (3, 1.0, 20000, 1, "COCINA", "1"), (4, 1.0, 20000, 0, "BARRA", "1")]
    inv = _filas(db, f"SELECT Item, Id_Item, Cantidad FROM {T}.temp_plato_producto_parcial WHERE Nro_Pedido=%s ORDER BY Item, Id_Item", nro)
    assert [(i["Item"], i["Id_Item"], i["Cantidad"]) for i in inv] == [(1, 1, 0.5), (1, 36, 0.5), (3, 1, 1.0), (3, 36, 1.0)]
    d = cliente.get("/api/ag/pedido", params={"nro": nro}, headers=_hdr(h)).json()
    assert (d["lineas"][0]["cantidad"], d["lineas"][0]["subtotal"], d["total"]) == (1.5, 30000, 30000)
    assert cliente.get("/api/ag/pedidos", headers=_hdr(h)).json()[0]["unidades"] == 1.5


def test_cantidad_decimal_redondeo(cliente, db, h):
    _sql(db, f"UPDATE {E}.platos SET Valor=8100 WHERE Id_Plato=11")
    nro = _crear(cliente, h, [{"id_plato": 11, "cantidad": 1.264}]).json()["nro_pedido"]
    det = _filas(db, f"SELECT Cantidad, Valor FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s ORDER BY Item", nro)
    assert [(d["Cantidad"], d["Valor"]) for d in det] == [(0.264, 2138), (1.0, 8100)]     # igual que avsextafruver


def test_mesa_nueva_en_escritorio_se_ve_sin_abrir_turno(cliente, db, h):
    _sql(db, f"INSERT INTO {E}.mesas (Id_Mesa, Mesa, Ubicacion, Activa, Id_Zona) VALUES (4,'S-03','SALON',1,1)")
    salon = next(z for z in cliente.get("/api/ag/mesas", headers=_hdr(h)).json()["zonas"] if z["nombre"] == "SALON")["mesas"]
    assert "S-03" in [m["nombre"] for m in salon]


def test_menu_guardado_en_escritorio_se_ve_sin_recargar_temporales(cliente, db, h):
    _sql(db, f"DELETE FROM {E}.menu_diario")
    assert cliente.get("/api/ag/catalogo/plato/15/opciones", headers=_hdr(h)).status_code == 409
    _sql(db, f"INSERT INTO {E}.menu_diario (Id_Menu, Id_Item, Fecha, Categoria, Descripcion, Agrupar, Seleccionado) "
             f"VALUES (53,146,'2026-10-03','01 SOPAS','FRIJOLADA',19,1)")
    assert cliente.get("/api/ag/catalogo/plato/15/opciones", headers=_hdr(h)).status_code == 200


# ───────────── fotos y colores del escritorio ─────────────

@pytest.fixture
def carpetas_fotos(db, tmp_path):
    from PIL import Image
    prod, cat = tmp_path / "Productos", tmp_path / "Categorias"
    prod.mkdir(); cat.mkdir()
    Image.new("RGB", (1200, 800), "red").save(prod / "Hamburguesa.JPG")
    Image.new("RGB", (200, 100), "blue").save(cat / "comidas.png")
    (tmp_path / "secreto.key").write_text("no")
    (prod / "virus.exe").write_text("no")
    _sql(db, f"INSERT INTO {E}.configuracion_sede (Id_Sede, Ruta_Foto_Productos, Ruta_Foto_Categorias) "
             f"VALUES (1, '{str(prod).replace(chr(92), chr(92)*2)}', '{str(cat).replace(chr(92), chr(92)*2)}')",
         f"UPDATE {E}.platos SET Ruta_Foto='hamburguesa.jpg' WHERE Id_Plato=10",          # mayúsculas distintas
         f"UPDATE {E}.platos SET Ruta_Foto='..\\..\\secreto.key' WHERE Id_Plato=11",
         f"UPDATE {E}.platos SET Ruta_Foto='virus.exe' WHERE Id_Plato=14",
         f"UPDATE {E}.platos SET Ruta_Foto='hamburguesa.jpg' WHERE Id_Plato=12",          # plato oculto
         f"UPDATE {E}.categoria_platos SET Nombre_foto='comidas.png' WHERE Cod_Categoria=1",
         f"INSERT INTO {E}.configuracion_tamano_letra (Color_Primario_Categorias, Color_Secundarios_Categorias, "
         f"Color_Primario_Productos, Color_Secundarios_Productos) VALUES ('&H00C0FFC0&','&H00FFFFC0&','&H00C0FFC0&','')")
    return prod


def test_carta_fotos_y_colores(cliente, h, carpetas_fotos):
    d = cliente.get("/api/ag/catalogo", headers=_hdr(h)).json()
    platos = {p["id"]: p for p in d["platos"]}
    assert platos[10]["foto"].startswith("/api/ag/fotos/plato/10?v=")
    assert platos[11]["foto"] is None and platos[14]["foto"] is None       # ruta maliciosa / no es imagen
    cats = {c["id"]: c for c in d["categorias"]}
    assert cats[1]["foto"].startswith("/api/ag/fotos/categoria/1?v=") and cats[2]["foto"] is None
    assert [c["nombre"] for c in d["categorias"]] == ["BEBIDAS", "COMIDAS"]  # orden alfabético
    assert d["colores"] == {"categorias": ["#c0ffc0", "#c0ffff"], "productos": ["#c0ffc0", None]}


def test_servir_fotos(cliente, h, carpetas_fotos):
    from io import BytesIO
    from PIL import Image
    r = cliente.get("/api/ag/fotos/plato/10?v=1")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    assert "public" in r.headers["cache-control"]
    assert max(Image.open(BytesIO(r.content)).size) <= 400                   # miniatura
    assert cliente.get("/api/ag/fotos/categoria/1").status_code == 200
    for ruta in ("/api/ag/fotos/plato/11", "/api/ag/fotos/plato/14", "/api/ag/fotos/plato/12",
                 "/api/ag/fotos/plato/999", "/api/ag/fotos/categoria/3", "/api/ag/fotos/plato/..%2F..%2Fsecreto.key"):
        assert cliente.get(ruta).status_code in (404, 422), ruta


def test_color_vb():
    from agente_local.servicios.catalogo import color_vb
    assert color_vb("&H00C0FFC0&") == "#c0ffc0" and color_vb("&H00FFFFC0&") == "#c0ffff"
    assert color_vb(12648384) == "#c0ffc0" and color_vb("12648384") == "#c0ffc0" and color_vb(255) == "#ff0000"
    assert color_vb("") is None and color_vb(None) is None and color_vb("xyz") is None


def test_textos_configurables(cliente, h, monkeypatch):
    d = cliente.get("/api/ag/config", headers=_hdr(h)).json()["textos"]
    assert (d["cuenta"], d["cuentas"], d["producto"], d["productos"]) == ("Cuenta", "Cuentas", "Producto", "Productos")
    monkeypatch.setenv("AG_TEXTO_MESERO", "Vendedor")
    d = cliente.get("/api/ag/config", headers=_hdr(h)).json()["textos"]
    assert (d["mesero"], d["meseros"]) == ("Vendedor", "Vendedores")


def test_lo_enviado_no_se_quita_desde_la_toma_de_pedidos(cliente, db, h):
    """Regla del negocio: lo enviado (aunque no esté impreso) solo se elimina desde el escritorio."""
    nro = _crear(cliente, h, [{"id_plato": 10, "cantidad": 1}, {"id_plato": 11, "cantidad": 1}]).json()["nro_pedido"]
    r = cliente.post("/api/ag/pedido/quitar", json={"nro_pedido": nro, "depende": 1}, headers=_hdr(h))
    assert r.status_code == 403 and "escritorio" in r.json()["detail"]
    assert len(_filas(db, f"SELECT * FROM {T}.temp_detalle_comanda WHERE Nro_pedido=%s", nro)) == 3
    assert len(_filas(db, f"SELECT * FROM {T}.temp_comanda WHERE Nro_Pedido=%s", nro)) == 1
    assert "rechazado" in [f["resultado"] for f in _filas(db, f"SELECT resultado FROM {T}.ag_auditoria WHERE evento='pedido_quitar'")]
