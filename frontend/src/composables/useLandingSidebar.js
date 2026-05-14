import { ref } from "vue"

const SEEN_KEY    = "landing_ads_seen"
const DISMISS_KEY = "landing_ads_dismissed"

// Singleton reactivo — compartido entre LandingView y LandingAdSidebar
const dismissed = ref(true)

export function initLandingSidebar() {
  // Siempre visible al cargar/recargar la página — sin importar sesión anterior
  dismissed.value = false
  localStorage.setItem(SEEN_KEY, "true")
}

export function dismissSidebar() {
  dismissed.value = true
  localStorage.setItem(DISMISS_KEY, "true")
}

export function expandSidebar() {
  dismissed.value = false
}

export function toggleSidebar() {
  if (dismissed.value) expandSidebar()
  else dismissSidebar()
}

export { dismissed as sidebarDismissed }
