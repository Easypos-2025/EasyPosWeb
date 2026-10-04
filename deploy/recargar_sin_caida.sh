#!/bin/bash
# =====================================================================
# Recarga del backend SIN CAÍDA (relevo escalonado de workers gunicorn)
#
# 1. Valida que el código nuevo importe (si no, NO toca nada).
# 2. Agrega N workers nuevos (TTIN): cargan el código nuevo mientras
#    los N viejos siguen atendiendo.
# 3. Espera a que los N nuevos terminen el startup.
# 4. Retira los N más viejos (TTOU: gunicorn siempre retira el más
#    antiguo); terminan sus peticiones en curso antes de salir.
#
# No usar `systemctl restart` ni HUP en deploys: restart deja la app sin
# responder mientras arranca; HUP apaga los workers viejos antes de que
# los nuevos estén listos (cada worker tarda ~30 s en cargar).
# =====================================================================
set -u
SVC=easyposweb
BACKEND=/var/www/easyposweb/backend
MAX_WAIT=180

MAIN=$(systemctl show -p MainPID --value "$SVC")
if [ -z "$MAIN" ] || [ "$MAIN" = "0" ]; then
  echo "Servicio detenido: se inicia normalmente."
  systemctl start "$SVC"; exit $?
fi

cd "$BACKEND" || exit 1
if ! venv/bin/python -c "import app.main" >/dev/null 2>&1; then
  echo "ERROR: el código nuevo no importa. No se recarga; sigue la versión anterior."
  venv/bin/python -c "import app.main" 2>&1 | tail -5
  exit 1
fi

N=$(pgrep -P "$MAIN" | wc -l)
[ "$N" -lt 1 ] && N=3
SINCE=$(date "+%Y-%m-%d %H:%M:%S")
sleep 1

for _ in $(seq 1 "$N"); do kill -TTIN "$MAIN"; sleep 0.5; done

READY=0
for _ in $(seq 1 "$MAX_WAIT"); do
  READY=$(journalctl -u "$SVC" --since "$SINCE" --no-pager 2>/dev/null | grep -c "Application startup complete")
  [ "$READY" -ge "$N" ] && break
  sleep 1
done

if [ "$READY" -lt "$N" ]; then
  echo "AVISO: solo $READY de $N workers nuevos listos en ${MAX_WAIT}s; se retiran los viejos igual."
fi

for _ in $(seq 1 "$N"); do kill -TTOU "$MAIN"; sleep 0.5; done
echo "Recarga sin caída completa: $N workers nuevos ($READY listos)."
