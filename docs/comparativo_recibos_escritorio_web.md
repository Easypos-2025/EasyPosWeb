# Comparativo Escritorio (VB6 / "maduritos") vs Web (EasyPosWeb) — Proceso de Registro de Recibo

> Documento de referencia — Paso 1 del proceso de estandarización del registro de Recibos/Facturas.
> Fuente Escritorio: base de datos local `maduritos` (211 tablas).
> Fuente Web: base de datos `easyposweb` (129 tablas).
> Generado: 2026-08-24.

---

## 1. Resumen — Estado de las 15 tablas de Escritorio

| # | Tabla Escritorio | Tabla Web equivalente | Estado |
|---|---|---|---|
| 1 | `clientes` | `clients` | ✅ Existe (con diferencias importantes, ver §2.1) |
| 2 | `consecutivo_factura_manual` | — | ❌ **NO EXISTE** (tabla ni endpoint) — ver §4 hallazgo crítico |
| 3 | `caja_recibos` | `pos_cash_register_receipts` | ✅ Existe |
| 4 | `recibos` | `pos_receipts` | ✅ Existe (mapeo 1:1 completo) |
| 5 | `recibos_credito` | — | ❌ **NO EXISTE** |
| 6 | `recibos_credito_pagos` | — | ❌ **NO EXISTE** |
| 7 | `recibos_descuentos` | `pos_receipt_discounts` | ✅ Existe |
| 8 | `recibos_forma_pago` | `pos_receipt_payment_methods` | ✅ Existe |
| 9 | `recibos_comanda` | `pos_receipt_orders` | ✅ Existe |
| 10 | `recibos_detalle_comanda` | `pos_receipt_order_details` | ✅ Existe |
| 11 | `recibos_detalle_factura` | `pos_receipt_invoice_details` | ✅ Existe |
| 12 | `recibos_detalle_comanda_producto` | `pos_receipt_order_detail_products` | ✅ Existe |
| 13 | `recibos_domicilio` | `receipt_delivery_fees` | ✅ Existe |
| 14 | `bonos` | — | ❌ **NO EXISTE** |
| 15 | `separados` | — | ❌ **NO EXISTE** |

**10 de 15 ya existen en Web** (todas las que conforman el "cuerpo" del recibo: cabecera, comanda, detalle, descuentos, forma de pago, domicilio, caja).
**5 no existen**: 1 relacionada con numeración (`consecutivo_factura_manual`) y 4 relacionadas con funcionalidades de negocio aún no portadas (crédito de clientes, bonos/tarjetas de regalo, apartados/separados).

---

## 2. Detalle campo a campo — Tablas que SÍ existen en ambos escenarios

Convenciones: `Escritorio → Web`. Cuando el campo no tiene equivalente se marca **[FALTA EN WEB]**. Los campos exclusivos de Web (no vienen de escritorio) se listan aparte — casi siempre son `company_id` (multi-tenant) y `synced`/`updated_at` (control de sincronización).

### 2.1 `clientes` → `clients`

| Escritorio | Tipo | Web | Tipo | Nota |
|---|---|---|---|---|
| Id_Cliente (PK, auto) | bigint | id (PK, auto) | int | |
| — | | company_id | int (PK/MUL) | multi-tenant, no existe en escritorio |
| cedula | varchar(50) | document_number | varchar(50) | |
| — | | document_type | varchar(20) | **[FALTA EN ESCRITORIO]** — desktop no distingue tipo de documento |
| nombres + Apellidos | varchar(50) x2 | name | varchar(200) | **Web unifica en un solo campo** — hay que definir regla de concatenación |
| direccion | varchar(50) | address | text | |
| telefono | varchar(250) | phone | varchar(20) | ⚠️ Web es más corto (20 vs 250) — revisar si telefono desktop guarda varios números |
| Mail | varchar(50) | email | varchar(150) | |
| Barrio | varchar(50) | — | | **[FALTA EN WEB]** |
| Cod_Barrio | int | — | | **[FALTA EN WEB]** |
| Dia_Cumple / Mes_Cumple | varchar(50) | — | | **[FALTA EN WEB]** |
| Edad | varchar(50) | — | | **[FALTA EN WEB]** |
| Ocupacion | varchar(50) | — | | **[FALTA EN WEB]** |
| Porc_Descuento | varchar(50) | price_list_id | int | Web usa **listas de precio** en vez de % de descuento individual — modelo distinto, no es mapeo directo |
| Observaciones | varchar(255) | — | | **[FALTA EN WEB]** |
| Fecha_Aniversario | date | — | | **[FALTA EN WEB]** |
| Fecha_Grado | date | — | | **[FALTA EN WEB]** |
| Empresa | varchar(150) | — | | **[FALTA EN WEB]** |
| Id_Klob | varchar(50) | — | | legado, probablemente no aplica |
| Tarjeta_Fiel | varchar(50) | — | | **[FALTA EN WEB]** (tarjeta de fidelización) |
| Id_Sede | int | — | | **[FALTA EN WEB]** (multi-sede) |
| Referencia | varchar(255) | — | | **[FALTA EN WEB]** |
| Enviada_MySql | tinyint | — | | ⚠️ `clients` en Web **no tiene columna `synced`** — a diferencia de todas las demás tablas de este flujo. Confirmar cómo se sincroniza un cliente hoy. |
| — | | is_active | smallint | exclusivo Web |
| — | | created_at | timestamp | exclusivo Web |
| — | | plan_blocked / plan_blocked_at | tinyint/datetime | exclusivo Web (control de plan SaaS) |

### 2.2 `caja_recibos` → `pos_cash_register_receipts`

| Escritorio | Web | Nota |
|---|---|---|
| Nro_Caja (PK) | register_number | ⚠️ En Web **no es parte de la llave primaria** (en escritorio sí). PK Web = (`receipt_number`, `company_id`). |
| Id_Caja | closing_id | ⚠️ Revisar semántica: ¿"Id_Caja" en escritorio identifica la caja física o el cierre? El nombre Web sugiere "cierre" (closing) |
| Nro_Factura (PK) | receipt_number (PK) | |
| Fecha | date | |
| Nro_Pedido | order_number | |
| Valor | amount | |
| Base | base_amount | |
| Impuesto_Iva | tax_vat | |
| Impuesto_Impoconsumo | tax_consumption | |
| Empleado | employee_id | |
| Turno | shift | |
| Pc_Desde | source_pc | |
| Cod_domiciliario | delivery_person_id | |
| Observacion_factura | notes | |
| Prefix | prefix | |
| Fac_PE | fac_pe | |
| Enviada_MySql | synced | |
| — | company_id (PK) | exclusivo Web |
| — | updated_at | exclusivo Web |

### 2.3 `recibos` → `pos_receipts`  ✅ (mapeo 1:1 completo, sin faltantes)

| Escritorio | Web |
|---|---|
| Nro_Factura (PK) | receipt_number (PK) |
| Fecha | date |
| Valor_Efectivo | cash_amount |
| Descuento | discount |
| Cedula | id_number |
| Empleado | employee_id |
| Anulada | voided |
| Pago_Iva | paid_vat |
| Arreglo | adjustment |
| Valor_T_Credito | credit_card_amount |
| Valor_T_Debito | debit_card_amount |
| Propina | tip |
| Turno | shift |
| Hora | time |
| Hora_Texto | time_text |
| Propina_Extra | extra_tip |
| Valor_Sin_Propina | amount_without_tip |
| Analizada | analyzed |
| Tipo_Moneda | currency_type |
| Valor_Extrangero | foreign_amount |
| Factura_Manual | manual_receipt |
| Id_Resolucion | resolution_id |
| Id_Cliente | customer_id |
| Factura_Reserva | reservation_receipt |
| Factura_Domicilio | delivery_receipt |
| Enviada_MySql | synced |
| — | company_id (PK), updated_at — exclusivos Web |

### 2.4 `recibos_descuentos` → `pos_receipt_discounts`

| Escritorio | Web | Nota |
|---|---|---|
| Id_Descuento | id_registro | ⚠️ En escritorio esta tabla **no tiene PK declarada** (ni PRI ni auto_increment). Web sí normalizó con `id` autoincrement propio + `id_registro` guardando el valor original. |
| Fecha | date | |
| Prefix | prefix | |
| Factura | receipt_number | |
| Id_Plato | dish_id | |
| Item | item | |
| Id_Tipificacion | typification_id | |
| Valor_Original_Producto | original_price | |
| Valor_Venta_Producto | sale_price | |
| Valor_Base | base_value | |
| Valor_Impuesto | tax_value | |
| Valor_Descuento_Pesos | discount_amount | |
| Porcentaje | percentage | |
| Motivo | reason | |
| Nro_Pedido | order_number | |
| Enviada_MySql | synced | |
| — | id (PK auto), company_id, updated_at | exclusivos Web |

### 2.5 `recibos_forma_pago` → `pos_receipt_payment_methods`

| Escritorio | Web | Nota |
|---|---|---|
| Item (PK) | item (PK) | |
| Id_Forma_Pago (PK) | payment_method_id (PK) | |
| Id_Tarjeta (PK) | card_id (PK) | |
| Nro_Factura (PK) | **invoice_number** (PK) | ⚠️ Inconsistencia de nombre: aquí se llama `invoice_number`, no `receipt_number` como en las demás tablas de recibo |
| Valor | amount | |
| Fecha | date | |
| Autorizacion | authorization | |
| Observacion | notes | |
| Valor_Domicilio | delivery_amount | |
| Prefix | prefix | |
| Fac_PE | fac_pe | |
| Nro_Pedido | order_number | |
| Enviada_MySql | synced | |
| — | company_id (PK), updated_at | exclusivos Web |

### 2.6 `recibos_comanda` → `pos_receipt_orders`

| Escritorio | Web |
|---|---|
| Nro_Pedido (PK) | order_number (PK) |
| Fecha (PK) | date (PK) |
| Nro_Factura (PK) | receipt_number (PK) |
| Mesa | table_name |
| Hora | time |
| Mesero | waiter_id |
| Cancelado | cancelled |
| Valor | amount |
| Novedad | notes |
| Cortesia | complimentary |
| Nro_Comenzales | guests_count |
| Domicilio | delivery |
| Id_Cliente | customer_id |
| Id_Mesa | table_id |
| Enviada_MySql | synced |
| — | company_id (PK), updated_at |

### 2.7 `recibos_detalle_comanda` → `pos_receipt_order_details`

| Escritorio | Web |
|---|---|
| Nro_pedido (PK) | order_number (PK) |
| Fecha (PK) | date (PK) |
| Nro_Factura (PK) | receipt_number (PK) |
| Id_Plato (PK) | dish_id (PK) |
| Item (PK) | item (PK) |
| Depende (PK) | depends_on (PK) |
| Cantidad | quantity |
| Valor | amount |
| Novedad | notes |
| Cortesia | complimentary |
| Porc_Descuento_Plato | dish_discount_pct |
| Porc_Descuento_General | general_discount_pct |
| Nro_Puesto | seat_number |
| Cambios | changes |
| Hora_Plato | dish_time |
| Paga_Impuesto | pays_tax |
| Impuesto | tax |
| Impuesto_Original | original_tax |
| Paga_Plato | pays_dish |
| Producto_Personalizado | custom_product |
| Enviada_MySql | synced |
| — | company_id (PK), updated_at |

### 2.8 `recibos_detalle_factura` → `pos_receipt_invoice_details`

| Escritorio | Web |
|---|---|
| Nro_Factura (PK) | receipt_number (PK) |
| Nro_Pedido (PK) | order_number (PK) |
| Fecha (PK) | date (PK) |
| Id_Plato (PK) | dish_id (PK) |
| Item (PK) | item (PK) |
| Depende (PK) | depends_on (PK) |
| Cantidad | quantity |
| Novedad | notes |
| Valor_Plato | dish_amount |
| Cortesia | complimentary |
| Porc_Descuento | discount_pct |
| Enviada_MySql | synced |
| — | company_id (PK), updated_at |

### 2.9 `recibos_detalle_comanda_producto` → `pos_receipt_order_detail_products`

| Escritorio | Web | Nota |
|---|---|---|
| Nro_pedido (PK) | order_number (PK) | |
| Fecha (PK) | date (PK) | |
| Nro_Factura (PK) | **invoice_number** (PK) | ⚠️ misma inconsistencia de nombre que en §2.5 |
| Id_Plato (PK) | dish_id (PK) | |
| Item (PK) | item (PK) | |
| Id_Grupo (PK) | group_id (PK) | |
| Id_Item (PK) | item_id (PK) | |
| Cantidad | quantity | |
| Enviada_MySql | synced | |
| — | company_id (PK), updated_at | |

### 2.10 `recibos_domicilio` → `receipt_delivery_fees`

| Escritorio | Web | Nota |
|---|---|---|
| Id_Registro | id_registro | Web agrega `id` (PK auto) nuevo y conserva el original en `id_registro` |
| Nro_Factura | invoice_number | |
| Valor | amount | |
| Fecha | date | |
| Nro_Pedido | order_number | |
| Vendedor | employee_id | |
| Id_Cliente | customer_id | |
| Enviada_MySql | synced | |
| — | id (PK auto), company_id, updated_at | |

> Nota: existe además `invoice_delivery_fees` en Web, estructuralmente idéntica — es la versión para **facturas** (documento fiscal), en paralelo a `receipt_delivery_fees` para **recibos** (documento interno). Confirma que Web ya distingue Recibo vs Factura como dos flujos paralelos con tablas espejo (`pos_receipt_*` vs tablas de factura equivalentes), tal como se planea abordar después para el registro de Factura (POS Electrónico / Factura Electrónica).

---

## 3. Tablas de Escritorio que AÚN NO EXISTEN en Web

Se listan tal cual están en escritorio, a la espera de la descripción funcional de cada una para diseñar su estructura Web (nombre de tabla, tipos, y si aplican company_id/synced/updated_at como en las demás).

### 3.1 `consecutivo_factura_manual`
| Campo | Tipo |
|---|---|
| Id_Consecutivo (PK, auto) | int |
| Nro_Pedido (UNIQUE) | varchar(255) |
| Fecha | date |
| Id_Resolucion | int |
| Enviada_MySql | tinyint |

### 3.2 `recibos_credito`
| Campo | Tipo |
|---|---|
| Id_Credito (PK, auto) | int |
| Nro_Factura | varchar(100) |
| Fecha | varchar(50) |
| Id_Cliente | int |
| Valor_Inicial | double |
| Valor_Actual | double |
| Observaciones | longtext |
| Cancelada | tinyint |
| Anulada | tinyint |
| Turno | tinyint |
| Enviada_MySql | tinyint |

### 3.3 `recibos_credito_pagos`
| Campo | Tipo |
|---|---|
| Id_Pago (PK, auto) | bigint |
| Id_Caja | bigint |
| Id_Credito | int |
| Fecha_Pago | varchar(50) |
| Valor_Pago | double |
| Valor_Actual | double |
| Observaciones | longtext |
| Turno | tinyint |
| Item_Forma_Pago | tinyint |
| Id_Forma_Pago | tinyint |
| Nro_Factura | varchar(50) |
| Enviada_MySql | tinyint |

### 3.4 `bonos`
| Campo | Tipo |
|---|---|
| Id_Bono (PK, auto) | bigint |
| Id_Cliente | double |
| Id_Tipo_Bono | double |
| Valor_Bono | double |
| Fecha_Inicio | date |
| Fecha_Vence | date |
| Redimido | tinyint |
| Fecha_Redimido | date |
| Anulado | tinyint |
| Nro_Factura | varchar(50) |
| Observaciones | mediumtext |
| Cod_Empleado | int |
| Nro_Factura_Recompra | varchar(50) |

### 3.5 `separados`
| Campo | Tipo |
|---|---|
| Id_Registro (PK) | bigint |
| Id_Cliente | double |
| Fecha_Registro | date |
| Valor_Total | double |
| Saldo | double |
| Bono | double |
| Codigo_Usuario | varchar(255) |
| Notas | varchar(255) |
| Anulada | tinyint |
| Facturado | tinyint |
| Nro_Factura | varchar(50) |
| Nro_Gasto | double |
| Id_Bono | double |
| Nota_Anulacion | mediumtext |

---

## 4. Hallazgos importantes a resolver antes de definir la función de registro

1. **`consecutivo_factura_manual` ya se intenta sincronizar y falla silenciosamente.** El script `vb6_sync/SincronizarConsecutivoFacturaManual.bas` apunta al endpoint `POST /sync/push/consecutivo-factura-manual`, pero ese endpoint **no existe** en `backend/app/routers/pos_sync_router.py` y la tabla `consecutivo_factura_manual` **no existe** en `easyposweb`. Cualquier instalación de escritorio que tenga este sync activo está recibiendo error 404 en este punto. Prioridad alta para el próximo paso.
2. **`clients` no tiene columna `synced`**, a diferencia de todas las demás tablas del flujo (que sí la tienen). Hay que confirmar cómo se resuelve hoy la sincronización/creación de clientes desde escritorio (¿por `document_number` con upsert directo, sin bandera de sync?).
3. **Inconsistencia de nombre de columna** `receipt_number` vs `invoice_number` dentro del mismo grupo de tablas de recibo (`pos_receipt_payment_methods` y `pos_receipt_order_detail_products` usan `invoice_number`; el resto usa `receipt_number`). No es un error funcional pero conviene tenerlo presente al construir la función unificada para no equivocar el nombre del parámetro.
4. **`clientes.nombres` + `clientes.Apellidos` (2 campos) vs `clients.name` (1 campo)** — falta definir la regla de combinación/separación al sincronizar en ambos sentidos.
5. **`clientes.Porc_Descuento` (% individual) vs `clients.price_list_id` (lista de precios)** — son modelos de negocio distintos, no un simple rename de columna.
6. **`caja_recibos`: la llave primaria cambia de forma** — en escritorio es (`Nro_Caja`, `Nro_Factura`); en Web es (`receipt_number`, `company_id`). Confirmar si `register_number` (antes `Nro_Caja`) sigue siendo relevante como dato o si se reemplazó conceptualmente por `company_id` + `closing_id`.
7. **`recibos_descuentos` no tiene PK en escritorio** (deuda técnica heredada); Web ya lo resolvió con un `id` autoincrement propio.

---

## 5. Próximo paso

Pendiente: el usuario aportará la descripción funcional de cada tabla (qué información guarda y para qué se usa) para completar el contexto de negocio, y con eso se procede a:
1. Resolver los hallazgos del §4.
2. Diseñar las 5 tablas Web faltantes (§3).
3. Definir la función/módulo único de registro de Recibo (y su contraparte de Factura, en una fase posterior).
