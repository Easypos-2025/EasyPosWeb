<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title"><i class="bi bi-file-earmark-spreadsheet me-2"></i>Reporte de Facturas</h1>
      <p class="page-subtitle">Facturación &rsaquo; Reportes &rsaquo; Facturas</p>
    </div>
    <div class="coming-soon-card">
      <i class="bi bi-tools"></i>
      <h2>Módulo en Desarrollo</h2>
      <p>El reporte de facturas estará disponible próximamente.</p>
    </div>
  </div>
</template>

<script setup></script>

<style scoped>
.page-container  { padding: 24px; max-width: 900px; }
.page-header     { margin-bottom: 24px; }
.page-title      { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle   { font-size: 13px; color: #94a3b8; margin: 0; }
.coming-soon-card {
  background: #fff; border-radius: 16px;
  box-shadow: 0 1px 8px rgba(0,0,0,.08);
  padding: 60px 24px; text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 12px;
}
.coming-soon-card .bi { font-size: 48px; color: #cbd5e1; }
.coming-soon-card h2  { font-size: 18px; font-weight: 700; color: #475569; margin: 0; }
.coming-soon-card p   { font-size: 14px; color: #94a3b8; margin: 0; }
</style>
