<template>
  <div class="kpi-card" :class="`kpi-card--${color}`">
    <div class="kpi-icon">
      <i :class="`bi ${icon}`"></i>
    </div>
    <div class="kpi-body">
      <span class="kpi-value">
        <span v-if="loading" class="kpi-loading"></span>
        <template v-else>{{ value }}</template>
      </span>
      <span class="kpi-label">{{ label }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  icon:    { type: String, default: "bi-bar-chart" },
  value:   { type: [Number, String], default: 0 },
  label:   { type: String, required: true },
  color:   { type: String, default: "blue" },   // blue | green | amber | red
  loading: { type: Boolean, default: false }
})
</script>

<style scoped>

.kpi-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #fff;
  border-radius: 14px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  border-left: 4px solid transparent;
  transition: box-shadow 0.2s;
}

.kpi-card:hover {
  box-shadow: 0 4px 14px rgba(0,0,0,0.12);
}

.kpi-card--blue  { border-left-color: #3b82f6; }
.kpi-card--green { border-left-color: #22c55e; }
.kpi-card--amber { border-left-color: #f59e0b; }
.kpi-card--red   { border-left-color: #ef4444; }
.kpi-card--slate { border-left-color: #64748b; }

.kpi-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.kpi-card--blue  .kpi-icon { background: #eff6ff; color: #3b82f6; }
.kpi-card--green .kpi-icon { background: #f0fdf4; color: #22c55e; }
.kpi-card--amber .kpi-icon { background: #fffbeb; color: #f59e0b; }
.kpi-card--red   .kpi-icon { background: #fef2f2; color: #ef4444; }
.kpi-card--slate .kpi-icon { background: #f8fafc; color: #64748b; }

.kpi-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1;
  margin-bottom: 4px;
}

.kpi-label {
  font-size: 13px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kpi-loading {
  display: inline-block;
  width: 28px;
  height: 14px;
  background: #e2e8f0;
  border-radius: 4px;
  animation: pulse 1.2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}

</style>
