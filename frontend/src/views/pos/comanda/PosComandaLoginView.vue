<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-card__logo">
        <i class="bi bi-cup-hot-fill"></i>
      </div>
      <h1 class="login-card__title">Comandera</h1>
      <p class="login-card__subtitle">Seleccione su nombre e ingrese el PIN</p>

      <!-- Selección de mesero -->
      <div class="waiter-grid" v-if="waiters.length">
        <button
          v-for="w in waiters"
          :key="w.id"
          class="waiter-btn"
          :class="{ 'waiter-btn--active': selectedWaiter?.id === w.id }"
          @click="selectWaiter(w)"
        >
          <i class="bi bi-person-circle waiter-btn__icon"></i>
          <span class="waiter-btn__name">{{ w.name }}</span>
        </button>
      </div>

      <div v-else-if="loadingWaiters" class="text-center text-muted py-3">
        <div class="spinner-border spinner-border-sm me-2"></div>Cargando...
      </div>

      <div v-else-if="!companyId" class="company-input">
        <label class="form-label fw-semibold">ID de empresa</label>
        <div class="input-group">
          <input
            v-model="cidInput"
            type="number"
            class="form-control form-control-lg"
            placeholder="Ej: 1"
            @keyup.enter="loadWaiters"
          />
          <button class="btn btn-primary" @click="loadWaiters">
            <i class="bi bi-arrow-right"></i>
          </button>
        </div>
      </div>

      <!-- PIN display -->
      <div class="pin-display" v-if="selectedWaiter">
        <div
          v-for="i in 4"
          :key="i"
          class="pin-dot"
          :class="{ 'pin-dot--filled': pin.length >= i }"
        ></div>
      </div>

      <!-- Teclado PIN -->
      <div class="pin-pad" v-if="selectedWaiter">
        <button
          v-for="n in [1,2,3,4,5,6,7,8,9,'',0,'⌫']"
          :key="n"
          class="pin-key"
          :class="{
            'pin-key--empty': n === '',
            'pin-key--del': n === '⌫',
            'pin-key--enter': pin.length === 4 && n === '⌫'
          }"
          :disabled="n === ''"
          @click="pressKey(n)"
        >
          {{ n }}
        </button>
      </div>

      <p v-if="error" class="login-error mt-3">
        <i class="bi bi-exclamation-circle me-1"></i>{{ error }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route  = useRoute()
const router = useRouter()

const companyId     = ref(null)
const cidInput      = ref('')
const waiters       = ref([])
const loadingWaiters = ref(false)
const selectedWaiter = ref(null)
const pin           = ref('')
const error         = ref('')

onMounted(() => {
  // 1. Query param ?cid=X
  if (route.query.cid) {
    companyId.value = parseInt(route.query.cid)
    localStorage.setItem('waiter_company_id', companyId.value)
    loadWaiters()
    return
  }
  // 2. Persisted from previous session
  const saved = localStorage.getItem('waiter_company_id')
  if (saved) {
    companyId.value = parseInt(saved)
    loadWaiters()
  }
})

async function loadWaiters() {
  const cid = companyId.value || parseInt(cidInput.value)
  if (!cid) return
  companyId.value = cid
  localStorage.setItem('waiter_company_id', cid)
  loadingWaiters.value = true
  try {
    const base = import.meta.env.VITE_API_URL
    const res  = await axios.get(`${base}/api/pos/comanda/auth/waiters?company_id=${cid}`)
    waiters.value = res.data
  } catch {
    error.value = 'No se pudo cargar la lista de meseros.'
  } finally {
    loadingWaiters.value = false
  }
}

function selectWaiter(w) {
  selectedWaiter.value = w
  pin.value = ''
  error.value = ''
}

async function pressKey(key) {
  if (key === '⌫') {
    pin.value = pin.value.slice(0, -1)
    return
  }
  if (typeof key === 'number' && pin.value.length < 4) {
    pin.value += String(key)
    if (pin.value.length === 4) await submitLogin()
  }
}

async function submitLogin() {
  error.value = ''
  try {
    const base = import.meta.env.VITE_API_URL
    const res  = await axios.post(`${base}/api/pos/comanda/auth/mesero`, {
      company_id: companyId.value,
      waiter_id:  selectedWaiter.value.id,
      pin:        pin.value,
    })
    localStorage.setItem('waiter_token', res.data.token)
    localStorage.setItem('waiter_data', JSON.stringify(res.data.waiter))
    router.push('/pos/comanda/mesas')
  } catch (e) {
    error.value = e.response?.data?.detail || 'PIN incorrecto'
    pin.value = ''
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  padding: 16px;
}

.login-card {
  background: #fff;
  border-radius: 20px;
  padding: 32px 24px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0,0,0,.4);
  text-align: center;
}

.login-card__logo {
  font-size: 3rem;
  color: #2563eb;
  margin-bottom: 8px;
}

.login-card__title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
}

.login-card__subtitle {
  color: #64748b;
  font-size: .875rem;
  margin-bottom: 24px;
}

/* Waiter grid */
.waiter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 10px;
  margin-bottom: 24px;
}

.waiter-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 8px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  background: #f8fafc;
  cursor: pointer;
  transition: all .2s;
  font-size: .85rem;
  font-weight: 600;
  color: #334155;
}

.waiter-btn:hover {
  border-color: #2563eb;
  background: #eff6ff;
}

.waiter-btn--active {
  border-color: #2563eb;
  background: #dbeafe;
  color: #1d4ed8;
}

.waiter-btn__icon {
  font-size: 1.8rem;
}

.waiter-btn__name {
  text-align: center;
  line-height: 1.2;
  word-break: break-word;
}

/* Company input */
.company-input {
  text-align: left;
  margin-bottom: 20px;
}

/* PIN display */
.pin-display {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 20px;
}

.pin-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #94a3b8;
  background: transparent;
  transition: all .15s;
}

.pin-dot--filled {
  background: #2563eb;
  border-color: #2563eb;
  transform: scale(1.15);
}

/* PIN pad */
.pin-pad {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  max-width: 260px;
  margin: 0 auto;
}

.pin-key {
  height: 64px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  background: #f8fafc;
  font-size: 1.4rem;
  font-weight: 700;
  color: #1e293b;
  cursor: pointer;
  transition: all .15s;
  touch-action: manipulation;
}

.pin-key:active {
  transform: scale(.93);
  background: #e2e8f0;
}

.pin-key--empty {
  border: none;
  background: transparent;
  cursor: default;
}

.pin-key--del {
  color: #ef4444;
  border-color: #fecaca;
  background: #fff5f5;
}

.login-error {
  color: #ef4444;
  font-size: .875rem;
  font-weight: 500;
}

/* Responsive */
@media (max-width: 768px) {
  .login-card {
    padding: 24px 16px;
  }
  .pin-key {
    height: 58px;
  }
}

@media (max-width: 576px) {
  .login-page {
    align-items: flex-start;
    padding-top: 32px;
  }
  .waiter-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
