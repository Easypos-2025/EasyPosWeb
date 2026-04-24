# CLAUDE.md — EasyPosWeb

Guía de referencia para todas las sesiones de desarrollo con Claude Code.
Leer antes de cualquier tarea. Actualizar cuando cambie arquitectura, decisiones o módulos.

---

## 1. Descripción del Proyecto

**Nombre:** EasyPosWeb
**Tipo:** SPA (Single Page Application) — ERP/BI Web Modular Multi-empresa y Multi-usuario
**Stack principal:** Vue 3 + FastAPI + Python + MariaDB

### Objetivo
Plataforma configurable para múltiples tipos de negocio: Restaurantes, Droguerías,
Licoreras, Fruver, Ferreterías, etc. Cada tipo de negocio tiene su propio perfil con
módulos, dashboard y dinámica adaptada. El sistema opera bajo modelo SaaS con planes
de suscripción.

### Terminología clave
| Término | Significado |
|---|---|
| **Asociado** | Empresa cliente que usa la plataforma (también llamada "Empresa") |
| **SYSADMIN** | Empresa propietaria de la plataforma (el desarrollador). Sin restricciones |
| **Perfil de negocio** | Tipo de empresa: Restaurante, Fruver, Task Manager, etc. |
| **Módulo** | Funcionalidad específica dentro de un perfil (Inventario, Caja, Pedidos, etc.) |

### Audiencia objetivo
Usuarios no técnicos. Interfaz limpia, letra legible, colores suaves.
Uso mayoritario desde **dispositivos móviles** — mobile-first en todo momento.

---

## 2. Stack Tecnológico

### Frontend
| Herramienta | Versión | Uso |
|---|---|---|
| Vue 3 | 3.5.x | Framework principal |
| Vite | 8.x | Build tool y dev server (puerto 5173) |
| Vue Router | 4.x | Routing SPA con guards de autenticación |
| Pinia | 3.x | State management global |
| Axios | 1.x | Cliente HTTP |
| Bootstrap 5 | 5.3.x | UI framework — usar clases nativas antes de CSS propio |
| Bootstrap Icons | 1.13.x | Iconografía |
| SweetAlert2 | 11.x | Notificaciones y confirmaciones |
| Cropper.js | 1.5.x | Recorte de imágenes |
| Vuedraggable | 4.x | Ordenamiento drag & drop |

### Backend
| Herramienta | Versión | Uso |
|---|---|---|
| Python | 3.13.7 | Lenguaje backend |
| FastAPI | latest | Framework API REST (puerto 8000) |
| SQLAlchemy | latest | ORM para modelos de BD |
| Alembic | latest | Migraciones de base de datos |
| PyJWT / python-jose | latest | Manejo de tokens JWT |
| Passlib / bcrypt | latest | Hash de contraseñas |
| Uvicorn | latest | Servidor ASGI |
| PyMySQL | latest | Conector MySQL/MariaDB |

### Base de datos
- **Motor:** MariaDB / MySQL
- **Nombre:** `easyposweb`
- **ORM:** SQLAlchemy con modelos declarativos
- **Migraciones:** Alembic (`/backend/alembic/`)

### Entorno de desarrollo
- **IDE:** VS Code + WSL en Windows 10
- **Node:** v22.16.0
- **Script de inicio:** `iniciar_proyecto.bat` (lanza backend + frontend)
- **Tunneling:** Cloudflare Tunnel (pendiente configurar al terminar Fase 1 del dashboard)
- **Git:** Pendiente inicializar al terminar Fase 1 del dashboard

---

## 3. Arquitectura del Sistema

### Multi-tenancy
- Cada Asociado tiene sus propios usuarios, roles, permisos y datos aislados
- Un NIT/documento puede tener una o varias empresas (mismos credenciales, diferente empresa)
- El selector de empresa en el Topbar permite cambiar de empresa sin cerrar sesión

### SYSADMIN
- Empresa especial con acceso total a todos los Asociados
- Puede ver, crear, modificar y eliminar datos de cualquier Asociado
- El selector de empresa en el Topbar muestra todos los Asociados
- Los Asociados solo ven su(s) propia(s) empresa(s) — el selector muestra solo las suyas

### Layout base (aplica a todos los perfiles)
```
┌─────────────────────────────────────────────────────┐
│                      TOPBAR                          │
│  Logo | Selector Empresa | Buscador Ayuda | Usuario  │
├──────────────┬──────────────────────┬────────────────┤
│              │                      │                │
│  SIDEBAR     │      CONTENIDO       │  SIDEBAR       │
│  LEFT        │      PRINCIPAL       │  RIGHT         │
│  (módulos    │                      │  (publicidad   │
│   del perfil)│                      │   3 divisiones)│
│              │                      │                │
├──────────────┴──────────────────────┴────────────────┤
│              FOOTER (siempre negro, fijo)             │
└─────────────────────────────────────────────────────┘
```

### SidebarLeft
- Muestra los módulos activos del perfil de negocio actual
- Personalizable por SYSADMIN — cada perfil tiene su propia configuración de menú
- Los Asociados no pueden modificar el orden ni los módulos visibles

### SidebarRight
- Tres divisiones iguales de publicidad
- Las pautas las crea SYSADMIN desde su panel de administración
- Destino: todos los Asociados, por perfil específico, o combinación
- Tipos de pauta: texto, imagen, audio, video
- Almacenamiento: archivos en disco con ruta en BD (no Base64)
- Cada pauta tiene: fecha inicio, fecha fin, valor y piezas publicitarias

### Buscador de ayuda (Topbar)
- Busca en los archivos de ayuda filtrados por el **perfil de la empresa activa**
- Al cambiar de empresa en el selector, el contexto de búsqueda cambia automáticamente
- Un Asociado con dos empresas de perfiles distintos ve la ayuda del perfil seleccionado
- Ayuda incluye: texto descriptivo, capturas de pantalla, videos de ejemplo

### Planes de suscripción
| Plan | Limitaciones |
|---|---|
| Free | Usuarios limitados, productos limitados, módulos básicos |
| Básico | Más usuarios/productos, sin algunos módulos avanzados |
| Estándar | Acceso ampliado a módulos |
| Premium | Todo incluido (ej. factura electrónica) |

### Personalización por Asociado
- Logo propio
- Color del Topbar y SidebarLeft
- Tamaño y color de fuente
- **El Footer siempre es negro — no personalizable**

---

## 4. Estado Actual del Desarrollo (referencia, verificar con el código)

| Área | Estado |
|---|---|
| Autenticación JWT + sesiones | Completo |
| Recuperación de contraseña por email | Completo (requiere revisión) |
| Gestión de Usuarios | Completo |
| Roles y Permisos | Completo |
| Gestión de Tareas (Tasks) | Completo |
| Gestión de Activos (Assets) | Completo |
| Empresas (Companies) | Completo |
| Temas por empresa (CompanyThemes) | Completo |
| Perfiles de negocio (BusinessProfiles) | Completo |
| Layout base (Topbar, Sidebars, Footer) | Estructura lista, mejoras pendientes |
| Dashboard principal | En curso — mejora visual y KPIs pendientes |
| Selector de empresa en Topbar | Pendiente |
| Formulario de registro de Asociados | Adelantado, requiere revisión y ajuste |
| Módulos de perfiles de negocio | Pendiente |

### Resuelto en configuración inicial
- ✅ Credenciales movidas a `backend/.env` (DATABASE_URL, JWT_SECRET_KEY, EMAIL_PASSWORD, FRONTEND_URL)
- ✅ Backend renombrado a `"EasyPosWeb API"` en `main.py`
- ✅ URL de email de recuperación lee `FRONTEND_URL` desde `.env`
- ✅ Base de datos renombrada de `easytask` a `easyposweb`

---

## 5. Orden de Desarrollo por Módulos

> **Regla:** Cada ítem debe estar **terminado, probado, con código documentado
> y con su archivo de ayuda** antes de pasar al siguiente.

### FASE 1 — Base del sistema

**1. Dashboard principal** ← EN CURSO
- Completar y mejorar visualmente el layout: SidebarLeft, SidebarRight, Topbar, Footer
- Agregar selector de empresa en Topbar (SYSADMIN ve todos, Asociado ve los suyos)
- Buscador de ayuda contextual en Topbar (filtra por perfil de empresa activa)
- KPIs básicos según perfil activo
- Verificar responsive en móvil antes de cerrar

**2. Formulario de Registro de Asociados**
- Formulario externo al dashboard (link público para compartir)
- Selección de plan de suscripción
- Validación de NIT/documento (permite múltiples empresas con el mismo)
- Email de confirmación con token seguro y expiración
- Revisar y ajustar el avance existente

### FASE 2 — Perfiles de negocio (uno a uno)

**3. Perfil: Administrador de Tareas** (primer perfil completo)
- Dashboard con métricas de tareas: pendientes, en ejecución, completadas
- Módulos específicos del perfil (definir al iniciar esta fase)

**4. Perfil: Restaurante** (segundo perfil → salida a producción al terminarlo)
- Dashboard con ventas del día, pedidos, metas
- Módulos específicos del perfil (definir al iniciar esta fase)

**5. Perfiles siguientes** (características se definen al llegar a cada uno)
- Fruver, Droguería, Licorera, Ferretería, etc.

> Los módulos transversales (Inventario, Caja, Reportes, Pedidos/Tienda online,
> Publicidad SidebarRight, Ayuda contextual) se construyen dentro de cada perfil
> y se reutilizan con configuración diferente según corresponda.

### Tareas de infraestructura (al terminar Fase 1 del Dashboard)
- Inicializar Git + `.gitignore` + primer commit
- Configurar Cloudflare Tunnel (reemplazar NGROK)

---

## 6. Reglas de Desarrollo

1. **Soporte tiende a cero.** Cada módulo, flujo y proceso debe diseñarse para que el Asociado pueda hacerlo solo, sin intervención del equipo EasyPosWeb. Antes de implementar cualquier proceso manual, preguntar: ¿puede automatizarse? ¿puede el Asociado hacerlo desde su propio panel?
2. **Un módulo a la vez.** No iniciar el siguiente hasta que el actual esté terminado y aprobado.
2. **Mobile-first siempre.** Verificar en móvil antes de declarar cualquier vista como completa.
3. **No romper lo que funciona.** No modificar funcionalidad existente sin confirmación explícita.
4. **Sin credenciales en código.** Nunca hardcodear contraseñas, claves JWT, URLs ni tokens — siempre variables de entorno.
5. **Sin media en Base64 en BD.** Guardar archivos en disco (`backend/app/uploads/`) y la ruta en la base de datos.
6. **Vue 3 Composition API siempre.** Nunca usar Options API.
7. **Async/await siempre.** Sin callbacks anidados ni cadenas de `.then()`.
8. **Bootstrap 5 primero.** Usar clases Bootstrap nativas antes de escribir CSS personalizado.
9. **Sin comentarios obvios.** Solo añadir comentario cuando el WHY no es evidente. Sin docstrings largos.
10. **Sin features fuera del módulo actual.** Anotar las ideas para módulos futuros en este archivo, pero no implementarlas.
11. **Cada módulo tiene su archivo de ayuda.** Al terminar un módulo, crear el documento de ayuda correspondiente.
12. **Botones estándar en tablas.** Siempre usar clases Bootstrap: Editar → `btn btn-warning btn-sm`, Eliminar → `btn btn-danger btn-sm`, Nuevo/Crear → `btn btn-primary`. No crear estilos scoped para botones de acción.
13. **Toast centrado y grande.** Usar siempre `showToast()` de `@/utils/toast.js`. El toast aparece centrado en pantalla con ícono animado (SweetAlert2). Nunca usar `alert()`, toasts de esquina, ni `console.log` como feedback visual.
13. **Validación con foco y resaltado.** Usar `validateForm()` de `@/utils/validate.js` en todos los formularios. Al fallar: resalta el campo inválido con borde rojo (clase `field-invalid`) y mueve el foco a ese campo. Solo mostrar un error a la vez (el primero que falla). La descripción y campos opcionales no se validan. Quitar el resaltado al momento en que el usuario escribe en el campo (`@input="clearError($event)"`).
14. **Errores legibles en español.** Toda respuesta de error del backend debe tener un mensaje entendible por el usuario.
14. **El Footer siempre es negro.** No es personalizable bajo ninguna circunstancia.
15. **Commits descriptivos.** Mensajes de commit claros que expliquen el QUÉ y el POR QUÉ.

---

## 7. Seguridad

### Ya implementado
- JWT con sesiones persistidas en base de datos
- Protección de rutas con guards en Vue Router
- Hash de contraseñas con bcrypt
- Tokens de recuperación de contraseña con expiración (30 min)
- CORS configurado para orígenes conocidos

### Pendiente implementar
- Mover `SECRET_KEY`, `DATABASE_URL`, `EMAIL_PASSWORD` a variables de entorno
- Rate limiting en endpoints de autenticación (login, recuperar contraseña)
- Headers de seguridad HTTP: `X-Frame-Options`, `X-Content-Type-Options`, `CSP`
- Suprimir stack traces en producción (configurar modo `debug=False` en FastAPI)
- Validación y sanitización de inputs de archivo (uploads)
- Refresh tokens para sesiones largas

### Reglas de seguridad fijas
- Nunca exponer datos de un Asociado a otro Asociado
- Nunca exponer datos internos de SYSADMIN a los Asociados
- Validar permisos en el backend — no confiar solo en el frontend
- Los planes de suscripción limitan funcionalidades: validar en backend, no solo en UI

---

## 8. Variables de Entorno

### Backend — `backend/.env` (crear si no existe)
```
DATABASE_URL=mysql+pymysql://usuario:password@localhost/easyposweb
JWT_SECRET_KEY=<clave-aleatoria-larga-y-segura>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
EMAIL_SENDER=easypos.co@gmail.com
EMAIL_PASSWORD=<app-password-de-gmail>
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
FRONTEND_URL=http://localhost:5173
```

### Frontend — `frontend/.env`
```
VITE_API_URL=http://127.0.0.1:8000
VITE_APP_VERSION=1.0.2
```
> En desarrollo local usar `http://127.0.0.1:8000`.
> Cuando se configure Cloudflare Tunnel, actualizar `VITE_API_URL` al dominio del túnel.

---

## 9. Tunneling para Testing del Equipo

**Herramienta decidida:** Cloudflare Tunnel (reemplaza NGROK)
**Estado:** Pendiente configurar al terminar Fase 1 del dashboard

**Ventajas sobre NGROK:**
- Completamente gratuito
- Dominio estático permanente (no cambia entre reinicios)
- Sin límite de conexiones simultáneas
- Puede tunnelizar backend (8000) y frontend (5173) simultáneamente

**Configuración pendiente:** instalar `cloudflared`, crear cuenta Cloudflare, configurar túnel y actualizar `VITE_API_URL` y las URLs de email.

---

## 10. Estructura de Archivos Clave

```
EasyPosWeb/
├── CLAUDE.md                    ← este archivo
├── iniciar_proyecto.bat         ← script de inicio (backend + frontend)
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/index.js      ← rutas y guards de autenticación
│   │   ├── views/               ← páginas completas
│   │   ├── components/
│   │   │   ├── layout/          ← MainLayout, SidebarLeft, SidebarRight, Topbar, FooterBar
│   │   │   └── dashboard/       ← KpiCards, TaskTable, ChartsArea
│   │   ├── services/            ← capa de llamadas a la API (apis.js, authService.js, etc.)
│   │   ├── stores/              ← Pinia stores (menuStore.js, etc.)
│   │   └── styles/              ← CSS global, variables, layout, forms
│   └── .env
└── backend/
    ├── app/
    │   ├── main.py              ← entrada FastAPI, CORS, routers
    │   ├── database.py          ← conexión SQLAlchemy
    │   ├── auth/                ← JWT, hash de contraseñas, dependencias
    │   ├── models/              ← modelos SQLAlchemy (22 tablas)
    │   ├── routers/             ← endpoints API (20 routers)
    │   ├── schemas/             ← Pydantic request/response
    │   ├── services/            ← lógica de negocio
    │   ├── crud/                ← operaciones de base de datos
    │   ├── utils/               ← email_service.py, etc.
    │   └── uploads/             ← archivos subidos (imágenes, audios, videos)
    └── alembic/                 ← migraciones de base de datos
```

---

## 11. Ideas y Features Futuras (no implementar hasta su módulo)

- Módulo de Pedidos: operable desde SidebarLeft o desde link externo; funciona online y en red local sin internet
- Módulo de Caja: cuadre diario con gastos, compras, vales, ingresos; reporte imprimible (pantalla, Excel, impresora Bluetooth/USB)
- Módulo de Inventario: gestión de productos, stock, seguimiento, impresión de etiquetas
- Módulo de Reportes: Excel, gráficos, estadísticas según perfil
- Tienda online / catálogo público por Asociado
- Factura electrónica (solo plan Premium)
- Soporte multi-idioma (estructura ya presente en BD)
- App nativa o PWA para instalación en móvil
