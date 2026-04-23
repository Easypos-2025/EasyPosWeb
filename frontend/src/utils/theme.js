import { reactive } from "vue"

// 🔥 estado global del theme
const themeState = reactive({
  logo: ""
})

export function applyTheme(perfil) {

  if (!perfil) return;

  const root = document.documentElement;

  // TOPBAR
  if (perfil.topbar_color) {
    root.style.setProperty('--topbar-bg', perfil.topbar_color);
  }

  // SIDEBAR
  if (perfil.sidebar_color) {
    root.style.setProperty('--sidebar-bg', perfil.sidebar_color);
  }

  // CONTENT
  if (perfil.bg_color) {
    root.style.setProperty('--color-bg', perfil.bg_color);
  }

  // FUENTE — aplica al html para que rem propague a todas las vistas y sidebar
  if (perfil.font_size) {
    const px = perfil.font_size + "px"
    root.style.setProperty("--font-size", px)
    root.style.fontSize = px          // fuerza la base rem en html
  }
  if (perfil.font_color) {
    root.style.setProperty("--font-color", perfil.font_color)
    root.style.setProperty("--color-text", perfil.font_color)
  }

  // 🔥 LOGO REACTIVO
  if (perfil.logo) {
    themeState.logo = perfil.logo
  }

  localStorage.setItem("app_theme", JSON.stringify(perfil))
  
}


// 🔥 getter global
export function getThemeState() {
  return themeState
}