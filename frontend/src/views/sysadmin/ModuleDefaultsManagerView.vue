<template>
  <div class="mdm-container">

    <!-- KPI BAR -->
    <div class="mdm-kpi-bar">
      <div class="mdm-kpi">
        <i class="bi bi-diagram-3-fill"></i>
        <div class="mdm-kpi-value">{{ kpi.parents }}</div>
        <div class="mdm-kpi-label">Grupos</div>
      </div>
      <div class="mdm-kpi">
        <i class="bi bi-check2-circle" style="color:#22c55e"></i>
        <div class="mdm-kpi-value">{{ kpi.defaults }}</div>
        <div class="mdm-kpi-label">Hijos Default</div>
      </div>
      <div class="mdm-kpi">
        <i class="bi bi-buildings" style="color:#f59e0b"></i>
        <div class="mdm-kpi-value">{{ kpi.profiles }}</div>
        <div class="mdm-kpi-label">Máx. perfiles</div>
      </div>
    </div>

    <!-- INSTRUCCIONES -->
    <div class="mdm-info-box">
      <i class="bi bi-info-circle-fill"></i>
      <span>
        Haz clic en un grupo para expandirlo. Activa el <strong>toggle</strong> de un hijo para marcarlo como default.
        Usa <strong>Propagar Todos</strong> en el padre para agregar todos sus hijos default a los perfiles que ya lo tienen.
      </span>
    </div>

    <!-- ESTADO VACÍO / CARGA -->
    <div v-if="loading" class="mdm-empty">
      <i class="bi bi-arrow-repeat spin"></i> Cargando módulos...
    </div>
    <div v-else-if="!tree.length" class="mdm-empty">
      <i class="bi bi-inbox"></i> No hay módulos padre con hijos registrados.
    </div>

    <!-- ACORDEÓN DE PADRES -->
    <div v-else class="mdm-tree">
      <div v-for="parent in tree" :key="parent.id" class="mdm-group" :class="{ 'mdm-group--open': expandedId === parent.id }">

        <!-- CABECERA CLICABLE -->
        <div class="mdm-group-header" @click="toggleAccordion(parent.id)">
          <span class="mdm-group-icon">
            <i v-if="parent.icon?.startsWith('bi-')" :class="`bi ${parent.icon}`"></i>
            <i v-else class="bi bi-folder2"></i>
          </span>

          <span class="mdm-group-name">{{ parent.name }}</span>

          <span class="mdm-badge-profiles">
            <i class="bi bi-buildings"></i> {{ parent.profile_count }} perfil(es)
          </span>

          <span class="mdm-badge-defaults" :class="{ 'mdm-badge-defaults--empty': !defaultCount(parent) }">
            <i class="bi bi-check2-circle"></i> {{ defaultCount(parent) }} default(s)
          </span>

          <!-- BOTÓN PROPAGAR TODOS (en la cabecera del padre) -->
          <button
            v-if="defaultCount(parent) > 0 && parent.profile_count > 0"
            class="mdm-btn-propagate-all"
            :disabled="propagatingParent === parent.id"
            title="Propagar todos los hijos default a los perfiles que tienen este padre"
            @click.stop="openPropagateAll(parent)"
          >
            <i v-if="propagatingParent === parent.id" class="bi bi-arrow-repeat spin"></i>
            <i v-else class="bi bi-send-fill"></i>
            {{ propagatingParent === parent.id ? 'Propagando...' : 'Propagar Todos' }}
          </button>

          <!-- CHEVRON ACORDEÓN -->
          <i class="mdm-chevron bi" :class="expandedId === parent.id ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
        </div>

        <!-- LISTA DE HIJOS (acordeón) -->
        <div v-show="expandedId === parent.id" class="mdm-children">
          <div
            v-for="child in parent.children"
            :key="child.id"
            class="mdm-child-item"
            :class="{ 'mdm-child--active': child.is_default_child }"
          >
            <span class="mdm-child-icon">
              <i v-if="child.icon?.startsWith('bi-')" :class="`bi ${child.icon}`"></i>
              <i v-else class="bi bi-file-earmark"></i>
            </span>

            <span class="mdm-child-name">{{ child.name }}</span>
            <span class="mdm-route">{{ child.route || '—' }}</span>

            <!-- TOGGLE is_default_child -->
            <button
              class="mdm-toggle"
              :class="child.is_default_child ? 'mdm-toggle--on' : 'mdm-toggle--off'"
              :disabled="toggling === child.id"
              :title="child.is_default_child ? 'Quitar del default' : 'Marcar como default'"
              @click="toggleDefault(parent, child)"
            >
              <i v-if="toggling === child.id" class="bi bi-arrow-repeat spin"></i>
              <template v-else>
                <i v-if="child.is_default_child" class="bi bi-toggle-on"></i>
                <i v-else class="bi bi-toggle-off"></i>
                {{ child.is_default_child ? 'Default' : 'Opcional' }}
              </template>
            </button>
          </div>
        </div>

      </div>
    </div>

    <!-- MODAL CONFIRMAR PROPAGAR TODOS -->
    <teleport to="body">
      <div v-if="propagateModal.open" class="mdm-overlay" @click.self="propagateModal.open = false">
        <div class="mdm-modal">
          <div class="mdm-modal-header">
            <span><i class="bi bi-send-fill" style="color:#f59e0b"></i> Propagar hijos default</span>
            <button class="mdm-modal-close" @click="propagateModal.open = false"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="mdm-modal-body">
            <p>
              Se agregarán <strong>{{ propagateModal.children.length }} hijo(s)</strong> a los
              <strong>{{ propagateModal.profileCount }} perfil(es)</strong> que tienen
              <strong>{{ propagateModal.parentName }}</strong>:
            </p>

            <ul class="mdm-modal-list">
              <li v-for="c in propagateModal.children" :key="c.id">
                <i class="bi bi-check2-circle" style="color:#22c55e"></i> {{ c.name }}
              </li>
            </ul>

            <p class="mdm-modal-note">
              <i class="bi bi-shield-check"></i>
              Acción <strong>no destructiva</strong>: solo agrega donde falta.
              Los módulos ya existentes en cada perfil no se tocan.
            </p>
          </div>

          <div class="mdm-modal-footer">
            <button class="btn mdm-btn-cancel" @click="propagateModal.open = false">Cancelar</button>
            <button class="btn mdm-btn-confirm" :disabled="propagatingParent === propagateModal.parentId" @click="confirmPropagateAll">
              <i v-if="propagatingParent === propagateModal.parentId" class="bi bi-arrow-repeat spin"></i>
              <i v-else class="bi bi-send-fill"></i>
              {{ propagatingParent === propagateModal.parentId ? 'Propagando...' : 'Confirmar' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const tree = ref([])
const loading = ref(true)
const toggling = ref(null)
const propagatingParent = ref(null)
const expandedId = ref(null)

const propagateModal = ref({
  open: false, parentId: null, parentName: "", profileCount: 0, children: []
})

const kpi = computed(() => ({
  parents: tree.value.length,
  defaults: tree.value.reduce((s, p) => s + p.children.filter(c => c.is_default_child).length, 0),
  profiles: tree.value.reduce((max, p) => Math.max(max, p.profile_count), 0),
}))

function defaultCount(parent) {
  return parent.children.filter(c => c.is_default_child).length
}

function toggleAccordion(id) {
  expandedId.value = expandedId.value === id ? null : id
}

async function loadTree() {
  loading.value = true
  try {
    const res = await api.get("/system-modules/defaults-tree/")
    tree.value = res.data
  } catch {
    showToast("Error cargando árbol de módulos", "error")
  } finally {
    loading.value = false
  }
}

async function toggleDefault(parent, child) {
  toggling.value = child.id
  try {
    const res = await api.patch(`/system-modules/${child.id}/toggle-default`)
    child.is_default_child = res.data.is_default_child
    showToast(`"${child.name}" ${child.is_default_child ? "activado como default" : "quitado del default"}`, "success")
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al cambiar default", "error")
  } finally {
    toggling.value = null
  }
}

function openPropagateAll(parent) {
  const defaultChildren = parent.children.filter(c => c.is_default_child)
  propagateModal.value = {
    open: true,
    parentId: parent.id,
    parentName: parent.name,
    profileCount: parent.profile_count,
    children: defaultChildren,
  }
}

async function confirmPropagateAll() {
  const { parentId, children } = propagateModal.value
  propagatingParent.value = parentId

  let totalPropagated = 0
  let totalSkipped = 0
  const errors = []

  for (const child of children) {
    try {
      const res = await api.post("/business-profile-module/propagate-default-child/", { child_module_id: child.id })
      totalPropagated += res.data.propagated ?? 0
      totalSkipped += res.data.skipped ?? 0
    } catch (e) {
      errors.push(child.name)
    }
  }

  if (errors.length) {
    showToast(`Error en: ${errors.join(", ")}`, "error")
  } else {
    showToast(
      `Propagados ${children.length} módulo(s) — ${totalPropagated} inserción(es), ${totalSkipped} ya existían`,
      "success"
    )
  }

  propagateModal.value.open = false
  propagatingParent.value = null
}

onMounted(loadTree)
</script>

<style scoped>
.mdm-container {
  padding: 20px;
  max-width: 860px;
}

/* ── KPI Bar ── */
.mdm-kpi-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.mdm-kpi {
  flex: 1;
  min-width: 120px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.mdm-kpi .bi { font-size: 20px; color: #3b82f6; }
.mdm-kpi-value { font-size: 24px; font-weight: 700; color: #e2e8f0; }
.mdm-kpi-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: .4px; }

/* ── Info box ── */
.mdm-info-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #1e3a5f;
  border: 1px solid #1d4ed8;
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 13px;
  color: #bfdbfe;
  margin-bottom: 16px;
}
.mdm-info-box .bi { font-size: 16px; color: #60a5fa; flex-shrink: 0; margin-top: 2px; }

/* ── Empty ── */
.mdm-empty {
  color: #64748b;
  padding: 32px 0;
  text-align: center;
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.mdm-empty .bi { font-size: 28px; }

/* ── Group (Padre / Acordeón) ── */
.mdm-group {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  margin-bottom: 10px;
  overflow: hidden;
  transition: border-color .15s;
}
.mdm-group--open {
  border-color: #3b82f6;
}

/* ── Cabecera clicable ── */
.mdm-group-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: #0f172a;
  cursor: pointer;
  user-select: none;
  flex-wrap: wrap;
  transition: background .15s;
}
.mdm-group-header:hover { background: #1e293b; }
.mdm-group--open .mdm-group-header { border-bottom: 1px solid #334155; }

.mdm-group-icon { font-size: 18px; color: #3b82f6; flex-shrink: 0; }
.mdm-group-name { font-size: 15px; font-weight: 700; color: #e2e8f0; flex: 1; min-width: 100px; }
.mdm-route { font-size: 11px; color: #475569; font-family: monospace; }

.mdm-chevron {
  font-size: 14px;
  color: #475569;
  flex-shrink: 0;
  transition: color .15s;
}
.mdm-group--open .mdm-chevron { color: #3b82f6; }

/* ── Badges ── */
.mdm-badge-profiles,
.mdm-badge-defaults {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 600;
  flex-shrink: 0;
}
.mdm-badge-profiles { background: #1e3a5f; color: #93c5fd; border: 1px solid #1d4ed8; }
.mdm-badge-defaults  { background: #14532d; color: #86efac; border: 1px solid #16a34a; }
.mdm-badge-defaults--empty { background: #1e293b; color: #475569; border-color: #334155; }

/* ── Botón Propagar Todos (en cabecera padre) ── */
.mdm-btn-propagate-all {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #78350f;
  color: #fde68a;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
  flex-shrink: 0;
}
.mdm-btn-propagate-all:hover:not(:disabled) { background: #92400e; }
.mdm-btn-propagate-all:disabled { opacity: .5; cursor: not-allowed; }

/* ── Children ── */
.mdm-children { padding: 10px 12px 12px; display: flex; flex-direction: column; gap: 8px; }

.mdm-child-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  transition: border-color .15s;
  flex-wrap: wrap;
}
.mdm-child--active {
  border-color: #16a34a;
  background: #052e16;
}

.mdm-child-icon { font-size: 15px; color: #64748b; flex-shrink: 0; }
.mdm-child-name { font-size: 13px; font-weight: 600; color: #e2e8f0; flex: 1; min-width: 80px; }

/* ── Toggle ── */
.mdm-toggle {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: none;
  border-radius: 20px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s, color .15s;
  flex-shrink: 0;
}
.mdm-toggle--on  { background: #14532d; color: #86efac; }
.mdm-toggle--off { background: #1e293b; color: #64748b; border: 1px solid #334155; }
.mdm-toggle--on:hover  { background: #166534; }
.mdm-toggle--off:hover { background: #334155; color: #94a3b8; }
.mdm-toggle:disabled   { opacity: .5; cursor: not-allowed; }
.mdm-toggle .bi { font-size: 16px; }

/* ── Modal ── */
.mdm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 16px;
}

.mdm-modal {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 14px;
  width: 100%;
  max-width: 460px;
  box-shadow: 0 20px 60px rgba(0,0,0,.5);
}

.mdm-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #334155;
  font-size: 15px;
  font-weight: 700;
  color: #e2e8f0;
  gap: 10px;
}
.mdm-modal-close {
  background: transparent; border: none; color: #64748b;
  font-size: 16px; cursor: pointer; border-radius: 6px; padding: 4px 6px;
}
.mdm-modal-close:hover { color: #f87171; }

.mdm-modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: #e2e8f0;
  font-size: 14px;
}

.mdm-modal-list {
  list-style: none;
  padding: 0;
  margin: 0;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  overflow: hidden;
}
.mdm-modal-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  font-size: 13px;
  border-bottom: 1px solid #1e293b;
}
.mdm-modal-list li:last-child { border-bottom: none; }

.mdm-modal-note {
  background: #0f172a;
  border: 1px solid #1d4ed8;
  border-radius: 8px;
  padding: 10px 14px;
  color: #93c5fd;
  font-size: 12px;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.mdm-modal-note .bi { flex-shrink: 0; margin-top: 2px; }

.mdm-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px 18px;
  border-top: 1px solid #334155;
}

.mdm-btn-cancel {
  background: #0f172a; color: #94a3b8;
  border: 1px solid #334155; border-radius: 8px;
  font-size: 13px; padding: 8px 18px;
}
.mdm-btn-cancel:hover { background: #1e293b; }

.mdm-btn-confirm {
  display: inline-flex; align-items: center; gap: 6px;
  background: #78350f; color: #fde68a;
  border: 1px solid #f59e0b; border-radius: 8px;
  font-size: 13px; font-weight: 600; padding: 8px 18px;
  cursor: pointer; transition: background .15s;
}
.mdm-btn-confirm:hover:not(:disabled) { background: #92400e; }
.mdm-btn-confirm:disabled { opacity: .5; cursor: not-allowed; }

/* ── Responsive 768px ── */
@media (max-width: 768px) {
  .mdm-kpi-bar { gap: 8px; }
  .mdm-kpi { min-width: 90px; padding: 10px 12px; }
  .mdm-kpi-value { font-size: 20px; }
  .mdm-group-name { font-size: 14px; }
  .mdm-child-item { padding: 12px; gap: 8px; }
  .mdm-child-name { font-size: 14px; }
  .mdm-route { display: none; }
  .mdm-toggle, .mdm-btn-propagate-all { font-size: 11px; padding: 5px 10px; }
}

/* ── Responsive 576px ── */
@media (max-width: 576px) {
  .mdm-container { padding: 12px; }
  .mdm-kpi-bar { flex-wrap: nowrap; overflow-x: auto; }
  .mdm-kpi { min-width: 100px; }
  .mdm-group-header { flex-direction: column; align-items: flex-start; }
  .mdm-child-item { flex-direction: column; align-items: flex-start; }
  .mdm-toggle, .mdm-btn-propagate-all { width: 100%; justify-content: center; }
}

.spin { animation: spin .7s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
</style>
