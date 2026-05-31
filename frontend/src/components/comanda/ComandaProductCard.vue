<template>
  <button class="product-card" @click="$emit('select', dish)">
    <div class="product-card__img" v-if="dish.photo_path">
      <img :src="photoUrl(dish.photo_path)" :alt="dish.name" loading="lazy" />
    </div>
    <div class="product-card__img product-card__img--placeholder" v-else>
      <i class="bi bi-image"></i>
    </div>
    <div class="product-card__body">
      <span class="product-card__name">{{ dish.name }}</span>
      <div class="product-card__footer">
        <span class="product-card__price">{{ formatPrice(dish.price) }}</span>
        <span class="product-card__badge" v-if="dish.has_assembly">
          <i class="bi bi-sliders2"></i>
        </span>
      </div>
    </div>
  </button>
</template>

<script setup>
const API_BASE = import.meta.env.VITE_API_URL || ''

defineProps({ dish: Object })
defineEmits(['select'])

function photoUrl(path) {
  if (!path) return null
  if (path.startsWith('blob:') || path.startsWith('http')) return path
  return API_BASE + path
}

function formatPrice(v) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
</script>

<style scoped>
.product-card {
  display: flex;
  flex-direction: column;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  cursor: pointer;
  transition: all .2s;
  text-align: left;
  padding: 0;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.product-card:hover {
  border-color: #2563eb;
  box-shadow: 0 4px 12px rgba(37,99,235,.15);
  transform: translateY(-2px);
}
.product-card:active { transform: scale(.97); }

.product-card__img {
  width: 100%;
  aspect-ratio: 4/3;
  overflow: hidden;
  background: #f1f5f9;
}
.product-card__img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.product-card__img--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #cbd5e1;
  font-size: 2rem;
}

.product-card__body {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.product-card__name {
  font-size: .85rem;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
}

.product-card__price {
  font-size: .9rem;
  font-weight: 700;
  color: #2563eb;
}

.product-card__badge {
  background: #fef3c7;
  color: #d97706;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: .75rem;
}
</style>
