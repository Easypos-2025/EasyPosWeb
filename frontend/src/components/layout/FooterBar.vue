<template>
  <div class="footer-content">

    <!-- MARCA EASYPOSWEB — izquierda -->
    <div class="footer-brand">
      <img
        src="/src/assets/logo.png"
        class="footer-logo"
        alt="EasyPosWeb"
        @error="e => e.target.style.display='none'"
      />
      <span class="footer-brand-name">EasyPosWeb</span>
    </div>

    <div class="footer-divider"></div>

    <!-- ESTADO -->
    <span class="footer-item">V {{ version }}</span>

    <span class="footer-item" v-if="!online" style="color:#f87171">
      ● Sin internet
    </span>
    <span class="footer-item" v-else :style="{ color: apiStatus ? '#4ade80' : '#fb923c' }">
      ● {{ apiStatus ? 'API Conectada' : 'API no responde' }}
    </span>

    <span class="footer-item footer-copy">© 2020 EasyPosWeb</span>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"

const apiStatus = ref(false)
const version   = import.meta.env.VITE_APP_VERSION || "1.0.0"
const online    = ref(navigator.onLine)

window.addEventListener("online",  () => { online.value = true  })
window.addEventListener("offline", () => { online.value = false })

const checkApi = async () => {
  try {
    await api.get("/auth/health/")
    apiStatus.value = true
  } catch {
    apiStatus.value = false
  }
}

onMounted(() => {
  checkApi()
  setInterval(checkApi, 10000)
})
</script>

<style scoped>

.footer-content {
  display: flex;
  align-items: center;
  gap: 20px;
  height: 40px;
  flex-shrink: 0;
  background: #111827;
  color: rgba(255,255,255,0.65);
  font-size: 12px;
  letter-spacing: 0.2px;
  padding: 0 20px;
}

/* Marca EasyPosWeb */
.footer-brand {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
}

.footer-logo {
  height: 24px;
  width: auto;
  object-fit: contain;
  opacity: 0.85;
  filter: brightness(1.1);
}

.footer-brand-name {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: rgba(255,255,255,0.8);
  white-space: nowrap;
}

.footer-divider {
  width: 1px;
  height: 16px;
  background: rgba(255,255,255,0.15);
  flex-shrink: 0;
}

.footer-item {
  white-space: nowrap;
}

.footer-copy {
  margin-left: auto;   /* empuja el copyright a la derecha */
}

/* Responsive */
@media (max-width: 768px) {
  .footer-copy    { display: none; }
  .footer-divider { display: none; }
  .footer-content { gap: 12px; padding: 0 12px; }
}

</style>
