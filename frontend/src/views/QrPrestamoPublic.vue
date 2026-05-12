<template>
  <div class="qr-page">
    <div class="qr-card">

      <!-- LOGO / MARCA -->
      <div class="qr-brand">
        <i class="bi bi-box-arrow-right brand-icon"></i>
        <span class="brand-name">EasyPosWeb</span>
      </div>

      <!-- LOADING -->
      <div v-if="loading" class="qr-state">
        <i class="bi bi-arrow-repeat spin"></i>
        <p>Verificando QR...</p>
      </div>

      <!-- ERROR -->
      <div v-else-if="error" class="qr-state qr-error">
        <i class="bi bi-x-circle-fill"></i>
        <h3>QR no válido</h3>
        <p>{{ error }}</p>
      </div>

      <!-- YA PROCESADO -->
      <div v-else-if="info && !info.accion_disponible" class="qr-state qr-done">
        <i class="bi bi-check-circle-fill"></i>
        <h3>Ya procesado</h3>
        <p>Este préstamo ya fue confirmado anteriormente.</p>
        <div class="info-block">
          <div class="info-row"><span>Artículo</span><strong>{{ info.articulo }}</strong></div>
          <div class="info-row"><span>Colaborador</span><strong>{{ info.colaborador_nombre }}</strong></div>
        </div>
      </div>

      <!-- CONFIRMAR RECEPCIÓN -->
      <template v-else-if="info && info.accion_disponible === 'confirmar_recepcion'">
        <div class="qr-icon-wrap recepcion">
          <i class="bi bi-box-arrow-down-right"></i>
        </div>
        <h2 class="qr-title">Confirmar Recepción</h2>
        <p class="qr-subtitle">Estás a punto de recibir el siguiente artículo</p>
        <div class="info-block">
          <div class="info-row"><span>Artículo</span><strong>{{ info.articulo }}</strong></div>
          <div v-if="info.articulo_codigo" class="info-row"><span>Código</span><strong>{{ info.articulo_codigo }}</strong></div>
          <div class="info-row"><span>Cantidad</span><strong>{{ info.cantidad }}</strong></div>
          <div v-if="info.task_leader_nombre" class="info-row"><span>Responsable</span><strong>{{ info.task_leader_nombre }}</strong></div>
          <div v-if="info.colaborador_nombre" class="info-row"><span>Colaborador</span><strong>{{ info.colaborador_nombre }}</strong></div>
          <div v-if="info.fecha_retorno_esperada" class="info-row"><span>Devolver antes del</span><strong>{{ fmtDate(info.fecha_retorno_esperada) }}</strong></div>
        </div>

        <!-- Selección de quién firma — solo si hay colaborador -->
        <div v-if="!confirmed && info.tiene_colaborador && !signedBy" class="signer-select">
          <p class="signer-label">¿Quién confirma la recepción?</p>
          <button class="btn-signer" @click="signedBy = 'leader'">
            <i class="bi bi-person-badge"></i>
            {{ info.task_leader_nombre || 'Líder de tarea' }}
            <small>Responsable</small>
          </button>
          <button class="btn-signer btn-signer-collab" @click="signedBy = 'collaborator'">
            <i class="bi bi-person"></i>
            {{ info.colaborador_nombre || 'Colaborador' }}
            <small>Colaborador externo</small>
          </button>
        </div>

        <div v-if="confirmed" class="qr-state qr-done">
          <i class="bi bi-check-circle-fill"></i>
          <h3>¡Recepción confirmada!</h3>
          <p>Queda registrado que recibiste el artículo.</p>
        </div>
        <button v-else-if="!info.tiene_colaborador || signedBy" class="btn-confirm recepcion-btn" @click="confirmar" :disabled="confirming">
          <i v-if="confirming" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-hand-thumbs-up"></i>
          {{ confirming ? 'Confirmando...' : 'Confirmar que lo recibí' }}
        </button>
      </template>

      <!-- CONFIRMAR DEVOLUCIÓN -->
      <template v-else-if="info && info.accion_disponible === 'confirmar_devolucion'">
        <div class="qr-icon-wrap devolucion">
          <i class="bi bi-box-arrow-up-left"></i>
        </div>
        <h2 class="qr-title">Confirmar Devolución</h2>
        <p class="qr-subtitle">Vas a devolver el siguiente artículo</p>
        <div class="info-block">
          <div class="info-row"><span>Artículo</span><strong>{{ info.articulo }}</strong></div>
          <div class="info-row"><span>Cantidad</span><strong>{{ info.cantidad }}</strong></div>
          <div v-if="info.task_leader_nombre" class="info-row"><span>Responsable</span><strong>{{ info.task_leader_nombre }}</strong></div>
          <div v-if="info.colaborador_nombre" class="info-row"><span>Colaborador</span><strong>{{ info.colaborador_nombre }}</strong></div>
        </div>

        <!-- Selección de quién firma — solo si hay colaborador -->
        <div v-if="!confirmed && info.tiene_colaborador && !signedBy" class="signer-select">
          <p class="signer-label">¿Quién confirma la devolución?</p>
          <button class="btn-signer" @click="signedBy = 'leader'">
            <i class="bi bi-person-badge"></i>
            {{ info.task_leader_nombre || 'Líder de tarea' }}
            <small>Responsable</small>
          </button>
          <button class="btn-signer btn-signer-collab" @click="signedBy = 'collaborator'">
            <i class="bi bi-person"></i>
            {{ info.colaborador_nombre || 'Colaborador' }}
            <small>Colaborador externo</small>
          </button>
        </div>

        <div v-if="confirmed" class="qr-state qr-done">
          <i class="bi bi-check-circle-fill"></i>
          <h3>¡Devolución confirmada!</h3>
          <p>Queda registrado que devolviste el artículo.</p>
        </div>
        <button v-else-if="!info.tiene_colaborador || signedBy" class="btn-confirm devolucion-btn" @click="confirmar" :disabled="confirming">
          <i v-if="confirming" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-box-arrow-in-left"></i>
          {{ confirming ? 'Confirmando...' : 'Confirmar que lo entregué' }}
        </button>
      </template>

    </div>

    <p class="qr-footer">Powered by EasyPosWeb</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"

const route    = useRoute()
const token    = route.params.token
const apiBase  = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

const loading   = ref(true)
const error     = ref(null)
const info      = ref(null)
const confirmed = ref(false)
const confirming = ref(false)
const signedBy  = ref(null)  // 'leader' | 'collaborator' | null

function fmtDate(iso) {
  if (!iso) return ""
  return new Date(iso).toLocaleDateString("es-CO", { day: "2-digit", month: "long", year: "numeric" })
}

async function loadInfo() {
  try {
    const res = await fetch(`${apiBase}/qr/prestamo/${token}`)
    if (!res.ok) {
      const data = await res.json()
      error.value = data.detail || "QR no válido"
      return
    }
    info.value = await res.json()
  } catch {
    error.value = "No se pudo conectar con el servidor."
  } finally {
    loading.value = false
  }
}

async function confirmar() {
  confirming.value = true
  try {
    const body = { signed_by: signedBy.value || "leader" }
    const res = await fetch(`${apiBase}/qr/prestamo/${token}/confirmar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const data = await res.json()
      alert(data.detail || "Error al confirmar")
      return
    }
    confirmed.value = true
  } catch {
    alert("Error de conexión. Intenta de nuevo.")
  } finally {
    confirming.value = false
  }
}

onMounted(loadInfo)
</script>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.qr-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 20px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.qr-card {
  background: #fff; border-radius: 20px;
  width: 100%; max-width: 400px;
  padding: 32px 28px;
  box-shadow: 0 25px 60px rgba(0,0,0,.35);
  display: flex; flex-direction: column; align-items: center; gap: 18px;
}

.qr-brand    { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.brand-icon  { font-size: 22px; color: #3b82f6; }
.brand-name  { font-size: 16px; font-weight: 800; color: #1e293b; }

.qr-icon-wrap {
  width: 72px; height: 72px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 32px;
}
.recepcion  { background: #dbeafe; color: #1d4ed8; }
.devolucion { background: #f3e8ff; color: #7c3aed; }

.qr-title    { font-size: 20px; font-weight: 800; color: #1e293b; text-align: center; }
.qr-subtitle { font-size: 13px; color: #64748b; text-align: center; }

.info-block {
  width: 100%; background: #f8fafc; border-radius: 12px; padding: 14px 16px;
  display: flex; flex-direction: column; gap: 10px;
}
.info-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; gap: 8px;
}
.info-row span  { color: #64748b; flex-shrink: 0; }
.info-row strong { color: #1e293b; text-align: right; }

.btn-confirm {
  width: 100%; padding: 16px; border: none; border-radius: 12px;
  font-size: 16px; font-weight: 700; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  transition: all .15s;
}
.recepcion-btn  { background: #3b82f6; color: #fff; }
.recepcion-btn:hover  { background: #2563eb; }
.devolucion-btn { background: #7c3aed; color: #fff; }
.devolucion-btn:hover { background: #6d28d9; }
.btn-confirm:disabled { opacity: .6; cursor: not-allowed; }

.qr-state {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 16px 0; text-align: center; width: 100%;
}
.qr-state .bi { font-size: 40px; }
.qr-state h3  { font-size: 17px; font-weight: 700; color: #1e293b; }
.qr-state p   { font-size: 13px; color: #64748b; }
.qr-error .bi { color: #ef4444; }
.qr-done  .bi { color: #22c55e; }

.qr-footer { margin-top: 20px; font-size: 11px; color: rgba(255,255,255,.4); }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

/* Selección de firmante */
.signer-select { width: 100%; display: flex; flex-direction: column; gap: 10px; }
.signer-label  { font-size: 13px; font-weight: 600; color: #475569; text-align: center; margin: 0; }
.btn-signer {
  width: 100%; padding: 14px 16px; border: 2px solid #bfdbfe; border-radius: 12px;
  background: #eff6ff; color: #1d4ed8; font-size: 14px; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; gap: 10px; text-align: left; transition: all .15s;
}
.btn-signer small { font-size: 11px; font-weight: 400; color: #64748b; margin-left: auto; }
.btn-signer:hover { background: #dbeafe; border-color: #93c5fd; }
.btn-signer-collab { border-color: #d8b4fe; background: #f3e8ff; color: #7c3aed; }
.btn-signer-collab:hover { background: #ede9fe; border-color: #c4b5fd; }
</style>
