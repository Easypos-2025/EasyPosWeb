"""
========================================================
ROLES DEL SISTEMA
========================================================

Este archivo define TODOS los roles del sistema.

Ventajas de centralizar los roles aquí:

1) Evita errores de escritura
2) Facilita cambios futuros
3) Permite validar permisos fácilmente
4) Mantiene consistencia en todo el backend

Los roles del sistema son:

SYSADMIN   → Usuario de sistemas (control total)
ADMIN      → Administrador del sistema
TASK_LEAD  → Responsable de ejecutar tareas
CONTROL    → Usuario de control y seguimiento

========================================================
"""

# ======================================================
# ROLES PRINCIPALES
# ======================================================

SYSADMIN = "SYSADMIN"

ADMIN = "ADMIN"

TASK_LEAD = "TASK_LEAD"

CONTROL = "CONTROL"


# ======================================================
# LISTA GENERAL DE ROLES
# ======================================================

ALL_ROLES = [
    SYSADMIN,
    ADMIN,
    TASK_LEAD,
    CONTROL
]