<template>
  <div class="efc-page">

    <!-- ENCABEZADO -->
    <div class="efc-header">
      <div>
        <h1 class="efc-title"><i class="bi bi-envelope-paper me-2"></i>Firma de Pie de Página (Email)</h1>
        <p class="efc-sub">
          Configura la identificación visual que aparece en todos los correos enviados desde la plataforma.
        </p>
      </div>
      <button class="btn-save" @click="saveAll" :disabled="saving">
        <i v-if="saving" class="bi bi-arrow-repeat spin me-1"></i>
        <i v-else class="bi bi-floppy me-1"></i>
        {{ saving ? 'Guardando...' : 'Guardar cambios' }}
      </button>
    </div>

    <div class="efc-layout">

      <!-- ── FORMULARIO ── -->
      <div class="efc-form-card">
        <h2 class="efc-section-title"><i class="bi bi-sliders me-2"></i>Campos configurables</h2>

        <div class="efc-field-group">
          <div class="efc-field">
            <label>Razón social *</label>
            <input v-model="fields.email_footer_legal_name" class="form-control"
              placeholder="Ej: EasyPosWeb SAS" @input="updatePreview" />
            <span class="efc-hint">Nombre legal que aparece en el copyright.</span>
          </div>

          <div class="efc-field">
            <label>NIT</label>
            <input v-model="fields.email_footer_nit" class="form-control"
              placeholder="Ej: 900.123.456-7" @input="updatePreview" />
          </div>

          <div class="efc-field efc-field--full">
            <label>Eslogan / Tagline</label>
            <input v-model="fields.email_footer_tagline" class="form-control"
              placeholder="Ej: Tu negocio, en línea. Sin complicaciones." @input="updatePreview" />
            <span class="efc-hint">Frase corta que refuerza la identidad de marca.</span>
          </div>

          <div class="efc-field">
            <label>Sitio web</label>
            <input v-model="fields.email_footer_website" class="form-control"
              placeholder="https://easyposweb.com" @input="updatePreview" />
          </div>

          <div class="efc-field">
            <label>Email de soporte</label>
            <input v-model="fields.email_footer_support_email" class="form-control"
              placeholder="soporte@easyposweb.com" @input="updatePreview" />
            <span class="efc-hint">Aparece como enlace en el aviso de no-reply.</span>
          </div>

          <div class="efc-field">
            <label>Teléfono <span class="efc-opt">(opcional)</span></label>
            <input v-model="fields.email_footer_phone" class="form-control"
              placeholder="+57 300 000 0000" @input="updatePreview" />
          </div>

          <div class="efc-field">
            <label>Dirección / País</label>
            <input v-model="fields.email_footer_address" class="form-control"
              placeholder="Bogotá, Colombia" @input="updatePreview" />
          </div>
        </div>
      </div>

      <!-- ── PREVIEW ── -->
      <div class="efc-preview-card">
        <h2 class="efc-section-title"><i class="bi bi-eye me-2"></i>Vista previa del pie</h2>
        <p class="efc-preview-note">
          Así se verá la firma en los emails enviados a asociados y usuarios.
        </p>

        <!-- Simulación de un email -->
        <div class="efc-email-mock">
          <div class="efc-email-header">
            <span class="efc-email-tag">De: EasyPosWeb &lt;noreply@easyposweb.com&gt;</span>
          </div>
          <div class="efc-email-body">
            <!-- Contenido de ejemplo del email -->
            <p style="color:#1e293b;font-size:14px;margin:0 0 8px;">
              <strong style="color:#10b981;">✓ ¡Pago aprobado!</strong> Tu plan está activo.
            </p>
            <p style="color:#64748b;font-size:13px;margin:0 0 16px;">
              Hola, el pago de activación de <strong>Tu Empresa SAS</strong> fue aprobado exitosamente...
            </p>

            <!-- Separador igual al del email real -->
            <div style="border-top:1px solid #e2e8f0;margin-top:20px;padding-top:16px;">

              <!-- Logotipo tricolor -->
              <p style="margin:0 0 4px;font-size:18px;font-weight:800;line-height:1;">
                <span style="color:#2563eb;">Easy</span><span style="color:#f59e0b;">Pos</span><span style="color:#10b981;">Web</span>
              </p>
              <p style="margin:0 0 10px;font-size:12px;color:#64748b;">
                {{ fields.email_footer_tagline || '—' }}
              </p>

              <!-- Contacto -->
              <p style="margin:0 0 6px;font-size:12px;color:#64748b;">
                <span v-if="fields.email_footer_phone">
                  &#128222; {{ fields.email_footer_phone }}&nbsp;&nbsp;
                </span>
                ✉ <span style="color:#2563eb;">{{ fields.email_footer_support_email || '—' }}</span>&nbsp;&nbsp;
                🌐 <span style="color:#2563eb;">{{ fields.email_footer_website || '—' }}</span>
              </p>

              <!-- Aviso no-reply -->
              <p style="margin:8px 0 6px;font-size:11px;color:#94a3b8;">
                Este correo fue generado automáticamente. Por favor no respondas a este mensaje.
                Si necesitas ayuda, escríbenos a
                <span style="color:#2563eb;">{{ fields.email_footer_support_email || '—' }}</span>.
              </p>

              <!-- Copyright -->
              <p style="margin:0;font-size:10px;color:#cbd5e1;">
                © {{ currentYear }} {{ fields.email_footer_legal_name || '—' }}
                &nbsp;·&nbsp; NIT {{ fields.email_footer_nit || '—' }}
                &nbsp;·&nbsp; {{ fields.email_footer_address || '—' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Emails que incluyen esta firma -->
        <div class="efc-emails-list">
          <h3 class="efc-emails-title">Emails que incluyen esta firma</h3>
          <ul class="efc-emails-ul">
            <li><i class="bi bi-key me-2 text-primary"></i>Recuperación de contraseña</li>
            <li><i class="bi bi-bell me-2 text-warning"></i>Notificación pago recibido (interno)</li>
            <li><i class="bi bi-check-circle me-2 text-success"></i>Pago aprobado al asociado</li>
            <li><i class="bi bi-x-circle me-2 text-danger"></i>Pago rechazado al asociado</li>
            <li><i class="bi bi-chat-dots me-2" style="color:#2563eb;"></i>Formulario de contacto (landing)</li>
          </ul>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const saving = ref(false)
const currentYear = computed(() => new Date().getFullYear())

const KEYS = [
  "email_footer_legal_name",
  "email_footer_nit",
  "email_footer_tagline",
  "email_footer_website",
  "email_footer_support_email",
  "email_footer_phone",
  "email_footer_address",
]

const fields = ref({
  email_footer_legal_name:    "",
  email_footer_nit:           "",
  email_footer_tagline:       "",
  email_footer_website:       "",
  email_footer_support_email: "",
  email_footer_phone:         "",
  email_footer_address:       "",
})

function updatePreview() {
  // El preview es reactivo directamente desde `fields`
}

async function load() {
  try {
    const res = await api.get("/system-config")
    for (const item of res.data) {
      if (KEYS.includes(item.config_key)) {
        fields.value[item.config_key] = item.config_value ?? ""
      }
    }
  } catch {
    showToast("Error cargando configuración", "error")
  }
}

async function saveAll() {
  if (!fields.value.email_footer_legal_name?.trim()) {
    showToast("La razón social es obligatoria", "warning")
    return
  }
  saving.value = true
  try {
    await Promise.all(
      KEYS.map(key =>
        api.put(`/system-config/${key}`, { config_value: fields.value[key] ?? "" })
      )
    )
    showToast("Firma de email guardada correctamente", "success")
  } catch {
    showToast("Error guardando la configuración", "error")
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.efc-page    { padding: 24px; max-width: 1200px; }
.efc-header  {
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 16px;
  margin-bottom: 24px; flex-wrap: wrap;
}
.efc-title   { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.efc-sub     { font-size: 13px; color: #64748b; margin: 0; }

.btn-save {
  display: flex; align-items: center; gap: 6px;
  background: #2563eb; color: #fff; border: none;
  padding: 10px 22px; border-radius: 8px;
  font-size: 14px; font-weight: 700; cursor: pointer;
  transition: background .2s; white-space: nowrap; flex-shrink: 0;
}
.btn-save:hover:not(:disabled) { background: #1d4ed8; }
.btn-save:disabled { opacity: .6; cursor: not-allowed; }

/* Layout 2 columnas */
.efc-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

/* Tarjetas */
.efc-form-card,
.efc-preview-card {
  background: #fff; border-radius: 14px;
  box-shadow: 0 1px 6px rgba(0,0,0,.08);
  padding: 24px;
}
.efc-section-title {
  font-size: 15px; font-weight: 700; color: #1e293b;
  margin: 0 0 18px; display: flex; align-items: center;
}

/* Campos del formulario */
.efc-field-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.efc-field { display: flex; flex-direction: column; gap: 4px; }
.efc-field--full { grid-column: span 2; }
.efc-field label {
  font-size: 13px; font-weight: 600; color: #374151;
}
.efc-hint { font-size: 11px; color: #94a3b8; line-height: 1.3; }
.efc-opt  { font-weight: 400; color: #94a3b8; font-size: 11px; }

/* Preview */
.efc-preview-note {
  font-size: 12px; color: #64748b; margin: -10px 0 14px;
}
.efc-email-mock {
  border: 1px solid #e2e8f0; border-radius: 10px;
  overflow: hidden; font-family: Arial, sans-serif;
}
.efc-email-header {
  background: #f8fafc; padding: 8px 14px;
  border-bottom: 1px solid #e2e8f0;
}
.efc-email-tag {
  font-size: 11px; color: #64748b;
}
.efc-email-body { padding: 16px 20px; }

/* Lista de emails incluidos */
.efc-emails-list {
  margin-top: 20px; padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}
.efc-emails-title {
  font-size: 13px; font-weight: 700; color: #374151; margin: 0 0 10px;
}
.efc-emails-ul {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 6px;
}
.efc-emails-ul li {
  font-size: 13px; color: #475569;
  display: flex; align-items: center;
}

.spin {
  display: inline-block;
  animation: spin .8s linear infinite;
}
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

/* Responsive */
@media (max-width: 900px) {
  .efc-layout { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .efc-field-group { grid-template-columns: 1fr; }
  .efc-field--full { grid-column: span 1; }
}
</style>
