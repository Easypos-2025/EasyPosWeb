from fastapi import Depends
from app.auth.tenant import tenant_guard
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import get_db
from app.models.user_model import User
from app.models.company_model import Company
from app.auth.dependencies import get_current_user, require_sysadmin

# Aislamiento multi-tenant: valida todo company_id que envíe el navegador (CLAUDE.md §6)
router = APIRouter(prefix="/menu", tags=["Menu"], dependencies=[Depends(tenant_guard)])


# Rutas que solo ve la empresa que tiene la función activada (igual que SidebarLeft.vue → filterByFeatureFlags)
FUNCIONES = (("/parking", "Parking"), ("/pos/facturas-electronicas", "POS electrónico"),
             ("/pos/utilitarios/pantallas-tv", "Pantallas TV"), ("/bodega-central", "Bodega Central"))


async def filas_menu(db: AsyncSession, profile_id: int) -> list[dict]:
    """Menú del cliente: módulos activos del perfil con su padre EXPLÍCITO (business_profile_modules.parent_id),
    en el orden del perfil. El sidebar (menuStore.buildTree) arma el árbol con esto."""
    filas = (await db.execute(text("""
        SELECT bpm.id AS bpm_id, COALESCE(NULLIF(TRIM(bpm.display_name), ''), sm.name) AS name,
               sm.route, sm.icon, bpm.parent_id
        FROM system_modules sm
        JOIN business_profile_modules bpm ON bpm.module_id = sm.id
        WHERE bpm.business_profile_id = :profile_id AND sm.is_active = 1
        ORDER BY bpm.parent_id, bpm.sort_order, sm.id
    """), {"profile_id": profile_id})).fetchall()
    return [{"id": m.bpm_id, "name": m.name, "route": m.route, "icon": m.icon, "parent_id": m.parent_id}
            for m in filas]


def _funcion(ruta: str | None) -> str | None:
    for prefijo, nombre in FUNCIONES:
        if ruta and (ruta == prefijo or ruta.startswith(prefijo + "/")):
            return nombre
    return None


async def vista_previa(db: AsyncSession, profile_id: int) -> dict:
    """Menú del perfil EXACTAMENTE como lo arma el sidebar del cliente (dos niveles; lo que no se ve, aparte):
      · un hijo cuyo padre no existe en el perfil NO se ve (buildTree lo descarta);
      · los nietos (tercer nivel) NO se ven; un hijo sin ruta tampoco;
      · un módulo inactivo NO se ve;
      · las rutas de una función (Parking, POS electrónico, TV, Bodega Central) se ven solo si la empresa la tiene.
    Cada rol ve además solo lo que tenga permitido."""
    filas = (await db.execute(text("""
        SELECT bpm.id, bpm.module_id, bpm.parent_id, bpm.sort_order, NULLIF(TRIM(bpm.display_name), '') AS display_name,
               sm.name AS nombre_catalogo, sm.route, sm.icon, sm.is_active,
               EXISTS (SELECT 1 FROM system_modules h WHERE h.parent_id = sm.id) AS padre_en_catalogo
        FROM business_profile_modules bpm JOIN system_modules sm ON sm.id = bpm.module_id
        WHERE bpm.business_profile_id = :p
        ORDER BY bpm.parent_id, bpm.sort_order, sm.id
    """), {"p": profile_id})).mappings().all()
    por_id = {f["id"]: f for f in filas}
    activos = {i for i, f in por_id.items() if f["is_active"]}

    def nodo(f, hijos=None):
        return {"id": f["id"], "module_id": f["module_id"], "name": f["display_name"] or f["nombre_catalogo"],
                "nombre_catalogo": f["nombre_catalogo"], "display_name": f["display_name"], "route": f["route"] or None,
                "icon": f["icon"], "parent_id": f["parent_id"], "funcion": _funcion(f["route"]),
                "children": hijos if hijos is not None else []}

    problemas = []

    def problema(f, tipo, texto):
        problemas.append({"id": f["id"], "name": f["display_name"] or f["nombre_catalogo"], "route": f["route"] or None,
                          "tipo": tipo, "texto": texto})

    arbol = []
    for f in filas:
        if f["parent_id"] is not None or f["id"] not in activos:
            continue
        hijos = []
        for h in filas:
            if h["parent_id"] != f["id"]:
                continue
            if h["id"] not in activos:
                continue
            if not h["route"]:
                problema(h, "hijo_sin_ruta", f"Está dentro de «{f['display_name'] or f['nombre_catalogo']}» pero no tiene "
                                             "pantalla: el cliente no lo ve.")
                continue
            hijos.append(nodo(h))
            for n in filas:
                if n["parent_id"] == h["id"]:
                    problema(n, "tercer_nivel", f"Cuelga de «{h['display_name'] or h['nombre_catalogo']}», que ya es un "
                                                "hijo: el menú solo muestra dos niveles, el cliente no lo ve.")
        if not f["route"] and not hijos:
            # el cliente lo ve como un título sin nada debajo
            problema(f, "grupo_vacio", "Es un grupo sin opciones: el cliente ve solo el título.")
        arbol.append(nodo(f, hijos))

    for f in filas:
        if f["id"] not in activos:
            problema(f, "inactivo", "El módulo está inactivo en el catálogo: el cliente no lo ve.")
        elif f["parent_id"] is not None and f["parent_id"] not in por_id:
            problema(f, "padre_inexistente", "Su grupo no existe en este perfil: el cliente no lo ve.")
        elif f["parent_id"] is not None and f["parent_id"] not in activos:
            problema(f, "padre_inactivo", "Su grupo está inactivo: el cliente no lo ve.")
        elif f["parent_id"] is not None:
            vistos, x = set(), f
            while x["parent_id"] is not None and x["parent_id"] in por_id and x["id"] not in vistos:
                vistos.add(x["id"])
                x = por_id[x["parent_id"]]
            if x["parent_id"] is not None and x["id"] in vistos:
                problema(f, "ciclo", "Quedó colgado en círculo (de uno de sus propios hijos): el cliente no lo ve.")

    # Grupos posibles para "Colgar bajo": raíces activas que son grupo (sin pantalla, ya con hijos o padres en catálogo)
    grupos = [{"id": n["id"], "name": n["name"], "nombre_catalogo": n["nombre_catalogo"]}
              for n in arbol if not n["route"] or n["children"] or por_id[n["id"]]["padre_en_catalogo"]]
    return {"arbol": arbol, "problemas": problemas, "grupos": grupos}
@router.get("/preview/{profile_id}")
async def preview_profile_menu(profile_id: int, db: AsyncSession = Depends(get_db),
                               current_user: User = Depends(require_sysadmin)):
    datos = await vista_previa(db, profile_id)
    # Catálogo para "Agregar o mover": cada módulo activo y, si ya está en el perfil, dónde está
    filas = (await db.execute(text("""
        SELECT sm.id, sm.name, sm.route, COALESCE(sm.is_sysadmin, 0) AS is_sysadmin, bpm.id AS bpm_id, bpm.parent_id,
               COALESCE(NULLIF(TRIM(pb.display_name), ''), psm.name) AS grupo
        FROM system_modules sm
        LEFT JOIN business_profile_modules bpm ON bpm.module_id = sm.id AND bpm.business_profile_id = :p
        LEFT JOIN business_profile_modules pb ON pb.id = bpm.parent_id
        LEFT JOIN system_modules psm ON psm.id = pb.module_id
        WHERE sm.is_active = 1
        ORDER BY sm.name
    """), {"p": profile_id})).mappings().all()
    datos["catalogo"] = [{"id": f["id"], "name": f["name"], "route": f["route"] or None, "bpm_id": f["bpm_id"],
                          "is_sysadmin": bool(f["is_sysadmin"]),
                          "en_perfil": f["bpm_id"] is not None,
                          "grupo": (f["grupo"] or "Raíz") if f["bpm_id"] is not None else None} for f in filas]
    return datos


@router.post("/preview/{profile_id}/reparar")
async def reparar_preview(profile_id: int, db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(require_sysadmin)):
    """Arregla lo que el cliente no puede ver por estar mal colgado (no toca módulos inactivos ni grupos vacíos):
    padre inexistente, inactivo, en círculo o grupo sin pantalla → a la raíz; tercer nivel → al grupo de su padre."""
    datos = await vista_previa(db, profile_id)
    movidos = 0
    for pr in datos["problemas"]:
        if pr["tipo"] in ("padre_inexistente", "padre_inactivo", "ciclo", "hijo_sin_ruta"):
            nuevo = None
        elif pr["tipo"] == "tercer_nivel":
            nuevo = (await db.execute(text("""
                SELECT p.parent_id FROM business_profile_modules b JOIN business_profile_modules p ON p.id = b.parent_id
                WHERE b.id = :b AND b.business_profile_id = :pf
            """), {"b": pr["id"], "pf": profile_id})).scalar()
        else:
            continue
        so = (await db.execute(text("""
            SELECT COALESCE(MAX(sort_order), -1) + 1 FROM business_profile_modules
            WHERE business_profile_id = :pf AND parent_id <=> :par
        """), {"pf": profile_id, "par": nuevo})).scalar()
        movidos += (await db.execute(text(
            "UPDATE business_profile_modules SET parent_id = :par, sort_order = :so WHERE id = :b AND business_profile_id = :pf"),
            {"par": nuevo, "so": so, "b": pr["id"], "pf": profile_id})).rowcount
    await db.commit()
    return {"movidos": movidos, **(await vista_previa(db, profile_id))}


@router.get("/my-menu/")
async def get_my_menu(
    company_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = current_user
    if not user:
        return []

    target_company_id = company_id if company_id else user.company_id
    result = await db.execute(select(Company).where(Company.id_company == target_company_id))
    company = result.scalar_one_or_none()

    if not company or not company.business_profile_id:
        return []

    return await filas_menu(db, company.business_profile_id)


@router.get("/by-company/{company_id}")
async def get_menu_by_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.auth.tenant import resolve_company
    company_id = await resolve_company(db, current_user, company_id)     # 403 si no tiene acceso
    result = await db.execute(select(Company).where(Company.id_company == company_id))
    company = result.scalar_one_or_none()

    if not company or not company.business_profile_id:
        return []

    return await filas_menu(db, company.business_profile_id)


def _build_tree(modules):
    module_dict = {m["id"]: {**m, "children": []} for m in modules}
    tree = []
    for m in module_dict.values():
        parent_id = m["parent_id"]
        if parent_id and parent_id in module_dict:
            module_dict[parent_id]["children"].append(m)
        else:
            tree.append(m)
    return tree


@router.get("/by-profile/{profile_id}")
async def get_menu_by_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(text("""
        SELECT
            bpm.id AS bpm_id, sm.id AS module_id,
            COALESCE(bpm.display_name, sm.name) AS name,
            bpm.display_name,
            sm.route, sm.icon,
            bpm.parent_id
        FROM system_modules sm
        JOIN business_profile_modules bpm ON bpm.module_id = sm.id
        WHERE bpm.business_profile_id = :profile_id
        ORDER BY bpm.parent_id, bpm.sort_order, sm.id
    """), {"profile_id": profile_id})
    modules = result.fetchall()

    data = [{"id": m.bpm_id, "module_id": m.module_id, "name": m.name,
             "display_name": m.display_name, "route": m.route, "icon": m.icon,
             "parent_id": m.parent_id}
            for m in modules]
    return _build_tree(data)

