from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import get_db
from app.models.user_model import User
from app.models.company_model import Company
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/menu", tags=["Menu"])


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

    result = await db.execute(text("""
        SELECT
            bpm.id        AS bpm_id,
            sm.name,
            sm.route,
            sm.icon,
            COALESCE(bpm.parent_id, parent_bpm.id) AS parent_id
        FROM system_modules sm
        JOIN business_profile_modules bpm ON bpm.module_id = sm.id
        LEFT JOIN business_profile_modules parent_bpm
            ON parent_bpm.module_id = sm.parent_id
            AND parent_bpm.business_profile_id = bpm.business_profile_id
        WHERE bpm.business_profile_id = :profile_id
          AND sm.is_active = 1
        ORDER BY COALESCE(bpm.parent_id, parent_bpm.id), bpm.sort_order, sm.id
    """), {"profile_id": company.business_profile_id})
    modules = result.fetchall()

    return [{"id": m.bpm_id, "name": m.name, "route": m.route, "icon": m.icon, "parent_id": m.parent_id}
            for m in modules]


@router.get("/by-company/{company_id}")
async def get_menu_by_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Company).where(Company.id_company == company_id))
    company = result.scalar_one_or_none()

    if not company or not company.business_profile_id:
        return []

    result = await db.execute(text("""
        SELECT
            bpm.id AS bpm_id, sm.name, sm.route, sm.icon,
            COALESCE(bpm.parent_id, parent_bpm.id) AS parent_id
        FROM system_modules sm
        JOIN business_profile_modules bpm ON bpm.module_id = sm.id
        LEFT JOIN business_profile_modules parent_bpm
            ON parent_bpm.module_id = sm.parent_id
            AND parent_bpm.business_profile_id = bpm.business_profile_id
        WHERE bpm.business_profile_id = :profile_id AND sm.is_active = 1
        ORDER BY COALESCE(bpm.parent_id, parent_bpm.id), bpm.sort_order
    """), {"profile_id": company.business_profile_id})
    modules = result.fetchall()

    return [{"id": m.bpm_id, "name": m.name, "route": m.route, "icon": m.icon, "parent_id": m.parent_id}
            for m in modules]


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
            sm.name, sm.route, sm.icon,
            COALESCE(bpm.parent_id, parent_bpm.id) AS parent_id
        FROM system_modules sm
        JOIN business_profile_modules bpm ON bpm.module_id = sm.id
        LEFT JOIN business_profile_modules parent_bpm
            ON parent_bpm.module_id = sm.parent_id
            AND parent_bpm.business_profile_id = bpm.business_profile_id
        WHERE bpm.business_profile_id = :profile_id
        ORDER BY COALESCE(bpm.parent_id, parent_bpm.id), bpm.sort_order, sm.id
    """), {"profile_id": profile_id})
    modules = result.fetchall()

    data = [{"id": m.bpm_id, "name": m.name, "route": m.route, "icon": m.icon, "parent_id": m.parent_id}
            for m in modules]
    return _build_tree(data)


@router.post("/repair-profile/{profile_id}")
async def repair_profile_menu(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted = await db.execute(text("""
        DELETE bpm FROM business_profile_modules bpm
        INNER JOIN system_modules sm ON sm.id = bpm.module_id
        WHERE bpm.business_profile_id = :pid AND sm.is_active = 0
    """), {"pid": profile_id})
    deleted_count = deleted.rowcount

    rows_result = await db.execute(text("""
        SELECT bpm.id AS bpm_id, sm.parent_id AS sm_parent_id
        FROM business_profile_modules bpm
        JOIN system_modules sm ON sm.id = bpm.module_id
        WHERE bpm.business_profile_id = :pid
    """), {"pid": profile_id})
    rows = rows_result.fetchall()

    sm_to_bpm = {}
    for r in rows:
        sm_res = await db.execute(text(
            "SELECT module_id FROM business_profile_modules WHERE id = :bid"
        ), {"bid": r.bpm_id})
        sm_id_res = sm_res.fetchone()
        if sm_id_res:
            sm_to_bpm[sm_id_res.module_id] = r.bpm_id

    for r in rows:
        new_parent = sm_to_bpm.get(r.sm_parent_id)
        await db.execute(text(
            "UPDATE business_profile_modules SET parent_id = :pid WHERE id = :bid"
        ), {"pid": new_parent, "bid": r.bpm_id})

    bpm_rows_result = await db.execute(text("""
        SELECT bpm.id AS bpm_id, bpm.parent_id AS bpm_parent
        FROM business_profile_modules bpm
        JOIN system_modules sm ON sm.id = bpm.module_id
        WHERE bpm.business_profile_id = :pid
        ORDER BY bpm.parent_id, sm.id
    """), {"pid": profile_id})
    bpm_rows = bpm_rows_result.fetchall()

    from collections import defaultdict
    groups = defaultdict(list)
    for r in bpm_rows:
        groups[r.bpm_parent].append(r.bpm_id)

    for parent_key, ids in groups.items():
        for idx, bpm_id in enumerate(ids):
            await db.execute(text(
                "UPDATE business_profile_modules SET sort_order = :so WHERE id = :bid"
            ), {"so": idx, "bid": bpm_id})

    fixed_perms = await db.execute(text("""
        INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
        SELECT DISTINCT r.id, bpm.module_id, 1, 0, 0, 0
        FROM roles r
        JOIN companies c ON c.id_company = r.company_id
        JOIN business_profile_modules bpm ON bpm.business_profile_id = c.business_profile_id
        JOIN system_modules sm ON sm.id = bpm.module_id AND sm.is_active = 1
        WHERE c.business_profile_id = :pid
          AND NOT EXISTS (
              SELECT 1 FROM role_modules rm2
              WHERE rm2.role_id = r.id AND rm2.module_id = bpm.module_id
          )
    """), {"pid": profile_id})
    perms_added = fixed_perms.rowcount

    await db.commit()

    tree = await get_menu_by_profile(profile_id, db, current_user)
    return {"deleted_inactive": deleted_count, "permissions_added": perms_added, "tree": tree}
