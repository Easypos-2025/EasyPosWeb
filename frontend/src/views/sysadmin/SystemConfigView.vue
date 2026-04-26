<template>
  <div class="page-wrap">

    <!-- ── HEADER ── -->
    <div class="page-header">
      <div class="page-header-left">
        <i class="bi bi-sliders page-icon"></i>
        <div>
          <h1 class="page-title">Configuración del Sistema</h1>
          <p class="page-sub">Parámetros globales del sistema — edita los valores con precaución</p>
        </div>
      </div>
    </div>

    <!-- ── LOADING ── -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div><span>Cargando configuración...</span>
    </div>

    <!-- ── GRUPOS DE CONFIG ── -->
    <div v-else class="configs-grid">
      <div
        v-for="cfg in configs"
        :key="cfg.config_key"
        class="config-card"
        :class="{ 'card-inactive': !cfg.is_active }"
      >
        <div class="config-card-header">
          <div class="config-key-wrap">
            <code class="config-key">{{ cfg.config_key }}</code>
            <span class="config-type-badge" :class="`type-${cfg.config_type}`">{{ cfg.config_type }}</span>
          </div>
          <button
            class="toggle-btn"
            :class="cfg.is_active ? 'toggle-on' : 'toggle-off'"
            @click="toggleActive(cfg)"
            :title="cfg.is_active ? 'Desactivar' : 'Activar'"
          >
            <span class="toggle-knob"></span>
          </button>
        </div>

        <p class="config-desc">{{ cfg.description || 'Sin descripción' }}</p>

        <!-- Editor inline por tipo -->
        <div class="config-value-row">
          <template v-if="cfg.config_type === 'boolean'">
            <select
              :value="cfg.config_value"
              @change="updateConfig(cfg, $event.target.value)"
              class="config-select"
            >
              <option value="1">Habilitado (1)</option>
              <option value="0">Deshabilitado (0)</option>
            </select>
            <span class="value-indicator" :class="cfg.config_value === '1' ? 'val-on' : 'val-off'">
              {{ cfg.config_value === '1' ? 'Activo' : 'Inactivo' }}
            </span>
          </template>

          <template v-else-if="cfg.config_type === 'integer'">
            <div class="int-editor">
              <button class="btn-adj" @click="adjustInt(cfg, -1)"><i class="bi bi-dash-lg"></i></button>
              <input
                class="config-int-input"
                type="number"
                :value="cfg.config_value"
                @blur="updateConfig(cfg, $event.target.value)"
                @keyup.enter="updateConfig(cfg, $event.target.value)"
                min="0"
              />
              <button class="btn-adj" @click="adjustInt(cfg, 1)"><i class="bi bi-plus-lg"></i></button>
              <span class="unit-hint">{{ unitHint(cfg.config_key) }}</span>
            </div>
          </template>

          <template v-else>
            <input
              class="config-text-input"
              type="text"
              :value="cfg.config_value"
              @blur="updateConfig(cfg, $event.target.value)"
              @keyup.enter="updateConfig(cfg, $event.target.value)"
            />
          </template>
        </div>

      </div>
    </div>

    <!-- ── INFO BOX ── -->
    <div class="info-box">
      <i class="bi bi-info-circle"></i>
      <p>Los cambios se aplican en tiempo real. Algunos parámetros como el intervalo del ticker del footer
         requieren recargar la página para surtir efecto completo.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const configs = ref([])
const loading = ref(true)

// ── Carga ─────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const res   = await api.get("/system-config")
    configs.value = res.data
  } catch {
    showToast("Error cargando configuración", "error")
  } finally {
    loading.value = false
  }
}

// ── Actualizar valor ──────────────────────────────────
async function updateConfig(cfg, newValue) {
  const val = String(newValue).trim()
  if (val === cfg.config_value) return

  try {
    await api.put(`/system-config/${cfg.config_key}`, { config_value: val })
    cfg.config_value = val
    showToast("Configuración actualizada", "success")
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al actualizar", "error")
  }
}

// ── Toggle is_active ──────────────────────────────────
async function toggleActive(cfg) {
  const newActive = !cfg.is_active
  try {
    await api.put(`/system-config/${cfg.config_key}`, {
      config_value: cfg.config_value,
      is_active: newActive
    })
    cfg.is_active = newActive
    showToast(newActive ? "Activado" : "Desactivado", "success")
  } catch { showToast("Error al actualizar", "error") }
}

// ── Ajuste de entero con ± ────────────────────────────
async function adjustInt(cfg, delta) {
  const current = parseInt(cfg.config_value) || 0
  const next    = Math.max(0, current + delta)
  await updateConfig(cfg, String(next))
}

// ── Hint de unidad por clave ──────────────────────────
function unitHint(key) {
  if (key.includes("_sec"))  return "seg"
  if (key.includes("_days")) return "días"
  if (key.includes("_min"))  return "min"
  return ""
}

onMounted(load)
</script>

<style scoped>
.page-wrap { padding: 24px; display: flex; flex-direction: column; gap: 20px; }

.page-header { display: flex; align-items: center; justify-content: space-between; }
.page-header-left { display: flex; align-items: center; gap: 14px; }
.page-icon  { font-size: 30px; color: #f59e0b; }
.page-title { font-size: 22px; font-weight: 700; margin: 0; color: var(--text-main, #1e293b); }
.page-sub   { font-size: 12px; color: var(--text-muted, #64748b); margin: 2px 0 0; }

/* Loading */
.loading-state { display: flex; align-items: center; gap: 12px; padding: 48px; justify-content: center; color: var(--text-muted, #64748b); }
.spinner { width: 22px; height: 22px; border: 3px solid rgba(0,0,0,0.1); border-top-color: #f59e0b; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Grid */
.configs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.config-card {
  background: var(--card-bg, #fff);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color 0.15s;
}
.config-card:hover { border-color: #f59e0b; }
.card-inactive { opacity: 0.5; }

.config-card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }

.config-key-wrap { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.config-key {
  font-size: 12px;
  font-weight: 700;
  font-family: monospace;
  background: var(--input-bg, #f1f5f9);
  padding: 3px 8px;
  border-radius: 5px;
  color: #6366f1;
}

.config-type-badge {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: 10px;
}
.type-integer { background: rgba(59,130,246,0.12); color: #2563eb; }
.type-boolean { background: rgba(34,197,94,0.12);  color: #16a34a; }
.type-string  { background: rgba(245,158,11,0.12); color: #d97706; }
.type-json    { background: rgba(99,102,241,0.12); color: #6366f1; }

.config-desc {
  font-size: 12px;
  color: var(--text-muted, #64748b);
  margin: 0;
  line-height: 1.4;
}

/* Editores inline */
.config-value-row { display: flex; align-items: center; gap: 10px; margin-top: 4px; }

.config-select {
  border: 1px solid var(--border, #d1d5db);
  border-radius: 7px;
  padding: 7px 10px;
  font-size: 13px;
  background: var(--input-bg, #f9fafb);
  color: var(--text-main, #1e293b);
  outline: none;
  cursor: pointer;
  flex: 1;
}
.config-select:focus { border-color: #f59e0b; }

.value-indicator { font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 10px; }
.val-on  { background: rgba(34,197,94,0.15); color: #16a34a; }
.val-off { background: rgba(148,163,184,0.2); color: #64748b; }

.int-editor { display: flex; align-items: center; gap: 6px; }

.btn-adj {
  width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 7px;
  background: var(--input-bg, #f1f5f9);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-main, #374151);
  transition: background 0.15s;
  flex-shrink: 0;
}
.btn-adj:hover { background: #e2e8f0; }

.config-int-input {
  width: 70px;
  text-align: center;
  border: 1px solid var(--border, #d1d5db);
  border-radius: 7px;
  padding: 6px 8px;
  font-size: 15px;
  font-weight: 700;
  outline: none;
  background: var(--input-bg, #f9fafb);
  color: var(--text-main, #1e293b);
}
.config-int-input:focus { border-color: #f59e0b; background: #fff; }

.unit-hint { font-size: 11px; color: var(--text-muted, #94a3b8); }

.config-text-input {
  flex: 1;
  border: 1px solid var(--border, #d1d5db);
  border-radius: 7px;
  padding: 7px 10px;
  font-size: 13px;
  outline: none;
  background: var(--input-bg, #f9fafb);
  color: var(--text-main, #1e293b);
}
.config-text-input:focus { border-color: #f59e0b; background: #fff; }

/* Toggle */
.toggle-btn { width: 40px; height: 22px; border-radius: 11px; border: none; cursor: pointer; position: relative; transition: background 0.2s; flex-shrink: 0; }
.toggle-on  { background: #22c55e; }
.toggle-off { background: #cbd5e1; }
.toggle-knob { position: absolute; top: 3px; width: 16px; height: 16px; background: #fff; border-radius: 50%; transition: left 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.25); }
.toggle-on  .toggle-knob { left: 21px; }
.toggle-off .toggle-knob { left: 3px;  }

/* Info box */
.info-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: rgba(245,158,11,0.08);
  border: 1px solid rgba(245,158,11,0.25);
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 12px;
  color: var(--text-muted, #64748b);
}
.info-box .bi { color: #f59e0b; font-size: 16px; flex-shrink: 0; margin-top: 1px; }
.info-box p   { margin: 0; line-height: 1.5; }

@media (max-width: 768px) {
  .page-wrap    { padding: 14px; }
  .configs-grid { grid-template-columns: 1fr; }
}
</style>
