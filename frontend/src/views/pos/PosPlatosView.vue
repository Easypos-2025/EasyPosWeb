<template>
  <div class="crud-view">

    <!-- HEADER -->
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">{{ moduleName }}</h5>
        <p class="crud-sub">Catálogo de platos, bebidas y servicios del menú.</p>
      </div>
      <div class="header-tools">
        <input v-model="busqueda" class="inp-buscar" placeholder="Buscar…" />
        <button class="btn-nuevo" @click="abrirEditor()">
          <i class="bi bi-plus-lg me-1"></i>Nuevo
        </button>
      </div>
    </div>

    <!-- SLIDE DE CATEGORÍAS -->
    <div class="cat-slider-wrap">
      <div class="cat-slider-inner">
        <button class="cat-arrow cat-arrow--left" :class="{ visible: canScrollLeft }" @click="scrollCats(-1)">
          <i class="bi bi-chevron-left"></i>
        </button>
        <div class="cat-track" ref="catTrackRef" @scroll="updateArrows">
          <button
            v-for="c in categorias" :key="c.id"
            :class="['cat-pill', { active: categoriaTab === c.id }]"
            @click="setCategoria(c.id)"
          >
            <span class="cat-dot"></span>
            <span>{{ c.name }}</span>
          </button>
        </div>
        <button class="cat-arrow cat-arrow--right" :class="{ visible: canScrollRight }" @click="scrollCats(1)">
          <i class="bi bi-chevron-right"></i>
        </button>
      </div>
      <button :class="['cat-pill cat-pill--todos', { active: categoriaTab === null }]" @click="setCategoria(null)">
        <i class="bi bi-grid-3x3-gap"></i><span>Todos</span>
      </button>
    </div>

    <!-- FILTROS ESTADO / FOTO -->
    <div class="filtros-wrap">
      <div class="filtros-grupo">
        <span class="filtros-label">Estado:</span>
        <button :class="['filtro-btn filtro-btn--activo', { active: filtroEstado === 1 }]" @click="setFiltroEstado(1)">Activos</button>
        <button :class="['filtro-btn filtro-btn--inactivo', { active: filtroEstado === 0 }]" @click="setFiltroEstado(0)">Inactivos</button>
        <button :class="['filtro-btn', { active: filtroEstado === null }]" @click="setFiltroEstado(null)">Todos</button>
      </div>
      <div class="filtros-grupo">
        <span class="filtros-label">Foto:</span>
        <button :class="['filtro-btn filtro-btn--confoto', { active: filtroFoto === 'con' }]" @click="setFiltroFoto('con')">Con foto</button>
        <button :class="['filtro-btn filtro-btn--sinfoto', { active: filtroFoto === 'sin' }]" @click="setFiltroFoto('sin')">Sin foto</button>
        <button :class="['filtro-btn', { active: filtroFoto === null }]" @click="setFiltroFoto(null)">Todos</button>
      </div>
    </div>

    <!-- LISTA -->
    <div v-if="loading" class="estado-carga">
      <div class="spinner-border spinner-border-sm text-primary"></div>
    </div>
    <div v-else-if="!filtrados.length" class="estado-vacio">
      <i class="bi bi-box-seam"></i>
      <p>No hay artículos. Crea el primero para comenzar.</p>
    </div>
    <div v-else class="grupos-wrap">
      <template v-for="grupo in itemsAgrupados" :key="grupo.id ?? 'none'">
        <div v-if="categoriaTab === null" class="seccion-hdr" :style="{ '--cat-color': grupo.color }">
          <span class="seccion-dot" :style="{ background: grupo.color }"></span>
          <span class="seccion-nombre">{{ grupo.name }}</span>
          <span class="seccion-count">{{ grupo.items.length }}</span>
        </div>
        <div class="items-grid seccion-grid">
          <div
            v-for="item in grupo.items" :key="item.id"
            class="item-card"
            :class="{ 'item-card--inactivo': !isActivo(item), 'item-card--dragging': dragId === item.id }"
            draggable="true"
            @dragstart="onDragStart($event, item)"
            @dragover.prevent="onDragOver($event, item)"
            @drop.prevent="onDrop"
            @dragend="onDragEnd"
          >
            <!-- Foto -->
            <div class="item-foto">
              <img v-if="item.photo_path" :src="imgSrc(item.photo_path)" class="item-foto-img" alt="" draggable="false" />
              <div v-else class="item-foto-placeholder"><i class="bi bi-image"></i></div>
              <span class="drag-handle" title="Arrastrar para reordenar"><i class="bi bi-grip-vertical"></i></span>
            </div>

            <div class="item-body">
              <div class="item-top">
                <span class="item-cat" :style="{ background: (item.category_color||'#1d4ed8')+'22', color: item.category_color||'#1d4ed8' }">
                  {{ item.category_name || 'Sin categoría' }}
                </span>
                <span :class="isActivo(item) ? 'badge-activo' : 'badge-inactivo'">
                  {{ isActivo(item) ? 'Activo' : 'Inactivo' }}
                </span>
              </div>
              <div class="item-nombre">{{ item.name }}</div>
              <div class="item-precios">
                <span v-if="item.compare_price" class="precio-tachado">{{ fmt(item.compare_price) }}</span>
                <span class="item-precio">{{ fmt(item.price) }}</span>
              </div>
              <div class="item-meta">
                <span title="Insumos fijos"><i class="bi bi-list-check"></i> {{ item.portion_count }}</span>
                <span title="Impresoras"><i class="bi bi-printer"></i> {{ item.printer_count }}</span>
                <span v-if="item.assembly_count" title="Categorías de armado" :class="{ 'badge-armar': item.offer_priority }"><i class="bi bi-sliders"></i> {{ item.assembly_count }}</span>
                <span v-if="item.presentation_count" title="Presentaciones"><i class="bi bi-box"></i> {{ item.presentation_count }}</span>
                <span v-if="item.variant_count" title="Variantes de precio" class="badge-variants"><i class="bi bi-tags"></i> {{ item.variant_count }}</span>
                <span v-if="item.tax" title="IVA"><i class="bi bi-percent"></i> {{ item.tax }}%</span>
              </div>
              <div class="item-acciones">
                <button class="btn-accion btn-accion--edit"   @click="abrirEditor(item, 'general')">
                  <i class="bi bi-pencil-fill"></i><span>Editar</span>
                </button>
                <button class="btn-accion btn-accion--build"  @click="abrirEditor(item, 'armar')">
                  <i class="bi bi-sliders"></i><span>Armado</span>
                </button>
                <button class="btn-accion btn-accion--recipe" @click="abrirEditor(item, 'fijos')">
                  <i class="bi bi-list-check"></i><span>Insumos</span>
                </button>
                <button class="btn-accion btn-accion--print"  @click="abrirEditor(item, 'aux')">
                  <i class="bi bi-image"></i><span>Foto</span>
                </button>
                <button class="btn-accion btn-accion--variants" @click="abrirEditor(item, 'variantes')">
                  <i class="bi bi-tags-fill"></i><span>Variantes</span>
                </button>
                <button class="btn-accion btn-accion--danger" @click="eliminar(item)">
                  <i class="bi bi-trash-fill"></i><span>Eliminar</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- ═══ EDITOR DEL PRODUCTO (pestañas como el escritorio) ═══ -->
    <div v-if="ed.visible" class="modal-overlay" @click.self="cerrarEditor">
      <div class="ed-card">
        <div class="modal-hdr">
          <div class="ed-hdr-info">
            <span class="ed-code" v-if="form.id">CÓDIGO {{ form.id }}</span>
            <span class="ed-title">{{ form.id ? (form.name || '—') : `Nuevo — ${moduleName}` }}</span>
          </div>
          <button class="btn-x" @click="cerrarEditor"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="panel-tabs">
          <button v-for="t in tabs" :key="t.key" :class="['ptab', { active: ed.tab === t.key }]"
                  :disabled="t.needsId && !form.id" :title="t.needsId && !form.id ? 'Guarde primero la información general' : ''"
                  @click="cambiarTab(t.key)">
            <i :class="t.icon"></i><span>{{ t.label }}</span>
          </button>
        </div>

        <div class="ed-body">
          <!-- ── TAB: INFORMACIÓN GENERAL ── -->
          <div v-show="ed.tab === 'general'" class="gen-grid">
            <div class="gen-col">
              <div class="campo">
                <label>Nombre *</label>
                <input v-model="form.name" class="inp inp-strong" maxlength="250" />
              </div>
              <div class="campo-row">
                <div class="campo">
                  <label>Categoría</label>
                  <select v-model="form.category_id" class="inp">
                    <option :value="null">— Sin categoría —</option>
                    <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
                <div class="campo">
                  <label>Código producto</label>
                  <input v-model="form.product_code" class="inp" maxlength="250" />
                </div>
              </div>
              <div class="campo-row">
                <div class="campo campo-money">
                  <label>Precio venta</label>
                  <CurrencyInput v-model="form.price" class="inp text-right" />
                </div>
                <div class="campo campo-money">
                  <label>Precio mínimo</label>
                  <CurrencyInput v-model="form.wholesale_price" class="inp text-right" />
                </div>
                <div class="campo campo-money">
                  <label>Costo producto</label>
                  <CurrencyInput v-model="form.product_cost" class="inp text-right" />
                </div>
              </div>
              <div v-if="form.wholesale_price > form.price" class="warn-line">
                <i class="bi bi-exclamation-triangle"></i> El precio mínimo es mayor que el precio de venta.
              </div>
              <div class="campo-row">
                <div class="campo">
                  <label>Impuesto %</label>
                  <input type="number" v-model.number="form.tax" class="inp" min="0" max="100" />
                </div>
                <div class="campo">
                  <label>Stock mínimo</label>
                  <input type="number" v-model.number="form.minimum_stock" class="inp" min="0" step="0.001" />
                </div>
                <div class="campo">
                  <label>Precio tachado <span class="label-hint">(web)</span></label>
                  <CurrencyInput v-model="form.compare_price" class="inp text-right" />
                </div>
              </div>

              <!-- Presentaciones (plato_producto) -->
              <div class="sec">
                <div class="sec-ttl">Presentaciones</div>
                <div class="pres-add">
                  <select v-model="presForm.measure_id" class="inp-sm">
                    <option :value="null">— Presentación —</option>
                    <option v-for="m in formasMedida" :key="m.id" :value="m.id">{{ m.name }}</option>
                  </select>
                  <select v-model="presForm.supplier_id" class="inp-sm">
                    <option :value="0">— Proveedor —</option>
                    <option v-for="p in proveedores" :key="p.id" :value="p.id">{{ p.name }}</option>
                  </select>
                  <input type="number" v-model.number="presForm.minimum_units" class="inp-sm" min="0.001" step="0.001" title="Unidades mínimas" placeholder="Und. mín." />
                  <CurrencyInput v-model="presForm.presentation_value" class="inp-sm text-right" title="Valor venta" />
                  <button class="btn-mini" :disabled="!presForm.measure_id" @click="agregarPresentacion"><i class="bi bi-plus"></i></button>
                </div>
                <div v-if="!presentaciones.length" class="mini-vacio">Sin presentaciones</div>
                <table v-else class="tbl-mini">
                  <thead><tr><th>Presentación</th><th>Proveedor</th><th class="text-right">Und. mín.</th><th class="text-right">Valor venta</th><th></th></tr></thead>
                  <tbody>
                    <tr v-for="p in presentaciones" :key="p.measure_id + '-' + p.supplier_id">
                      <td>{{ p.measure_name }}</td>
                      <td class="text-muted">{{ p.supplier_name || '—' }}</td>
                      <td class="text-right">
                        <input type="number" class="inp-qty-sm" :value="p.minimum_units" min="0.001" step="0.001"
                               @change="editarPresentacion(p, { minimum_units: +$event.target.value })" />
                      </td>
                      <td class="text-right">{{ fmt(p.presentation_value) }}</td>
                      <td><button class="btn-x-sm" @click="quitarPresentacion(p)" title="Quitar"><i class="bi bi-x-lg"></i></button></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="gen-col">
              <!-- Impresoras -->
              <div class="sec">
                <div class="sec-ttl">Impresoras</div>
                <div v-if="!impresoras.length" class="mini-vacio">Sin impresoras configuradas</div>
                <label v-for="imp in impresoras" :key="imp.id" class="chk-row">
                  <input type="checkbox" v-model="imp.assigned" :true-value="1" :false-value="0" />
                  <span>{{ imp.name }}</span>
                </label>
              </div>

              <!-- Opciones (campos reutilizados de platos) -->
              <div class="sec flags-sec">
                <label class="flag-row"><span>Pedir descripción producto</span><input type="checkbox" v-model="form.ask_product_description" :true-value="1" :false-value="0" /></label>
                <label class="flag-row"><span>Armar producto</span><input type="checkbox" v-model="form.offer_priority" :true-value="1" :false-value="0" /></label>
                <label class="flag-row"><span>Pedir peso</span><input type="checkbox" v-model="form.pre_preparation" :true-value="1" :false-value="0" /></label>
                <label class="flag-row"><span>No sumar en venta</span><input type="checkbox" v-model="form.offer" :true-value="1" :false-value="0" /></label>
                <label class="flag-row"><span>No imprime comanda</span><input type="checkbox" v-model="form.preparation_time" :true-value="1" :false-value="0" /></label>
                <label class="flag-row"><span>Desactivar al vender</span><input type="checkbox" v-model="form.extra_print" :true-value="1" :false-value="0" /></label>
                <label class="flag-row flag-row--danger"><span>Desactivar</span><input type="checkbox" v-model="form.active" :true-value="1" :false-value="0" /></label>
              </div>
            </div>
          </div>

          <!-- ── TAB: OPCIONES ADICIONALES ARMAR ── -->
          <div v-if="ed.tab === 'armar' && form.id">
            <div v-if="!form.offer_priority" class="info-line">
              <i class="bi bi-info-circle"></i> "Armar producto" está desmarcado: al comandar este plato NO se piden estas opciones. Márquelo en Información general para que sea plato de armado.
            </div>
            <div class="armar-add">
              <select v-model="armarCat" class="inp-sm">
                <option :value="null">— Seleccione categoría de armado —</option>
                <option v-for="c in categoriasArmado" :key="c.id" :value="c.id" :disabled="armado.some(g => g.category_code === c.id)">{{ c.name }}</option>
              </select>
              <button class="btn-mini" :disabled="!armarCat" @click="agregarCategoriaArmado"><i class="bi bi-plus"></i> Agregar categoría</button>
            </div>

            <div v-if="!armado.length" class="mini-vacio"><i class="bi bi-sliders"></i> Sin categorías de armado</div>
            <div class="armar-grid">
              <div v-for="g in armado" :key="g.category_code" class="grupo-card">
                <div class="grupo-hdr grupo-hdr--armar">
                  <span class="grupo-nombre">{{ g.category_name }}</span>
                  <span v-if="!g.is_assembly" class="chip-no-armado" title="Categoría sin 'Porcentaje = 1' o inactiva: no se ofrece al comandar">No es de armado</span>
                  <button class="btn-mini btn-mini--sm" @click="abrirPicker('armar', g)" title="Agregar insumos"><i class="bi bi-plus"></i> Insumo</button>
                </div>
                <table class="tbl-mini">
                  <thead><tr><th>Insumo</th><th class="text-center">Cant. desc.</th><th class="text-right">Valor adic.</th><th class="text-center">Def.</th><th></th></tr></thead>
                  <tbody>
                    <tr v-for="o in g.options" :key="o.position">
                      <td>{{ o.item_name }}</td>
                      <td class="text-center">
                        <input type="number" class="inp-qty-sm" :value="o.discount_qty" min="0.001" step="0.1"
                               @change="editarOpcion(g, o, { discount_qty: +$event.target.value })" />
                      </td>
                      <td class="text-right">
                        <CurrencyInput :model-value="o.supply_price" class="inp-qty-sm inp-money-sm"
                                       @update:model-value="v => editarOpcion(g, o, { supply_price: v })" />
                      </td>
                      <td class="text-center">
                        <input type="checkbox" :checked="o.is_default" @change="editarOpcion(g, o, { is_default: $event.target.checked ? 1 : 0 })" />
                      </td>
                      <td><button class="btn-x-sm" @click="quitarOpcion(g, o)"><i class="bi bi-x-lg"></i></button></td>
                    </tr>
                    <tr v-if="!g.options.length"><td colspan="5" class="text-muted text-center">Sin insumos</td></tr>
                  </tbody>
                </table>
                <div class="grupo-ftr">
                  <label class="mini-field-inline">Opciones permitidas
                    <input type="number" class="inp-qty-sm" v-model.number="g.max_choices" min="1" max="50" @change="editarCategoria(g)" />
                  </label>
                  <label class="mini-check-inline"><input type="checkbox" v-model="g.is_required" @change="editarCategoria(g)" /> Exigir cantidad</label>
                  <label class="mini-check-inline"><input type="checkbox" v-model="g.print_on_change_only" @change="editarCategoria(g)" /> Imprimir si hay cambios</label>
                  <button class="btn-quitar-cat" @click="quitarCategoria(g)"><i class="bi bi-trash"></i> Quitar categoría</button>
                </div>
              </div>
            </div>
          </div>

          <!-- ── TAB: DETALLE PRODUCTO - INSUMO (fijos) ── -->
          <div v-if="ed.tab === 'fijos' && form.id" class="fijos-grid">
            <div>
              <div class="sec-ttl">Seleccione el insumo que descuenta siempre este producto</div>
              <InsumoPicker :categorias="categoriasInsumo" :excluded="fijos.map(f => f.id_item)" @select="seleccionarFijo" />
              <div v-if="fijoSel" class="fijo-confirm">
                <span class="fijo-name">{{ fijoSel.description }}</span>
                <label>Porciones a descontar
                  <input type="number" v-model.number="fijoPorciones" class="inp-qty-sm" min="0.001" step="0.001" />
                </label>
                <button class="btn-mini btn-mini--cancel" @click="fijoSel = null">Cancelar</button>
                <button class="btn-mini" @click="agregarFijo">Aceptar / Guardar</button>
              </div>
            </div>
            <div>
              <div class="sec-ttl">Insumos fijos ({{ fijos.length }})</div>
              <div v-if="!fijos.length" class="mini-vacio">Sin insumos fijos</div>
              <table v-else class="tbl-mini">
                <thead><tr><th>Insumo</th><th>Categoría</th><th class="text-center">Porciones</th><th></th></tr></thead>
                <tbody>
                  <tr v-for="f in fijos" :key="f.id_item">
                    <td>{{ f.insumo_nombre || `Insumo ${f.id_item}` }}</td>
                    <td class="text-muted">{{ f.category_name || '—' }}</td>
                    <td class="text-center">
                      <input type="number" class="inp-qty-sm" :value="f.porciones" min="0.001" step="0.001"
                             @change="editarFijo(f, +$event.target.value)" />
                    </td>
                    <td><button class="btn-x-sm" @click="quitarFijo(f)"><i class="bi bi-x-lg"></i></button></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── TAB: INFO. AUX. (foto y descripción) ── -->
          <div v-show="ed.tab === 'aux'" class="aux-grid">
            <div class="campo">
              <label>Foto</label>
              <ImageUploader :current-url="form.photo_path ? imgSrc(form.photo_path) : null" @change="onFotoChanged" @remove="onFotoRemoved" />
            </div>
            <div class="aux-col">
              <div class="campo">
                <label>Descripción <span class="label-hint">(se muestra en la carta)</span></label>
                <textarea v-model="form.description" class="inp" rows="4" maxlength="5000"></textarea>
              </div>
              <div class="campo">
                <label>Procedimiento / emplatado</label>
                <textarea v-model="form.procedure" class="inp" rows="6" maxlength="5000"></textarea>
              </div>
            </div>
          </div>

          <!-- ── TAB: VARIANTES (solo web) ── -->
          <div v-if="ed.tab === 'variantes' && form.id">
            <div class="sub-header">
              <span>Versiones con precio propio (Pequeña, Familiar…)</span>
              <button class="btn-mini" @click="abrirFormVariante()"><i class="bi bi-plus"></i> Agregar</button>
            </div>
            <div v-if="!variantes.length" class="mini-vacio"><i class="bi bi-tags"></i> Sin variantes de precio</div>
            <div v-else class="variantes-lista">
              <div v-for="v in variantes" :key="v.id" class="variante-item">
                <div class="variante-info">
                  <span class="variante-nombre">{{ v.name }}</span>
                  <div class="variante-precios">
                    <span v-if="v.compare_price" class="variante-tachado">{{ fmt(v.compare_price) }}</span>
                    <span class="variante-precio">{{ fmt(v.price) }}</span>
                  </div>
                </div>
                <div class="variante-acc">
                  <button class="btn-mini btn-mini--sm" @click="abrirFormVariante(v)"><i class="bi bi-pencil"></i></button>
                  <button class="btn-x-sm" @click="eliminarVariante(v.id)"><i class="bi bi-trash"></i></button>
                </div>
              </div>
            </div>
            <div v-if="formVariante.visible" class="mini-modal">
              <input v-model="formVariante.name" class="inp-sm" maxlength="100" placeholder="Nombre (Pequeña, Mediana, Familiar…)" />
              <div class="mini-row">
                <CurrencyInput v-model="formVariante.price" class="inp-sm text-right" />
                <CurrencyInput v-model="formVariante.compare_price" class="inp-sm text-right" />
              </div>
              <div class="mini-modal-btns">
                <button class="btn-mini btn-mini--cancel" @click="formVariante.visible=false">Cancelar</button>
                <button class="btn-mini" @click="guardarVariante">{{ formVariante.id ? 'Actualizar' : 'Agregar' }}</button>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-ftr">
          <button v-if="form.id" class="btn-del" @click="eliminar(form)"><i class="bi bi-trash"></i> Eliminar</button>
          <button class="btn-cancel" @click="cerrarEditor">Salir</button>
          <button v-if="['general','aux'].includes(ed.tab)" class="btn-save" :disabled="guardando || !form.name?.trim()" @click="guardarGeneral">
            <span v-if="guardando" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-check-lg me-1"></i>{{ form.id ? 'Guardar cambios' : 'Guardar producto' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Selector de insumos para una categoría de armado -->
    <div v-if="picker.visible" class="modal-overlay modal-top" @click.self="picker.visible = false">
      <div class="ed-card ed-card--sm">
        <div class="modal-hdr">
          <span>Agregar insumos a {{ picker.grupo?.category_name }}</span>
          <button class="btn-x" @click="picker.visible = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="ed-body">
          <InsumoPicker :categorias="categoriasInsumo.filter(c => c.id === picker.grupo?.category_code)" armado
                        :default-category="picker.grupo?.category_code"
                        :excluded="picker.grupo?.options.map(o => o.position) || []" @select="agregarOpcion" />
        </div>
        <div class="modal-ftr"><button class="btn-cancel" @click="picker.visible = false">Listo</button></div>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import api from '@/services/apis.js'
import { showToast } from '@/utils/toast.js'
import ImageUploader from '@/components/ImageUploader.vue'
import InsumoPicker from '@/components/pos/InsumoPicker.vue'
import { useModuleName } from '@/composables/useModuleName'

const BASE = '/api/pos-catalogo/platos'
const API_BASE = import.meta.env.VITE_API_URL || ''
const { moduleName } = useModuleName()

// Convención VB6 (platos.Activo reutilizado como "Desactivar"): active 0 = activo, 1 = desactivado
const isActivo = item => Number(item.active) === 0

const items            = ref([])
const categorias       = ref([])   // pos_dish_categories (categoría del producto)
const categoriasInsumo = ref([])   // pos_product_categories (categorías de armado / insumos)
// Categorías de armado: categoria_productos.Porcentaje = 1 y Activa = 1
const categoriasArmado = computed(() => categoriasInsumo.value.filter(c => c.is_assembly))
const formasMedida     = ref([])
const proveedores      = ref([])
const loading    = ref(true)
const guardando  = ref(false)
const busqueda   = ref('')
const categoriaTab  = ref(null)
const filtroEstado  = ref(null)
const filtroFoto    = ref(null)

const fmtCOP = new Intl.NumberFormat('es-CO', { style:'currency', currency:'COP', minimumFractionDigits:0 })
const fmt = v => fmtCOP.format(v || 0)

function imgSrc(path) {
  if (!path) return null
  if (path.startsWith('blob:') || path.startsWith('http')) return path
  return API_BASE + path
}

// ── Filtrado / agrupado ───────────────────────────────────────────────────────
const filtrados = computed(() => {
  let r = items.value
  if (categoriaTab.value !== null) r = r.filter(i => i.category_id === categoriaTab.value)
  if (filtroEstado.value !== null) r = r.filter(i => filtroEstado.value === 1 ? isActivo(i) : !isActivo(i))
  if (filtroFoto.value !== null)   r = r.filter(i => filtroFoto.value === 'con' ? !!i.photo_path : !i.photo_path)
  if (busqueda.value) {
    const q = busqueda.value.toLowerCase()
    r = r.filter(i => i.name.toLowerCase().includes(q) || (i.category_name||'').toLowerCase().includes(q))
  }
  return r
})

const itemsAgrupados = computed(() => {
  const map = new Map()
  for (const item of filtrados.value) {
    const key = item.category_id ?? '__none__'
    if (!map.has(key)) map.set(key, { id: item.category_id, name: item.category_name || 'Sin categoría', color: '#1d4ed8', items: [] })
    map.get(key).items.push(item)
  }
  const arr = []
  for (const [key, g] of map) { if (key !== '__none__') arr.push(g) }
  if (map.has('__none__')) arr.push(map.get('__none__'))
  return arr
})

// ── Slider de categorías ──────────────────────────────────────────────────────
const catTrackRef    = ref(null)
const canScrollLeft  = ref(false)
const canScrollRight = ref(false)
function updateArrows() {
  const el = catTrackRef.value
  if (!el) return
  canScrollLeft.value  = el.scrollLeft > 4
  canScrollRight.value = el.scrollLeft < el.scrollWidth - el.clientWidth - 4
}
function scrollCats(dir) {
  const el = catTrackRef.value
  if (!el) return
  el.scrollBy({ left: dir * 220, behavior: 'smooth' })
  setTimeout(updateArrows, 320)
}
watch(categorias, async () => { await nextTick(); updateArrows() })
const setCategoria    = id => { categoriaTab.value = id }
const setFiltroEstado = v  => { filtroEstado.value = v }
const setFiltroFoto   = v  => { filtroFoto.value = v }

// ── Drag-and-drop (orden de la carta) ─────────────────────────────────────────
let dragFromItem = null
const dragId = ref(null)
function onDragStart(e, item) { dragFromItem = item; dragId.value = item.id; e.dataTransfer.effectAllowed = 'move' }
function onDragOver(e, targetItem) {
  if (!dragFromItem || dragFromItem.id === targetItem.id) return
  const fromIdx = items.value.findIndex(i => i.id === dragFromItem.id)
  const toIdx   = items.value.findIndex(i => i.id === targetItem.id)
  if (fromIdx !== -1 && toIdx !== -1) {
    const [moved] = items.value.splice(fromIdx, 1)
    items.value.splice(toIdx, 0, moved)
  }
}
async function onDrop() {
  if (!dragFromItem) return
  dragId.value = null; dragFromItem = null
  try { await api.put(`${BASE}/orden`, { ids: items.value.map(i => i.id) }) }
  catch { showToast('Error al guardar orden', 'error') }
}
function onDragEnd() { dragId.value = null; dragFromItem = null }

// ── Carga inicial ─────────────────────────────────────────────────────────────
onMounted(() => Promise.all([cargarItems(), cargarCategorias(), cargarCatalogos()]))

async function cargarItems() {
  loading.value = true
  try { const { data } = await api.get(BASE); items.value = data }
  catch { items.value = [] }
  finally { loading.value = false }
}
async function cargarCategorias() {
  try {
    const { data } = await api.get('/api/pos-catalogo/categorias')
    const activas = data.filter(c => c.is_active).sort((a, b) => a.name.localeCompare(b.name, 'es'))
    categorias.value = activas
    if (activas.length > 0) categoriaTab.value = activas[0].id
  } catch { categorias.value = [] }
}
async function cargarCatalogos() {
  const [ci, fm, pr] = await Promise.allSettled([
    api.get(`${BASE}/armado/categorias-disponibles`),
    api.get(`${BASE}/catalogos/formas-medida`),
    api.get(`${BASE}/catalogos/proveedores`),
  ])
  categoriasInsumo.value = ci.status === 'fulfilled' ? ci.value.data : []
  formasMedida.value     = fm.status === 'fulfilled' ? fm.value.data : []
  proveedores.value      = pr.status === 'fulfilled' ? pr.value.data : []
}

// ── Editor ────────────────────────────────────────────────────────────────────
const tabs = [
  { key: 'general',   label: 'Información general', icon: 'bi bi-card-text' },
  { key: 'armar',     label: 'Op. adicionales armar', icon: 'bi bi-sliders', needsId: true },
  { key: 'fijos',     label: 'Detalle producto - insumo', icon: 'bi bi-list-check', needsId: true },
  { key: 'aux',       label: 'Info. aux. (foto, desc.)', icon: 'bi bi-image' },
  { key: 'variantes', label: 'Variantes', icon: 'bi bi-tags', needsId: true },
]
const ed   = ref({ visible: false, tab: 'general' })
const form = ref({})
const impresoras     = ref([])
const presentaciones = ref([])     // guardadas (o pendientes si el producto es nuevo)
const presForm       = ref({ measure_id: null, supplier_id: 0, minimum_units: 1, presentation_value: 0 })
const armado   = ref([])
const armarCat = ref(null)
const fijos    = ref([])
const fijoSel  = ref(null)
const fijoPorciones = ref(1)
const variantes     = ref([])
const formVariante  = ref({ visible:false, id:null, name:'', price:0, compare_price:0 })
const picker   = ref({ visible: false, grupo: null })
const fotoPendiente = ref(null)
const fotoEliminada = ref(false)

const CAMPOS = ['name','product_code','price','compare_price','category_id','description','procedure','tax',
                'wholesale_price','product_cost','minimum_stock','ask_product_description','pre_preparation',
                'offer','preparation_time','extra_print','offer_priority','active']

function formVacio() {
  return { id: null, name: '', product_code: '', price: 0, compare_price: 0, category_id: categoriaTab.value,
           description: '', procedure: '', tax: 0, wholesale_price: 0, product_cost: 0, minimum_stock: 0,
           ask_product_description: 0, pre_preparation: 0, offer: 0, preparation_time: 0, extra_print: 0,
           offer_priority: 0, active: 0, photo_path: null }
}

async function abrirEditor(item = null, tab = 'general') {
  fotoPendiente.value = null; fotoEliminada.value = false
  presentaciones.value = []; armado.value = []; fijos.value = []; variantes.value = []; fijoSel.value = null
  presForm.value = { measure_id: null, supplier_id: 0, minimum_units: 1, presentation_value: 0 }
  form.value = item
    ? { ...formVacio(), ...Object.fromEntries(CAMPOS.map(k => [k, item[k] ?? formVacio()[k]])), id: item.id, photo_path: item.photo_path }
    : formVacio()
  ed.value = { visible: true, tab: item ? tab : 'general' }
  await cargarImpresoras()
  if (item) {
    await cargarPresentaciones()
    await cargarTab(ed.value.tab)
  }
}
function cerrarEditor() { ed.value.visible = false; picker.value.visible = false }

async function cambiarTab(tab) {
  ed.value.tab = tab
  await cargarTab(tab)
}
async function cargarTab(tab) {
  if (!form.value.id) return
  if (tab === 'armar')     await cargarArmado()
  if (tab === 'fijos')     await cargarFijos()
  if (tab === 'variantes') await cargarVariantes()
}

// ── Guardar información general + foto + impresoras + presentaciones pendientes
async function guardarGeneral() {
  const f = form.value
  if (!f.name?.trim()) { showToast('El nombre es obligatorio', 'warning'); ed.value.tab = 'general'; return }
  guardando.value = true
  try {
    const payload = Object.fromEntries(CAMPOS.map(k => [k, f[k]]))
    payload.name = f.name.trim()
    payload.product_code = (f.product_code || '').trim() || null
    payload.compare_price = f.compare_price || null
    const nuevo = !f.id
    let id = f.id
    if (nuevo) { const { data } = await api.post(BASE, payload); id = data.id; form.value.id = id }
    else       { await api.put(`${BASE}/${id}`, payload) }

    await api.put(`${BASE}/${id}/impresoras`, {
      printers: impresoras.value.filter(i => i.assigned).map(i => ({ printer_id: i.id, print_copies: i.print_copies || 1 })),
    })
    if (nuevo) {
      for (const p of presentaciones.value) {
        await api.post(`${BASE}/${id}/presentaciones`, {
          measure_id: p.measure_id, supplier_id: p.supplier_id, minimum_units: p.minimum_units, presentation_value: p.presentation_value,
        })
      }
      await cargarPresentaciones()
    }
    if (fotoPendiente.value) {
      const fd = new FormData()
      fd.append('file', fotoPendiente.value, 'photo.webp')
      const { data } = await api.post(`${BASE}/${id}/foto`, fd)
      form.value.photo_path = data.url
      fotoPendiente.value = null
    } else if (fotoEliminada.value) {
      await api.delete(`${BASE}/${id}/foto`)
      form.value.photo_path = null
      fotoEliminada.value = false
    }
    showToast('Guardado', 'success')
    await cargarItems()
    if (nuevo && f.offer_priority) await cambiarTab('armar')
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error al guardar', 'error')
  } finally { guardando.value = false }
}

function onFotoChanged(blob) { fotoPendiente.value = blob; fotoEliminada.value = false }
function onFotoRemoved()     { fotoPendiente.value = null; fotoEliminada.value = true }

// ── Impresoras ────────────────────────────────────────────────────────────────
async function cargarImpresoras() {
  try {
    if (form.value.id) {
      impresoras.value = (await api.get(`${BASE}/${form.value.id}/impresoras`)).data
    } else {
      const { data } = await api.get('/api/pos-catalogo/impresoras')
      impresoras.value = data.map(p => ({ id: p.id, name: p.name, assigned: 0, print_copies: 1 }))
    }
  } catch { impresoras.value = [] }
}

// ── Presentaciones ────────────────────────────────────────────────────────────
async function cargarPresentaciones() {
  try { presentaciones.value = (await api.get(`${BASE}/${form.value.id}/presentaciones`)).data }
  catch { presentaciones.value = [] }
}
async function agregarPresentacion() {
  const p = { ...presForm.value }
  if (!p.measure_id || !(p.minimum_units > 0)) { showToast('Seleccione la presentación y las unidades mínimas', 'warning'); return }
  if (presentaciones.value.some(x => x.measure_id === p.measure_id && x.supplier_id === p.supplier_id)) {
    showToast('Esa presentación ya está agregada', 'warning'); return
  }
  if (!form.value.id) {               // producto nuevo: queda pendiente hasta guardar
    presentaciones.value.push({ ...p,
      measure_name: formasMedida.value.find(m => m.id === p.measure_id)?.name,
      supplier_name: proveedores.value.find(s => s.id === p.supplier_id)?.name })
  } else {
    try { await api.post(`${BASE}/${form.value.id}/presentaciones`, p); await cargarPresentaciones() }
    catch (e) { showToast(e?.response?.data?.detail || 'Error al agregar presentación', 'error'); return }
  }
  presForm.value = { measure_id: null, supplier_id: 0, minimum_units: 1, presentation_value: form.value.price || 0 }
}
async function editarPresentacion(p, cambios) {
  const nuevo = { minimum_units: p.minimum_units, presentation_value: p.presentation_value, ...cambios }
  if (!(nuevo.minimum_units > 0)) { showToast('Las unidades mínimas deben ser mayores a 0', 'warning'); return }
  if (!form.value.id) { Object.assign(p, nuevo); return }
  try { await api.put(`${BASE}/${form.value.id}/presentaciones/${p.measure_id}/${p.supplier_id}`, nuevo); Object.assign(p, nuevo) }
  catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error') }
}
async function quitarPresentacion(p) {
  if (!form.value.id) { presentaciones.value = presentaciones.value.filter(x => x !== p); return }
  try { await api.delete(`${BASE}/${form.value.id}/presentaciones/${p.measure_id}/${p.supplier_id}`); await cargarPresentaciones() }
  catch { showToast('Error al quitar presentación', 'error') }
}

// ── Armado ────────────────────────────────────────────────────────────────────
async function cargarArmado() {
  try { armado.value = (await api.get(`${BASE}/${form.value.id}/armado`)).data }
  catch { armado.value = [] }
}
async function agregarCategoriaArmado() {
  try {
    await api.post(`${BASE}/${form.value.id}/armado/categoria`, { category_code: armarCat.value, max_choices: 1, is_required: 0, print_on_change_only: 0 })
    armarCat.value = null
    await cargarArmado(); await cargarItems()
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al agregar categoría', 'error') }
}
async function editarCategoria(g) {
  const mc = parseInt(g.max_choices) || 1
  g.max_choices = Math.min(Math.max(mc, 1), 50)
  try {
    await api.put(`${BASE}/${form.value.id}/armado/categoria/${g.category_code}`, {
      max_choices: g.max_choices, is_required: g.is_required ? 1 : 0, print_on_change_only: g.print_on_change_only ? 1 : 0,
    })
  } catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error'); await cargarArmado() }
}
async function quitarCategoria(g) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Quitar la categoría "${g.category_name}"?`, text: 'Se quitarán también sus insumos.',
    icon: 'warning', showCancelButton: true, confirmButtonColor: '#e11d48', confirmButtonText: 'Quitar', cancelButtonText: 'Cancelar',
  })
  if (!isConfirmed) return
  try { await api.delete(`${BASE}/${form.value.id}/armado/categoria/${g.category_code}`); await cargarArmado(); await cargarItems() }
  catch { showToast('Error al quitar categoría', 'error') }
}
function abrirPicker(tipo, grupo) { picker.value = { visible: true, grupo } }
async function agregarOpcion(insumo) {
  const g = picker.value.grupo
  try {
    await api.post(`${BASE}/${form.value.id}/armado/categoria/${g.category_code}/opcion`,
                   { position: insumo.id_item, discount_qty: 1, supply_price: 0, is_default: 0 })
    await cargarArmado()
    picker.value.grupo = armado.value.find(x => x.category_code === g.category_code) || g
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al agregar insumo', 'error') }
}
async function editarOpcion(g, o, cambios) {
  const nuevo = { discount_qty: o.discount_qty, supply_price: o.supply_price, is_default: o.is_default ? 1 : 0, ...cambios }
  if (!(nuevo.discount_qty > 0)) { showToast('La cantidad a descontar debe ser mayor a 0', 'warning'); await cargarArmado(); return }
  if (nuevo.discount_qty === o.discount_qty && nuevo.supply_price === o.supply_price && !!nuevo.is_default === !!o.is_default) return
  try {
    await api.put(`${BASE}/${form.value.id}/armado/categoria/${g.category_code}/opcion/${o.position}`, nuevo)
    Object.assign(o, nuevo)
  } catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error'); await cargarArmado() }
}
async function quitarOpcion(g, o) {
  try { await api.delete(`${BASE}/${form.value.id}/armado/categoria/${g.category_code}/opcion/${o.position}`); await cargarArmado() }
  catch { showToast('Error al quitar insumo', 'error') }
}

// ── Insumos fijos ─────────────────────────────────────────────────────────────
async function cargarFijos() {
  try { fijos.value = (await api.get(`${BASE}/${form.value.id}/insumos-fijos`)).data }
  catch { fijos.value = [] }
}
function seleccionarFijo(insumo) { fijoSel.value = insumo; fijoPorciones.value = 1 }
async function agregarFijo() {
  if (!(fijoPorciones.value > 0)) { showToast('Las porciones deben ser mayores a 0', 'warning'); return }
  try {
    await api.post(`${BASE}/${form.value.id}/insumos-fijos`, { id_item: fijoSel.value.id_item, porciones: fijoPorciones.value })
    fijoSel.value = null
    await cargarFijos(); await cargarItems()
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al agregar insumo', 'error') }
}
async function editarFijo(f, porciones) {
  if (!(porciones > 0)) { showToast('Las porciones deben ser mayores a 0', 'warning'); await cargarFijos(); return }
  try { await api.put(`${BASE}/${form.value.id}/insumos-fijos/${f.id_item}`, { porciones }); f.porciones = porciones }
  catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error') }
}
async function quitarFijo(f) {
  try { await api.delete(`${BASE}/${form.value.id}/insumos-fijos/${f.id_item}`); await cargarFijos(); await cargarItems() }
  catch { showToast('Error al quitar insumo', 'error') }
}

// ── Variantes (solo web) ──────────────────────────────────────────────────────
async function cargarVariantes() {
  try { variantes.value = (await api.get(`${BASE}/${form.value.id}/variantes`)).data }
  catch { variantes.value = [] }
}
function abrirFormVariante(v = null) {
  formVariante.value = v
    ? { visible:true, id:v.id, name:v.name, price:v.price, compare_price:v.compare_price || 0 }
    : { visible:true, id:null, name:'', price:0, compare_price:0 }
}
async function guardarVariante() {
  if (!formVariante.value.name?.trim()) { showToast('El nombre es obligatorio', 'warning'); return }
  const p = { name: formVariante.value.name.trim(), price: formVariante.value.price || 0, compare_price: formVariante.value.compare_price || null }
  try {
    if (formVariante.value.id) await api.put(`${BASE}/${form.value.id}/variantes/${formVariante.value.id}`, p)
    else await api.post(`${BASE}/${form.value.id}/variantes`, p)
    formVariante.value.visible = false; await cargarVariantes(); await cargarItems()
  } catch { showToast('Error al guardar variante', 'error') }
}
async function eliminarVariante(varId) {
  try { await api.delete(`${BASE}/${form.value.id}/variantes/${varId}`); await cargarVariantes(); await cargarItems() }
  catch { showToast('Error', 'error') }
}

// ── Desactivar / eliminar ─────────────────────────────────────────────────────
async function eliminar(item) {
  const { isConfirmed, isDenied } = await window.Swal.fire({
    title: item.name,
    html: '<p style="margin:0;color:#475569;font-size:14px">¿Qué deseas hacer con este artículo?</p>',
    icon: 'warning', showCancelButton: true, showDenyButton: true,
    confirmButtonColor: '#f59e0b', denyButtonColor: '#e11d48',
    confirmButtonText: 'Desactivar', denyButtonText: 'Eliminar definitivamente', cancelButtonText: 'Cancelar',
  })
  if (isConfirmed) {
    try {
      await api.delete(`${BASE}/${item.id}`)
      showToast('Artículo desactivado', 'success')
      if (form.value.id === item.id) form.value.active = 1
      await cargarItems()
    } catch { showToast('Error al desactivar', 'error') }
  } else if (isDenied) {
    const { isConfirmed: ok2 } = await window.Swal.fire({
      title: '¿Eliminar permanentemente?',
      html: '<p style="margin:0;color:#475569;font-size:14px">Se borrarán presentaciones, insumos fijos, impresoras, armado y variantes.<br><b>Esta acción no se puede deshacer.</b></p>',
      icon: 'error', showCancelButton: true, confirmButtonColor: '#e11d48', confirmButtonText: 'Sí, eliminar', cancelButtonText: 'Cancelar',
    })
    if (!ok2) return
    try {
      await api.delete(`${BASE}/${item.id}/definitivo`)
      showToast('Artículo eliminado definitivamente', 'success')
      if (form.value.id === item.id) cerrarEditor()
      await cargarItems()
    } catch (e) {
      window.Swal.fire({ title: 'No se puede eliminar', text: e?.response?.data?.detail || 'Error al eliminar', icon: 'error' })
    }
  }
}
</script>


<style scoped>
.crud-view { padding:0; }
.crud-header { display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;gap:12px; }
.crud-titulo { font-weight:700;font-size:16px;color:#1e3a5f;margin:0; }
.crud-sub    { font-size:13px;color:#64748b;margin:2px 0 0; }
.header-tools{ display:flex;gap:10px;align-items:center;flex-shrink:0; }
.inp-buscar  { border:1.5px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:13px;color:#1e3a5f;outline:none;width:160px; }
.inp-buscar:focus { border-color:#1d4ed8; }
.btn-nuevo   { display:flex;align-items:center;gap:6px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap; }

/* ── Slider de categorías ────────────────────────────────────────────────────── */
.cat-slider-wrap {
  position:sticky;top:0;z-index:20;
  display:flex;align-items:center;gap:10px;
  background:linear-gradient(135deg,#1e3a5f 0%,#1d4ed8 100%);
  border-radius:14px;padding:10px 10px 10px 14px;margin-bottom:16px;
  box-shadow:0 4px 16px rgba(29,78,216,.25);
}
.cat-slider-inner {
  position:relative;flex:1;min-width:0;
  display:flex;align-items:center;
  padding:0 40px;
}
.cat-pill--todos {
  flex-shrink:0;
  position:relative;
  margin-right:4px;
}
.cat-pill--todos::before {
  content:'';
  position:absolute;left:-7px;top:15%;height:70%;
  width:1px;background:rgba(255,255,255,.28);
  pointer-events:none;
}
.cat-track {
  display:flex;gap:8px;flex:1;
  overflow-x:auto;scroll-behavior:smooth;
  -webkit-overflow-scrolling:touch;
  scrollbar-width:none;-ms-overflow-style:none;
  padding:2px 0;
}
.cat-track::-webkit-scrollbar { display:none; }

.cat-pill {
  display:flex;align-items:center;gap:6px;
  padding:9px 18px;border-radius:22px;flex-shrink:0;
  border:2px solid rgba(255,255,255,.28);
  background:rgba(255,255,255,.13);
  color:rgba(255,255,255,.88);
  font-size:12px;font-weight:700;cursor:pointer;
  white-space:nowrap;transition:all .18s;
  min-width:max-content;
}
.cat-pill:hover { background:rgba(255,255,255,.25);color:#fff;border-color:rgba(255,255,255,.55); }
.cat-pill.active {
  background:#fff;color:#1e3a5f;border-color:#fff;
  box-shadow:0 4px 14px rgba(0,0,0,.22);
}
.cat-pill i { font-size:13px; }
.cat-dot {
  width:7px;height:7px;border-radius:50%;flex-shrink:0;
  background:rgba(255,255,255,.6);
}
.cat-pill.active .cat-dot { background:#1d4ed8; }

.cat-arrow {
  position:absolute;top:50%;transform:translateY(-50%);z-index:5;
  width:34px;height:34px;border-radius:50%;
  border:2px solid rgba(255,255,255,.45);
  background:rgba(15,30,60,.55);backdrop-filter:blur(4px);
  color:#fff;display:flex;align-items:center;justify-content:center;
  cursor:pointer;font-size:13px;transition:all .18s;
  opacity:0;pointer-events:none;
}
.cat-arrow.visible { opacity:1;pointer-events:auto; }
.cat-arrow:hover { background:rgba(15,30,60,.85);border-color:#fff; }
.cat-arrow--left  { left:7px; }
.cat-arrow--right { right:7px; }

/* ── Filtros estado / foto ──────────────────────────────────────────────────── */
.filtros-wrap  { display:flex;flex-wrap:wrap;gap:12px;margin-bottom:14px;align-items:center; }
.filtros-grupo { display:flex;align-items:center;gap:6px; }
.filtros-label { font-size:11px;font-weight:600;color:#64748b;white-space:nowrap; }
.filtro-btn {
  padding:4px 12px;border-radius:20px;border:1.5px solid #e2e8f0;
  background:#f8fafc;font-size:12px;font-weight:600;color:#475569;
  cursor:pointer;transition:.15s;white-space:nowrap;
}
.filtro-btn:hover { border-color:#1d4ed8;color:#1d4ed8; }
.filtro-btn.active { background:#1d4ed8;color:#fff;border-color:#1d4ed8; }
.filtro-btn--activo.active   { background:#16a34a;border-color:#16a34a; }
.filtro-btn--inactivo.active { background:#94a3b8;border-color:#94a3b8; }
.filtro-btn--confoto.active  { background:#7c3aed;border-color:#7c3aed; }
.filtro-btn--sinfoto.active  { background:#e11d48;border-color:#e11d48; }

/* ── Grid de tarjetas ────────────────────────────────────────────────────────── */
.estado-carga,.estado-vacio { display:flex;flex-direction:column;align-items:center;gap:10px;padding:60px 20px;color:#94a3b8;font-size:14px; }
.estado-vacio i { font-size:40px; }
.items-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px; }

/* ── Grupos con cabecera de categoría (OlaClick style) ───────────────────────── */
.grupos-wrap { display:flex;flex-direction:column; }
.seccion-hdr {
  position:sticky;top:62px;z-index:5;
  background:var(--color-bg,#f8fafc);
  display:flex;align-items:center;gap:8px;
  padding:9px 8px 9px 12px;
  margin:16px 0 10px;
  border-left:4px solid var(--cat-color,#1d4ed8);
  border-radius:0 6px 6px 0;
}
.seccion-hdr:first-child { margin-top:0; }
.seccion-dot   { width:9px;height:9px;border-radius:50%;flex-shrink:0; }
.seccion-nombre{ font-weight:700;font-size:12px;color:#1e3a5f;flex:1;text-transform:uppercase;letter-spacing:.06em; }
.seccion-count { font-size:11px;color:#94a3b8;background:#e2e8f0;border-radius:20px;padding:1px 8px;font-weight:600; }
.seccion-grid  { margin-bottom:4px; }

.item-card {
  background:#fff;border:2px solid #e2e8f0;border-radius:14px;
  overflow:hidden;display:flex;flex-direction:column;transition:border-color .15s, box-shadow .15s;
  cursor:grab;
}
.item-card:hover { border-color:#1d4ed8;box-shadow:0 4px 16px rgba(29,78,216,.1); }
.item-card--inactivo { opacity:.5; }
.item-card--dragging { opacity:.6;border-color:#1d4ed8;box-shadow:0 8px 24px rgba(0,0,0,.2); }
.item-card:active { cursor:grabbing; }

/* Foto */
.item-foto { position:relative;height:160px;background:#f1f5f9;overflow:hidden;flex-shrink:0; }
.item-foto-img { width:100%;height:100%;object-fit:cover;display:block;image-rendering:high-quality;image-rendering:-webkit-optimize-contrast; }
.item-foto-placeholder { display:flex;align-items:center;justify-content:center;height:100%;color:#cbd5e1;font-size:36px; }
.drag-handle {
  position:absolute;top:6px;right:6px;background:rgba(0,0,0,.4);
  color:#fff;border-radius:6px;padding:2px 5px;font-size:12px;
  cursor:grab;opacity:0;transition:opacity .15s;
}
.item-card:hover .drag-handle { opacity:1; }

.item-body { padding:12px;display:flex;flex-direction:column;gap:6px;flex:1; }
.item-top    { display:flex;justify-content:space-between;align-items:center;gap:4px; }
.item-cat    { font-size:10px;font-weight:700;border-radius:10px;padding:2px 8px;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.badge-activo  { font-size:10px;background:#dcfce7;color:#16a34a;border-radius:10px;padding:2px 8px;font-weight:700;white-space:nowrap; }
.badge-inactivo{ font-size:10px;background:#f1f5f9;color:#94a3b8;border-radius:10px;padding:2px 8px;white-space:nowrap; }
.item-nombre { font-weight:700;font-size:14px;color:#1e3a5f;line-height:1.3; }
.item-precios { display:flex;align-items:baseline;gap:6px; }
.precio-tachado { font-size:12px;color:#94a3b8;text-decoration:line-through; }
.item-precio { font-size:18px;font-weight:800;color:#1d4ed8; }
.item-meta   { display:flex;gap:10px;font-size:11px;color:#94a3b8;flex-wrap:wrap; }
.item-meta span { display:flex;align-items:center;gap:3px; }
.badge-variants { color:#7c3aed;font-weight:700; }
.item-acciones {
  display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin-top:6px;
}
.btn-accion {
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:3px;border-radius:8px;padding:7px 4px 6px;cursor:pointer;
  border:1.5px solid #e2e8f0;background:#f8fafc;
  font-size:15px;transition:all .15s;line-height:1;
}
.btn-accion span { font-size:9px;font-weight:700;letter-spacing:.01em;line-height:1; }
.btn-accion--edit     { color:#1d4ed8; }
.btn-accion--edit:hover     { background:#eff6ff;border-color:#1d4ed8; }
.btn-accion--recipe   { color:#16a34a; }
.btn-accion--recipe:hover   { background:#f0fdf4;border-color:#16a34a; }
.btn-accion--print    { color:#ea580c; }
.btn-accion--print:hover    { background:#fff7ed;border-color:#ea580c; }
.btn-accion--build    { color:#7c3aed; }
.btn-accion--build:hover    { background:#f5f3ff;border-color:#7c3aed; }
.btn-accion--variants { color:#0891b2; }
.btn-accion--variants:hover { background:#ecfeff;border-color:#0891b2; }
.btn-accion--danger   { color:#e11d48; }
.btn-accion--danger:hover   { background:#fff1f2;border-color:#e11d48; }

/* ── Modal ───────────────────────────────────────────────────────────────────── */
.modal-overlay { position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:1050;padding:16px; }
.modal-card  { background:#fff;border-radius:16px;width:100%;max-width:480px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.25); }
.modal-hdr   { display:flex;justify-content:space-between;align-items:center;padding:16px 20px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;font-weight:700;font-size:15px; }
.btn-x       { background:none;border:none;color:#fff;cursor:pointer;font-size:16px;opacity:.8; }
.btn-x:hover { opacity:1; }
.modal-body  { padding:20px;display:flex;flex-direction:column;gap:12px;max-height:75vh;overflow-y:auto; }
.campo       { display:flex;flex-direction:column;gap:4px; }
.campo label { font-size:12px;font-weight:600;color:#475569; }
.label-hint  { font-weight:400;color:#94a3b8; }
.campo-row   { display:flex;gap:12px; }
.campo-row .campo { flex:1; }
.inp         { border:1.5px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:14px;color:#1e3a5f;outline:none;width:100%;box-sizing:border-box; }
.inp:focus   { border-color:#1d4ed8; }
.campo-check { display:flex;align-items:center;gap:8px;font-size:13px;color:#475569; }
.modal-ftr   { display:flex;gap:10px;justify-content:flex-end;padding:14px 20px;border-top:1px solid #f1f5f9; }
.btn-cancel  { background:#f1f5f9;border:none;border-radius:8px;padding:9px 18px;font-size:14px;cursor:pointer;color:#475569;font-weight:600; }
.btn-save    { background:linear-gradient(90deg,#1e3a5f,#1d4ed8);border:none;border-radius:8px;padding:9px 20px;font-size:14px;font-weight:700;color:#fff;cursor:pointer; }
.btn-save:disabled { opacity:.6;cursor:not-allowed; }

/* ── Panel lateral ───────────────────────────────────────────────────────────── */
.panel-overlay  { position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:1040;display:flex;justify-content:flex-end; }
.panel-lateral  { width:100%;max-width:480px;height:100%;background:#fff;display:flex;flex-direction:column;box-shadow:-8px 0 32px rgba(0,0,0,.18);overflow:hidden; }
.panel-hdr      { display:flex;justify-content:space-between;align-items:center;padding:14px 18px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;gap:12px; }
.panel-hdr-info { display:flex;align-items:center;gap:10px;min-width:0; }
.panel-thumb    { width:40px;height:40px;border-radius:8px;object-fit:cover;flex-shrink:0;border:2px solid rgba(255,255,255,.3); }
.panel-titulo   { font-weight:700;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.panel-sub      { font-size:12px;opacity:.8; }
.panel-tabs     { display:flex;overflow-x:auto;border-bottom:2px solid #e2e8f0;background:#f8fafc;-webkit-overflow-scrolling:touch; }
.ptab           { flex-shrink:0;display:flex;flex-direction:column;align-items:center;gap:2px;padding:10px 14px;border:none;background:none;font-size:11px;font-weight:500;color:#64748b;cursor:pointer;border-bottom:3px solid transparent;transition:.15s;margin-bottom:-2px;min-width:70px; }
.ptab i         { font-size:16px; }
.ptab.active    { color:#1d4ed8;border-bottom-color:#1d4ed8;font-weight:700; }
.panel-body     { flex:1;overflow-y:auto;padding:16px; }
.sub-header     { display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;font-size:13px;color:#475569;font-weight:600; }
.mini-carga     { display:flex;justify-content:center;padding:30px; }
.mini-vacio     { display:flex;align-items:center;gap:8px;justify-content:center;padding:30px;color:#94a3b8;font-size:13px; }

/* Receta */
.receta-lista { display:flex;flex-direction:column;gap:6px;margin-bottom:12px; }
.receta-item  { display:flex;align-items:center;justify-content:space-between;background:#f8fafc;border-radius:8px;padding:8px 12px; }
.receta-info  { display:flex;flex-direction:column;gap:2px; }
.receta-nombre{ font-weight:600;font-size:13px;color:#1e3a5f; }
.receta-qty   { font-size:11px;color:#64748b; }

/* Impresoras */
.imp-lista          { display:flex;flex-direction:column;gap:8px; }
.imp-item           { display:flex;align-items:center;gap:12px;border:2px solid #e2e8f0;border-radius:10px;padding:12px 14px;cursor:pointer;transition:all .15s;user-select:none; }
.imp-item:hover     { border-color:#93c5fd;background:#f8faff; }
.imp-item--sel      { border-color:#1d4ed8;background:#eef2ff; }
.imp-icon-print     { font-size:20px;color:#94a3b8;flex-shrink:0;transition:color .15s; }
.imp-item--sel .imp-icon-print { color:#1d4ed8; }
.imp-info           { flex:1;min-width:0; }
.imp-nombre         { font-weight:700;font-size:13px;color:#1e3a5f; }
.imp-tipo           { font-size:11px;color:#64748b; }
.imp-check-indicator{ font-size:22px;flex-shrink:0;color:#cbd5e1;transition:color .15s; }
.imp-item--sel .imp-check-indicator { color:#1d4ed8; }

/* Modificadores / Armado */
.grupos-lista     { display:flex;flex-direction:column;gap:10px;margin-bottom:12px; }
.grupo-card       { border:2px solid #e2e8f0;border-radius:10px;overflow:hidden; }
.grupo-card--off  { opacity:.55; }
.grupo-hdr        { display:flex;align-items:center;gap:8px;padding:10px 12px;background:#f8fafc; }
.grupo-nombre     { font-weight:700;font-size:13px;color:#1e3a5f;flex:1; }
.chip-no-armado   { font-size:10px;font-weight:700;color:#b45309;background:#fef3c7;border-radius:10px;padding:1px 7px;margin-right:6px;white-space:nowrap; }
.grupo-badges     { display:flex;gap:4px;flex-wrap:wrap; }
.badge-req        { font-size:10px;background:#fef3c7;color:#d97706;border-radius:6px;padding:1px 6px;font-weight:700; }
.badge-mul        { font-size:10px;background:#ede9fe;color:#7c3aed;border-radius:6px;padding:1px 6px;font-weight:700; }
.badge-off-sm     { font-size:10px;background:#f1f5f9;color:#94a3b8;border-radius:6px;padding:1px 6px; }
.badge-def        { font-size:10px;background:#dbeafe;color:#2563eb;border-radius:6px;padding:1px 6px;font-weight:700; }
.badge-vb6        { font-size:10px;background:#f0fdf4;color:#16a34a;border-radius:6px;padding:2px 8px;font-weight:700;border:1px solid #bbf7d0;cursor:default; }
.grupo-acc        { display:flex;gap:4px; }
.detalles-lista   { padding:8px 12px;display:flex;flex-direction:column;gap:4px; }
.detalle-item     { display:flex;align-items:center;gap:8px;font-size:13px; }
.det-nombre       { flex:1;color:#1e3a5f; }
.det-precio       { font-weight:700;font-size:12px;color:#64748b; }
.det-qty          { color:#0891b2; }
.precio-pos       { color:#16a34a; }
.precio-neg       { color:#e11d48; }

/* Armado CRUD extras */
.detalle-item--armado { gap:6px; }
.inp-qty-sm {
  width: 60px;
  border: 1.5px solid #e2e8f0;
  border-radius: 6px;
  padding: 2px 6px;
  font-size: 12px;
  text-align: center;
  color: #1e3a5f;
}
.inp-qty-sm:focus { border-color: #1d4ed8; outline: none; }
.det-default { display:flex;align-items:center;gap:3px;font-size:11px;color:#64748b;cursor:pointer; }
.default-label { font-size:11px; }
.mini-label-b { font-weight:700;font-size:12px;color:#1e3a5f;display:block;margin-bottom:4px; }
.mini-label-s { font-size:11px;color:#64748b;display:block;margin-bottom:2px; }
.mini-field   { display:flex;flex-direction:column; }
.mini-check-inline { display:flex;align-items:center;gap:5px;font-size:12px;color:#475569;margin-top:14px;cursor:pointer; }

/* Variantes */
.variantes-lista  { display:flex;flex-direction:column;gap:8px;margin-bottom:12px; }
.variante-item    { display:flex;align-items:center;gap:8px;border:2px solid #e2e8f0;border-radius:10px;padding:10px 12px; }
.variante-info    { flex:1;display:flex;flex-direction:column;gap:2px; }
.variante-nombre  { font-weight:700;font-size:13px;color:#1e3a5f; }
.variante-precios { display:flex;align-items:baseline;gap:6px; }
.variante-tachado { font-size:11px;color:#94a3b8;text-decoration:line-through; }
.variante-precio  { font-size:14px;font-weight:800;color:#1d4ed8; }
.variante-acc     { display:flex;gap:4px; }

/* Shared mini-modal */
.mini-modal  { background:#f0f4ff;border:2px solid #1d4ed8;border-radius:10px;padding:14px;display:flex;flex-direction:column;gap:8px;margin-top:10px; }
.mini-label  { font-size:12px;color:#475569;margin:0; }
.mini-row    { display:flex;gap:8px; }
.inp-sm      { border:1.5px solid #cbd5e1;border-radius:6px;padding:6px 10px;font-size:13px;color:#1e3a5f;outline:none;width:100%;box-sizing:border-box; }
.inp-sm:focus{ border-color:#1d4ed8; }
.mini-checks { display:flex;gap:14px;font-size:13px;color:#475569; }
.mini-modal-btns{ display:flex;gap:8px;justify-content:flex-end; }
.btn-mini    { display:flex;align-items:center;gap:4px;background:#1d4ed8;color:#fff;border:none;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer; }
.btn-mini--sm{ padding:3px 8px; }
.btn-mini--cancel{ background:#f1f5f9;color:#475569; }
.btn-x-sm   { background:none;border:none;color:#94a3b8;cursor:pointer;font-size:14px;padding:2px 4px; }
.btn-x-sm:hover{ color:#e11d48; }

/* ── Responsive ──────────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .crud-header { flex-direction:column;gap:10px; }
  .header-tools { flex-wrap:wrap;width:100%; }
  .inp-buscar { flex:1;min-width:120px; }
  .items-grid { grid-template-columns:1fr 1fr; }
  .panel-lateral { max-width:100%; }
  .item-foto { height:130px; }
  .filtros-wrap { gap:8px; }
  .cat-slider-wrap { padding:8px 8px 8px 10px;border-radius:10px; }
  .cat-slider-inner { padding:0 34px; }
  .cat-pill { padding:8px 14px;font-size:11px; }
  .cat-arrow { width:30px;height:30px;font-size:12px; }
  .cat-arrow--left  { left:5px; }
  .cat-arrow--right { right:5px; }
  .seccion-hdr { top:54px; }
}
@media (max-width: 576px) {
  .items-grid { grid-template-columns:1fr; }
  .campo-row  { flex-direction:column; }
  .item-foto  { height:160px; }
  .filtros-wrap { flex-direction:column;align-items:flex-start; }
  .cat-slider-wrap { padding:8px 6px 8px 8px;border-radius:8px;margin-bottom:12px; }
  .cat-slider-inner { padding:0 30px; }
  .cat-pill { padding:7px 12px;font-size:11px; }
  .seccion-hdr { top:50px; }
}

/* ── Editor del producto ─────────────────────────────────────────────────────── */
.ed-card { background:#fff;border-radius:16px;width:100%;max-width:1100px;max-height:94vh;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.25); }
.ed-card--sm { max-width:720px; }
.modal-top { z-index:1060; }
.ed-hdr-info { display:flex;align-items:center;gap:10px;min-width:0; }
.ed-code  { font-size:11px;background:rgba(255,255,255,.18);border-radius:6px;padding:2px 8px;white-space:nowrap; }
.ed-title { overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.ed-body  { flex:1;overflow-y:auto;padding:16px 20px; }
.ptab:disabled { opacity:.4;cursor:not-allowed; }
.gen-grid { display:grid;grid-template-columns:1.6fr 1fr;gap:18px; }
.gen-col  { display:flex;flex-direction:column;gap:12px;min-width:0; }
.inp-strong { font-weight:700;font-size:15px; }
.text-right { text-align:right; }
.text-center { text-align:center; }
.text-muted { color:#94a3b8; }
.warn-line { font-size:12px;color:#b45309;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:6px 10px; }
.info-line { font-size:12px;color:#1e40af;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:6px 10px;margin-bottom:10px; }
.sec      { border:1.5px solid #e2e8f0;border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:8px; }
.sec-ttl  { font-size:12px;font-weight:700;color:#1e3a5f;text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px; }
.chk-row  { display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;color:#1e3a5f;cursor:pointer; }
.chk-row input, .flag-row input { width:17px;height:17px;cursor:pointer; }
.flags-sec { background:#f0fdf4;border-color:#bbf7d0; }
.flag-row { display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:13px;font-weight:600;color:#14532d;cursor:pointer;padding:3px 0; }
.flag-row--danger { color:#b91c1c; }
.pres-add { display:grid;grid-template-columns:1.3fr 1.3fr .7fr .9fr auto;gap:6px;align-items:center; }
.tbl-mini { width:100%;border-collapse:collapse;font-size:12px; }
.tbl-mini th { background:#f8fafc;color:#475569;font-weight:700;font-size:10px;text-transform:uppercase;padding:6px 8px;border-bottom:1px solid #e2e8f0;text-align:left; }
.tbl-mini td { padding:5px 8px;border-bottom:1px solid #f1f5f9;vertical-align:middle; }
.inp-money-sm { width:90px;text-align:right; }
.armar-add  { display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap; }
.armar-add .inp-sm { flex:1;min-width:200px; }
.armar-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px; }
.grupo-hdr--armar { background:#fef2f2; }
.grupo-ftr  { display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:8px 12px;background:#fdf4ff;border-top:1px solid #f5d0fe; }
.mini-field-inline { display:flex;align-items:center;gap:6px;font-size:12px;font-weight:700;color:#701a75; }
.grupo-ftr .mini-check-inline { margin-top:0; }
.btn-quitar-cat { margin-left:auto;border:none;background:#fee2e2;color:#b91c1c;font-size:11px;font-weight:700;border-radius:6px;padding:4px 8px;cursor:pointer; }
.fijos-grid { display:grid;grid-template-columns:1.2fr 1fr;gap:16px; }
.fijo-confirm { display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:10px;background:#fefce8;border:1.5px solid #fde047;border-radius:10px;padding:10px; }
.fijo-name { font-weight:700;color:#1e3a5f;flex:1 1 100%; }
.fijo-confirm label { display:flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:#475569; }
.aux-grid { display:grid;grid-template-columns:320px 1fr;gap:18px; }
.aux-col  { display:flex;flex-direction:column;gap:12px; }
.btn-del  { margin-right:auto;background:#fff1f2;border:1.5px solid #fecdd3;color:#e11d48;border-radius:8px;padding:9px 14px;font-size:13px;font-weight:700;cursor:pointer; }
.badge-armar { color:#a16207;font-weight:700; }

@media (max-width: 1024px) {
  .gen-grid, .fijos-grid { grid-template-columns:1fr; }
  .aux-grid { grid-template-columns:1fr; }
}
@media (max-width: 768px) {
  .modal-overlay { padding:0;align-items:flex-end; }
  .ed-card { max-height:100vh;height:100%;border-radius:0; }
  .ed-card--sm { height:auto;max-height:92vh;border-radius:16px 16px 0 0; }
  .ed-body { padding:12px 14px; }
  .pres-add { grid-template-columns:1fr 1fr; }
  .pres-add .btn-mini { grid-column:span 2;justify-content:center; }
  .armar-grid { grid-template-columns:1fr; }
  .campo-row { flex-wrap:wrap; }
  .campo-money { min-width:130px; }
}
@media (max-width: 576px) {
  .ptab span { font-size:10px; }
  .ptab { min-width:64px;padding:8px 10px; }
  .tbl-mini th, .tbl-mini td { padding:4px 5px; }
  .inp-money-sm { width:72px; }
  .modal-ftr { flex-wrap:wrap; }
  .modal-ftr .btn-save { flex:1 1 100%; }
  .btn-del { margin-right:0; }
}
</style>
