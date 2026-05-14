import { ref } from "vue"

const SEEN_KEY    = "landing_ads_seen"
const DISMISS_KEY = "landing_ads_dismissed"

// Singleton reactivo — compartido entre LandingView y LandingAdSidebar
const dismissed = ref(true)

export function initLandingSidebar() {
  const hasSeen      = localStorage.getItem(SEEN_KEY)      === "true"
  const hasDismissed = localStorage.getItem(DISMISS_KEY)   === "true"
  // Primera visita: siempre visible; siguientes: respetar preferencia
  dismissed.value = hasSeen && hasDismissed
  if (!hasSeen) localStorage.setItem(SEEN_KEY, "true")
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
