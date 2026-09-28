
Nota: Actúa como un Arquitecto de Software Senior. Antes de tocar el código, analiza el problema y dame la informacion para poder proceder con el arreglo y recuerda que todo debe seguir con todos los standares de seguridad, anti robots y todo posible ataque debe estar controlado

## 1. OBJETIVO
Porceso de Registro de Recibos-Facturas Opcion Pedidos Montados desde toma de pedido. usaremos el perfil restaurante.

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
- La aplicación esta enfocada todo se haga en un 80% desde movil, entonces siempre tener en cuenta los dos media querys, para los dos tamaños de movil, para tablet y para pc

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

---

## 5. REGLA: CAPTIONS DINÁMICOS DESDE BD

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


### 7.6 Integración de Datos y Conectividad
- **Estructura de Base de Datos**: No diseñar un esquema nuevo. El sistema debe acoplarse, leer y escribir respetando estrictamente la estructura de datos preexistente en el software de escritorio actual.
- **Sincronización**: Toda transacción hecha en la web de meseros, caja o plataforma web debe actualizar el inventario, los estados de mesas y las colas de impresión de la base de datos unificada del software de escritorio.

### 7.7 No hacer commit + deploy hasta que no se diga o acepte con un Ok
Presentar siempre una propuesta de diseño antes de hacer cualquier cambio, no inventar ni suponer nada, siempre preguntar.

---

## 8. PROCESO: REGISTRO DE RECIBO

Existen dos modalidades para asentar el pago de un pedido:

- **Opción Cuentas**: se usa para asentar el recibo de una cuenta previamente abierta al montar el pedido. **Este es el flujo que se está desarrollando/revisando actualmente.**
- **Opción Plazoleta**: se monta el pedido y, en la misma pantalla, se hace el registro de Recibo/Factura. **Pendiente de desarrollo.**

### 8.1 Tabla `clientes`
- Todo recibo debe tener SIEMPRE un cliente asignado por defecto.
- Cliente por defecto: `id = 1`, `cedula_nit = 222222222222`, `Nombres = "Consumidor Final"`.
- Si no existe en la tabla, se debe crear la primera vez que se necesite.
- La misma regla aplica para la función **Registrar Factura**.

### 8.2 Tabla `consecutivo_factura_manual`
- Primer paso del registro del recibo: insertar un registro enviando `Nro_Pedido` y `Fecha`.
- `Nro_Pedido` se calcula como `nombre_equipo + fecha-hora` (garantiza que nunca se repita).
- Tras el insert, se consulta el consecutivo autoincremental que le tocó → ese valor es el `Nro_Factura` que relaciona todas las demás tablas involucradas en el registro del recibo.
- Si el `Nro_Pedido` ya existe: se debe mostrar un mensaje y NO continuar con el registro.
  - Solución: eliminar el `Nro_Pedido` actual (actualizando en todas las tablas temporales de `datatemppos` involucradas) y reenviar el insert.

### 8.3 Tabla `caja_recibos`
- Guarda un registro por cada recibo.
- `Nro_Caja`: identifica el número de caja (relacionada con la tabla `Cajas`, ej. caja uno, dos, tres).
- `Id_Caja`: id de la apertura de esa caja (ej. la caja 2 pudo ser abierta por un usuario X, quien luego cerró turno; otro usuario pudo abrir turno después en la misma caja). Esta información se almacena en `cajas_cierres` (`Cierre = 0` = turno abierto).
- Permite identificar: usuarios que iniciaron sesión y tuvieron venta en la caja que abrieron, venta de un usuario X en una caja/sesión específica, o toda la venta de una caja. (Aplica igual para el proceso de Registro de Facturas).
- Un usuario puede volver a abrir turno en otra caja, siempre que no tenga sesiones de caja abiertas.
- Todo movimiento que involucre dinero (gastos, compras, ingresos, etc.) debe tener un campo `id_caja` para poder determinar a cuál caja y por ende a cuál usuario corresponde, igual que `caja_recibos.id_caja`.

### 8.4 Tabla `cajas_cierres`
- Registra cada inicio de turno de un usuario en un `cajas.Nro_Caja`. **Proceso pendiente de implementar.**
- Flujo esperado:
  - Al ingresar, cada usuario debe seleccionar una caja disponible.
  - Esa caja se bloquea automáticamente (`cajas.Abierta`) para que no pueda ser abierta por otro usuario en otro PC u otra sesión.
  - Se genera de forma autoincremental el `id_caja` que usará ese usuario para todos los movimientos de su turno.
- Campos relevantes:
  - `Nro_Caja` seleccionada.
  - `Fecha`.
  - `Base_Inicial`: valor entregado al cajero para las vueltas/devueltas.
  - `Venta_Clientes` (campo reciclado): código del usuario.
  - `Pc_Abierta`: nombre del dispositivo donde se abrió la caja.
  - `Fecha_Hora_Apertura`.
  - `Cierre`: `0` = caja abierta, `1` = caja cerrada.
  - `Fecha_Hora_Cierre`: se actualiza al momento de cerrar.

### 8.5 Tabla `recibos`
- Guarda la información del encabezado del recibo. **Este proceso ya se está haciendo — revisar para confirmar que esté correcto.**

### 8.6 Tabla `recibos_comanda`
- Guarda información relevante del encabezado del pedido. **Ya implementado — revisar.**

### 8.7 Tabla `recibos_detalle_comanda`
- Guarda información relevante del detalle del pedido. **Ya implementado — revisar.**

### 8.8 Tabla `recibos_detalle_factura`
- Guarda información relevante del detalle del recibo/factura. **Ya implementado — revisar.**

### 8.9 Tabla `recibos_forma_pago`
- Guarda el detalle de la forma de pago: un registro por cada forma de pago usada.
- Solo se pueden seleccionar formas de pago con `forma_pago.Activo = 1`.
- Se puede seleccionar una o varias formas de pago hasta completar el valor total del recibo (el valor que debe pagar el cliente).
- No se debe permitir registrar el pago hasta que el total quede completamente cubierto por las formas de pago seleccionadas.

### 8.10 Tabla `forma_pago`
Catálogo de formas de pago con sus variantes:
- `Seleccionar_Tarjeta`: al seleccionar esta forma de pago, debe aparecer la opción de escoger la tarjeta usada de una lista (`tarjetas_baucher.Activa = 1`).
- `Pedir_Observacion`: exige capturar una observación para poder continuar con el proceso.
- `Pedir_Cliente`: obliga a seleccionar un cliente de la tabla `clientes`.
- `Forma_Pago_Default`: identifica la forma de pago por defecto (generalmente EFECTIVO), la cual el sistema usa automáticamente al momento de liquidar un recibo. El usuario puede cambiarla a una o varias, pero siempre debe quedar una marcada como default.

Debe existir una forma de pago **CREDITO** (`forma_pago.Descripcion_Forma_Pago = "CREDITO"`), que obligatoriamente debe tener activo `Pedir_Cliente` para seleccionar el cliente al que se le asigna el crédito.
- Al marcar el recibo como CREDITO: suma en venta, pero NO suma en dinero en efectivo para el cuadre de caja — solo suma en venta y en la casilla del cuadre "Venta a Crédito".
- Se guarda el registro correspondiente en la tabla `recibos_credito`.
- Un recibo puede tener un abono en efectivo u otra forma de pago, y el restante asignarlo a la forma de pago CREDITO. Ese restante es el valor que se guarda en `recibos_credito`, y el detalle del pago en otros medios se guarda en `recibos_credito_pagos`, de forma que la suma de ambos dé el total de la factura.

### Crear Crud Tabla forma_pago: crear el CRUD de `forma_pago` y ubicarlo en Configuración del sidebar, ya que se utiliza en todos los perfiles.

### 8.11 Tabla `recibos_credito`
Encabezado del crédito generado al escoger la forma de pago "CREDITO" al momento de pagar un recibo:
- `Id_Credito`: incremental.
- `Nro_Factura`: número del recibo.
- `Fecha`.
- `Id_Cliente`: cliente al que se le asignó el crédito (deudor).
- `Valor_Inicial`: valor de la deuda.
- `Valor_Actual`: valor de la deuda; inicia igual al `Valor_Inicial` y se va descontando con cada abono. `Valor_Actual = 0` indica que el crédito está cancelado en su totalidad.
- `Observaciones`: observación adicional relacionada con el crédito.

### 8.12 Tabla `recibos_credito_pagos`
- Guarda los registros de los pagos/abonos hechos al crédito: un registro por abono, hasta completar el `Valor_Inicial` del recibo y poder cambiar el estado a `recibos_credito.Cancelado = 1`.
- Se llena en dos situaciones:
  1. Cuando se registra el recibo y se hizo un abono parcial en otro medio de pago.
  2. Cuando se hacen abonos posteriores al crédito.

### 8.13 Tabla `recibos_descuentos`
- Guarda los descuentos generados a un recibo: un registro por cada descuento (`recibos_detalle_comanda.item`).
- Cada descuento tiene una tipificación de la tabla `tipificaciones_descuentos` (ej. descuento en pesos a un ítem, descuento del 10% a otro, cortesía 100% a otro, etc.).

### 8.14 Tabla `recibos_detalle_comanda_producto`
- Se usa para el descuento de inventarios: registra qué se debe descontar de inventario por cada ítem de `recibos_detalle_comanda`.
- Ejemplo: el producto-plato "HAMBURGUESA" es el ítem del recibo en `recibos_detalle_comanda`, pero debe descontar de inventario (`inventario_actual_porciones`) cada insumo relacionado registrado en esta tabla (Pan-Ham, Carne-Hamb, Ripio-Pap, etc.) cada vez que se venda.

### 8.15 Tabla `recibos_domicilio`
- Cuando el pedido es para domicilio, al generar el recibo se debe registrar en esta tabla: el valor cobrado por el domicilio, el `nro_recibo` (`nro_factura`), `fecha`, `nro_pedido`, el domiciliario (o el vendedor/usuario que abrió caja, en caso de no asignarse ni domiciliario ni vendedor), y el `id_cliente` al que se le lleva el domicilio.
- Si ese cliente no está en base de datos, se debe agregar al momento de registrar el pago.

### 8.16 Tabla `bonos`
Registra un bono generado en distintos escenarios:
- **Bono_x_Separado**: se genera al momento de asentar el abono inicial de un separado (módulo pendiente de desarrollo). El cliente lo presenta para ser descontado al pagar la compra total del separado. Tiene detalle en la tabla `separados` y `separados_detalle`.
- **Bono_x_Recompra**: se usa en campañas de descuento en la próxima compra (módulo pendiente de desarrollo).
- **Bono_x_Cambio**: ocurre cuando el cliente hace un cambio de prenda/producto y le queda dinero a favor; el bono se usa en su próxima compra o al momento de asentar el cambio.
- `bonos.Redimido = false` indica que el bono está disponible.
- Los bonos deben aparecer en un selector al momento de realizar un recibo, pero solo si previamente se escogió un cliente en la ventana de pago. Los bonos se manejan como una forma de pago, por lo que los distintos conceptos de bono deben existir también en `forma_pago`.
- Cuando un bono se redime, se cambia el estado a `Redimido = true` (cancelado), para que no vuelva a ser usado.
- Solo `Bono_x_Separado` genera detalle (en `separados`/`separados_detalle`); los bonos por otro concepto no generan detalle, solo los datos de la tabla `bonos`.

### 8.17 Tablas `separados` / `separados_detalle`
- **Pendientes de desarrollo.** Se abordarán cuando se trabaje ese módulo.

### 8.18 Tabla `Cajas`
- Cajas disponibles registradas por cada `company`.
- Se usa al abrir una caja: el `Nro_Caja` seleccionado por el usuario se registra en `cajas_cierres`, permitiendo identificar en cuál caja abrió turno cada usuario.

### 8.19 Funciones a ejecutar al registrar el recibo
Al momento de registrar el recibo se deben ejecutar, en este orden:
1. `Call DescontarStockRecibo(conn, Var_Nro_Recibo, Var_Fecha_Facturacion)`
2. `Call Imprimir_Recibo(Var_Nro_Recibo, Var_Nro_Pedido_Pos, False, False, False)`
3. `Call Enviar_Pedido_Impresion(Var_Nro_Pedido_Facturar_Pos, Var_Pedido_Nuevo, False, 0)`
4. `Call Imprimir_comanda_Corta(Var_Nro_Pedido_Facturar_Pos)`

### 8.20 Notas y alcance del desarrollo
- Revisar el proceso ya existente de toma del pedido, ya que es el punto de partida para asentar el pago del recibo.
- **Alcance inicial**: solo se hará Registro de Recibo sobre los pedidos tomados desde la web. Los de escritorio se seguirán manejando desde el programa de VB de escritorio.
- **Flujo esperado**:
  1. Se monta el pedido (revisar procesos ya existentes).
  2. Al momento de registrar el recibo, se debe escoger entre los pedidos montados (web).
  3. Se abre la pantalla de pago (revisar lo que ya se tiene al respecto) — aplica tanto para Recibos como para Facturas (inicialmente se desarrolla para Recibos).
- **La vista de pago (Recibo/Factura) debe permitir**:
  - Selectores de: vendedor, domiciliario, cliente, forma de pago, separado (si aplica), bono (si el separado tiene uno asociado, o por otro concepto).
  - Pagos parciales: pagar todos los ítems del pedido o seleccionar solo algunos (ej. cuando en una cuenta deciden pagar todos los comensales por separado).
  - Aplicar tipificación de descuento — **no se permite descuento sobre descuento** (si un ítem ya tiene descuento aplicado al montar el pedido, no se le puede aplicar un descuento adicional al recibo).
  - Calcular la propina si la `company` tiene habilitada la opción de liquidar propina, mostrando el % de la propina sobre la base de la cuenta a cancelar. El valor de la propina debe poder modificarse.
  - Opción **FACTURA** (si está habilitada la opción de POS electrónico).
  - Opción **RECIBO CUENTA_PREVIA**: mismo formato del recibo, pero solo informativo — NO asienta el recibo, es únicamente para mostrarle al cliente en cuánto va su cuenta.
  - Poder modificar el valor del domicilio.

### Notas Adicionales.
- revisar la estructura de las Tablas en localhost DB maduritos, y comparar con las tablas web DB EasyPosWeb Restaurante Test company_id=68, esta es la base de datos que usaremos para hacer las pruebas
- 