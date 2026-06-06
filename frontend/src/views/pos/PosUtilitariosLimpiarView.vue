<template>
  <div class="crud-view">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Limpiar Temporales</h5>
        <p class="crud-sub">Elimina del servidor los pedidos que ya no existen en el sistema de escritorio</p>
      </div>
    </div>

    <div class="util-cards">
      <div class="util-card">
        <div class="util-card__icon">
          <i class="bi bi-trash3-fill"></i>
        </div>
        <div class="util-card__body">
          <h6>Limpiar pedidos huérfanos</h6>
          <p>
            Elimina de las tablas temporales web los pedidos que VB6 ya no tiene activos:
            pedidos facturados, eliminados, cancelados o que desaparecieron del escritorio
            sin notificar al servidor.
          </p>
          <ul class="util-card__list">
            <li><i class="bi bi-check2-circle text-success"></i> Pedidos con estado Cancelado</li>
            <li><i class="bi bi-check2-circle text-success"></i> Pedidos en histórico de eliminados</li>
            <li><i class="bi bi-check2-circle text-success"></i> Pedidos facturados (factura / recibo)</li>
            <li><i class="bi bi-check2-circle text-success"></i> Pedidos que ya no llegan en el ciclo de sync</li>
          </ul>
          <div class="util-card__nota">
            <i class="bi bi-info-circle"></i>
            Los pedidos web (canal online) <strong>no se verán afectados</strong>.
            Esta operación es segura e idempotente.
          </div>
        </div>
        <div class="util-card__action">
          <button class="btn-ejecutar" :disabled="loading" @click="confirmar">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else class="bi bi-play-circle me-2"></i>
            Ejecutar limpieza
          </button>
        </div>
      </div>
    </div>

    <!-- Modal confirmación -->
    <div v-if="showConfirm" class="modal-overlay" @click.self="showConfirm=false">
      <div class="modal-box">
        <div class="modal-box__icon"><i class="bi bi-exclamation-triangle-fill"></i></div>
        <h6>¿Confirmar limpieza de temporales?</h6>
        <p>Esta acción eliminará del servidor web todos los pedidos huérfanos.<br>
           <strong>No afecta pedidos activos ni datos del escritorio.</strong></p>
        <div class="modal-box__btns">
          <button class="btn-cancelar" @click="showConfirm=false">Cancelar</button>
          <button class="btn-confirmar" @click="ejecutar">Sí, limpiar</button>
        </div>
      </div>
    </div>

    <!-- Resultado -->
    <div v-if="resultado" class="util-resultado" :class="resultado.ok ? 'util-resultado--ok' : 'util-resultado--err'">
      <template v-if="resultado.ok">
        <i class="bi bi-check-circle-fill"></i>
        Limpieza completada — <strong>{{ resultado.headers }} cabeceras</strong> y
        <strong>{{ resultado.details }} detalles</strong> eliminados.
      </template>
      <template v-else>
        <i class="bi bi-x-circle-fill"></i> {{ resultado.msg }}
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/apis'

const loading     = ref(false)
const showConfirm = ref(false)
const resultado   = ref(null)

function confirmar() {
  resultado.value = null
  showConfirm.value = true
}

async function ejecutar() {
  showConfirm.value = false
  loading.value = true
  resultado.value = null
  try {
    const res = await api.post('/pos/utilitarios/cleanup-temp')
    resultado.value = {
      ok:      true,
      headers: res.data.deleted_headers ?? 0,
      details: res.data.deleted_details  ?? 0,
    }
  } catch (e) {
    resultado.value = {
      ok:  false,
      msg: e.response?.data?.detail || 'Error al ejecutar la limpieza',
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.util-cards { display:flex; flex-direction:column; gap:16px; margin-top:8px; }

.util-card {
  background:#fff;
  border:1px solid #e2e8f0;
  border-radius:12px;
  padding:24px;
  display:flex;
  gap:20px;
  align-items:flex-start;
}

.util-card__icon {
  width:52px; height:52px;
  border-radius:12px;
  background:#fff3cd;
  display:flex; align-items:center; justify-content:center;
  font-size:1.6rem;
  color:#e67e22;
  flex-shrink:0;
}

.util-card__body { flex:1; }
.util-card__body h6 { font-weight:700; margin-bottom:6px; font-size:.95rem; }
.util-card__body p  { font-size:.85rem; color:#64748b; margin-bottom:10px; }

.util-card__list {
  list-style:none; padding:0; margin:0 0 12px;
  display:flex; flex-direction:column; gap:4px;
}
.util-card__list li { font-size:.83rem; display:flex; align-items:center; gap:6px; color:#374151; }

.util-card__nota {
  font-size:.8rem; color:#6b7280;
  background:#f8fafc; border-left:3px solid #3b82f6;
  border-radius:0 6px 6px 0;
  padding:8px 12px;
}
.util-card__nota i { margin-right:4px; }

.util-card__action { flex-shrink:0; display:flex; align-items:center; }

.btn-ejecutar {
  background:#e67e22; color:#fff;
  border:none; border-radius:8px;
  padding:10px 20px; font-size:.88rem; font-weight:600;
  cursor:pointer; display:flex; align-items:center;
  transition:background .15s;
}
.btn-ejecutar:hover:not(:disabled) { background:#d35400; }
.btn-ejecutar:disabled { opacity:.6; cursor:not-allowed; }

/* Modal */
.modal-overlay {
  position:fixed; inset:0;
  background:rgba(0,0,0,.45);
  display:flex; align-items:center; justify-content:center;
  z-index:9999;
}
.modal-box {
  background:#fff; border-radius:14px;
  padding:32px 28px; max-width:420px; width:90%;
  text-align:center; box-shadow:0 20px 60px rgba(0,0,0,.2);
}
.modal-box__icon { font-size:2.4rem; color:#e67e22; margin-bottom:12px; }
.modal-box h6 { font-weight:700; font-size:1rem; margin-bottom:8px; }
.modal-box p  { font-size:.87rem; color:#64748b; margin-bottom:20px; }
.modal-box__btns { display:flex; gap:10px; justify-content:center; }
.btn-cancelar  { padding:9px 22px; border:1px solid #d1d5db; border-radius:8px; background:#fff; cursor:pointer; font-size:.88rem; }
.btn-confirmar { padding:9px 22px; border:none; border-radius:8px; background:#e67e22; color:#fff; font-weight:600; cursor:pointer; font-size:.88rem; }
.btn-confirmar:hover { background:#d35400; }

/* Resultado */
.util-resultado {
  margin-top:16px; padding:14px 18px;
  border-radius:10px; font-size:.88rem;
  display:flex; align-items:center; gap:8px;
}
.util-resultado--ok  { background:#d1fae5; color:#065f46; border:1px solid #6ee7b7; }
.util-resultado--err { background:#fee2e2; color:#991b1b; border:1px solid #fca5a5; }

/* Responsive */
@media (max-width: 768px) {
  .util-card { flex-direction:column; }
  .util-card__action { width:100%; }
  .btn-ejecutar { width:100%; justify-content:center; }
}
@media (max-width: 576px) {
  .util-card { padding:16px; }
  .util-card__icon { width:44px; height:44px; font-size:1.3rem; }
}
</style>
