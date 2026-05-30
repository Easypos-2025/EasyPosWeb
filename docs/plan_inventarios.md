# Plan de Inventarios — EasyPosWeb
**Versión:** 1.0 — 2026-05-29  
**Perfil:** Restaurantes (business_profile_id = 1)  
**Segmento objetivo:** Pequeñas y medianas empresas (PyMEs)

---

## 1. El campo central: `supply_items.stock_qty`

Saldo vivo de cada insumo. Es el único número que representa la existencia real
en bodega en todo momento. No existe otro lugar donde consultar el stock actual.
Todo evento que lo modifica (venta, entrada, salida, inventario físico) queda
registrado en `stock_movements` para trazabilidad completa.

---

## 2. Ciclo de vida del stock

```
PUNTO CERO
    │
    ▼
Inventario Físico ──── establece stock_qty (reemplaza TODO, siempre parte de cero)
    │
    │   ← SUMA:  Entradas manuales (compras)       → VB6 Desktop por ahora
    │   ← RESTA: Salidas manuales (daños, mermas)  → VB6 Desktop por ahora
    │   ← RESTA: Ventas (3 canales web + VB6)
    │
    ▼
Nuevo Inventario Físico ──── guarda histórico del corte → aplica nuevos valores
```

---

## 2.1 Inventario Físico — El evento de corte (`inventory_physical`)

### Comportamiento exacto
- El formulario carga todos los insumos activos con `control_stock = 1` con **cantidad = 0**
- El usuario recorre la bodega y llena las cantidades reales encontradas:
  - Forma **manual**: digita la cantidad en cada campo
  - Forma **código de barras**: escanea el código → el campo del insumo se enfoca → digita cantidad
  - `supply_items` ya tiene campo de código de barras para este efecto
- Si no digita nada en un ítem → queda en `0` → significa "no había existencias"
- **No arrastra ni pre-carga el `stock_qty` actual** — siempre arranque limpio en cero
- **Sin flujo de aprobación** para PyMEs. El campo `autorizada` existe por compatibilidad
  con VB6 pero la web siempre lo envía en `1` — se aplica al instante.

### Proceso de cierre ("Generar corte")

```
Paso 1 → SNAPSHOT
         Se registra en stock_movements (movement_type = 'physical_snapshot')
         el stock_qty actual de TODOS los insumos activos con control_stock = 1,
         antes de sobreescribir nada.

Paso 2 → APLICAR
         Se actualiza stock_qty de TODOS los insumos:
         - Los contados  → nuevo valor digitado
         - Los no tocados → 0
         Se insertan registros en inventory_physical (uno por ítem).
         Se insertan registros en stock_movements (movement_type = 'physical')
         con qty_before = valor del snapshot, qty_after = valor contado.

Paso 3 → REPORTE DE DIFERENCIAS
         Se genera y muestra comparativo:
         Insumo | Stock sistema (antes) | Conteo físico | Diferencia | %
         Diferencia negativa = faltante (base para cobros)
         Diferencia positiva = sobrante (posible error en receta o descuento)
         Exportable a PDF / Excel.
```

### Historial de cortes
Cada evento de inventario físico se identifica por `fecha` en `inventory_physical`.
El historial agrupa por fecha y permite ver el reporte de diferencias de cualquier
corte pasado.

---

## 2.2 Entradas — `inventory_entries` (suma al stock)

- **Por ahora desde VB6 Desktop.**
- El sync VB6 sube vía `POST /api/pos/sync/push/inventory-entries`.
- El servidor aplica `stock_qty += cantidad` y registra en `stock_movements`.
- Vista web de entradas: **fase posterior**.

---

## 2.3 Salidas — `inventory_exits` (resta al stock)

- **Por ahora desde VB6 Desktop.**
- El sync VB6 sube vía `POST /api/pos/sync/push/inventory-exits`.
- El servidor aplica `stock_qty -= cantidad` y registra en `stock_movements`.
- Vista web de salidas: **fase posterior**.

---

## 2.4 Ventas — Descuento automático de stock

### Los 3 canales

| Canal | Mecanismo | Cuándo descuenta |
|---|---|---|
| **VB6 Desktop** | Sync sube tablas de detalle → servidor aplica descuento | Al momento del sync |
| **Web (factura / recibo web)** | Backend aplica en tiempo real al confirmar la venta | Al momento de facturar |
| **Canal online (tipo Rappi)** | Al aceptar + facturar el pedido, backend aplica | Al momento de facturar |

### Las dos tablas de consumo de insumos por venta

Hay dos tipos de documento de venta, cada uno con su tabla de insumos:

| Tipo de documento | Tabla de insumos consumidos |
|---|---|
| Factura DIAN | `pos_order_detail_products` |
| Recibo no-DIAN | `pos_receipt_order_detail_products` |

Ambas tienen la misma estructura (`id_item`, `quantity`, etc.).
**Ambas deben descontar `stock_qty`** — tanto por sync VB6 como por venta web.

### Sin riesgo de doble descuento
- VB6 marca registros con `Enviada_MySql = 1` tras sincronizar → no se reenvían
- Facturas/recibos web están ya en el servidor → VB6 nunca los sincroniza
- Cada canal toca exclusivamente sus propios registros

---

## 2.5 Trazabilidad — `stock_movements`

Toda modificación de `stock_qty` deja una fila en esta tabla.

| Campo | Descripción |
|---|---|
| `movement_type` | `physical_snapshot` / `physical` / `entry` / `exit` / `sale_vb6` / `sale_web` / `sale_online` |
| `qty_before` | Stock antes del evento |
| `qty_after` | Stock después del evento |
| `qty` | Delta (qty_after - qty_before) |
| `movement_date` | Fecha del movimiento |
| `reference_type` | Origen (`physical` / `entry` / `exit` / `invoice` / `receipt`) |
| `reference_id` | ID del documento origen |
| `created_by` | ID de usuario que generó el movimiento |

---

## 3. Las vistas del módulo de inventario

### 3.1 Stocks Actuales ← PRIORIDAD 1 (nueva)

**Propósito:** Monitorear el saldo vivo de todos los insumos en tiempo real.

**Filtros:**
- Categoría (select dinámico)
- Estado: Activos / Inactivos / Todos (toggle)
- "Solo críticos": `stock_qty ≤ min_stock` (toggle)
- Búsqueda por nombre o código de barras

**Tabla:**

| Cód. | Insumo | Categoría | Stock actual | Unidad | Mínimo ✏️ | Estado |
|---|---|---|---|---|---|---|
| 001 | Harina trigo | Secos | 12.5 | kg | [5.0] | ✅ OK |
| 002 | Aceite girasol | Aceites | 3.0 | lt | [5.0] | 🔴 Crítico |
| 003 | Tomate chonto | Verduras | 0.0 | kg | [2.0] | ⛔ Agotado |

- `min_stock`: único campo editable inline (click → editar → Enter para guardar)
- `stock_qty`: solo lectura — se actualiza únicamente por movimientos
- Click en fila → panel/modal con historial de `stock_movements` de ese insumo

**Alertas visuales:**
- ⛔ Agotado: `stock_qty = 0`
- 🔴 Crítico: `0 < stock_qty ≤ min_stock`
- ✅ OK: `stock_qty > min_stock`
- ⚪ Sin control: `control_stock = 0` o `min_stock = 0`

**Exportar (respeta el filtro activo):**
- PDF hoja carta
- PDF tirilla térmica 80mm (código + nombre + stock + mínimo)
- Excel

---

### 3.2 Inventario Físico — PRIORIDAD 2 (mejorar la actual)

**Tab A — "Tomar inventario":**
- Selector de fecha del conteo
- Campo de búsqueda por nombre o escaneo de código de barras
- Lista de todos los insumos (`control_stock = 1`) con campo cantidad = 0
- Campo cantidad: diseño mobile-first (grande, teclado numérico)
- Botón "Generar corte": ejecuta Snapshot → Aplicar → Mostrar reporte diferencias

**Tab B — "Historial de cortes":**
- Lista de inventarios pasados agrupados por fecha
- Click en un corte → reporte de diferencias de ese día
- Exportar reporte (PDF / Excel)

---

### 3.3 Movimientos / Trazabilidad — PRIORIDAD 3 (nueva)

**Propósito:** Auditoría completa de `stock_movements`.

**Filtros:** Insumo (búsqueda), Tipo de movimiento (select), Rango de fechas

**Tabla:**

| Fecha | Insumo | Tipo | Δ Cantidad | Stock antes | Stock después | Referencia | Usuario |
|---|---|---|---|---|---|---|---|
| 29/05 | Harina trigo | Venta VB6 | -0.5 kg | 13.0 | 12.5 | Fact #1423 | sync |
| 29/05 | Harina trigo | Físico | =12.5 kg | 11.0 | 12.5 | Inv #45 | admin |
| 28/05 | Aceite | Entrada VB6 | +5.0 lt | 6.0 | 11.0 | Ent #38 | VB6 |

---

## 4. Estado actual vs. requerido

| Componente | Estado | Fase |
|---|---|---|
| `supply_items.stock_qty` | ✅ Existe | — |
| Tablas `inventory_*` y `stock_movements` | ✅ Existen | — |
| Sync VB6 entradas / salidas / físico | ✅ Funciona | — |
| Descuento stock por venta VB6 (ambas tablas) | ✅ Confirmado | — |
| Descuento stock por venta web | ⚠️ Verificar en facturación web | Próximo |
| **Vista Stocks Actuales** | ❌ No existe | **Prioridad 1** |
| **Vista Inventario Físico mejorada** | ⚠️ Versión básica | **Prioridad 2** |
| **Vista Movimientos / Trazabilidad** | ❌ No existe | **Prioridad 3** |
| CRUD Entradas / Salidas web | ⚠️ Básico | Fase posterior |
| Exportación PDF / Excel | ❌ No existe | Con Prioridad 1 |
| `PATCH /api/inventory/stock/{id_item}/min-stock` | ❌ No existe | Con Prioridad 1 |
| `POST /api/inventory/physical/bulk` | ❌ No existe | Con Prioridad 2 |
| `GET /api/inventory/physical/report/{date}` | ❌ No existe | Con Prioridad 2 |
| `GET /api/inventory/movements` con filtros | ❌ No existe | Con Prioridad 3 |

---

## 5. Módulos VB6 que afectan inventario (referencia)

| Módulo VB6 | Endpoint servidor | Efecto en stock_qty |
|---|---|---|
| SincronizarInventariosFisicos | `/sync/push/inventory-physical` | Reemplaza (si autorizada=1) |
| SincronizarInventariosEntradas | `/sync/push/inventory-entries` | Suma |
| SincronizarInventariosSalidas | `/sync/push/inventory-exits` | Resta |
| SincronizarDetalleComanda (facturas) | `/sync/push/order-detail-products` | Resta (por receta) |
| SincronizarDetalleRecibosComanda | `/sync/push/receipt-detail-products` | Resta (por receta) |
