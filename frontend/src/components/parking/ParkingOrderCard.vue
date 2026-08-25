<template>
  <div :class="['pkcard', `pkcard--${orden.estado}`]" @click="handleClick">

    <!-- Foto -->
    <div v-if="orden.foto_url" class="pkcard-foto">
      <img :src="orden.foto_url" alt="Foto vehículo" class="pkcard-foto-img" />
    </div>

    <!-- Badge + hora -->
    <div class="pkcard-top">
      <span :class="['pkcard-badge', `pkcard-badge--${orden.estado}`]">
        {{ LABELS[orden.estado] || orden.estado }}
      </span>
      <span class="pkcard-hora">{{ fmtHora(orden.hora_ingreso) }}</span>
    </div>

    <!-- ID -->
    <div class="pkcard-id">#{{ orden.id }}</div>

    <!-- Placa -->
    <div class="pkcard-placa">{{ orden.placa }}</div>

    <!-- Fecha ingreso -->
    <div class="pkcard-fecha">{{ fmtFecha(orden.hora_ingreso) }}</div>

    <!-- Tipo vehículo + datos técnicos -->
    <div v-if="orden.tipo_vehiculo || orden.marca" class="pkcard-tipo-wrap">
      <span v-if="orden.tipo_vehiculo" class="pkcard-tipo">{{ orden.tipo_vehiculo }}</span>
      <span v-if="orden.marca || orden.modelo" class="pkcard-vehiculo-det">
        {{ [orden.marca, orden.modelo, orden.color, orden.anio].filter(Boolean).join(' · ') }}
      </span>
    </div>

    <!-- Cliente / propietario -->
    <div v-if="orden.cliente_nombre" class="pkcard-cliente">
      <i class="bi bi-person-fill"></i> {{ orden.cliente_nombre }}
      <span v-if="orden.cliente_telefono" class="pkcard-cliente-tel">
        · <i class="bi bi-telephone"></i> {{ orden.cliente_telefono }}
      </span>
    </div>

    <!-- Items / personas -->
    <div class="pkcard-items">
      <template v-if="orden.items && orden.items.length">
        <span v-for="it in orden.items" :key="it.nombre" class="pkcard-pill">
          {{ it.nombre }} <strong>×{{ it.cantidad }}</strong>
        </span>
      </template>
      <template v-else>
        <span v-if="orden.adultos > 0" class="pkcard-pill">
          <i class="bi bi-person-fill"></i> {{ orden.adultos }}
        </span>
        <span v-if="orden.ninos > 0" class="pkcard-pill pkcard-pill--nino">
          <i class="bi bi-person-hearts"></i> {{ orden.ninos }}
        </span>
        <span v-if="orden.mascotas > 0" class="pkcard-pill pkcard-pill--mascota">
          <i class="bi bi-circle-fill" style="font-size:.5rem"></i> {{ orden.mascotas }}
        </span>
      </template>
    </div>

    <!-- Observaciones -->
    <div v-if="orden.obs_portero || orden.obs_mesero" class="pkcard-obs-wrap">
      <div v-if="orden.obs_portero" class="pkcard-obs">
        <i class="bi bi-chat-left-text"></i> {{ orden.obs_portero }}
      </div>
      <div v-if="orden.obs_mesero" class="pkcard-obs pkcard-obs--mesero">
        <i class="bi bi-person-badge"></i> {{ orden.obs_mesero }}
      </div>
    </div>

    <!-- Registrado por -->
    <div v-if="orden.portero_nombre" class="pkcard-quien">
      <i class="bi bi-person-check"></i> {{ orden.portero_nombre }}
    </div>

    <!-- Confirmado por -->
    <div v-if="orden.mesero_nombre" class="pkcard-quien pkcard-quien--mesero">
      <i class="bi bi-check2"></i> {{ orden.mesero_nombre }}
    </div>

    <!-- Footer: número orden + acciones -->
    <div class="pkcard-footer">
      <span class="pkcard-orden">{{ orden.numero_orden }}</span>
      <div class="pkcard-acciones">

        <!-- PORTERO: botón reimprimir en todos los estados excepto cancelado/anulado -->
        <button
          v-if="mode === 'portero' && !['cancelado','anulado'].includes(orden.estado)"
          class="pkcard-btn pkcard-btn--print"
          title="Reimprimir ticket"
          @click.stop="emit('reprint', orden)"
        >
          <i class="bi bi-printer"></i>
        </button>

        <!-- CAJERO: acciones según estado -->
        <template v-if="mode === 'cajero'">
          <button
            v-if="orden.estado === 'ingresado'"
            class="pkcard-btn pkcard-btn--anular"
            title="Anular ingreso"
            @click.stop="emit('anular', orden)"
          >
            <i class="bi bi-x-octagon"></i> Anular
          </button>
          <button
            v-else-if="orden.estado === 'registrado'"
            class="pkcard-btn pkcard-btn--cobrar"
            @click.stop="emit('cobrar', orden)"
          >
            <i class="bi bi-cash-coin"></i> Cobrar
          </button>
          <button
            v-else-if="orden.estado === 'pagado'"
            class="pkcard-btn pkcard-btn--print"
            @click.stop="emit('reprint', orden)"
          >
            <i class="bi bi-printer-fill"></i> Reimprimir
          </button>
        </template>

      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  orden: { type: Object, required: true },
  // 'portero' → muestra botón reimprimir; clic abre confirm si ingresado
  // 'cajero'  → muestra Cobrar / Anular / Reimprimir según estado
  mode: { type: String, default: 'portero' },
})

const emit = defineEmits(['card-click', 'reprint', 'cobrar', 'anular'])

const LABELS = {
  ingresado:  'Ingresado',
  registrado: 'Confirmado',
  pagado:     'Pagado',
  cancelado:  'Cancelado',
  anulado:    'Anulado',
}

function fmtHora(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
}

function fmtFecha(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

function handleClick() {
  emit('card-click', props.orden)
}
</script>

<style scoped>
.pkcard {
  background: #fff; border-radius: 12px; padding: 14px;
  border: 2px solid #e9ecef; cursor: pointer; transition: all .2s;
  display: flex; flex-direction: column; gap: 6px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.pkcard:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(0,0,0,.1); }
.pkcard--pagado   { opacity: .7; }
.pkcard--cancelado, .pkcard--anulado { opacity: .5; cursor: default; }
.pkcard--ingresado  { border-color: #ffc107; }
.pkcard--ingresado:hover { border-color: #fd7e14; }
.pkcard--registrado { border-color: #0d6efd; }
.pkcard--pagado     { border-color: #d1e7dd; }
.pkcard--cancelado, .pkcard--anulado { border-color: #f8d7da; }

/* Foto */
.pkcard-foto { width: 100%; height: 80px; overflow: hidden; border-radius: 8px; margin-bottom: 2px; }
.pkcard-foto-img { width: 100%; height: 100%; object-fit: cover; }

/* Top */
.pkcard-top { display: flex; align-items: center; justify-content: space-between; }
.pkcard-badge {
  font-size: .7rem; font-weight: 700; padding: 3px 8px; border-radius: 20px;
  text-transform: uppercase; letter-spacing: .3px;
}
.pkcard-badge--ingresado  { background: #fff3cd; color: #856404; }
.pkcard-badge--registrado { background: #cfe2ff; color: #084298; }
.pkcard-badge--pagado     { background: #d1e7dd; color: #0a3622; }
.pkcard-badge--cancelado  { background: #f8d7da; color: #842029; }
.pkcard-badge--anulado    { background: #f8d7da; color: #842029; }
.pkcard-hora { font-size: .75rem; color: #6c757d; }

/* ID */
.pkcard-id {
  font-size: .78rem; font-weight: 800; color: #0d6efd;
  text-align: center; letter-spacing: 1px;
}

/* Placa */
.pkcard-placa {
  font-size: 1.8rem; font-weight: 900; letter-spacing: 3px;
  text-align: center; color: #212529; line-height: 1;
  border: 2px solid #212529; border-radius: 6px; padding: 4px 0;
}

/* Fecha ingreso */
.pkcard-fecha { text-align: center; font-size: .72rem; color: #6c757d; letter-spacing: .2px; }

/* Tipo + datos vehículo */
.pkcard-tipo-wrap { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.pkcard-tipo { text-align: center; font-size: .78rem; color: #6c757d; }
.pkcard-vehiculo-det {
  text-align: center; font-size: .72rem; color: #adb5bd; font-style: italic;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%;
}

/* Cliente */
.pkcard-cliente {
  display: flex; align-items: center; gap: 4px; flex-wrap: wrap;
  font-size: .78rem; color: #0d6efd; font-weight: 600; justify-content: center;
}
.pkcard-cliente-tel { font-weight: 400; color: #6c757d; font-size: .72rem; }

/* Items */
.pkcard-items { display: flex; gap: 5px; justify-content: center; flex-wrap: wrap; }
.pkcard-pill {
  display: inline-flex; align-items: center; gap: 4px;
  background: #f8f9fa; border: 1px solid #dee2e6;
  padding: 3px 10px; border-radius: 20px; font-size: .82rem; font-weight: 600;
}
.pkcard-pill--nino    { background: #fff3cd; border-color: #ffc107; }
.pkcard-pill--mascota { background: #e2d9f3; border-color: #6f42c1; }

/* Observaciones */
.pkcard-obs-wrap { display: flex; flex-direction: column; gap: 3px; }
.pkcard-obs {
  font-size: .78rem; color: #6c757d; font-style: italic;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  display: flex; align-items: center; gap: 4px;
}
.pkcard-obs--mesero { color: #0d6efd; }

/* Quién */
.pkcard-quien { font-size: .73rem; color: #6c757d; display: flex; align-items: center; gap: 4px; }
.pkcard-quien--mesero { color: #0d6efd; }

/* Footer */
.pkcard-footer {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 4px; border-top: 1px solid #f1f3f5; padding-top: 6px;
}
.pkcard-orden { font-size: .72rem; color: #adb5bd; font-family: monospace; }
.pkcard-acciones { display: flex; gap: 6px; }

/* Botones de acción */
.pkcard-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 10px; border-radius: 8px; border: none;
  font-size: .8rem; font-weight: 600; cursor: pointer; transition: all .15s;
}
.pkcard-btn--print {
  background: #f8f9fa; color: #495057; border: 1px solid #dee2e6;
}
.pkcard-btn--print:hover { background: #e9ecef; }
.pkcard-btn--cobrar {
  background: #198754; color: #fff;
}
.pkcard-btn--cobrar:hover { background: #157347; }
.pkcard-btn--anular {
  background: #fff3cd; color: #856404; border: 1px solid #ffc107;
}
.pkcard-btn--anular:hover { background: #ffc107; color: #fff; }

@media (max-width: 768px) {
  .pkcard-placa { font-size: 1.4rem; letter-spacing: 2px; }
  .pkcard-btn { padding: 4px 8px; font-size: .75rem; }
}

@media (max-width: 576px) {
  .pkcard-foto { height: 65px; }
  .pkcard-placa { font-size: 1.2rem; }
}
</style>
