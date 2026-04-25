<template>
  <div class="kpi-strip">
    <div
      v-for="(kpi, i) in kpis"
      :key="i"
      class="kpi-item"
      :class="{ 'kpi-item--divider': i < kpis.length - 1 }"
      :title="kpi.label"
    >
      <div class="kpi-icon-wrap">
        <i :class="`bi ${kpi.icon}`"></i>
      </div>
      <div class="kpi-text">
        <span class="kpi-value">
          <span v-if="loading" class="kpi-skeleton"></span>
          <template v-else>{{ kpi.value }}</template>
        </span>
        <span v-if="showLabels && kpi.label" class="kpi-label">{{ kpi.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  kpis:       { type: Array,   default: () => [] },
  loading:    { type: Boolean, default: false },
  showLabels: { type: Boolean, default: false },
})
</script>

<style scoped>
/* ── Franja pegada al topbar, ancho total del content ── */
.kpi-strip {
  display: flex;
  align-items: center;
  background: linear-gradient(90deg, #1e3a5f 0%, #1d4ed8 100%);
  /* Cancela el padding del .content para ir de borde a borde */
  margin: -24px -24px 20px;
  padding: 0;
  /* Sin border-radius — va pegada al topbar */
  border-radius: 0;
}

.kpi-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 5px 16px;
  position: relative;
  min-height: 0;
}

.kpi-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.kpi-label {
  font-size: 10px;
  color: rgba(255,255,255,0.65);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  line-height: 1;
}

/* Divisor vertical */
.kpi-item--divider::after {
  content: "";
  position: absolute;
  right: 0;
  top: 15%;
  height: 70%;
  width: 1px;
  background: rgba(255,255,255,0.15);
}

.kpi-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255,255,255,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  color: #fff;
  flex-shrink: 0;
}

.kpi-value {
  font-size: 22px;
  font-weight: 800;
  color: #fff;
  line-height: 1;
  white-space: nowrap;
}

.kpi-skeleton {
  display: inline-block;
  width: 36px;
  height: 18px;
  background: rgba(255,255,255,0.2);
  border-radius: 4px;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}

/* RESPONSIVE */
@media (max-width: 768px) {
  .kpi-strip   { flex-wrap: wrap; margin: -16px -16px 16px; }
  .kpi-item    { flex: 1 1 45%; padding: 10px 12px; }
  .kpi-item--divider::after { display: none; }
  .kpi-value   { font-size: 18px; }
}

@media (max-width: 480px) {
  .kpi-item { flex: 1 1 50%; }
}
</style>
