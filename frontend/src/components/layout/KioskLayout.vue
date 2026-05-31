<template>
  <div class="kiosk-shell">
    <header class="kiosk-header">
      <div class="kiosk-header__brand">
        <i class="bi bi-cup-hot-fill me-2"></i>
        <span class="kiosk-header__title">Comandera</span>
      </div>
      <div class="kiosk-header__waiter" v-if="waiterName">
        <i class="bi bi-person-fill me-1"></i>
        <span>{{ waiterName }}</span>
      </div>
      <button class="kiosk-header__logout" @click="logout" title="Salir">
        <i class="bi bi-box-arrow-right"></i>
      </button>
    </header>

    <main class="kiosk-body">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const waiterName = computed(() => {
  try {
    const data = JSON.parse(localStorage.getItem('waiter_data') || '{}')
    return data.name || ''
  } catch {
    return ''
  }
})

function logout() {
  localStorage.removeItem('waiter_token')
  localStorage.removeItem('waiter_data')
  const cid = localStorage.getItem('waiter_company_id') || ''
  router.push(`/pos/comanda/login?cid=${cid}`)
}
</script>

<style scoped>
.kiosk-shell {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  background: #f0f2f5;
  overflow: hidden;
}

.kiosk-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  height: 52px;
  background: #1e293b;
  color: #fff;
  flex-shrink: 0;
  z-index: 100;
}

.kiosk-header__brand {
  display: flex;
  align-items: center;
  font-weight: 700;
  font-size: 1rem;
  color: #f1f5f9;
}

.kiosk-header__title {
  letter-spacing: .5px;
}

.kiosk-header__waiter {
  margin-left: auto;
  font-size: .85rem;
  color: #94a3b8;
}

.kiosk-header__logout {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.15rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: color .2s, background .2s;
}
.kiosk-header__logout:hover {
  color: #f87171;
  background: rgba(248, 113, 113, .1);
}

.kiosk-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
