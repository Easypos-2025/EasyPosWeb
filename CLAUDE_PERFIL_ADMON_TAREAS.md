# CLAUDE_PERFIL_ADMON_TAREAS.md
# Perfil: Administrador de Tareas — EasyPosWeb
# business_profile_id = 2

> **Uso:** Este archivo guía el desarrollo del perfil "Administrador de Tareas".
> Leer ESTE archivo en cada sesión de trabajo de este perfil.
> NO leer CLAUDE.md principal hasta cambiar de perfil/fase.

---

## 1. Objetivo del Perfil

Sistema de gestión y seguimiento de tareas de mantenimiento sobre **activos** (buildings, vehículos, equipos, actividades, etc.). Permite crear tareas, asignarlas a personal, registrar evidencias, controlar costos vs presupuesto y generar reportes de ejecución.

---

## 2. Roles del Perfil

| Rol | Código | Descripción |
|---|---|---|
| Administrador Operativo | `ADMIN` | Gestión total: usuarios, todas las tareas, reportes generales |
| Líder de Tareas | `TASK_LEADER` | Crea tareas, asigna ejecutores, reporta avances, adjunta evidencias |
| Auditor / Supervisor | `AUDITOR` | Solo lectura + reportes, puede asignar tareas a Task Leaders, envía mensajes |

> **Ejecutores** (Maestro, Técnico, Auxiliar, Proveedor externo): NO tienen acceso al sistema. Solo se registran como workers asignados a una tarea.

---

## 3. Flujo de una Tarea

```
[Crear Tarea] → [Asignar Ejecutor] → [Reporte de Avance + Evidencias] → [Finalizar Tarea]
```

---

## 4. Estados de las Tareas

| Estado | Color sugerido | Descripción |
|---|---|---|
| Pendiente | Naranja | Creada, sin asignar |
| Asignada | Azul | Asignada a Task Leader o ejecutor |
| En Progreso | Verde | Trabajo iniciado |
| En Revisión | Morado | Terminada, esperando aprobación |
| Finalizada | Verde oscuro | Aprobada y cerrada |
| Cancelada | Rojo | Cancelada por cualquier motivo |

> **Acción:** Poblar la tabla `task_status` con estos 6 estados al iniciar el módulo.

---

## 5. Información que registra una Tarea

### Datos base
- Nombre / descripción de la tarea
- Asset relacionado (`assets.id`)
- Task Leader responsable
- Ejecutores asignados (`workers`)
- Estado actual
- Fecha inicio / fecha fin estimada / fecha fin real
- Porcentaje de avance (0–100%)
- Presupuesto estimado
- Costo real ejecutado

### Sub-módulos por tarea
| Sub-módulo | Tabla existente | Descripción |
|---|---|---|
| Evidencias | `task_evidence` | Imágenes, videos, audios, texto |
| Materiales | `task_material` | Materiales y herramientas usados |
| Comentarios / Novedades | `task_comment` | Mensajes internos, novedades |
| Gastos pagados | pendiente crear | Registro de pagos realizados |
| Reportes de avance | pendiente crear | Reportes parciales con % y descripción |

---

## 6. Tablas existentes (reutilizar)

| Tabla | Estado | Uso |
|---|---|---|
| `tasks` | ✅ Existe | Modelo base de tarea |
| `task_status` | ✅ Existe (vacía) | Poblar con 6 estados |
| `task_evidence` | ✅ Existe | Evidencias multimedia |
| `task_material` | ✅ Existe | Materiales usados |
| `task_comment` | ✅ Existe | Comentarios/novedades |
| `assets` | ✅ Existe | Activos a los que se asignan tareas |
| `workers` | ✅ Existe | Ejecutores (sin acceso al sistema) |

### Tablas a crear
| Tabla | Propósito |
|---|---|
| `task_expenses` | Gastos pagados por tarea |
| `task_progress_reports` | Reportes parciales de avance |

---

## 7. Vistas a construir (orden de desarrollo)

### FASE A — Base del perfil
1. **Poblar task_status** con los 6 estados (script BD)
2. **DashboardAdmonTareas** — KPI strip con datos reales + indicadores por estado
3. **TareasView mejorado** — formulario completo con todos los campos del punto 5

### FASE B — Gestión por rol
4. **Vista Task Leader** — mis tareas asignadas, avance, evidencias, materiales
5. **Vista Auditor** — todas las tareas filtradas por estado, asignar a Task Leaders, enviar mensajes
6. **Vista Admin** — igual que auditor + gestión de usuarios del perfil

### FASE C — Sub-módulos por tarea (dentro del detalle de tarea)
7. **Evidencias** — subir imágenes/videos/audios/texto con preview
8. **Materiales y gastos** — registrar materiales usados y gastos pagados
9. **Reportes de avance** — reportes parciales con % completado + descripción
10. **Novedades / Mensajes** — comunicación interna sobre la tarea

### FASE D — Reportes y análisis
11. **Historial por Asset** — todas las tareas de un activo, filtradas por estado → PDF/Excel
12. **Resumen de tarea** — análisis de ejecución: tiempos, costo real vs presupuesto, materiales
13. **Reporte general** — todas las tareas del período con filtros → PDF/Excel

---

## 8. Dashboard del Perfil (DashboardAdmonTareas)

### KPI Strip (barra de indicadores — mismos colores que todos)
| Indicador | Ícono | Fuente |
|---|---|---|
| Tareas pendientes | `bi-hourglass-split` | `task_status = Pendiente` |
| En ejecución | `bi-play-circle` | `task_status = En Progreso` |
| Atrasadas | `bi-exclamation-triangle` | `fecha_fin < hoy AND status != Finalizada` |
| Finalizadas | `bi-check2-circle` | `task_status = Finalizada` |

### Contenido del dashboard (a definir con el usuario antes de implementar)
- Tabla de tareas recientes por estado
- Gráfico de distribución por estado
- Tareas por Task Leader
> ⚠️ No implementar hasta que el usuario confirme el diseño exacto.

---

## 9. SidebarRight para este perfil

- **Div 1:** Mensajes/notificaciones entre Admin/Auditor y Task Leaders sobre tareas
- **Div 2 y 3:** Ocultos si no hay contenido (no mostrar placeholder vacío)
- Regla: los divs del SidebarRight sin información **deben estar ocultos**, no mostrar "Espacio vacío"

---

## 10. Funcionalidades especiales

### Historial de Asset
- Filtrar todas las tareas de un activo específico
- Ver por estado (completadas, pendientes, en curso)
- Exportar a PDF o Excel
- Incluye: nombre tarea, fecha, responsable, costo, estado

### Análisis de ejecución (por tarea)
- Tiempo real vs tiempo estimado (% de desviación)
- Costo real vs presupuesto (% de desviación)
- Materiales usados vs presupuestados
- Gráfico de avance en el tiempo

### Mensajería interna
- Admin/Auditor envía mensaje al Task Leader de una tarea
- Task Leader lo recibe en el SidebarRight al entrar al dashboard
- No requiere chat en tiempo real — es asíncrono (como comentarios)

---

## 11. Reglas específicas de este perfil

1. El Task Leader solo ve SUS tareas asignadas, no las de otros
2. El Auditor ve TODAS las tareas pero no puede modificar el avance
3. El Admin tiene acceso total al perfil
4. Los ejecutores (workers) NO tienen login — solo se registran en la tarea
5. Una tarea no puede pasar a "Finalizada" sin al menos una evidencia registrada
6. Los reportes de avance deben registrar el % actual al momento de guardarlo
7. El presupuesto es estimado; el costo real se va acumulando con los gastos registrados

---

## 12. Orden de desarrollo sesión a sesión

```
Sesión 1: Poblar task_status + KPI strip con datos reales en dashboard
Sesión 2: Formulario completo de creación/edición de tarea
Sesión 3: Vista Task Leader (mis tareas)
Sesión 4: Sub-módulo evidencias
Sesión 5: Sub-módulo materiales y gastos
Sesión 6: Vista Auditor (todas las tareas + filtros)
Sesión 7: Reportes de avance + historial por asset
Sesión 8: Análisis de ejecución + exportación PDF/Excel
Sesión 9: Mensajería interna + SidebarRight
Sesión 10: Pulido visual, pruebas, commit
```

---

## 13. Archivos clave del perfil

### Backend
- `backend/app/models/task_model.py` — modelo base (revisar campos faltantes)
- `backend/app/models/task_status_model.py` — poblar con 6 estados
- `backend/app/models/task_evidence_model.py` — evidencias
- `backend/app/models/task_material_model.py` — materiales
- `backend/app/models/task_comment_model.py` — comentarios
- `backend/app/models/worker_model.py` — ejecutores
- `backend/app/models/asset_model.py` — activos
- `backend/app/routers/task_router.py` — ampliar con nuevos endpoints
- `backend/app/routers/worker_router.py` — revisar/ampliar

### Frontend
- `frontend/src/views/dashboards/DashboardAdmonTareas.vue` — dashboard del perfil
- `frontend/src/views/TareasView.vue` — vista base (mejorar)
- `frontend/src/views/AssetsView.vue` — activos

---

## 14. Antes de empezar cada sesión

1. Leer este archivo completo
2. Verificar en qué sesión del punto 12 estamos
3. Confirmar con el usuario si hay ajustes al plan
4. Solo implementar lo de esa sesión — nada más
