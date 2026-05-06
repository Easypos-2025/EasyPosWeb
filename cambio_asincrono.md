# MIGRACIÓN ASYNC — EasyPosWeb Backend
> Contexto: EasyPosWeb es un SaaS público multitenant. Meta inicial ~1500 usuarios concurrentes,
> ~500 empresas × perfil, ~50 perfiles en roadmap. La migración async es necesaria antes del lanzamiento.

---

## POR QUÉ SE HACE
El backend actual usa `def` síncrono + `Session` síncrono de SQLAlchemy.
Cada request bloquea un hilo mientras espera la BD. Con cientos de usuarios simultáneos
el threadpool de FastAPI se satura. La solución: `async def` + `AsyncSession`.

---

## CIFRAS DEL PROYECTO
- **58 routers** en `backend/app/routers/`
- **55 de 58** usan `db.query()` (sintaxis vieja, debe cambiar a `select()`)
- **9 modelos** tienen `relationship()` — deben agregar `lazy="selectin"`
- **~370 funciones** en total (endpoints + helpers)

---

## PATRÓN DE CONVERSIÓN (aplicar en TODOS los routers)

### 1. database.py — base de todo
```python
# ANTES
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

# DESPUÉS
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Cambiar URL: mysql+pymysql → mysql+aiomysql
DATABASE_URL = "mysql+aiomysql://root:123456@localhost/easyposweb"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,           # APAGAR en producción
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=1800,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### 2. Firma del endpoint
```python
# ANTES
def get_item(id: int, db: Session = Depends(get_db)):

# DESPUÉS
async def get_item(id: int, db: AsyncSession = Depends(get_db)):
```

### 3. Queries ORM (db.query → select)
```python
# ANTES
item = db.query(Model).filter(Model.id == id).first()
items = db.query(Model).all()
items = db.query(Model).filter(Model.active == True).order_by(Model.name).all()

# DESPUÉS
from sqlalchemy import select
result = await db.execute(select(Model).where(Model.id == id))
item = result.scalar_one_or_none()

result = await db.execute(select(Model))
items = result.scalars().all()

result = await db.execute(select(Model).where(Model.active == True).order_by(Model.name))
items = result.scalars().all()
```

### 4. Insert / Update / Delete
```python
# ANTES
db.add(obj)
db.commit()
db.refresh(obj)
db.delete(obj)
db.commit()

# DESPUÉS (add y delete no necesitan await)
db.add(obj)
await db.commit()
await db.refresh(obj)
await db.delete(obj)
await db.commit()
```

### 5. Raw SQL con text()
```python
# ANTES
result = db.execute(text("SELECT ..."), {"param": value}).fetchall()

# DESPUÉS
result = await db.execute(text("SELECT ..."), {"param": value})
rows = result.fetchall()
```

### 6. Modelos con relationship — agregar lazy="selectin"
```python
# ANTES
children = relationship("SystemModule", backref="parent", remote_side=[id])

# DESPUÉS
children = relationship("SystemModule", backref="parent", remote_side=[id], lazy="selectin")
```

### 7. main.py — init_db
```python
# ANTES
@app.on_event("startup")
def startup():
    init_db()

# DESPUÉS
@app.on_event("startup")
async def startup():
    await init_db()
```

---

## DEPENDENCIA NUEVA — instalar antes de empezar
```bash
pip install aiomysql
# requirements.txt: agregar aiomysql
```

---

## SESIÓN 1 — Fundación + 20 routers simples
**Objetivo:** Todo lo que el resto depende + catálogos/maestros

### Paso 1.1 — database.py
Archivo: `backend/app/database.py`
Aplicar patrón completo del bloque "database.py" de arriba.

### Paso 1.2 — main.py
Archivo: `backend/app/main.py`
Cambiar `startup()` a `async def startup()` con `await init_db()`.

### Paso 1.3 — 9 modelos con relationship
Archivos en `backend/app/models/`:
- `business_profile_module.py`
- `company_model.py`
- `company_theme_model.py`
- `profession_model.py`
- `role_model.py`
- `role_module_model.py`
- `system_module_model.py`
- `user_model.py`
- `worker_model.py`

En cada uno: agregar `lazy="selectin"` a todos los `relationship()`.

### Paso 1.4 — 20 routers simples (CRUD básico)
Aplicar patrón completo a cada uno:

| Router | Endpoints |
|--------|-----------|
| `country_router.py` | 1 |
| `language_router.py` | 1 |
| `department_router.py` | 1 |
| `municipality_router.py` | 1 |
| `type_currency_router.py` | 1 |
| `dashboard_router.py` | 1 |
| `profile_router.py` | 1 |
| `task_status_router.py` | 5 |
| `asset_category_router.py` | 5 |
| `bodega_items_router.py` | 5 |
| `clients_router.py` | 5 |
| `conceptos_compras_router.py` | 5 |
| `conceptos_gastos_router.py` | 5 |
| `external_collaborators_router.py` | 5 |
| `insumos_router.py` | 5 |
| `product_categories_router.py` | 5 |
| `profession_router.py` | 5 |
| `suppliers_router.py` | 5 |
| `unidades_medida_router.py` | 5 |
| `worker_router.py` | 5 |

**Al final de sesión 1:** levantar el servidor y verificar que no hay errores de import.

---

## SESIÓN 2 — 22 routers de complejidad media
**Prerequisito:** Sesión 1 completa y servidor levantando sin errores.

| Router | Endpoints | Notas |
|--------|-----------|-------|
| `assets_router.py` | 6 | |
| `business_profile_module.py` | 1 | ya tiene text() |
| `business_profile_router.py` | 7 | ya tiene text() |
| `company_plan_router.py` | 3 | |
| `company_router.py` | 5 | |
| `company_theme_router.py` | 5 | |
| `invitation_router.py` | 5 | |
| `loans_router.py` | 7 | |
| `menu_router.py` | 6 | ya tiene text(), tiene get_db propio — eliminar, usar el de database.py |
| `plan_router.py` | 13 | |
| `price_lists_router.py` | 8 | |
| `products_router.py` | 11 | |
| `purchase_orders_router.py` | 7 | |
| `qr_public_router.py` | 3 | |
| `register_router.py` | 3 | |
| `role_router.py` | 7 | |
| `supply_items_router.py` | 8 | |
| `system_config_router.py` | 6 | |
| `system_module_router.py` | 7 | |
| `topbar_menu_router.py` | 8 | |
| `user_notification_router.py` | 9 | |
| `user_router.py` | 8 | |

**Nota especial — menu_router.py:**
Tiene su propio `get_db()` local (duplicado). Eliminarlo y usar el `get_db` de `database.py`.
```python
# ELIMINAR estas líneas del menu_router.py:
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Al final de sesión 2:** probar los endpoints principales desde el frontend.

---

## SESIÓN 3 — 13 routers complejos + verificación final
**Prerequisito:** Sesiones 1 y 2 completas.

| Router | Endpoints | Por qué es complejo |
|--------|-----------|---------------------|
| `auth_router.py` | 10 | JWT, bcrypt, heartbeat, lógica de acceso |
| `footer_router.py` | 6 | |
| `landing_router.py` | 25 | El más grande, múltiples modelos |
| `novelty_router.py` | 18 | |
| `payment_router.py` | 23 | Lógica de pagos, estados |
| `support_ticket_router.py` | 12 | |
| `task_router.py` | 18 | Lógica compleja, múltiples joins |
| `task_collaborators_router.py` | 7 | |
| `task_comment_router.py` | 6 | |
| `task_evidence_router.py` | 6 | Manejo de archivos (upload) — los uploads no cambian, solo el DB access |
| `task_materials_router.py` | 10 | |
| `task_progress_router.py` | 6 | |
| `task_purchases_router.py` | 5 | |

**Verificación final:**
1. Levantar servidor — cero errores de import
2. Login funciona
3. Sidebar carga menú
4. CRUD básico de assets/tareas funciona
5. Upload de evidencias funciona
6. `git add . && git commit -m "refactor: migración completa a async SQLAlchemy"`

---

## ERRORES COMUNES A VIGILAR

### Error: MissingGreenlet
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called
```
**Causa:** Se accedió a una relación sin `lazy="selectin"`.
**Fix:** Agregar `lazy="selectin"` al relationship en el modelo, o cargar explícito con `selectinload()`.

### Error: ObjectDeletedError después de commit
**Causa:** `expire_on_commit=True` (default). Ya está resuelto con `expire_on_commit=False` en el `async_sessionmaker`.

### Error de URL de BD
```
Can't load plugin: sqlalchemy.dialects:mysql+pymysql
```
**Causa:** URL no actualizada. Cambiar `mysql+pymysql` → `mysql+aiomysql` en el `.env` o en `database.py`.

---

## CÓMO ARRANCAR CADA SESIÓN
Al inicio de cada sesión nueva, decirle a Claude:
> "Continúa con la migración async del backend. El plan está en `cambio_asincrono.md`.
> Sesión X — [completar qué sesión toca]."

Claude leerá este archivo y sabrá exactamente qué hacer sin necesidad de explicar el contexto.
