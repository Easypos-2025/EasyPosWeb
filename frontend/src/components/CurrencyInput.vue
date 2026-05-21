<template>
  <input
    ref="inputRef"
    type="text"
    inputmode="numeric"
    v-bind="$attrs"
    :value="displayValue"
    @focus="handleFocus"
    @blur="handleBlur"
    @input="handleInput"
    @keydown="handleKeydown"
  />
</template>

<script setup>
import { ref, computed } from "vue"

const props = defineProps({
  modelValue: { type: Number, default: 0 },
})
const emit = defineEmits(["update:modelValue"])

const inputRef  = ref(null)
const focused   = ref(false)
const rawValue  = ref("")

const displayValue = computed(() => {
  if (focused.value) return rawValue.value
  const num = Number(props.modelValue) || 0
  return new Intl.NumberFormat("es-CO").format(num)
})

function handleFocus() {
  focused.value  = true
  rawValue.value = String(Number(props.modelValue) || 0)
  requestAnimationFrame(() => inputRef.value?.select())
}

function handleBlur() {
  focused.value = false
  const num = parseFloat(rawValue.value.replace(/[^\d.]/g, "")) || 0
  emit("update:modelValue", num)
}

function handleInput(e) {
  rawValue.value = e.target.value
}

function handleKeydown(e) {
  const permitted = ["Backspace","Delete","Tab","Enter","ArrowLeft","ArrowRight","Home","End"]
  if (!permitted.includes(e.key) && !/^\d$/.test(e.key)) {
    e.preventDefault()
  }
}
</script>
