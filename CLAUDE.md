# CLAUDE.md — Perfil 15: Talleres Mecánica - Lavaderos - Latonería y Pintura
# business_profile_id = 15

Nota: Actúa como un Arquitecto de Software Senior. Antes de tocar el código, analiza el problema y dame la informacion para poder proceder con el arreglo y recuerda que todo debe seguir con todos los standares de seguridad, anti robots y todo posible ataque debe estar controlado

---

## 1. OBJETIVO

Sistema ERP integral para el taller mecánico, centro de estética automotriz y centro de colisión **"Perfil Serví-Cars"**. Gestiona servicios para autos y motos, venta de repuestos, taller mecánico, lavado/aspirado, y latonería y pintura. Soporta flujos de trabajo con roles específicos, gestión de convenios empresariales con reglas contables especiales, pago diario de mano de obra a operarios y venta cruzada mediante combos de servicios.

---

## 2. REGLAS DE OPERACIÓN

- **Planifica-Primero**: Antes de escribir código o crear archivos, presenta un plan breve y espera mi confirmación ("OK" o "Dale").
- **Auto-Deploy**: Cuando el usuario escriba la palabra **"commit"**, ejecutar el siguiente flujo completo en orden:
  1. `npm run build` en frontend — si hay errores, detener y reportar.
  2. `git add . && git commit -m "feat/fix: [resumen de cambios]\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"`
  3. `git push origin master`
  4. SSH al servidor: `cd /var/www/easyposweb && git pull origin master && backend/venv/bin/pip install -r backend/requirements.txt --quiet && cd frontend && npm run build && systemctl restart easyposweb`
     Comando SSH completo: `ssh -i C:\Users\Personal\.ssh\id_ed25519 root@209.38.152.254 "cd /var/www/easyposweb && git pull origin master && backend/venv/bin/pip install -r backend/requirements.txt --quiet && cd frontend && npm run build && systemctl restart easyposweb"`
  5. Actualizar `app_version` en BD del servidor con el número de compilación nuevo:
     `ssh -i C:\Users\Personal\.ssh\id_ed25519 root@209.38.152.254 "mysql -u root -p123456 easyposweb -e \"UPDATE system_config SET config_value='[BUILD]' WHERE config_key='app_version';\"""`
  6. Reportar al usuario: **"Deploy listo. Compilación: v[BUILD]"** — donde BUILD = `YY.MM.DD·shortHash`
  - El footer ya muestra el BUILD automáticamente al hacer build en servidor (vite.config `__APP_BUILD__`).
- **Switch-Profile**: Para cambiar perfil: `cp CLAUDE.md CLAUDE_PERFIL_[ANT].md` y luego `cp CLAUDE_PERFIL_[NUEVO].md CLAUDE.md`.
- Todos los campos donde se describa un valor de pesos debe tener el formato de moneda correspondiente al país del Asociado.
- La aplicación está enfocada a que todo se haga en un 80% desde móvil; siempre tener en cuenta los dos media queries: dos tamaños de móvil, tablet y PC.

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

## 7. NO HACER COMMIT + DEPLOY SIN APROBACIÓN EXPLÍCITA

Presentar siempre una propuesta de diseño antes de hacer cualquier cambio. No inventar ni suponer nada; siempre preguntar.

---

## 8. ROLES Y ACTORES DEL SISTEMA

| Rol | Responsabilidades |
|---|---|
| **Administrador / Caja** | Gestión de inventarios, facturación, CxC, egresos de nómina diaria y reportes financieros |
| **Jefe de Taller** | Apertura de órdenes, asignación de mecánicos y control de calidad en taller |
| **Jefe de Patio** | Apertura de órdenes, asignación de lavadores y control de calidad en lavado |
| **Jefe de Latonería** | Diagnóstico de colisiones, preparación, pintura y ensamble de piezas |
| **Mecánico** | Operario de ejecución en órdenes de trabajo mecánico |
| **Lavador** | Operario de ejecución en órdenes de lavado y aspirado |
| **Latonero** | Operario de reparación de piezas de carrocería |
| **Pintor** | Operario de preparación y acabado (pintura, fondo, transparente) |
| **Cliente Convenio** | Empresa aliada con condiciones de pago diferido (crédito / acumulación de órdenes) |

---

## 9. REGLAS DE NEGOCIO CRÍTICAS

### 9.1 Gestión de Convenios Empresariales (Flujo de Crédito Colectivo)
- **Operación sin Pago Inmediato:** Los vehículos vinculados a un convenio empresarial ingresan al servicio, se les genera una Orden de Servicio (OS) normal, pero se retiran **sin liquidar pago** en el momento.
- **Acumulación de Órdenes:** El sistema agrupa y mantiene en estado "Pendiente por Facturar" todas las órdenes asociadas a una misma empresa/convenio.
- **Facturación Consolidada:** El administrador puede seleccionar múltiples órdenes acumuladas (mezclando lavados, mecánicas, latonería, repuestos, etc.) y unificarlas en **una única factura o relación de cobro** detallada.

### 9.2 Lógica Contable de Caja: Convenios vs. Flujo de Efectivo Diario
- **Reconocimiento de la Venta:** Los servicios de convenios o créditos **ingresan y se registran como venta del día** (ingreso operativo / contabilidad de devengo).
- **Control de Caja Chica:** Estas ventas por convenio **NO suman en el dinero físico/efectivo del día** ni alteran el saldo real de la caja del turno; se marcan como "Cuenta por Cobrar (CxC) de Convenio".
- **Egreso por Pago Diario a Operarios:** El personal (lavadores, mecánicos, latoneros, pintores) recibe su pago por mano de obra **de forma diaria**, independientemente de si el vehículo era de convenio o particular. El sistema registra salidas de dinero diarias bajo el concepto *"Egreso: Pago de Mano de Obra Diaria"*, descontando el efectivo real de la caja del día.

### 9.3 Módulo Dinámico de Combos (Paquetes de Servicios)
Paquetes comerciales parametrizables que unifiquen mano de obra, repuestos, latonería y estética:

| Combo | Servicios incluidos |
|---|---|
| **Lavado** | Lavado sencillo + Aspirado + Polichado |
| **Revisión** | Revisión General Mecánica + Lavado Especial |
| **Mantenimiento** | Cambio de Aceite + Filtros + Lavado Sencillo |
| **Estético** | Pintura de Pieza + Lavado Especial |

---

## 10. ARQUITECTURA DE MÓDULOS

### 10.1 Módulo de Clientes, Vehículos e Historial (Core)
- **Ficha Única por Placa:** El vehículo es la entidad central. Al digitar la placa se despliega el expediente completo.
- **Datos del Vehículo:** Tipo (Auto / Moto), Modelo, Año, Kilometraje, Color, Propietario (Nombre, Documento, Teléfono, Vínculo a Convenio).
- **Historial Clínico Integral:** Trazabilidad intermodular: qué se le hizo (Mecánica / Lavado / Latonería), repuestos instalados, operario asignado, jefe responsable, fecha/hora de entrada y salida.
- **Métrica de Frecuencia:** Indicadores automáticos de comportamiento (ej. "Este vehículo asiste cada 3 meses" / "Última visita: 15/03/2026").
- **Motor de Búsqueda Global:** Filtros por Placa, Nombre del cliente, Documento, Mecánico, Lavador, Latonero/Pintor, Jefe de patio, Jefe de taller, Rango de fechas o Mes específico.

### 10.2 Módulo de Órdenes de Trabajo — Taller Mecánico
- **Apertura de Orden:** Registro mandatorio mediante Placa del vehículo.
- **Evidencia Gráfica:** Captura obligatoria de fotografías del estado del vehículo al ingresar (registro visual de daños previos).
- **Asignación de Personal:** Mecánico ejecutor + Jefe de Taller supervisor.
- **Detalle Operativo:** Diagnóstico inicial, trabajo realizado, mano de obra aplicada y repuestos utilizados.
- **Línea de Tiempo:** Fecha/Hora de Entrada, Promesa de Entrega y Entrega Real.
- **Salida Documental:** Impresión de Orden de Trabajo (física/digital) y pre-factura.

### 10.3 Módulo de Lavado y Aspirado — Centro de Estética
- **Apertura de Orden:** Registro inicial mediante Placa del vehículo.
- **Evidencia Gráfica:** Captura de fotos de ingreso para control de reclamaciones.
- **Asignación de Personal:** Jefe de Patio supervisor + Lavador ejecutor.
- **Selección de Servicios / Combos:** Catálogo parametrizado (Lavado sencillo, lavado especial, combos).
- **Tiempos:** Control de Fecha/Hora de Entrada y de Entrega.
- **Salida Documental:** Comprobante de servicio o factura directa.

### 10.4 Módulo de Latonería y Pintura — Centro de Colisión
- **Apertura de Orden:** Registro mandatorio mediante Placa + toma de kilometraje.
- **Evidencia Gráfica Rigurosa:** Fotos obligatorias de ingreso (latas, rayones, abolladuras) y registro visual **Antes / Durante / Después**.
- **Asignación de Personal:** Jefe de Latonería + Latonero (reparación de piezas) + Pintor (preparación y acabado).
- **Detalle del Servicio:** Inventario de piezas a reparar / cambiar, tipo de pintura (general, por piezas, retoque), materiales e insumos (masilla, fondo, pintura, transparente).
- **Tiempos de Proceso:** Fecha/Hora de Entrada, tiempo de preparación, tiempo de cabina/secado y Entrega Real.
- **Salida Documental:** Orden de servicio técnica y presupuesto/factura detallada.

### 10.5 Módulo de Inventario de Auto Repuestos
- **Control por Codificación:** Catálogo con Código único, Marca, Precio de Compra y Precio de Venta (Correas, filtros, aceites, insumos de pintura, etc.).
- **Descuento de Stock en Tiempo Real:** Resta automática del inventario al añadir a cualquier orden (Mecánica o Latonería) o vender por mostrador.
- **Sistema de Alertas:** Notificaciones visuales de Stock Mínimo (ej. "Quedan 2 tarros de transparente, reponer mercancía").
- **Auditoría de Inventario:** Interfaz para cuadre físico vs. sistema.
- **Módulo de Compras:** Registro formal de entrada de mercancía e insumos indexados por proveedor.

### 10.6 Reportes Financieros y Gestión de Caja
- **Cierre de Caja Diario:** Resumen dividido en: Total Ventas del Día (Efectivo + Convenios) vs. Total Dinero Real Recaudado (solo Efectivo/Transferencias).
- **Módulo de Egresos Diarios:** Panel para registrar pagos en efectivo del día a operarios (Mecánicos, Lavadores, Latoneros), restando el valor del saldo neto de la caja física.
- **Productividad de Personal:** Reporte de rendimiento por operario (mano de obra / servicios en el mes) para cálculo de comisiones o destajo diario.
- **Trazabilidad Financiera por Placa:** Reporte consolidado de todo el dinero facturado a un vehículo específico.
- **Cartera (CxC):** Panel de seguimiento de saldos acumulados de Convenios Empresariales y alertas de facturación masiva.

---

## 11. REQUERIMIENTOS TÉCNICOS Y USABILIDAD

- **Módulo de Alertas de Fidelización:** Recordatorios automáticos de mantenimiento preventivo (ej. "Cambio de aceite en 5,000 km") para estrategias de telemercadeo.
- **Gestión Multimedia:** Soporte para almacenamiento local/nube de fotos de inspección (Antes / Durante / Después).
- **Arquitectura Híbrida (Offline First):** El sistema debe garantizar operatividad local (apertura de órdenes, consulta de fichas e inventario) aun sin conexión a internet.
- **Respaldos:** Automatización de copias de seguridad en la nube para contingencias de hardware.

---

## 12. REGLA CONTABLE FORMAL DE CAJA

Se define formalmente la separación contable entre:
- **Ingreso Devengado**: venta del día de convenios (registrada, no cobrada en efectivo).
- **Flujo de Caja Real**: dinero físico disponible en caja.

El sistema registra los egresos en efectivo para el pago diario de mano de obra de latoneros y lavadores **sin descuadrar la caja principal**.
