<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="notas-modal">

      <!-- Header -->
      <div class="notas-modal__header">
        <div class="notas-modal__title">
          <i class="bi bi-chat-text me-2 text-primary"></i>
          <span>{{ item?.dish_name }}</span>
        </div>
        <button class="close-btn" @click="$emit('close')" title="Cerrar">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <!-- Body: two-column layout -->
      <div class="notas-modal__body">

        <!-- Left: available notes -->
        <div class="col-disponibles">
          <div class="col-label">
            <i class="bi bi-grid me-1"></i>Novedades disponibles
            <span class="col-label__sub" v-if="categoryNotes.length === 0">
              (sin novedades para esta categoría)
            </span>
          </div>

          <div class="notes-grid" v-if="categoryNotes.length">
            <button
              v-for="n in categoryNotes"
              :key="n.id"
              class="note-chip"
              :class="{ 'note-chip--active': isSelected(n.name) }"
              @click="toggleNote(n.name)"
            >
              <i class="bi me-1" :class="isSelected(n.name) ? 'bi-check-circle-fill' : 'bi-circle'"></i>
              {{ n.name }}
            </button>
          </div>
          <div v-else class="notes-empty">
            <i class="bi bi-info-circle text-muted"></i>
            <span class="text-muted small ms-1">No hay novedades para esta categoría</span>
          </div>

          <!-- Campo comentario personalizado -->
          <div class="custom-note-wrap">
            <label class="col-label mt-3">
              <i class="bi bi-pencil me-1"></i>Comentario libre
            </label>
            <input
              v-model="customNote"
              type="text"
              class="custom-input"
              placeholder="Escribe una novedad o comentario…"
              maxlength="200"
              @keyup.enter="addCustom"
            />
            <button v-if="customNote.trim()" class="add-custom-btn" @click="addCustom">
              <i class="bi bi-plus-lg me-1"></i>Agregar
            </button>
          </div>

          <!-- Cambios de inventario -->
          <div class="custom-note-wrap">
            <label class="col-label mt-2">
              <i class="bi bi-arrow-left-right me-1 text-warning"></i>
              Cambios <small class="text-muted">(afectan inventario)</small>
            </label>
            <input
              v-model="changesText"
              type="text"
              class="custom-input"
              placeholder="Ej: PAPA → YUCA, SIN CEBOLLA"
              maxlength="250"
            />
          </div>
        </div>

        <!-- Right: selected notes -->
        <div class="col-seleccionadas">
          <div class="col-label">
            <i class="bi bi-check2-all me-1 text-success"></i>
            Seleccionadas
            <span class="selected-count" v-if="allSelected.length">{{ allSelected.length }}</span>
          </div>

          <div v-if="allSelected.length" class="selected-list">
            <button
              v-for="(note, idx) in allSelected"
              :key="idx"
              class="selected-chip"
              @click="removeSelected(note)"
              title="Toca para quitar"
            >
              <span>{{ note }}</span>
              <i class="bi bi-x-circle-fill ms-1"></i>
            </button>
          </div>
          <div v-else class="selected-empty">
            <i class="bi bi-bag text-muted fs-3"></i>
            <p class="text-muted small mt-1">Ninguna seleccionada</p>
          </div>
        </div>

      </div>

      <!-- Footer -->
      <div class="notas-modal__footer">
        <button class="btn btn-outline-secondary" @click="$emit('close')">
          <i class="bi bi-x me-1"></i>Cancelar
        </button>
        <button class="btn btn-primary" @click="save">
          <i class="bi bi-check-lg me-1"></i>Guardar
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  item: Object,
  preloadedNotes: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'save'])

const selectedNotes = ref([])
const customNote    = ref('')
const changesText   = ref('')

// Notes filtered to this dish's category
const categoryNotes = computed(() => {
  const catId = props.item?.category_id
  if (!catId) return props.preloadedNotes
  const filtered = props.preloadedNotes.filter(n => n.cod_categoria === catId)
  return filtered.length ? filtered : props.preloadedNotes
})

// All selected: preset chips + custom entries
const allSelected = computed(() => [...selectedNotes.value])

watch(() => props.item, (newItem) => {
  if (!newItem) return
  const existingNotes = (newItem.notes || '').split('|').map(n => n.trim()).filter(Boolean)
  const knownNames    = props.preloadedNotes.map(n => n.name)
  selectedNotes.value = existingNotes.filter(n => knownNames.includes(n))
  customNote.value    = existingNotes.filter(n => !knownNames.includes(n)).join(', ')
  changesText.value   = newItem.changes || ''
}, { immediate: true })

function isSelected(name) {
  return selectedNotes.value.includes(name)
}

function toggleNote(name) {
  const idx = selectedNotes.value.indexOf(name)
  if (idx >= 0) selectedNotes.value.splice(idx, 1)
  else selectedNotes.value.push(name)
}

function removeSelected(note) {
  const idx = selectedNotes.value.indexOf(note)
  if (idx >= 0) selectedNotes.value.splice(idx, 1)
}

function addCustom() {
  const text = customNote.value.trim()
  if (!text) return
  if (!selectedNotes.value.includes(text)) selectedNotes.value.push(text)
  customNote.value = ''
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
  max-width: 760px;
  max-height: 90dvh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 -8px 40px rgba(0,0,0,.2);
}

/* Header */
.notas-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 14px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.notas-modal__title {
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  min-width: 0;
}
.notas-modal__title span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.close-btn {
  flex-shrink: 0;
  background: #f1f5f9;
  border: none;
  border-radius: 50%;
  width: 34px;
  height: 34px;
  font-size: 1rem;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .15s;
  margin-left: 10px;
}
.close-btn:hover { background: #fee2e2; color: #ef4444; }

/* Body */
.notas-modal__body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  gap: 0;
  min-height: 0;
}

/* Columns */
.col-disponibles {
  flex: 1;
  padding: 16px;
  border-right: 1px solid #f1f5f9;
  overflow-y: auto;
}

.col-seleccionadas {
  width: 220px;
  flex-shrink: 0;
  padding: 16px;
  background: #f8fafc;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* Column labels */
.col-label {
  display: flex;
  align-items: center;
  font-size: .8rem;
  font-weight: 700;
  color: #475569;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: .04em;
}

.col-label__sub {
  font-weight: 400;
  font-size: .72rem;
  text-transform: none;
  color: #94a3b8;
  margin-left: 4px;
}

.selected-count {
  background: #2563eb;
  color: #fff;
  font-size: .7rem;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 10px;
  margin-left: 6px;
}

/* Notes grid: 2 cols */
.notes-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.note-chip {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  font-size: .8rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all .15s;
  text-align: left;
}
.note-chip:hover { border-color: #2563eb; color: #2563eb; background: #eff6ff; }
.note-chip--active {
  border-color: #2563eb;
  background: #dbeafe;
  color: #1d4ed8;
}

.notes-empty {
  padding: 16px 0;
  display: flex;
  align-items: center;
}

/* Custom input */
.custom-note-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.custom-input {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: .875rem;
  color: #1e293b;
  outline: none;
  transition: border-color .15s;
}
.custom-input:focus { border-color: #2563eb; }

.add-custom-btn {
  align-self: flex-end;
  padding: 6px 14px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: .8rem;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
}
.add-custom-btn:hover { background: #1d4ed8; }

/* Selected chips */
.selected-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.selected-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: #fff;
  border: 1.5px solid #bfdbfe;
  border-radius: 8px;
  font-size: .8rem;
  font-weight: 600;
  color: #1d4ed8;
  cursor: pointer;
  text-align: left;
  transition: all .15s;
}
.selected-chip:hover { background: #fee2e2; border-color: #fca5a5; color: #ef4444; }
.selected-chip i { flex-shrink: 0; font-size: .9rem; }

.selected-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  opacity: .5;
}

/* Footer */
.notas-modal__footer {
  display: flex;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #f1f5f9;
  justify-content: flex-end;
  flex-shrink: 0;
}

/* Tablet+ → centered modal */
@media (min-width: 600px) {
  .modal-overlay { align-items: center; }
  .notas-modal { border-radius: 20px; max-height: 82dvh; }
}

/* Mobile: stack columns vertically, 1-col notes grid */
@media (max-width: 599px) {
  .notas-modal__body { flex-direction: column; }
  .col-disponibles { border-right: none; border-bottom: 1px solid #f1f5f9; }
  .col-seleccionadas { width: 100%; background: #fff; }
  .notes-grid { grid-template-columns: 1fr; }
}
</style>
