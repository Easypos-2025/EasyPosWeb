import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import Swal from "sweetalert2"
window.Swal = Swal

// Bootstrap
import "bootstrap/dist/css/bootstrap.min.css"
import "bootstrap/dist/js/bootstrap.bundle.min.js"

// estilos globales

import "./styles/global.css"
import "./styles/layout.css"

import './styles/variables.css'
import "./styles/forms.css"
import { createPinia } from "pinia"
import "cropperjs/dist/cropper.css"
import CurrencyInput from "./components/CurrencyInput.vue"
import { installErrorReporter } from "./utils/errorReporter"
import { ordenAlfa, ordenItemDesc } from "./utils/orden"

const app = createApp(App)
installErrorReporter(app)
const pinia = createPinia()

app.use(router)
app.use(pinia)
app.component("CurrencyInput", CurrencyInput)
// NORMA: todo selector/catálogo A-Z → usar $ordenAlfa(lista, 'campo') en las plantillas
app.config.globalProperties.$ordenAlfa     = ordenAlfa
app.config.globalProperties.$ordenItemDesc = ordenItemDesc

app.mount("#app")