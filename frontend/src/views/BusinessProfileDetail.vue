<template>
  <div class="container mt-4 pb-5 bpd">

    <!-- 🔥 SELECTOR DE PERFIL -->
    <div class="mb-3">
      <label class="form-label">Seleccionar perfil</label>
      <select class="form-select" :value="selectedProfileId" @change="pedirCambioPerfil($event)">
        <option disabled value="">Seleccione un perfil</option>
        <option v-for="p in $ordenAlfa(profiles, 'name')" :key="p.id" :value="p.id">
          {{ p.name }}
        </option>
      </select>
    </div>

    <!-- MÓDULOS -->
    <div class="card p-3 mt-4">

      <!-- ENCABEZADO: título + guardar en la misma línea -->
      <div class="bpd-head">
        <h5 class="mb-0">
          Módulos del perfil
          <span v-if="selectedProfileId" class="bpd-total">
            · {{ selectedModules.length }} de {{ modules.length }}
          </span>
        </h5>
        <button
          class="btn btn-success"
          @click="abrirResumen"
          :disabled="!selectedProfileId || !cambios.total || guardando"
        >
          <span v-if="guardando" class="spinner-border spinner-border-sm me-1"></span>
          {{ cambios.total ? `Guardar (${cambios.total} ${cambios.total === 1 ? 'cambio' : 'cambios'})` : 'Guardar módulos' }}
        </button>
      </div>

      <div v-if="!selectedProfileId" class="text-muted mt-3">
        Seleccione un perfil para ver sus módulos.
      </div>

      <template v-else>
        <!-- BUSCADOR -->
        <div class="input-group mt-3">
          <span class="input-group-text"><i class="bi bi-search"></i></span>
          <input
            v-model="busqueda"
            type="text"
            class="form-control"
            placeholder="Buscar módulo por nombre o ruta..."
            maxlength="60"
          />
          <button v-if="busqueda" class="btn btn-outline-secondary" @click="busqueda = ''">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <!-- PESTAÑAS (solo móvil) -->
        <div class="bpd-tabs mt-3">
          <button :class="{ activa: tabMovil === 'sel' }" @click="tabMovil = 'sel'">
            Seleccionados ({{ selectedModules.length }})
          </button>
          <button :class="{ activa: tabMovil === 'disp' }" @click="tabMovil = 'disp'">
            Disponibles ({{ modules.length - selectedModules.length }})
          </button>
        </div>

        <div class="row mt-3 g-3">
          <div
            v-for="panel in paneles"
            :key="panel.key"
            class="col-md-6 bpd-col"
            :class="{ 'oculto-movil': tabMovil !== panel.key }"
          >
            <div class="card p-3 h-100">
              <h5 :class="panel.key === 'sel' ? 'text-success' : 'text-secondary'">
                {{ panel.titulo }}
              </h5>

              <div v-if="panel.grupos.length">
                <div
                  v-for="g in panel.grupos"
                  :key="g.key"
                  class="bpd-grupo"
                  :class="{ incompleto: g.incompleto }"
                >
                  <!-- Fila del padre -->
                  <div class="bpd-grupo-head" @click="toggleGrupo(g.key)">
                    <div class="bpd-grupo-titulo">
                      <i class="bi bpd-chevron" :class="estaAbierto(g.key) ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
                      <i v-if="g.icon" class="bi" :class="g.icon"></i>
                      <span class="bpd-grupo-nombre">{{ g.nombre }}</span>
                    </div>
                    <div class="bpd-grupo-pie">
                      <span
                        class="badge bpd-contador"
                        :class="g.incompleto ? 'bg-warning text-dark' : 'bg-light text-secondary'"
                        :title="g.incompleto ? 'Incompleto' : ''"
                      >
                        {{ g.selHijos }}/{{ g.totalHijos }} {{ g.independiente ? 'módulos' : (g.totalHijos === 1 ? 'hijo' : 'hijos') }}
                      </span>
                      <span v-if="g.faltaPadre" class="bpd-falta-padre">
                        <i class="bi bi-exclamation-triangle"></i>
                        {{ panel.key === 'sel' ? 'Padre no agregado' : 'Falta agregar el padre' }}
                      </span>
                      <button
                        v-if="panel.key === 'disp'"
                        class="btn btn-sm btn-outline-success bpd-accion"
                        @click.stop="agregarGrupo(g)"
                        :title="g.independiente ? 'Agregar todos los módulos independientes' : 'Agregar el padre con todos sus hijos'"
                      >
                        <i class="bi bi-plus-lg"></i><span class="bpd-accion-txt"> Agregar todo</span>
                      </button>
                      <button
                        v-else
                        class="btn btn-sm btn-outline-danger bpd-accion"
                        @click.stop="quitarGrupo(g)"
                        :title="g.independiente ? 'Quitar todos los módulos independientes' : 'Quitar el padre con todos sus hijos'"
                      >
                        <i class="bi bi-dash-lg"></i><span class="bpd-accion-txt"> Quitar todo</span>
                      </button>
                    </div>
                  </div>

                  <!-- Hijos -->
                  <div v-if="estaAbierto(g.key)" class="bpd-hijos">
                    <div
                      v-for="r in g.filas"
                      :key="r.m.id"
                      class="bpd-fila"
                      :class="{ contexto: r.contexto, incompleto: r.incompleto }"
                      :style="{ paddingLeft: `${0.5 + r.nivel * 1.1}rem` }"
                    >
                      <i v-if="r.m.icon" class="bi" :class="r.m.icon"></i>
                      <div class="bpd-fila-txt">
                        <div class="bpd-fila-nombre">
                          {{ r.m.name }}
                          <span v-if="r.contexto" class="bpd-nota">
                            {{ panel.key === 'sel' ? '(no agregado)' : '(ya agregado)' }}
                          </span>
                          <span v-if="r.m.is_sysadmin" class="badge bg-dark ms-1">SYSADMIN</span>
                          <span v-if="!r.m.is_active" class="badge bg-secondary ms-1">Inactivo</span>
                          <span v-if="r.incompleto" class="badge bg-warning text-dark ms-1">{{ r.selHijos }}/{{ r.total - 1 }}</span>
                        </div>
                        <div v-if="r.m.route" class="bpd-ruta">{{ r.m.route }}</div>
                      </div>
                      <button
                        v-if="panel.key === 'disp'"
                        class="btn btn-sm btn-outline-success bpd-btn-fila"
                        @click="agregar(r.m.id)"
                        :title="r.tieneHijos ? 'Agregar con todos sus hijos' : 'Agregar'"
                      >
                        <i class="bi bi-plus-lg"></i>
                      </button>
                      <button
                        v-else
                        class="btn btn-sm btn-outline-danger bpd-btn-fila"
                        @click="quitar(r.m.id)"
                        :title="r.tieneHijos ? 'Quitar con todos sus hijos' : 'Quitar'"
                      >
                        <i class="bi bi-dash-lg"></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else>
                <p class="text-muted mb-0">{{ busqueda ? 'Sin coincidencias' : panel.vacio }}</p>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- RESUMEN ANTES DE GUARDAR -->
    <div v-if="modalResumen" class="bpd-modal-fondo" @click.self="modalResumen = false">
      <div class="bpd-modal">
        <h5 class="mb-2">Confirmar cambios</h5>
        <p class="text-muted small mb-3">
          Afecta a todas las empresas del perfil <strong>{{ nombrePerfil }}</strong>.
        </p>
        <div v-if="cambios.agregados.length" class="mb-3">
          <div class="fw-semibold text-success mb-1">Se agregarán ({{ cambios.agregados.length }})</div>
          <ul class="bpd-lista">
            <li v-for="m in cambios.agregados" :key="m.id">{{ rutaNombre(m) }}</li>
          </ul>
        </div>
        <div v-if="cambios.quitados.length" class="mb-3">
          <div class="fw-semibold text-danger mb-1">Se quitarán ({{ cambios.quitados.length }})</div>
          <ul class="bpd-lista">
            <li v-for="m in cambios.quitados" :key="m.id">{{ rutaNombre(m) }}</li>
          </ul>
        </div>
        <div class="d-flex justify-content-end gap-2">
          <button class="btn btn-outline-secondary" @click="modalResumen = false">Cancelar</button>
          <button class="btn btn-success" @click="saveModules" :disabled="guardando">Guardar</button>
        </div>
      </div>
    </div>

    <!-- CAMBIOS SIN GUARDAR AL CAMBIAR DE PERFIL -->
    <div v-if="perfilPendiente" class="bpd-modal-fondo" @click.self="perfilPendiente = null">
      <div class="bpd-modal">
        <h5 class="mb-2">Cambios sin guardar</h5>
        <p class="mb-3">
          Tiene {{ cambios.total }} {{ cambios.total === 1 ? 'cambio' : 'cambios' }} sin guardar en
          <strong>{{ nombrePerfil }}</strong>. Si cambia de perfil se perderán.
        </p>
        <div class="d-flex justify-content-end gap-2">
          <button class="btn btn-outline-secondary" @click="perfilPendiente = null">Seguir aquí</button>
          <button class="btn btn-danger" @click="confirmarCambioPerfil">Descartar y cambiar</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>

/* =================================================
IMPORTS
================================================= */

import { ref, onMounted, computed } from "vue";
import api from "@/services/apis";
import { showToast } from "@/utils/toast";
import { useMenuStore } from "@/stores/menuStore";
import { ordenAlfa } from "@/utils/orden";

/* =================================================
STATE
================================================= */

const menuStore = useMenuStore();
const profiles = ref([]);
const selectedProfileId = ref("");

const modules = ref([]);
const selectedModules = ref([]);
const originalModules = ref([]);

const busqueda = ref("");
const grupoAbierto = ref(null);   // un solo padre expandido a la vez (en ambos paneles)
const tabMovil = ref("disp");
const modalResumen = ref(false);
const perfilPendiente = ref(null);
const guardando = ref(false);

const INDEPENDIENTES = "__independientes__";

/* =================================================
ÁRBOL DEL CATÁLOGO (system_modules.parent_id)
================================================= */

const porId = computed(() => new Map(modules.value.map(m => [m.id, m])));

const hijosDe = computed(() => {
  const mapa = new Map();
  for (const m of modules.value) {
    if (m.parent_id == null || !porId.value.has(m.parent_id)) continue;
    if (!mapa.has(m.parent_id)) mapa.set(m.parent_id, []);
    mapa.get(m.parent_id).push(m);
  }
  for (const [k, lista] of mapa) mapa.set(k, ordenAlfa(lista, "name"));
  return mapa;
});

const raices = computed(() =>
  ordenAlfa(modules.value.filter(m => m.parent_id == null || !porId.value.has(m.parent_id)), "name")
);

const selSet = computed(() => new Set(selectedModules.value));

// id + todos sus descendientes
const subarbol = (id, acc = []) => {
  acc.push(id);
  for (const h of hijosDe.value.get(id) || []) subarbol(h.id, acc);
  return acc;
};

const ancestros = (id) => {
  const res = [];
  let m = porId.value.get(id);
  const vistos = new Set();
  while (m && m.parent_id != null && porId.value.has(m.parent_id) && !vistos.has(m.id)) {
    vistos.add(m.id);
    res.push(m.parent_id);
    m = porId.value.get(m.parent_id);
  }
  return res;
};

const normalizar = (t) => String(t ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

const coincide = (m) => {
  const q = normalizar(busqueda.value.trim());
  return !q || normalizar(m.name).includes(q) || normalizar(m.route).includes(q);
};

/* =================================================
PANELES
================================================= */

// Filas visibles de un subárbol en un panel. Un nodo se muestra si le toca a ese panel o si
// tiene descendientes que le tocan (en ese caso sale atenuado como contexto).
const construirFilas = (nodo, panel, nivel, filas) => {
  const ids = subarbol(nodo.id);
  const sel = ids.filter(i => selSet.value.has(i)).length;
  const propio = panel === "sel" ? selSet.value.has(nodo.id) : !selSet.value.has(nodo.id);
  const algunoEnPanel = panel === "sel" ? sel > 0 : sel < ids.length;
  if (!algunoEnPanel) return false;

  const pos = filas.length;
  let hijoVisible = false;
  for (const h of hijosDe.value.get(nodo.id) || []) {
    if (construirFilas(h, panel, nivel + 1, filas)) hijoVisible = true;
  }
  if (!hijoVisible && (!propio || !coincide(nodo))) return false;

  const tieneHijos = ids.length > 1;
  filas.splice(pos, 0, {
    m: nodo,
    nivel,
    contexto: !propio,
    tieneHijos,
    sel,
    selHijos: sel - (selSet.value.has(nodo.id) ? 1 : 0),
    total: ids.length,
    incompleto: tieneHijos && sel > 0 && sel < ids.length,
  });
  return true;
};

const gruposDe = (panel) => {
  const grupos = [];
  const sueltos = [];
  for (const r of raices.value) {
    const ids = subarbol(r.id);
    if (ids.length === 1) { sueltos.push(r); continue; }
    const filas = [];
    for (const h of hijosDe.value.get(r.id) || []) construirFilas(h, panel, 0, filas);
    const sel = ids.filter(i => selSet.value.has(i)).length;
    const raizEnPanel = panel === "sel" ? selSet.value.has(r.id) : !selSet.value.has(r.id);
    if (!filas.length && !(raizEnPanel && coincide(r))) continue;
    grupos.push({
      key: r.id,
      id: r.id,
      nombre: r.name,
      icon: r.icon,
      sel,
      total: ids.length,
      // El contador muestra solo los hijos; si falta el padre se avisa aparte
      selHijos: sel - (selSet.value.has(r.id) ? 1 : 0),
      totalHijos: ids.length - 1,
      faltaPadre: sel > 0 && !selSet.value.has(r.id),
      incompleto: sel > 0 && sel < ids.length,
      independiente: false,
      filas,
    });
  }

  // Módulos sin padre ni hijos van juntos al final
  const filasSueltas = sueltos
    .filter(m => (panel === "sel" ? selSet.value.has(m.id) : !selSet.value.has(m.id)) && coincide(m))
    .map(m => ({ m, nivel: 0, contexto: false, tieneHijos: false, sel: 0, total: 1, incompleto: false }));
  if (filasSueltas.length) {
    grupos.push({
      key: INDEPENDIENTES,
      nombre: "Módulos independientes",
      icon: "bi-grid",
      sel: sueltos.filter(m => selSet.value.has(m.id)).length,
      total: sueltos.length,
      selHijos: sueltos.filter(m => selSet.value.has(m.id)).length,
      totalHijos: sueltos.length,
      faltaPadre: false,
      incompleto: false,
      independiente: true,
      ids: filasSueltas.map(f => f.m.id),
      filas: filasSueltas,
    });
  }
  return grupos;
};

const paneles = computed(() => [
  { key: "sel", titulo: "Seleccionados", vacio: "Sin módulos seleccionados", grupos: gruposDe("sel") },
  { key: "disp", titulo: "Disponibles", vacio: "Todos los módulos están seleccionados", grupos: gruposDe("disp") },
]);

const estaAbierto = (key) => !!busqueda.value.trim() || grupoAbierto.value === key;

const toggleGrupo = (key) => {
  if (busqueda.value.trim()) return;
  grupoAbierto.value = grupoAbierto.value === key ? null : key;
};

/* =================================================
ACCIONES (agregar un hijo agrega su padre; quitar un padre quita sus hijos)
================================================= */

const agregar = (id) => {
  const nuevo = new Set(selectedModules.value);
  for (const i of [...subarbol(id), ...ancestros(id)]) nuevo.add(i);
  selectedModules.value = [...nuevo];
};

const quitar = (id) => {
  const fuera = new Set(subarbol(id));
  selectedModules.value = selectedModules.value.filter(i => !fuera.has(i));
};

const agregarGrupo = (g) => {
  if (g.independiente) {
    selectedModules.value = [...new Set([...selectedModules.value, ...g.ids])];
  } else {
    agregar(g.id);
  }
};

const quitarGrupo = (g) => {
  if (g.independiente) {
    const fuera = new Set(g.ids);
    selectedModules.value = selectedModules.value.filter(i => !fuera.has(i));
  } else {
    quitar(g.id);
  }
};

/* =================================================
CAMBIOS
================================================= */

const cambios = computed(() => {
  const orig = new Set(originalModules.value);
  const agregados = selectedModules.value.filter(i => !orig.has(i)).map(i => porId.value.get(i)).filter(Boolean);
  const quitados = originalModules.value.filter(i => !selSet.value.has(i)).map(i => porId.value.get(i)).filter(Boolean);
  return {
    agregados: ordenAlfa(agregados, rutaNombre),
    quitados: ordenAlfa(quitados, rutaNombre),
    total: agregados.length + quitados.length,
  };
});

function rutaNombre(m) {
  return [...ancestros(m.id)].reverse().map(i => porId.value.get(i)?.name).concat(m.name).join(" › ");
}

const nombrePerfil = computed(() =>
  profiles.value.find(p => String(p.id) === String(selectedProfileId.value))?.name || ""
);

/* =================================================
LOAD DATA
================================================= */

const loadProfiles = async () => {
  try {
    const res = await api.get("/business-profiles/");
    profiles.value = res.data.data;
  } catch (error) {
    console.error("Error loading profiles:", error);
  }
};

const loadAllModules = async () => {
  try {
    const res = await api.get("/system-modules/flat/");
    modules.value = res.data;
  } catch (error) {
    console.error("Error loading modules:", error);
  }
};

const loadProfileModules = async () => {
  if (!selectedProfileId.value) return;

  try {
    const res = await api.get(`/business-profiles/${selectedProfileId.value}/modules/`);
    selectedModules.value = res.data.map(m => m.id);
    originalModules.value = [...selectedModules.value];
  } catch (error) {
    console.error("Error loading profile modules:", error);
    showToast("Error al cargar los módulos del perfil", "error");
  }
};

/* =================================================
EVENTS
================================================= */

const cambiarPerfil = async (id) => {
  selectedProfileId.value = id;
  grupoAbierto.value = null;
  busqueda.value = "";
  await loadProfileModules();
};

const pedirCambioPerfil = (e) => {
  const id = e.target.value;
  if (cambios.value.total) {
    e.target.value = selectedProfileId.value;   // se mantiene hasta que confirme
    perfilPendiente.value = id;
    return;
  }
  cambiarPerfil(id);
};

const confirmarCambioPerfil = async () => {
  const id = perfilPendiente.value;
  perfilPendiente.value = null;
  await cambiarPerfil(id);
};

/* =================================================
SAVE
================================================= */

const abrirResumen = () => {
  if (cambios.value.total) modalResumen.value = true;
};

const saveModules = async () => {
  guardando.value = true;
  try {
    await api.post(
      `/business-profiles/${selectedProfileId.value}/modules/`,
      selectedModules.value
    );
    modalResumen.value = false;
    await loadProfileModules();
    await menuStore.loadMenu();
    showToast("Módulos guardados correctamente", "success");
  } catch (error) {
    console.error("Error saving modules:", error);
    showToast(error?.response?.data?.detail || "Error al guardar módulos", "error");
  } finally {
    guardando.value = false;
  }
};

/* =================================================
INIT
================================================= */

onMounted(async () => {
  await loadProfiles();
  await loadAllModules();
});

</script>

<style scoped>
.bpd-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.bpd-total {
  font-size: 0.85rem;
  font-weight: 400;
  color: #6c757d;
}

.bpd-tabs { display: none; }

.bpd-grupo {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-left: 4px solid transparent;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  background: rgba(255, 255, 255, 0.55);
  overflow: hidden;
}
.bpd-grupo.incompleto {
  border-left-color: #f0ad00;
  background: #fff8e1;
}
.bpd-grupo-head {
  padding: 0.45rem 0.6rem;
  cursor: pointer;
  user-select: none;
}
.bpd-grupo-titulo {
  display: flex;
  align-items: flex-start;
  gap: 0.45rem;
  font-size: 0.9rem;
}
.bpd-grupo-titulo .bi { line-height: 1.35; }
.bpd-grupo-pie {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.3rem;
  padding-left: 1.2rem;
}
.bpd-grupo-pie .bpd-accion { margin-left: auto; }
.bpd-falta-padre { font-size: 0.72rem; color: #9a6700; font-weight: 600; }
.bpd-grupo-head:hover { background: rgba(0, 0, 0, 0.04); }
.bpd-chevron { font-size: 0.8rem; color: #6c757d; }
.bpd-grupo-nombre { font-weight: 600; flex: 1; min-width: 0; line-height: 1.35; overflow-wrap: break-word; }
.bpd-contador { font-size: 0.7rem; }
.bpd-accion { white-space: nowrap; font-size: 0.78rem; padding: 0.15rem 0.5rem; }

.bpd-hijos { border-top: 1px solid rgba(0, 0, 0, 0.08); background: #fff; }
.bpd-fila {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.6rem;
  font-size: 0.85rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
.bpd-fila:last-child { border-bottom: 0; }
.bpd-fila.incompleto { background: #fff8e1; }
.bpd-fila.contexto .bpd-fila-nombre,
.bpd-fila.contexto > .bi { color: #9aa0a6; }
.bpd-fila-txt { flex: 1; min-width: 0; }
.bpd-fila-nombre { line-height: 1.25; }
.bpd-nota { font-size: 0.75rem; font-style: italic; }
.bpd-ruta {
  font-size: 0.68rem;
  color: #8a9199;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bpd-btn-fila { padding: 0.05rem 0.4rem; font-size: 0.8rem; }
.bpd-fila .badge { font-size: 0.62rem; }

.bpd-modal-fondo {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1060;
  padding: 16px;
}
.bpd-modal {
  background: #fff;
  border-radius: 12px;
  padding: 1.25rem;
  width: 100%;
  max-width: 520px;
  max-height: 85vh;
  overflow-y: auto;
}
.bpd-lista {
  max-height: 30vh;
  overflow-y: auto;
  padding-left: 1.1rem;
  margin-bottom: 0;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .bpd-head {
    position: sticky;
    top: 0;
    z-index: 5;
    background: inherit;
    padding-bottom: 0.5rem;
  }
  .bpd-tabs {
    display: flex;
    gap: 0.25rem;
    background: rgba(0, 0, 0, 0.06);
    border-radius: 8px;
    padding: 0.25rem;
  }
  .bpd-tabs button {
    flex: 1;
    border: 0;
    background: transparent;
    padding: 0.45rem;
    border-radius: 6px;
    font-size: 0.9rem;
  }
  .bpd-tabs button.activa { background: #fff; font-weight: 600; }
  .bpd-col.oculto-movil { display: none; }
}

@media (max-width: 576px) {
  .bpd { padding-left: 0; padding-right: 0; }
  .bpd-accion-txt { display: none; }
  .bpd-grupo-head { padding: 0.5rem; }
  .bpd-head .btn { font-size: 0.85rem; padding: 0.35rem 0.6rem; }
}
</style>
