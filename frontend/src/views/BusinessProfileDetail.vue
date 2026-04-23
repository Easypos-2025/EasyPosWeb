<template>
  <div class="container mt-4 pb-5">

    <!-- HEADER -->
    

    <!-- 🔥 SELECTOR DE PERFIL -->
    <div class="mb-3">
      <label class="form-label">Seleccionar perfil</label>
      <select class="form-select" v-model="selectedProfileId" @change="onChangeProfile">
        <option disabled value="">Seleccione un perfil</option>
        <option v-for="p in profiles" :key="p.id" :value="p.id">
          {{ p.name }}
        </option>
      </select>
    </div>

    <!-- MÓDULOS -->
    <div class="card p-3 mt-4">
      <h5>Módulos del perfil</h5>

      <div class="row mt-3">

        <!-- ✅ SELECCIONADOS -->
        <div class="col-md-6">
          <div class="card p-3 h-100">
            <h5 class="text-success">Seleccionados</h5>

            <div v-if="selectedList.length">
              <div v-for="m in selectedList" :key="m.id">
                <label class="d-flex align-items-center gap-2">
                  <input
                    type="checkbox"
                    :value="m.id"
                    v-model="selectedModules"
                  />
                  {{ m.name }}
                </label>
              </div>
            </div>

            <div v-else>
              <p class="text-muted">Sin módulos seleccionados</p>
            </div>
          </div>
        </div>

        <!-- ❌ DISPONIBLES -->
        <div class="col-md-6">
          <div class="card p-3 h-100">
            <h5 class="text-secondary">Disponibles</h5>

            <div v-if="availableList.length">
              <div v-for="m in availableList" :key="m.id">
                <label class="d-flex align-items-center gap-2">
                  <input
                    type="checkbox"
                    :value="m.id"
                    v-model="selectedModules"
                  />
                  {{ m.name }}
                </label>
              </div>
            </div>
            <div v-else>
              <p class="text-muted">
                Todos los módulos están seleccionados
              </p>
            </div>
          </div>
        </div>

      </div>

      <!-- BOTÓN -->
      <div class="mt-4 text-end">
        <button
          class="btn btn-success"
          @click="saveModules"
          :disabled="!selectedProfileId"
        >
          Guardar módulos
        </button>
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

/* =================================================
STATE
================================================= */

const profiles = ref([]);
const selectedProfileId = ref("");

const modules = ref([]);
const selectedModules = ref([]);

/* =================================================
COMPUTED
================================================= */

const selectedList = computed(() =>
  modules.value.filter(m => selectedModules.value.includes(m.id))
);

const availableList = computed(() =>
  modules.value.filter(m => !selectedModules.value.includes(m.id))
);

/* =================================================
LOAD DATA
================================================= */

const loadProfiles = async () => {
  try {
    const res = await api.get("/business-profiles/");
    /*console.log("PROFILES:", res.data) // 🔥 AGREGAR*/
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
  } catch (error) {
    console.error("Error loading profile modules:", error);
  }
};

/* =================================================
EVENTS
================================================= */

const onChangeProfile = async () => {
  await loadProfileModules();
};

/* =================================================
SAVE
================================================= */

const saveModules = async () => {
  try {
    await api.post(
      `/business-profiles/${selectedProfileId.value}/modules/`,
      selectedModules.value
    );

    showToast("Módulos guardados correctamente", "success");

  } catch (error) {
    console.error("Error saving modules:", error);
    showToast("Error al guardar módulos", "error");
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