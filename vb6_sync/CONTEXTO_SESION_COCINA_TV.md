# Contexto de Sesión — Cocina TV + Sync VB6 → datatemppos
**Fecha:** 2026-06-02 / 2026-06-03  
**Estado:** En progreso — pendiente verificar sync VB6→web

---

## 1. ARQUITECTURA GENERAL

### Bases de datos
- **`easyposweb`** → BD principal del sistema web (usuarios, módulos, pedidos históricos, etc.)
- **`datatemppos`** → BD de pedidos ACTIVOS en curso (temp_comanda, temp_detalle_comanda_parcial, etc.)
  - Existe en **local** (PC con VB6 EasyPOS desktop)
  - Existe en **servidor web** (VPS 209.38.152.254) — replicada vía HTTP API
- **`datatemppos_sync`** → BD de staging/relay creada por Claude en sesión anterior (solo en local por ahora)
  - Tablas: `sync_control`, `sync_inbox`, `sync_locks`, `sync_outbox`
  - Propósito: fue diseñada como mecanismo intermedio de sincronización (detalles en sesión anterior)

### Flujo de datos temp (pedidos activos VB6 → Web TV Cocina)
```
VB6 Desktop
  ↓ guarda pedido
datatemppos LOCAL (temp_comanda, temp_detalle_comanda_parcial, etc.)
  ↓ SubirTemp*.bas llaman ApiPost() → HTTPS POST
https://easyposweb.com/api/pos/sync/push/temp-*
  ↓ backend FastAPI escribe en
datatemppos WEB (mismo esquema, servidor VPS)
  ↓ get_cocina endpoint lee
Pantalla TV Cocina (PosKitchenView.vue)
```
 
---

## 2. ARCHIVOS VB6 SYNC RELEVANTES

Los 4 procesos que suben datos de comandas activas:
- `vb6_sync/SubirTempComandas.bas` → POST `/api/pos/sync/push/temp-comanda`
- `vb6_sync/SubirTempDetalleComanda.bas` → POST `/api/pos/sync/push/temp-details-replace`
- `vb6_sync/SubirTempPlatosProductoParcial.bas` → POST `/api/pos/sync/push/temp-assembly-replace`
- `vb6_sync/SubirTempNovedadesPlatoPedido.bas` → POST `/api/pos/sync/push/temp-notes-replace`

**Query crítica en SubirTempComandas.bas (línea 17):**
```vb
rs.Open "SELECT * FROM temp_comanda " & _
        "WHERE Movil=0 AND Fecha=DATE(NOW()) " & _
        "LIMIT " & Var_Limit_Registros, conn
```

**PROBLEMA IDENTIFICADO:** El MySQL local corre en timezone UTC. El VB6 guarda `Fecha` con la fecha Colombia (UTC-5). Después de las 7 PM Colombia, `DATE(NOW())` en MySQL local ya devuelve el día siguiente (UTC), pero los pedidos tienen la fecha Colombia del día anterior → `rs.EOF = True` → nunca llama `ApiPost` → nada llega al servidor.

**Verificado con estas queries en datatemppos LOCAL:**
```sql
-- Retorna 1 fila (filtro hardcodeado = funciona)
SELECT COUNT(*) FROM temp_comanda WHERE Movil=0 AND Fecha='2026/06/02';

-- Retorna 0 filas (DATE(NOW()) ya dice 2026-06-03 en UTC)
SELECT COUNT(*) FROM temp_comanda WHERE Movil=0 AND Fecha=DATE(NOW());
```

---

## 3. BACKEND — ENDPOINTS TEMP (pos_temp_router.py)

```
backend/app/routers/pos_temp_router.py
```

Endpoints implementados y funcionando:
- `POST /api/pos/sync/push/temp-comanda` → inserta en `datatemppos.temp_comanda`
- `POST /api/pos/sync/push/temp-details-replace` → DELETE + INSERT en `temp_detalle_comanda_parcial`
- `POST /api/pos/sync/push/temp-assembly-replace` → DELETE + INSERT en `temp_plato_producto_parcial`
- `POST /api/pos/sync/push/temp-notes-replace` → DELETE + INSERT en `temp_novedades_plato_pedido`
- `GET /api/pos/sync/pull/temp-comanda` → lectura para TV cocina
- `GET /api/pos/sync/pull/temp-details` → lectura items

**Test manual confirmado funcionando:**
```bash
curl -X POST 'https://easyposweb.com/api/pos/sync/push/temp-comanda' \
  -H 'x-api-key: easypos-sync-key-2024' \
  -H 'Content-Type: application/json' \
  -d '[{"order_number":"TEST-001","company_id":1,"date":"2026-06-03","table_name":"TEST-MESA","time":"10:00","waiter_id":1,"amount":1000}]'
# Respuesta: {"saved":["TEST-001|2026-06-03"],"failed":[],"total_sent":1,"total_saved":1,"total_failed":0}
```

---

## 4. CONFIGURACIÓN SERVIDOR (VPS 209.38.152.254)

### .env del backend (`/var/www/easyposweb/backend/.env`)
```
DATABASE_URL=mysql+aiomysql://easypos_user:EasyPos2026$Secure@localhost/easyposweb
DATATEMPPOS_URL=mysql+aiomysql://easypos_user:EasyPos2026$Secure@localhost/datatemppos
JWT_SECRET_KEY=55c86d93321f1c8d76052db16f61c599ec47373eafe50ffe34f404b56cfafa2d
...
```

### database.py
```python
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
# IMPORTANTE: la ruta busca /var/www/easyposweb/.env pero el archivo
# está en /var/www/easyposweb/backend/.env — funciona igual porque
# systemd carga el .env vía EnvironmentFile=/var/www/easyposweb/backend/.env
```

### systemd service
```
EnvironmentFile=/var/www/easyposweb/backend/.env
WorkingDirectory=/var/www/easyposweb/backend
```

### Permisos MySQL en servidor
```sql
-- easypos_user tiene acceso a AMBAS bases:
GRANT ALL PRIVILEGES ON easyposweb.* TO 'easypos_user'@'%';
GRANT ALL PRIVILEGES ON datatemppos.* TO 'easypos_user'@'%';
GRANT ALL PRIVILEGES ON easyposweb.* TO 'easypos_user'@'localhost';
GRANT ALL PRIVILEGES ON datatemppos.* TO 'easypos_user'@'localhost';
```

---

## 5. COCINA TV — LO QUE ESTÁ IMPLEMENTADO

### Backend: `pos_comanda_router.py`
- `GET /api/pos/comanda/cocina?token=...` → endpoint que lee `datatemppos.temp_comanda` + `temp_detalle_comanda_parcial`
- Agrupa ítems por `(order_number, Hora_Plato)` → una tarjeta TV por batch
- Distingue **NUEVO** (primer batch del pedido) vs **AGREGADO** (batches subsecuentes)
- Filtra: solo muestra pedidos con `tc.Salio=1` (ya enviados a cocina)
- Lee `pos_kitchen_events` para eventos **CANCELADO** y **REIMPRESION**
- Ordena DESC por `latest_dish_time` → más nuevos arriba

### Frontend: `PosKitchenView.vue`
- Cards con colores rotativos (5 colores) en el badge `#N`
- Labels: `PEDIDO NUEVO` (verde), `PEDIDO AGREGADO` (ámbar), `PEDIDO CANCELADO` (rojo + blink), `REIMPRESIÓN PEDIDO` (cyan)
- Muestra `Hora` por ítem (cuando el mesero tomó cada plato)
- Muestra `order_hora` en header (cuando se abrió la mesa)
- Sin botones de dismiss — cards se empujan hacia abajo a medida que entran nuevas

### Tabla nueva creada
```sql
-- En easyposweb (no datatemppos)
CREATE TABLE pos_kitchen_events (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  company_id INT NOT NULL,
  event_type ENUM('cancelado','reimpresion') NOT NULL,
  order_number VARCHAR(255) NOT NULL,
  table_name VARCHAR(200) DEFAULT NULL,
  waiter_id INT DEFAULT 0,
  items_snapshot MEDIUMTEXT DEFAULT NULL,
  event_date DATE NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_active (company_id, event_date)
);
-- Script: vb6_sync/migration_pos_kitchen_events.sql
```

---

## 6. PROBLEMA PENDIENTE A RESOLVER

### Root cause confirmado
El MySQL local (en PC con VB6) corre en timezone UTC. Los pedidos se guardan con fecha Colombia. Después de las 19:00 Colombia el filtro `WHERE Fecha=DATE(NOW())` falla.

### Solución propuesta (pendiente implementar)
**Opción A — Fix en MySQL local (sin tocar VB6):**
```sql
SET GLOBAL time_zone = 'America/Bogota';
```
Y en `my.ini` agregar:
```ini
[mysqld]
default-time-zone = 'America/Bogota'
```

**Opción B — Fix en VB6 (query usa fecha VB6 en lugar de NOW()):**
Cambiar en `SubirTempComandas.bas` (y los otros 3 Subir*):
```vb
' En lugar de: WHERE Movil=0 AND Fecha=DATE(NOW())
' Usar:
"WHERE Movil=0 AND Fecha='" & Format(Date, "YYYY/MM/DD") & "'"
```
Esto usa la fecha del PC local (VB6), que siempre coincide con la fecha guardada en `Fecha`.

**Recomendación:** Opción B es más robusta porque funciona independientemente del timezone del MySQL local.

---

## 7. OTROS PROBLEMAS DETECTADOS (MENORES)

### Token cocina TV expirado
En logs nginx aparece:
```
GET /api/pos/comanda/cocina?token=b96ff5e3894e33abfe761b434a47a1807507de3ccbaeb17ea365683c9d148694 → 403
```
El token en la URL de la TV de cocina expiró. El usuario debe copiar el nuevo token desde el panel de administración.

### invoice-delivery-fees retorna 422
```
POST /api/pos/sync/push/invoice-delivery-fees → 422
```
Error de validación en el payload — pendiente revisar.

---

## 8. OBSERVACIÓN IMPORTANTE SOBRE LOS LOGS

Los endpoints de tablas maestras (`zones`, `measure-forms`, `payment-types`, etc.) que aparecen en nginx corresponden a **otros asociados** que ya tienen la sincronización activa. No son del mismo asociado que está probando el sync de temp. Ambos procesos (tablas maestras y tablas temp) son independientes y correctos.

---

## 9. DEPLOY

```bash
# Comando SSH completo para deploy
ssh -i C:\Users\Personal\.ssh\id_ed25519 root@209.38.152.254 \
  "cd /var/www/easyposweb && git pull origin master && cd frontend && npm run build && systemctl restart easyposweb"
```

Versión actual: v26.06.03-95cc69e
