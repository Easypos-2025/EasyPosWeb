# CLAUDE.md — EasyPosWeb (v2)
# Stack: Vue 3 + FastAPI + MariaDB | Multi-tenant SaaS

## 1. CORE LOGIC
- **Multi-tenancy**: Aislamiento total por Asociado (empresa). 
- **Roles**: SYSADMIN (Acceso total global) | ADMIN (Gestiona su Asociado).
- **Selector Empresa**: En Topbar. SYSADMIN ve todos; Asociado solo los suyos (mismo NIT puede tener >1 empresa).
- **Mobile-first**: UI limpia, Bootstrap 5 nativo, colores suaves, letra legible.

## 2. ARQUITECTURA LAYOUT
- **Topbar**: Logo, Selector Empresa, Buscador Ayuda (contextual al perfil activo), Usuario.
- **SidebarLeft**: Módulos activos según Perfil de Negocio (Configurable por SYSADMIN).
- **SidebarRight**: Publicidad (3 divisiones). Admin por SYSADMIN. Tipos: texto/img/audio/video.
- **Footer**: Fijo, color NEGRO (No personalizable).

## 3. REGLAS TÉCNICAS
- **Backend**: FastAPI en puerto 8000. Credenciales en `backend/.env`. DB: `easyposweb`.
- **Frontend**: Vite en puerto 5173. Pinia para estado. Bootstrap Icons.
- **Personalización**: Asociado cambia Logo, colores (Topbar/SidebarLeft) y fuentes.
- **Ayuda**: Buscador filtra archivos de ayuda por `business_profile_id`.
- **Archivos**: Publicidad/Evidencias se guardan en DISCO (no Base64), ruta en BD.
- **Safe-Commit**: Antes de cada commit, verificar sintaxis. Ejecutar: `git add . && git commit -m "Auto-save: [descripción]"`
- **i18n**: Usar `vue-i18n` para traducciones. Idioma default: `es`.
- **Moneda**: Formatear siempre según el Asociado (`currency_code`). Usar `Intl.NumberFormat`.
- **Backend**: Los mensajes de error de la API deben venir del backend ya traducidos o con códigos de error estándar.


## 4. REGLAS DE OPERACIÓN
- **Safe-Manual-Commit**: Solo cuando el usuario escriba la palabra "commit", verifica errores de sintaxis (linter/build) y, si es válido, ejecuta: `git add . && git commit -m "Auto-save: [resumen de cambios]"`
- **Planifica-Primero**: Antes de escribir código o crear archivos, presenta un plan breve y espera mi confirmación ("OK" o "Dale").
- **Safe-Manual-Commit**: Solo cuando escriba "commit", verifica sintaxis y ejecuta: `git add . && git commit -m "Auto-save: [resumen]"`
- **Switch-Profile**: Para cambiar perfil: `cp CLAUDE.md CLAUDE_PERFIL_[ANT].md` y luego `cp CLAUDE_PERFIL_[NUEVO].md CLAUDE.md`.
- Todos los campos donde se decriba un valor de pesos, debe tener formato de $$.


## 5. REGLAS DE CAMBIO DE PERFIL
- **Switch-Profile**: Cuando el usuario diga "Cambiar a perfil [NOMBRE]", debes:
  1. Renombrar el `CLAUDE.md` actual a `CLAUDE_PERFIL_[NOMBRE_ANTERIOR].md`.
  2. Buscar el archivo `CLAUDE_PERFIL_[NOMBRE_NUEVO].md` y renombrarlo a `CLAUDE.md`.
  3. Confirmar que el cambio se hizo y resumir las nuevas reglas activas.


## 6. ESTADO Y PRIORIDADES
### En Curso: FASE 1 (Base)
1. **Dashboard**: Pulir visual, KPIs básicos y responsive.
2. **Selector Empresa**: Implementar lógica en Topbar.
3. **Buscador Ayuda**: Lógica contextual por perfil.
4. **Registro Asociados**: Formulario público, selección de Plan, validación NIT, Email confirmación.

### Siguientes: FASE 2 (Perfiles)
1. **Perfil Administrador de Tareas** (Ver `CLAUDE_PERFIL_ADMON_TAREAS.md`).
2. **Perfil Restaurante** (Próximamente).

## 7. RESTRICCIONES DE PLANES
- **Free/Básico**: Usuarios/Productos limitados.
- **Estándar/Premium**: Acceso total + Factura Electrónica (Premium).
