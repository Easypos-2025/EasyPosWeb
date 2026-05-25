# CLAUDE.md — Perfil 1: Restaurantes
# business_profile_id = 1

Nota: Actúa como un Arquitecto de Software Senior. Antes de tocar el código, analiza el problema y dame la informacion para poder proceder con el arreglo y recuerda que todo debe seguir con todos los standares de seguridad, anti robots y todo posible ataque debe estar controlado

## 1. OBJETIVO
Sistema de Gestión Gastronómica Integral (POS & ERP).

Este sistema es un ecosistema de software para restaurantes enfocado en la omnicanalidad (Mesa, Llevar, Web Propia) y el control hiperpreciso de inventarios a través de recetas y configuraciones híbridas. Interactúa directamente con la estructura de datos existente del software de escritorio y añade interfaces web dinámicas tanto para la toma de pedidos como para la visualización en cocina.

---

## 2. REGLAS DE OPERACIÓN

- **Planifica-Primero**: Antes de escribir código o crear archivos, presenta un plan breve y espera mi confirmación ("OK" o "Dale").
- **Auto-Deploy**: Cuando el usuario escriba la palabra **"commit"**, ejecutar el siguiente flujo completo en orden:
  1. `npm run build` en frontend — si hay errores, detener y reportar.
  2. `git add . && git commit -m "feat/fix: [resumen de cambios]\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"`
  3. `git push origin master`
  4. SSH al servidor: `cd /var/www/easyposweb && git pull origin master && cd frontend && npm run build && systemctl restart easyposweb`
     Comando SSH completo: `ssh -i C:\Users\Personal\.ssh\id_ed25519 root@209.38.152.254 "cd /var/www/easyposweb && git pull origin master && cd frontend && npm run build && systemctl restart easyposweb"`
  5. Actualizar `app_version` en BD del servidor con el número de compilación nuevo:
     `ssh -i C:\Users\Personal\.ssh\id_ed25519 root@209.38.152.254 "mysql -u root -p123456 easyposweb -e \"UPDATE system_config SET config_value='[BUILD]' WHERE config_key='app_version';\"""`
  6. Reportar al usuario: **"Deploy listo. Compilación: v[BUILD]"** — donde BUILD = `YY.MM.DD·shortHash`
  - El footer ya muestra el BUILD automáticamente al hacer build en servidor (vite.config `__APP_BUILD__`).
- **Switch-Profile**: Para cambiar perfil: `cp CLAUDE.md CLAUDE_PERFIL_[ANT].md` y luego `cp CLAUDE_PERFIL_[NUEVO].md CLAUDE.md`.
- Todos los campos donde se describa un valor de pesos debe tener el formato de moneda correspondiente al país del Asociado.
-la apliacion esta enfocada todo se haga en un 80% desde movil, entonces siempre tener en cuenta los dos media querys, para los dos tamaños de movil, para tablet y para pc
---

## 3. REGLAS TÉCNICAS

- **i18n**: Usar `vue-i18n` para traducciones. Idioma default: `es`.
- **Moneda**: Formatear siempre según el Asociado (`currency_code`). Usar `Intl.NumberFormat`.
- **Backend**: Los mensajes de error de la API deben venir del backend ya traducidos o con códigos de error estándar.

---

## 4. REGLA: NUEVA VISTA → SIEMPRE REGISTRAR EN system_modules

- **Auto-SystemModule**: Cada vez que se cree una vista nueva con ruta propia (`/xxx/yyy`), ejecutar automáticamente:
  ```sql
  INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
  VALUES ('[Nombre]', '/ruta/vista', 'bi-icon', NULL, 1, 0, 0);
  ```
  - `parent_id = NULL` para que el usuario lo asigne en SidebarMenuManager.
  - `is_sysadmin = 0` salvo que sea exclusiva de SYSADMIN.
  - Sin esta entrada la vista no aparece en el menú ni funciona el sistema de permisos por roles.

---

## 5. REGLA: NUEVO PERFIL DE NEGOCIO → BARRA DE INDICADORES OBLIGATORIA

- **Auto-KPI-Bar**: Todo dashboard de perfil de negocio nuevo (incluyendo SYSADMIN) debe incluir una barra de indicadores (KPI bar) al inicio de la vista.
- La barra muestra tarjetas de métricas clave del perfil (ej: totales, pendientes, alertas).
- Todos los perfiles actuales ya la tienen; es regla global para perfiles futuros.
- La barra de indicadores debe ser responsive y alineada al diseño del perfil activo.
- Crear texto de bienvenida en la tabla correspondiente con información relacionada con el perfil actual, que sea de guía para el nuevo asociado. La vista ya está creada; solo es llenar la tabla con la información del perfil.

---

## 6. REGLA: CAPTIONS DINÁMICOS DESDE BD

- **Dynamic-Captions**: Ningún caption visible (títulos, botones, placeholders, mensajes vacíos) debe tener quemado el nombre de un módulo o entidad que provenga de `system_modules`.
- Usar siempre el composable `useModuleName()` (`@/composables/useModuleName.js`):
  - Sin parámetro → usa la ruta actual para encontrar el módulo en `menuStore`.
  - Con ruta explícita → `useModuleName('/ruta/modulo')` para referenciar otro módulo (ej: padre).
- Ejemplos correctos: `Nuevo {{ moduleName }}`, `:placeholder="\`Buscar ${moduleName}...\`"`.
- Si el nombre cambia en BD, todos los captions se actualizan solos sin tocar código.
- **Aplica a todas las vistas nuevas y a las existentes cuando se modifiquen.**

---

## 7. HOJA DE RUTA

### 7.1 Origen y Estado de los Pedidos (Canales)
- **Servicio a la Mesa**: Comandado por meseros desde su interfaz web móvil. Vinculado a zonas y mesas.
- **Para Llevar (Takeout)**: Facturado o comandado directamente desde caja.
- **Compra Online (Web Propia)**: Los pedidos ingresan al sistema en estado "Pendiente". El sistema debe emitir una notificación/alerta en pantalla. No se envían a producción hasta que el pago sea confirmado y el pedido sea explícitamente "Aceptado" por el administrador.
- Nota: No se contempla integración nativa con plataformas externas (Rappi, etc.) en esta etapa.

### 7.2 Control de Inventario y Recetas (Lógica de Descuento)
El motor de inventario descuenta insumos del almacén basándose en el costo y cantidad de la receta. Un producto descuenta existencias según dos posibles orígenes:
- **Insumos Fijos**: Ingredientes obligatorios predefinidos en la receta (Ej: El pan y la carne de una hamburguesa).
- **Insumos Dinámicos (Opciones de Armado / Modificadores)**: Opciones que el cliente elige al momento (Ej: Tamaño de pizza, ingredientes extra, adiciones). Cada opción suma/resta sus respectivos insumos.

**Menú Ejecutivo / Diario (Estructura Híbrida):**
- **Regla de Bloqueo**: Si el administrador no "arma" el menú del día por la mañana (asignando qué sopa, qué principio y qué proteína aplican para la fecha), el producto queda bloqueado y no se puede comandar.
- **Descuento Combinado**: Al venderse, descuenta los insumos fijos (Ej: Arroz, jugo) MÁS los insumos de las opciones seleccionadas por el cliente en la mesa para ese día específico.
- **Validación de Captura**: Si el artículo está tipificado para requerir Peso exacto o Cantidad, la interfaz de la comanda exige obligatoriamente esta información antes de permitir el guardado.
- **Stocks**: Control estricto de stocks mínimos por insumo (asociados a sus unidades de medida).

### 7.3 Listas de Precios Contextuales
Un mismo artículo de venta debe soportar múltiples precios simultáneos. El sistema aplica el precio correcto de forma automática según la tipificación del pedido:
- **Lista 1**: Consumo en Mesa (Local).
- **Lista 2**: Para Llevar (Takeout).
- **Lista 3**: Compra por Plataforma Web Propia.

### 7.4 Sistema Multimpresión de Comandas
Los productos no están limitados a una sola tiquetera. Al crearse o editarse un producto, el administrador puede seleccionar una o múltiples impresoras de destino.
- **Regla de Ruteo**: Al confirmar una comanda, el sistema fragmenta el pedido y envía las copias en paralelo a todas las impresoras seleccionadas (Ej: Un combo de hamburguesa con cerveza imprime simultáneamente el pedido completo en la tiquetera de Cocina y solo la bebida en la tiquetera de la Barra).

### 7.5 Monitor Web de Cocina / Producción (Pantalla de TV)
- **Vista de Producción**: Interfaz web optimizada para pantallas de TV en cocina que muestra en tiempo real los pedidos aceptados y pendientes de preparación.
- **Flujo de Salida**: Los pedidos se listan de forma cronológica o por prioridad. En el momento en que un pedido es facturado o marcado como despachado en el sistema central, sale automáticamente de la pantalla del televisor.

### 7.6 Integración de Datos y Conectividad
- **Estructura de Base de Datos**: No diseñar un esquema nuevo. El sistema debe acoplarse, leer y escribir respetando estrictamente la estructura de datos preexistente en el software de escritorio actual.
- **Sincronización**: Toda transacción hecha en la web de meseros, caja o plataforma web debe actualizar el inventario, los estados de mesas y las colas de impresión de la base de datos unificada del software de escritorio.

### 7.7 No hacer commit + deploy hasta que no se diga o acepte con un Ok
presentar siempre una propuesta de diseño antes de hacer cualqueier cambio, no inventr ni suponer nada siempre preguntar. 