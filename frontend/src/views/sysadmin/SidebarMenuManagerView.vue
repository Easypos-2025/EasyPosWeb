<template>
  <div class="smm-page">
    <div class="smm-head">
      <h4 class="smm-h"><i class="bi bi-layout-sidebar-inset me-2"></i>{{ moduleName || 'Menú del Cliente (Vista previa)' }}</h4>
      <p class="smm-sub">
        Así ve el menú cada empresa del perfil, en el mismo orden y con los mismos nombres. Lo que no está aquí, el cliente
        no lo ve. Cada rol ve además solo lo que tenga permitido.
      </p>
    </div>

    <!-- PERFIL -->
    <div class="smm-card">
      <label class="smm-label">Perfil (tipo de negocio)</label>
      <select v-model="perfilId" class="form-select">
        <option value="">— Seleccionar —</option>
        <option v-for="p in $ordenAlfa(perfiles, 'name')" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </div>

    <template v-if="perfilId">
      <div v-if="cargando" class="smm-empty"><div class="spinner-border text-primary"></div></div>
      <template v-else>
        <!-- PROBLEMAS -->
        <div v-if="previa.problemas.length" class="smm-card smm-card--alerta">
          <div class="smm-alerta-head">
            <span><i class="bi bi-exclamation-triangle-fill"></i> {{ previa.problemas.length }} opción(es) que el cliente NO ve</span>
            <button v-if="reparables" class="smm-btn smm-btn--sec" :disabled="trabajando" @click="reparar">
              <i class="bi bi-tools"></i> Reparar {{ reparables }}
            </button>
          </div>
          <ul class="smm-problemas">
            <li v-for="p in previa.problemas" :key="`${p.tipo}-${p.id}`">
              <b>{{ p.name }}</b> <span v-if="p.route" class="smm-route">{{ p.route }}</span> — {{ p.texto }}
            </li>
          </ul>
          <p class="smm-nota">Reparar sube a la raíz lo que está mal colgado (y lo del tercer nivel lo pasa a su grupo), así el
            cliente lo vuelve a ver. Los módulos inactivos y los grupos vacíos no se tocan.</p>
        </div>

        <!-- AGREGAR O MOVER -->
        <div class="smm-card">
          <div class="smm-titulo"><i class="bi bi-plus-circle-fill"></i> Agregar o mover una opción</div>
          <div class="smm-form">
            <div class="smm-field smm-field--2">
              <label class="smm-label">Módulo</label>
              <select v-model="form.module_id" class="form-select">
                <option :value="null">— Seleccionar —</option>
                <option v-for="m in $ordenAlfa(previa.catalogo, 'name')" :key="m.id" :value="m.id">
                  {{ m.name }}{{ m.route ? ` · ${m.route}` : ' · (grupo)' }}{{ m.en_perfil ? ` — ya está en ${m.grupo}` : '' }}
                </option>
              </select>
              <small v-if="seleccionado?.en_perfil" class="smm-ya">
                <i class="bi bi-info-circle"></i> Ya está en este perfil, en «{{ seleccionado.grupo }}». Cada módulo va una sola
                vez por perfil: se moverá al grupo y con el nombre que escoja aquí.
              </small>
            </div>
            <div class="smm-field">
              <label class="smm-label">Nombre que verá el cliente <span class="smm-opc">(opcional)</span></label>
              <input v-model.trim="form.display_name" class="form-control" maxlength="100" placeholder="Vacío = nombre del catálogo" />
            </div>
            <div class="smm-field">
              <label class="smm-label">Grupo</label>
              <select v-model="form.parent_id" class="form-select" :disabled="form.includeDefaults && defaults.length > 0">
                <option :value="null">— Raíz (primer nivel) —</option>
                <option v-for="g in gruposPara(seleccionado?.bpm_id)" :key="g.id" :value="g.id">{{ etiquetaGrupo(g) }}</option>
              </select>
            </div>
          </div>
          <label v-if="defaults.length && !seleccionado?.en_perfil" class="smm-check">
            <input v-model="form.includeDefaults" type="checkbox" />
            Incluir {{ defaults.length }} opción(es) por defecto: <em>{{ defaults.map(c => c.name).join(', ') }}</em>
            <small v-if="form.includeDefaults">(un grupo con opciones va en la raíz: el menú del cliente muestra dos niveles)</small>
          </label>
          <div class="smm-acc">
            <button class="smm-btn" :disabled="!form.module_id || trabajando" @click="agregarOMover">
              <span v-if="trabajando" class="spinner-border spinner-border-sm"></span>
              <i v-else class="bi" :class="seleccionado?.en_perfil ? 'bi-arrow-left-right' : 'bi-plus-lg'"></i>
              {{ seleccionado?.en_perfil ? 'Mover aquí' : 'Agregar' }}
            </button>
          </div>
        </div>

        <!-- VISTA PREVIA -->
        <div class="smm-card smm-card--menu">
          <div class="smm-menu-head">
            <div class="smm-titulo"><i class="bi bi-eye"></i> Menú que ve el cliente</div>
            <div class="smm-buscar">
              <i class="bi bi-search"></i>
              <input v-model.trim="buscar" class="form-control" placeholder="Buscar opción..." />
            </div>
          </div>
          <p class="smm-nota">Arrastre por <i class="bi bi-grip-vertical"></i> para cambiar el orden. Se abre un grupo a la vez.</p>

          <div v-if="!previa.arbol.length" class="smm-empty"><i class="bi bi-inbox"></i> Este perfil no tiene opciones</div>
          <draggable v-else v-model="previa.arbol" item-key="id" handle=".smm-drag" :disabled="!!buscar"
                     @end="guardarOrden(previa.arbol, null)">
            <template #item="{ element: g }">
              <div v-show="visible(g)" class="smm-nodo" :class="{ 'smm-nodo--grupo': g.children.length }">
                <div class="smm-fila" :class="{ 'smm-fila--abre': g.children.length }" @click="g.children.length && toggle(g.id)">
                  <span class="smm-drag" @click.stop><i class="bi bi-grip-vertical"></i></span>
                  <i class="smm-ico bi" :class="g.icon?.startsWith('bi-') ? g.icon : 'bi-dot'"></i>
                  <div class="smm-txt">
                    <span class="smm-nombre">{{ g.name }}</span>
                    <small v-if="g.display_name && g.display_name !== g.nombre_catalogo" class="smm-cat">({{ g.nombre_catalogo }})</small>
                    <span v-if="g.funcion" class="smm-badge">solo con {{ g.funcion }}</span>
                    <small class="smm-route">{{ g.route || (g.children.length ? `${g.children.length} opción(es)` : 'grupo vacío') }}</small>
                  </div>
                  <button class="smm-ib" title="Editar" @click.stop="abrirEditar(g)"><i class="bi bi-pencil-square"></i></button>
                  <button class="smm-ib smm-ib--rojo" title="Quitar del perfil" @click.stop="pedirQuitar(g)"><i class="bi bi-trash3"></i></button>
                  <i v-if="g.children.length" class="bi smm-chev" :class="abierto(g) ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
                </div>
                <draggable v-if="g.children.length && abierto(g)" v-model="g.children" item-key="id" handle=".smm-drag"
                           class="smm-hijos" :disabled="!!buscar" @end="guardarOrden(g.children, g.id)">
                  <template #item="{ element: h }">
                    <div v-show="visible(h)" class="smm-fila smm-fila--hijo">
                      <span class="smm-drag"><i class="bi bi-grip-vertical"></i></span>
                      <i class="smm-ico bi" :class="h.icon?.startsWith('bi-') ? h.icon : 'bi-dot'"></i>
                      <div class="smm-txt">
                        <span class="smm-nombre">{{ h.name }}</span>
                        <small v-if="h.display_name && h.display_name !== h.nombre_catalogo" class="smm-cat">({{ h.nombre_catalogo }})</small>
                        <span v-if="h.funcion" class="smm-badge">solo con {{ h.funcion }}</span>
                        <small class="smm-route">{{ h.route }}</small>
                      </div>
                      <button class="smm-ib" title="Editar" @click="abrirEditar(h)"><i class="bi bi-pencil-square"></i></button>
                      <button class="smm-ib smm-ib--rojo" title="Quitar del perfil" @click="pedirQuitar(h)"><i class="bi bi-trash3"></i></button>
                    </div>
                  </template>
                </draggable>
              </div>
            </template>
          </draggable>
        </div>
      </template>
    </template>

    <!-- QUITAR -->
    <teleport to="body">
      <div v-if="quitar.item" class="smm-overlay" @click.self="quitar.item = null">
        <div class="smm-modal">
          <div class="smm-modal-head"><b><i class="bi bi-trash3 text-danger"></i> Quitar del perfil</b>
            <button class="smm-x" @click="quitar.item = null"><i class="bi bi-x-lg"></i></button></div>
          <div class="smm-modal-body">
            <p>¿Quitar <b>{{ quitar.item.name }}</b> del menú de este perfil? Ninguna empresa del perfil lo volverá a ver.</p>
            <p v-if="quitar.item.children?.length" class="smm-nota">Sus {{ quitar.item.children.length }} opción(es) pasan a la raíz.</p>
          </div>
          <div class="smm-modal-foot">
            <button class="smm-btn smm-btn--sec" @click="quitar.item = null">Cancelar</button>
            <button class="smm-btn smm-btn--rojo" :disabled="trabajando" @click="confirmarQuitar">Quitar</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- EDITAR -->
    <teleport to="body">
      <div v-if="edit.item" class="smm-overlay" @click.self="edit.item = null">
        <div class="smm-modal">
          <div class="smm-modal-head"><b><i class="bi bi-pencil-square"></i> {{ edit.item.nombre_catalogo }}</b>
            <button class="smm-x" @click="edit.item = null"><i class="bi bi-x-lg"></i></button></div>
          <div class="smm-modal-body">
            <div class="smm-field">
              <label class="smm-label">Nombre que verá el cliente <span class="smm-opc">(vacío = {{ edit.item.nombre_catalogo }})</span></label>
              <input v-model.trim="edit.display_name" class="form-control" maxlength="100" />
            </div>
            <div class="smm-field">
              <label class="smm-label">Grupo</label>
              <select v-model="edit.parent_id" class="form-select" :disabled="edit.item.children?.length > 0">
                <option :value="null">— Raíz (primer nivel) —</option>
                <option v-for="g in gruposPara(edit.item.id)" :key="g.id" :value="g.id">{{ etiquetaGrupo(g) }}</option>
              </select>
              <small v-if="edit.item.children?.length" class="smm-nota">Es un grupo con opciones: va en la raíz.</small>
            </div>
          </div>
          <div class="smm-modal-foot">
            <button class="smm-btn smm-btn--sec" @click="edit.item = null">Cancelar</button>
            <button class="smm-btn" :disabled="trabajando" @click="guardarEdicion">Guardar</button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
// Menú del Cliente (Vista previa): el menú de cada perfil EXACTAMENTE como lo ve el cliente (backend /menu/preview).
import { ref, computed, watch, onMounted } from "vue"
import draggable from "vuedraggable"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useMenuStore } from "@/stores/menuStore"
import { useModuleName } from "@/composables/useModuleName"

const { moduleName } = useModuleName()
const menuStore = useMenuStore()
const perfiles = ref([])
const perfilId = ref("")
const previa = ref({ arbol: [], problemas: [], grupos: [], catalogo: [] })
const cargando = ref(false)
const trabajando = ref(false)
const buscar = ref("")
const grupoAbierto = ref(null)
const form = ref({ module_id: null, display_name: "", parent_id: null, includeDefaults: false })
const defaults = ref([])
const quitar = ref({ item: null })
const edit = ref({ item: null, display_name: "", parent_id: null })

const REPARABLES = ["padre_inexistente", "padre_inactivo", "ciclo", "hijo_sin_ruta", "tercer_nivel"]
const reparables = computed(() => previa.value.problemas.filter(p => REPARABLES.includes(p.tipo)).length)
const seleccionado = computed(() => previa.value.catalogo.find(m => m.id === form.value.module_id) || null)
const error = (e, d) => e?.response?.data?.detail || d

const norm = (t) => String(t ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
const coincide = (n) => !buscar.value || [n.name, n.nombre_catalogo, n.route].some(v => norm(v).includes(norm(buscar.value)))
const visible = (n) => coincide(n) || (n.children || []).some(coincide)
const abierto = (g) => (buscar.value ? (g.children || []).some(coincide) || coincide(g) : grupoAbierto.value === g.id)
const toggle = (id) => { if (!buscar.value) grupoAbierto.value = grupoAbierto.value === id ? null : id }
const etiquetaGrupo = (g) => (g.name !== g.nombre_catalogo ? `${g.name} (${g.nombre_catalogo})` : g.name)
const gruposPara = (bpmId) => previa.value.grupos.filter(g => g.id !== bpmId)

async function cargarPerfiles() {
  try {
    const { data } = await api.get("/business-profiles/")
    perfiles.value = data.data ?? data
  } catch { perfiles.value = [] }
}

async function cargar(silencioso = false) {
  if (!perfilId.value) return
  if (!silencioso) cargando.value = true
  try {
    const { data } = await api.get(`/menu/preview/${perfilId.value}`)
    previa.value = data
  } catch (e) { showToast(error(e, "Error cargando el menú del perfil"), "error") }
  cargando.value = false
}

async function refrescar() {
  await cargar(true)
  await menuStore.loadMenu()
}

watch(perfilId, () => {
  grupoAbierto.value = null
  buscar.value = ""
  form.value = { module_id: null, display_name: "", parent_id: null, includeDefaults: false }
  cargar()
})

watch(() => form.value.module_id, async (id) => {
  defaults.value = []
  form.value.includeDefaults = false
  const m = seleccionado.value
  if (m?.en_perfil) {
    // se precarga su lugar y nombre actual para moverlo
    const nodo = previa.value.arbol.flatMap(g => [g, ...g.children]).find(n => n.id === m.bpm_id)
    form.value.parent_id = nodo?.parent_id ?? null
    form.value.display_name = nodo?.display_name || ""
    return
  }
  if (!id) return
  try {
    const { data } = await api.get(`/system-modules/${id}/defaults-preview/`)
    defaults.value = data
    form.value.includeDefaults = data.length > 0
  } catch { defaults.value = [] }
})

async function agregarOMover() {
  const m = seleccionado.value
  if (!m) return
  trabajando.value = true
  try {
    if (m.en_perfil) {
      await api.patch(`/business-profile-module/${m.bpm_id}`, { parent_id: form.value.parent_id, display_name: form.value.display_name || null })
      showToast(`«${m.name}» movido`, "success")
    } else if (form.value.includeDefaults && defaults.value.length) {
      const { data } = await api.post("/business-profile-module/add-parent-with-defaults/", {
        profile_id: perfilId.value, module_id: m.id, display_name: form.value.display_name || null })
      showToast(data.message || "Agregado con sus opciones", "success")
    } else {
      await api.post("/business-profile-module/add-module/", {
        profile_id: perfilId.value, module_id: m.id, parent_id: form.value.parent_id, display_name: form.value.display_name || null })
      showToast(`«${m.name}» agregado`, "success")
    }
    form.value = { module_id: null, display_name: "", parent_id: null, includeDefaults: false }
    await refrescar()
  } catch (e) { showToast(error(e, "No se pudo guardar"), "error") }
  trabajando.value = false
}

// Solo se guarda el orden de la lista que se movió (nunca se borra nada al reordenar)
async function guardarOrden(lista, parentId) {
  try {
    await api.put("/business-profile-module/reorder/", lista.map((n, i) => ({ id: n.id, parent_id: parentId, sort_order: i })))
    await menuStore.loadMenu()
  } catch (e) {
    showToast(error(e, "Error guardando el orden"), "error")
    await cargar(true)
  }
}

function pedirQuitar(item) { quitar.value.item = item }

async function confirmarQuitar() {
  trabajando.value = true
  try {
    await api.delete(`/business-profile-module/${quitar.value.item.id}`)
    showToast(`«${quitar.value.item.name}» quitado del perfil`, "success")
    quitar.value.item = null
    await refrescar()
  } catch (e) { showToast(error(e, "Error al quitar"), "error") }
  trabajando.value = false
}

function abrirEditar(item) {
  edit.value = { item, display_name: item.display_name || "", parent_id: item.parent_id ?? null }
}

async function guardarEdicion() {
  trabajando.value = true
  try {
    await api.patch(`/business-profile-module/${edit.value.item.id}`, {
      parent_id: edit.value.parent_id, display_name: edit.value.display_name || null })
    showToast("Opción actualizada", "success")
    edit.value.item = null
    await refrescar()
  } catch (e) { showToast(error(e, "Error al guardar"), "error") }
  trabajando.value = false
}

async function reparar() {
  trabajando.value = true
  try {
    const { data } = await api.post(`/menu/preview/${perfilId.value}/reparar`)
    showToast(`${data.movidos} opción(es) reubicadas: el cliente ya las ve`, "success")
    await refrescar()
  } catch (e) { showToast(error(e, "Error al reparar"), "error") }
  trabajando.value = false
}

onMounted(cargarPerfiles)
</script>

<style scoped>
.smm-page { padding: 20px; max-width: 860px; }
.smm-head { margin-bottom: 10px; }
.smm-h { font-weight: 800; color: #1e293b; margin: 0; }
.smm-sub { font-size: 13px; color: #475569; margin: 4px 0 0; }
.smm-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; color: #e2e8f0; padding: 14px; margin-top: 12px; }
.smm-card--alerta { background: #451a03; border-color: #b45309; }
.smm-alerta-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; font-weight: 700; color: #fde68a; }
.smm-problemas { margin: 8px 0 4px; padding-left: 18px; font-size: 13px; color: #fef3c7; }
.smm-problemas li { margin: 3px 0; }
.smm-titulo { font-size: 15px; font-weight: 700; display: flex; align-items: center; gap: 8px; color: #e2e8f0; }
.smm-titulo .bi { color: #60a5fa; }
.smm-label { font-size: 11.5px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: .3px; margin-bottom: 4px; display: block; }
.smm-opc { text-transform: none; font-weight: 400; color: #64748b; }
.smm-nota { font-size: 12px; color: #94a3b8; margin: 6px 0 0; }
.smm-ya { display: block; margin-top: 4px; font-size: 12px; color: #fbbf24; }
.smm-form { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
.smm-field { display: flex; flex-direction: column; min-width: 0; }
.smm-field--2 { grid-column: 1 / -1; }
.smm-check { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; font-size: 13px; color: #cbd5e1; margin-top: 10px; }
.smm-check small { color: #94a3b8; width: 100%; }
.smm-acc { display: flex; justify-content: flex-end; margin-top: 12px; }
.smm-btn { display: inline-flex; align-items: center; gap: 6px; border: none; border-radius: 9px; padding: 8px 16px; font-weight: 700; font-size: 14px; background: #2563eb; color: #fff; cursor: pointer; }
.smm-btn:disabled { opacity: .5; cursor: not-allowed; }
.smm-btn--sec { background: #334155; color: #e2e8f0; }
.smm-btn--rojo { background: #dc2626; }
.smm-menu-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
.smm-buscar { position: relative; width: 260px; max-width: 100%; }
.smm-buscar .bi { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: #64748b; }
.smm-buscar input { padding-left: 30px; }
.smm-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; color: #64748b; padding: 24px 0; }
.smm-nodo { margin-top: 6px; border-radius: 9px; background: #0f172a; border: 1px solid #334155; }
.smm-nodo--grupo { border-left: 3px solid #3b82f6; }
.smm-fila { display: flex; align-items: center; gap: 8px; padding: 9px 10px; }
.smm-fila--abre { cursor: pointer; }
.smm-fila--hijo { background: #1e293b; border-radius: 8px; margin: 4px 0; border-left: 3px solid #64748b; }
.smm-hijos { padding: 0 8px 8px 22px; }
.smm-drag { color: #475569; font-size: 17px; cursor: grab; padding: 4px 2px; touch-action: none; }
.smm-ico { color: #94a3b8; font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }
.smm-txt { flex: 1; min-width: 0; display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 8px; }
.smm-nombre { font-weight: 600; font-size: 14px; color: #f1f5f9; }
.smm-cat { color: #94a3b8; font-size: 12px; }
.smm-route { color: #64748b; font-size: 11px; font-family: monospace; width: 100%; }
.smm-badge { font-size: 10.5px; font-weight: 700; background: #422006; color: #fbbf24; border-radius: 999px; padding: 1px 7px; }
.smm-ib { border: 1px solid #334155; background: transparent; color: #93c5fd; border-radius: 7px; width: 32px; height: 32px; flex-shrink: 0; }
.smm-ib--rojo { color: #fca5a5; }
.smm-chev { color: #64748b; flex-shrink: 0; }
.smm-overlay { position: fixed; inset: 0; background: rgba(2,6,23,.6); display: flex; align-items: center; justify-content: center; z-index: 1060; padding: 16px; }
.smm-modal { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; border-radius: 12px; width: 100%; max-width: 460px; }
.smm-modal-head { display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; border-bottom: 1px solid #334155; }
.smm-modal-body { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.smm-modal-foot { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 14px; border-top: 1px solid #334155; }
.smm-x { border: none; background: none; color: #94a3b8; font-size: 16px; }

@media (max-width: 768px) {
  .smm-page { padding: 12px 10px 80px; }
  .smm-form { grid-template-columns: 1fr; }
  .smm-buscar { width: 100%; }
  .smm-overlay { align-items: flex-end; padding: 0; }
  .smm-modal { max-width: none; border-radius: 12px 12px 0 0; }
}
@media (max-width: 576px) {
  .smm-h { font-size: 18px; }
  .smm-hijos { padding-left: 10px; }
  .smm-ib { width: 30px; height: 30px; }
  .smm-route { display: none; }
}
</style>
