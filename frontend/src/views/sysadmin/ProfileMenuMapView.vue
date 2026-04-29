<template>
  <div class="map-wrap">

    <!-- HEADER -->
    <div class="map-header">
      <div class="map-header-left">
        <h1 class="map-title">
          <i class="bi bi-map"></i> Mapa de Menú por Perfil
        </h1>
        <p class="map-sub">Visualiza todos los módulos asignados a un perfil de negocio.</p>
      </div>
      <div class="map-header-right">
        <select v-model="selectedProfileId" class="profile-select" @change="loadMap">
          <option value="">— Seleccionar perfil —</option>
          <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <button
          v-if="selectedProfileId"
          class="btn-manage btn-repair"
          :disabled="repairing"
          @click="repairProfile"
          title="Limpiar módulos inactivos y re-sincronizar jerarquía"
        >
          <i v-if="repairing" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-wrench-adjustable"></i>
          {{ repairing ? 'Reparando...' : 'Reparar perfil' }}
        </button>
      </div>
    </div>

    <!-- KPI BAR -->
    <div v-if="selectedProfileId && !loading" class="kpi-bar">
      <div class="kpi-card">
        <i class="bi bi-grid-3x3-gap-fill kpi-icon" style="color:#3b82f6"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ totalModules }}</span>
          <span class="kpi-lbl">Módulos totales</span>
        </div>
      </div>
      <div class="kpi-card">
        <i class="bi bi-folder2-open kpi-icon" style="color:#8b5cf6"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ totalGroups }}</span>
          <span class="kpi-lbl">Grupos / Padres</span>
        </div>
      </div>
      <div class="kpi-card">
        <i class="bi bi-link-45deg kpi-icon" style="color:#10b981"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ totalLeaves }}</span>
          <span class="kpi-lbl">Módulos hoja</span>
        </div>
      </div>
      <div class="kpi-card">
        <i class="bi bi-bar-chart-steps kpi-icon" style="color:#f59e0b"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ maxDepth }}</span>
          <span class="kpi-lbl">Niveles de menú</span>
        </div>
      </div>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="state-msg">
      <i class="bi bi-arrow-repeat spin"></i> Cargando mapa...
    </div>

    <!-- PLACEHOLDER -->
    <div v-else-if="!selectedProfileId" class="state-msg">
      <i class="bi bi-map" style="font-size:40px;opacity:0.3;display:block;margin-bottom:10px"></i>
      Selecciona un perfil para ver su mapa de menú
    </div>

    <!-- SIN MÓDULOS -->
    <div v-else-if="tree.length === 0" class="state-msg">
      <i class="bi bi-inbox" style="font-size:40px;opacity:0.3;display:block;margin-bottom:10px"></i>
      Este perfil no tiene módulos asignados
    </div>

    <!-- ÁRBOL VISUAL -->
    <div v-else class="tree-canvas">
      <div
        v-for="node in tree"
        :key="node.id"
        class="node-card"
        :class="node.children && node.children.length ? 'node-parent' : 'node-leaf'"
      >
        <!-- CABECERA DEL NODO -->
        <div class="node-head">
          <span class="node-icon"><i :class="`bi ${node.icon || 'bi-circle'}`"></i></span>
          <div class="node-info">
            <span class="node-name">{{ node.name }}</span>
            <span class="node-route">{{ node.route || '—' }}</span>
          </div>
          <span v-if="node.children && node.children.length" class="node-badge">
            {{ node.children.length }} sub
          </span>
        </div>

        <!-- HIJOS -->
        <div v-if="node.children && node.children.length" class="children-grid">
          <div
            v-for="child in node.children"
            :key="child.id"
            class="child-card"
            :class="child.children && child.children.length ? 'child-has-sub' : ''"
          >
            <span class="child-icon"><i :class="`bi ${child.icon || 'bi-circle'}`"></i></span>
            <div class="child-info">
              <span class="child-name">{{ child.name }}</span>
              <span class="child-route">{{ child.route || '—' }}</span>
            </div>

            <!-- Sub-hijos (nivel 3) -->
            <div v-if="child.children && child.children.length" class="sub-list">
              <div v-for="sub in child.children" :key="sub.id" class="sub-item">
                <i :class="`bi ${sub.icon || 'bi-circle'}`"></i>
                <span>{{ sub.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"


const profiles          = ref([])
const selectedProfileId = ref("")
const tree              = ref([])
const loading           = ref(false)
const repairing         = ref(false)

// ── KPIs derivados ──────────────────────────────────────
function countNodes(nodes, depth = 1) {
  let total = nodes.length
  let groups = 0
  let leaves = 0
  let maxD   = depth
  for (const n of nodes) {
    if (n.children && n.children.length) {
      groups++
      const sub = countNodes(n.children, depth + 1)
      total  += sub.total
      groups += sub.groups
      leaves += sub.leaves
      maxD    = Math.max(maxD, sub.maxD)
    } else {
      leaves++
    }
  }
  return { total, groups, leaves, maxD }
}

const stats = computed(() => {
  if (!tree.value.length) return { total: 0, groups: 0, leaves: 0, maxD: 0 }
  return countNodes(tree.value)
})
const totalModules = computed(() => stats.value.total)
const totalGroups  = computed(() => stats.value.groups)
const totalLeaves  = computed(() => stats.value.leaves)
const maxDepth     = computed(() => stats.value.maxD)

// ── Carga ────────────────────────────────────────────────
async function loadProfiles() {
  try {
    const res = await api.get("/business-profiles/")
    profiles.value = res.data.data ?? res.data
  } catch {
    showToast("Error cargando perfiles", "error")
  }
}

async function loadMap() {
  if (!selectedProfileId.value) { tree.value = []; return }
  loading.value = true
  try {
    const res = await api.get(`/menu/by-profile/${selectedProfileId.value}`)
    tree.value = res.data
  } catch {
    showToast("Error cargando mapa", "error")
    tree.value = []
  } finally {
    loading.value = false
  }
}

async function repairProfile() {
  const profileName = profiles.value.find(p => p.id === selectedProfileId.value)?.name || "este perfil"
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Reparar "${profileName}"?`,
    html: `
      <div style="text-align:left;font-size:14px;color:#475569">
        Esto realizará:<br><br>
        <b>1.</b> Eliminar módulos inactivos del perfil<br>
        <b>2.</b> Re-sincronizar la jerarquía padre-hijo<br><br>
        <span style="color:#ef4444">No elimina módulos activos — solo limpia inconsistencias.</span>
      </div>`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, reparar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#1e3a5f"
  })
  if (!isConfirmed) return

  repairing.value = true
  try {
    const res = await api.post(`/menu/repair-profile/${selectedProfileId.value}`)
    const { deleted_inactive, permissions_added, tree: fixedTree } = res.data
    tree.value = fixedTree
    const parts = []
    if (deleted_inactive > 0) parts.push(`${deleted_inactive} módulo(s) inactivo(s) eliminado(s)`)
    if (permissions_added > 0) parts.push(`${permissions_added} permiso(s) de rol añadido(s)`)
    showToast(
      parts.length ? `Reparado: ${parts.join(' · ')}` : 'Perfil ya estaba sincronizado',
      parts.length ? "success" : "info"
    )
  } catch (e) {
    showToast(e.response?.data?.detail || "Error reparando perfil", "error")
  } finally {
    repairing.value = false
  }
}

onMounted(loadProfiles)
</script>

<style scoped>
.map-wrap {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 0;
}

/* HEADER */
.map-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.map-title {
  font-size: 20px;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.map-sub { font-size: 13px; color: #64748b; margin: 0; }

.map-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.profile-select {
  padding: 7px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  background: #fff;
  min-width: 220px;
  outline: none;
  cursor: pointer;
}
.profile-select:focus { border-color: #3b82f6; }

.btn-manage {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: #1e3a5f;
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.15s;
  white-space: nowrap;
}
.btn-manage:hover { background: #2563eb; color: #fff; }
.btn-repair { background: #1e3a5f; cursor: pointer; border: none; }
.btn-repair:hover:not(:disabled) { background: #16a34a; }
.btn-repair:disabled { opacity: 0.65; cursor: not-allowed; }

/* KPI BAR */
.kpi-bar {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}
.kpi-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-radius: 12px;
  padding: 14px 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  min-width: 150px;
  flex: 1;
}
.kpi-icon { font-size: 26px; }
.kpi-body { display: flex; flex-direction: column; line-height: 1.2; }
.kpi-val  { font-size: 22px; font-weight: 800; color: #1e293b; }
.kpi-lbl  { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.4px; }

/* ESTADO */
.state-msg {
  text-align: center;
  color: #94a3b8;
  font-size: 15px;
  padding: 60px 20px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

/* ÁRBOL */
.tree-canvas {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  align-items: start;
}

/* NODO PADRE (con hijos) */
.node-card {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08);
  overflow: hidden;
}

.node-parent { border-top: 3px solid #3b82f6; }
.node-leaf   { border-top: 3px solid #10b981; }

.node-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
}
.node-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #eff6ff;
  color: #3b82f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  flex-shrink: 0;
}
.node-leaf .node-icon { background: #f0fdf4; color: #10b981; }

.node-info { flex: 1; min-width: 0; }
.node-name {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.node-route {
  display: block;
  font-size: 11px;
  color: #94a3b8;
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-badge {
  font-size: 10px;
  font-weight: 700;
  background: #eff6ff;
  color: #3b82f6;
  padding: 2px 8px;
  border-radius: 20px;
  white-space: nowrap;
  flex-shrink: 0;
}

/* HIJOS GRID */
.children-grid {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.child-card {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  transition: background 0.15s;
}
.child-card:hover { background: #eff6ff; border-color: #bfdbfe; }
.child-has-sub { background: #fefce8; border-color: #fde68a; }

.child-icon {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  background: #e0e7ff;
  color: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  flex-shrink: 0;
  margin-top: 1px;
}
.child-info { flex: 1; min-width: 0; }
.child-name {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}
.child-route {
  display: block;
  font-size: 10px;
  color: #94a3b8;
  font-family: monospace;
}

/* SUB-ITEMS (nivel 3) */
.sub-list {
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-left: 4px;
  border-left: 2px solid #fde68a;
  margin-left: 2px;
}
.sub-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #64748b;
  padding: 2px 4px;
}
.sub-item .bi { font-size: 10px; color: #f59e0b; }

/* Spin */
.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }

/* RESPONSIVE */
@media (max-width: 600px) {
  .tree-canvas { grid-template-columns: 1fr; }
  .map-header  { flex-direction: column; }
  .profile-select { min-width: 100%; }
}
</style>
