# CLAUDE_PERFIL_ADMON_TAREAS.md
# business_profile_id = 2

## 1. ROLES Y LÓGICA
- ADMIN: Total. | TASK_LEADER: Sus tareas, avances, evidencias. | AUDITOR: Lectura, asignación, mensajes.
- WORKERS: Solo registro (sin login). Task Leader reporta por ellos.

## 2. ESTADOS (task_status)
1. Pendiente (Naranja) | 2. Asignada (Azul) | 3. En Progreso (Verde) | 4. En Revisión (Morado) | 5. Finalizada (Verde oscuro) | 6. Cancelada (Rojo).

## 3. ESQUEMA
- Existentes: `tasks`, `task_status`, `task_evidence`, `task_material`, `task_comment`, `assets`, `workers`.
- Nuevas: `task_expenses` (gastos), `task_progress_reports` (% avance).

## 4. REGLAS CRÍTICAS
- Task Leader solo ve lo propio. Finalizar requiere >=1 evidencia.
- KPI Dashboard: Pendientes, Ejecución, Atrasadas (fecha_fin < hoy), Finalizadas.
- UI: SidebarRight oculta divs vacíos (`v-if`). 
- Costo Real = suma de `task_expenses`.

## 5. REGLAS DE OPERACIÓN
- **Safe-Manual-Commit**: Solo cuando el usuario escriba la palabra "commit", verifica errores de sintaxis (linter/build) y, si es válido, ejecuta: `git add . && git commit -m "Auto-save: [resumen de cambios]"`
- **Planifica-Primero**: Antes de escribir código o crear archivos, presenta un plan breve y espera mi confirmación ("OK" o "Dale").
- **Safe-Manual-Commit**: Solo cuando escriba "commit", verifica sintaxis y ejecuta: `git add . && git commit -m "Auto-save: [resumen]"`
- **Switch-Profile**: Para cambiar perfil: `cp CLAUDE.md CLAUDE_PERFIL_[ANT].md` y luego `cp CLAUDE_PERFIL_[NUEVO].md CLAUDE.md`.
- Todos los campos donde se decriba un valor de pesos, debe tener formato de $$.


## 6. REGLAS DE CAMBIO DE PERFIL
- **Switch-Profile**: Cuando el usuario diga "Cambiar a perfil [NOMBRE]", debes:
  1. Renombrar el `CLAUDE.md` actual a `CLAUDE_PERFIL_[NOMBRE_ANTERIOR].md`.
  2. Buscar el archivo `CLAUDE_PERFIL_[NOMBRE_NUEVO].md` y renombrarlo a `CLAUDE.md`.
  3. Confirmar que el cambio se hizo y resumir las nuevas reglas activas.

## 7. REGLAS TÉCNICAS
- **i18n**: Usar `vue-i18n` para traducciones. Idioma default: `es`.
- **Moneda**: Formatear siempre según el Asociado (`currency_code`). Usar `Intl.NumberFormat`.
- **Backend**: Los mensajes de error de la API deben venir del backend ya traducidos o con códigos de error estándar.


## 8. REGLA: NUEVA VISTA → SIEMPRE REGISTRAR EN system_modules
- **Auto-SystemModule**: Cada vez que se cree una vista nueva con ruta propia (`/xxx/yyy`), ejecutar automáticamente:
  ```sql
  INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
  VALUES ('[Nombre]', '/ruta/vista', 'bi-icon', NULL, 1, 0, 0);
  ```
  - `parent_id = NULL` para que el usuario lo asigne en SidebarMenuManager.
  - `is_sysadmin = 0` salvo que sea exclusiva de SYSADMIN.
  - Sin esta entrada la vista no aparece en el menú ni funciona el sistema de permisos por roles.

## 9. HOJA DE RUTA
1. DB Status + Dashboard KPIs. | 2. CRUD Tareas. | 3. Vista Task Leader. | 4. Evidencias/Materiales. | 5. Vista Auditor. | 6. Reportes & PDF. | 7. Mensajería.
