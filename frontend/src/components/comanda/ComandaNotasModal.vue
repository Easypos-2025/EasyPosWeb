<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="notas-modal">
      <div class="notas-modal__header">
        <h4>
          <i class="bi bi-chat-text me-2"></i>
          {{ item?.dish_name }}
        </h4>
        <button class="close-btn" @click="$emit('close')">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <div class="notas-modal__body">

        <!-- Novedades (no afectan inventario) -->
        <div class="section">
          <label class="section__label">
            <i class="bi bi-pencil-fill me-1 text-secondary"></i>
            Novedades <small class="text-muted">(solo comentarios)</small>
          </label>

          <!-- Chips precargados -->
          <div class="chips">
            <button
              v-for="n in preloadedNotes"
              :key="n.id"
              class="chip"
              :class="{ 'chip--active': selectedNotes.includes(n.name) }"
              @click="toggleNote(n.name)"
            >
              {{ n.name }}
            </button>
          </div>

          <!-- Campo libre -->
          <input
            v-model="customNote"
            type="text"
            class="form-control mt-2"
            placeholder="Comentario adicional..."
            maxlength="200"
          />
        </div>

        <!-- Cambios (afectan inventario) -->
        <div class="section mt-3">
          <label class="section__label">
            <i class="bi bi-arrow-left-right me-1 text-warning"></i>
            Cambios <small class="text-muted">(afectan inventario)</small>
          </label>
          <input
            v-model="changesText"
            type="text"
            class="form-control"
            placeholder="Ej: PAPA → YUCA, SIN CEBOLLA → EXTRA LIMÓN"
            maxlength="250"
          />
          <small class="text-muted">Use INGREDIENTE ORIGINAL → SUSTITUTO</small>
        </div>

      </div>

      <div class="notas-modal__footer">
        <button class="btn btn-outline-secondary" @click="$emit('close')">Cancelar</button>
        <button class="btn btn-primary" @click="save">
          <i class="bi bi-check-lg me-1"></i>Guardar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import apiComanda from '@/services/apiComanda'

const props = defineProps({
  item: Object,
  preloadedNotes: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'save'])

const selectedNotes = ref([])
const customNote    = ref('')
const changesText   = ref('')

watch(() => props.item, (newItem) => {
  if (!newItem) return
  // Parse existing notes
  const existingNotes = (newItem.notes || '').split('|').map(n => n.trim()).filter(Boolean)
  const knownNames    = props.preloadedNotes.map(n => n.name)
  selectedNotes.value = existingNotes.filter(n => knownNames.includes(n))
  customNote.value    = existingNotes.filter(n => !knownNames.includes(n)).join(', ')
  changesText.value   = newItem.changes || ''
}, { immediate: true })

function toggleNote(name) {
  const idx = selectedNotes.value.indexOf(name)
  if (idx >= 0) selectedNotes.value.splice(idx, 1)
  else selectedNotes.value.push(name)
}

function save() {
  const parts = [...selectedNotes.value]
  if (customNote.value.trim()) parts.push(customNote.value.trim())
  emit('save', {
    notes:   parts.join(' | '),
    changes: changesText.value.trim(),
  })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1100;
}

.notas-modal {
  background: #fff;
  border-radius: 20px 20px 0 0;
  width: 100%;
  max-width: 600px;
  max-height: 85dvh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 -8px 40px rgba(0,0,0,.2);
}

.notas-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.notas-modal__header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.1rem;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
}

.notas-modal__body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.section__label {
  display: block;
  font-weight: 600;
  font-size: .875rem;
  color: #475569;
  margin-bottom: 10px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 6px 14px;
  border: 1.5px solid #e2e8f0;
  border-radius: 20px;
  background: #f8fafc;
  font-size: .8rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all .15s;
}
.chip:hover { border-color: #2563eb; color: #2563eb; }
.chip--active {
  border-color: #2563eb;
  background: #dbeafe;
  color: #1d4ed8;
}

.notas-modal__footer {
  display: flex;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #f1f5f9;
  justify-content: flex-end;
  flex-shrink: 0;
}

@media (min-width: 600px) {
  .modal-overlay { align-items: center; }
  .notas-modal { border-radius: 20px; max-height: 80dvh; }
}

@media (max-width: 576px) {
  .notas-modal__body { padding: 12px 14px; }
  .notas-modal__footer { padding: 12px 14px; }
}
</style>
