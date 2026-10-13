<template>
  <div class="bc-page">
    <div class="bc-head">
      <h2 class="bc-title"><i class="bi bi-boxes me-2"></i>{{ moduleName || 'Bodega Central' }}</h2>
      <p v-if="info" class="bc-sub">
        {{ info.bodega.nombre }} · NIT {{ info.bodega.nit }}
        <span v-if="info.cargue_unitario" class="bc-chip bc-chip--imei"><i class="bi bi-upc-scan"></i> Cargue unitario (IMEI)</span>
      </p>
      <div v-if="info" class="bc-sedes">
        <span class="bc-sedes-lbl">Sedes:</span>
        <span v-for="s in $ordenAlfa(info.sedes, 'nombre')" :key="s.id" class="bc-chip">
          <i class="bi" :class="s.con_escritorio ? 'bi-pc-display' : 'bi-globe'"></i> {{ s.nombre }}
        </span>
        <span v-if="!info.sedes.length" class="bc-nota">No hay otras empresas activas con este NIT.</span>
      </div>
    </div>

    <div v-if="loading" class="bc-state"><div class="spinner-border text-primary"></div></div>

    <div v-else-if="bloqueo" class="bc-bloqueo">
      <i class="bi bi-lock-fill"></i>
      <div>
        <b>{{ bloqueo }}</b>
        <p>La bodega central la habilita el administrador del sistema en una empresa con el mismo NIT de sus sedes.</p>
      </div>
    </div>

    <template v-else>

      <!-- ── Productos ── -->
      <section v-if="tab === 'productos'" class="bc-card">
        <div class="bc-toolbar">
          <div class="bc-search">
            <i class="bi bi-search"></i>
            <input v-model.trim="buscar" class="bc-inp" placeholder="Buscar por nombre, código o categoría..." />
          </div>
          <button class="bc-btn" @click="abrirNuevo"><i class="bi bi-plus-lg me-1"></i>Nuevo producto</button>
        </div>
        <div class="bc-resumen">{{ filtrados.length }} producto(s) · {{ fmtCant(totalUnidades) }} unidad(es) en bodega</div>

        <div v-if="cargandoProductos" class="bc-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
        <div v-else-if="!filtrados.length" class="bc-vacio">
          <i class="bi bi-box-seam"></i>
          <p>{{ productos.length ? 'Sin resultados para la búsqueda.' : 'La bodega está vacía. Cree productos o importe el catálogo de una sede.' }}</p>
        </div>

        <div v-else class="bc-lista">
          <article v-for="p in filtrados" :key="p.id" class="bc-prod" :class="{ 'bc-prod--inactivo': p.active }">
            <div class="bc-prod-main">
              <div class="bc-prod-nombre">{{ p.name }}</div>
              <div class="bc-prod-meta">
                <span><i class="bi bi-upc"></i> {{ p.product_code || '—' }}</span>
                <span><i class="bi bi-tag"></i> {{ p.categoria || 'Sin categoría' }}</span>
                <span v-if="p.proveedor"><i class="bi bi-truck"></i> {{ p.proveedor }}</span>
                <span v-if="p.extra_print" class="bc-chip bc-chip--imei">Desactivar al vender</span>
              </div>
              <div v-if="p.sedes.length" class="bc-prod-sedes">
                <span v-for="s in p.sedes" :key="s.sede_id" class="bc-chip" :class="`bc-chip--${s.estado.toLowerCase()}`">{{ s.sede }}</span>
              </div>
            </div>
            <div class="bc-prod-nums">
              <div><small>Venta</small><b>{{ fmt(p.price) }}</b></div>
              <div><small>Mínimo</small><b>{{ fmt(p.wholesale_price) }}</b></div>
              <div><small>Costo</small><b>{{ fmt(p.product_cost) }}</b></div>
              <div class="bc-stock" :class="{ 'bc-stock--cero': p.stock <= 0 }"><small>Stock</small><b>{{ fmtCant(p.stock) }}</b></div>
            </div>
            <div class="bc-prod-acc">
              <button v-if="!(info.cargue_unitario && p.extra_print)" class="bc-btn-sm" @click="abrirEntrada(p)">
                <i class="bi bi-box-arrow-in-down"></i> Entrada
              </button>
              <button v-if="info.cargue_unitario" class="bc-btn-sm bc-btn-sm--imei" @click="abrirReplicar(p)">
                <i class="bi bi-copy"></i> Replicar
              </button>
            </div>
          </article>
        </div>
      </section>

      <!-- ── Importar datos de una sede ── -->
      <section v-if="tab === 'importar'" class="bc-card bc-card--angosta">
        <h3 class="bc-card-ttl"><i class="bi bi-cloud-download"></i> Importar datos de una sede</h3>
        <p class="bc-help">
          Escoja la sede y los datos que quiere traer a la bodega. Lo que ya existe en la bodega no se duplica
          (categorías y unidades por nombre, proveedores por NIT y nombre, productos por código, clientes por cédula),
          así que puede importar de una sede y luego de otra. Los productos entran con <b>cantidad 0</b> y traen
          con ellos la categoría y el proveedor que usan.
        </p>
        <div class="bc-field">
          <label>Sede</label>
          <select v-model.number="importarSede" class="bc-inp" @change="cargarResumenSede">
            <option :value="0">— Seleccionar —</option>
            <option v-for="s in $ordenAlfa(info.sedes, 'nombre')" :key="s.id" :value="s.id">{{ s.nombre }}</option>
          </select>
        </div>

        <div v-if="cargandoResumen" class="bc-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
        <div v-else-if="importarSede && resumenSede.length" class="bc-datos">
          <label class="bc-dato bc-dato--todo">
            <input type="checkbox" :checked="todosMarcados" @change="marcarTodos($event.target.checked)" />
            <span>Seleccionar todo</span>
          </label>
          <label v-for="d in resumenSede" :key="d.clave" class="bc-dato" :class="{ 'bc-dato--vacio': !d.registros }">
            <input v-model="datosMarcados" type="checkbox" :value="d.clave" :disabled="!d.registros" />
            <span class="bc-dato-nom">{{ d.nombre }}</span>
            <span class="bc-dato-n">{{ fmtCant(d.registros) }}</span>
            <small v-if="d.clave === 'productos' && d.sin_codigo" class="bc-dato-nota">{{ fmtCant(d.sin_codigo) }} sin código no se importan</small>
            <small v-else-if="!d.registros" class="bc-dato-nota">La sede no tiene registros en la web</small>
          </label>
        </div>

        <button class="bc-btn bc-btn--full" :disabled="!importarSede || !datosMarcados.length || importando" @click="importar">
          <span v-if="importando" class="spinner-border spinner-border-sm me-1"></span>
          <i v-else class="bi bi-cloud-download me-1"></i>Importar {{ datosMarcados.length ? `(${datosMarcados.length})` : '' }}
        </button>

        <div v-if="resultadoImportar" class="bc-res">
          <div class="bc-res-fila bc-res-fila--head"><span>Dato</span><span>Nuevos</span><span>Ya estaban</span><span>Omitidos</span></div>
          <div v-for="r in resultadoImportar" :key="r.clave" class="bc-res-fila">
            <span>{{ r.nombre }}</span><b>{{ fmtCant(r.creados) }}</b><span>{{ fmtCant(r.existentes) }}</span><span>{{ fmtCant(r.omitidos) }}</span>
          </div>
        </div>
      </section>

      <!-- ── Enviar a sedes (administración central) ── -->
      <section v-if="tab === 'enviar'" class="bc-card">
        <p class="bc-help">
          Proveedores, categorías, roles y formas de pago se crean y modifican solo aquí, en la bodega, y se envían a las
          sedes: en cada sede se crea lo que falta y se <b>sobrescribe</b> lo que ya existe (proveedor por NIT o nombre; lo
          demás por nombre, el rol con sus pantallas y permisos). En las sedes quedan de solo consulta.
          <template v-if="envio.tipo === 'formas_pago'"><br>El envío nunca cambia cuál es el EFECTIVO (forma de pago Default) de
          cada sede, y CRÉDITO solo se envía si pide cliente.</template>
        </p>
        <div class="bc-chips">
          <button v-for="t in tiposEnvio" :key="t.clave" class="bc-tab" :class="{ 'bc-tab--on': envio.tipo === t.clave }" @click="cambiarTipoEnvio(t.clave)">
            <i :class="t.icon"></i><span>{{ t.nombre }}</span>
          </button>
          <router-link class="bc-link" :to="tipoEnvio.ruta"><i class="bi bi-pencil-square"></i> Crear o editar {{ tipoEnvio.nombre.toLowerCase() }}</router-link>
        </div>

        <div class="bc-envio">
          <div class="bc-envio-col">
            <div class="bc-search">
              <i class="bi bi-search"></i>
              <input v-model.trim="envio.buscar" class="bc-inp" :placeholder="`Buscar en ${tipoEnvio.nombre.toLowerCase()}...`" />
            </div>
            <div v-if="envio.cargando" class="bc-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
            <div v-else-if="!envio.registros.length" class="bc-vacio"><i class="bi bi-inbox"></i><p>La bodega no tiene {{ tipoEnvio.nombre.toLowerCase() }}. Créelos o impórtelos de una sede.</p></div>
            <div v-else class="bc-datos bc-datos--scroll">
              <label class="bc-dato bc-dato--todo">
                <input type="checkbox" :checked="registrosTodos" @change="marcarRegistros($event.target.checked)" />
                <span>Seleccionar todo ({{ envioFiltrados.length }})</span>
              </label>
              <label v-for="r in envioFiltrados" :key="r.id" class="bc-dato" :class="{ 'bc-dato--vacio': !r.is_active || r.es_admin || r.bloqueado }">
                <input v-model="envio.ids" type="checkbox" :value="r.id" :disabled="r.es_admin || r.bloqueado" />
                <span class="bc-dato-nom">{{ r.name }}</span>
                <span class="bc-dato-n">{{ r.nit || (r.is_active ? '' : 'Inactivo') }}</span>
                <small v-if="r.es_admin" class="bc-dato-nota">El rol administrador no se envía: cada sede conserva el suyo</small>
              </label>
            </div>
          </div>
          <div class="bc-envio-col bc-envio-col--sedes">
            <div class="bc-datos">
              <label class="bc-dato bc-dato--todo">
                <input type="checkbox" :checked="sedesTodas" @change="envio.sedes = $event.target.checked ? info.sedes.map(s => s.id) : []" />
                <span>Todas las sedes</span>
              </label>
              <label v-for="s in $ordenAlfa(info.sedes, 'nombre')" :key="s.id" class="bc-dato">
                <input v-model="envio.sedes" type="checkbox" :value="s.id" />
                <span class="bc-dato-nom">{{ s.nombre }}</span>
                <i class="bi" :class="s.con_escritorio ? 'bi-pc-display' : 'bi-globe'"></i>
              </label>
            </div>
            <button class="bc-btn bc-btn--full" :disabled="!envio.ids.length || !envio.sedes.length || envio.enviando" @click="enviarSedes">
              <span v-if="envio.enviando" class="spinner-border spinner-border-sm me-1"></span>
              <i v-else class="bi bi-send me-1"></i>Enviar {{ envio.ids.length }} a {{ envio.sedes.length }} sede(s)
            </button>
            <div v-if="envio.resultado" class="bc-res">
              <div class="bc-res-fila bc-res-fila--3 bc-res-fila--head"><span>Sede</span><span>Nuevos</span><span>Actualizados</span></div>
              <template v-for="r in envio.resultado" :key="r.sede_id">
                <div class="bc-res-fila bc-res-fila--3">
                  <span>{{ r.sede }}</span><b>{{ fmtCant(r.creados) }}</b><span>{{ fmtCant(r.actualizados) }}</span>
                </div>
                <div v-for="(er, i) in (r.errores || [])" :key="i" class="bc-res-error"><i class="bi bi-exclamation-triangle"></i> {{ er }}</div>
              </template>
            </div>
          </div>
        </div>
      </section>

      <!-- ── Usuarios del grupo ── -->
      <section v-if="tab === 'usuarios'" class="bc-card">
        <p class="bc-help">
          Cada persona entra con su correo y <b>una sola contraseña</b> a las empresas donde tenga acceso, con un rol en cada
          una. Los usuarios se invitan y administran solo aquí; en las sedes quedan de solo consulta.
        </p>
        <div class="bc-toolbar">
          <div class="bc-search">
            <i class="bi bi-search"></i>
            <input v-model.trim="usr.buscar" class="bc-inp" placeholder="Buscar por nombre o correo..." />
          </div>
          <button class="bc-btn" @click="abrirInvitar"><i class="bi bi-person-plus me-1"></i>Invitar usuario</button>
        </div>
        <div v-if="usr.cargando" class="bc-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
        <div v-else-if="!usuariosFiltrados.length" class="bc-vacio"><i class="bi bi-people"></i><p>Sin usuarios.</p></div>
        <div v-else class="bc-lista">
          <article v-for="p in usuariosFiltrados" :key="p.email" class="bc-persona">
            <div class="bc-persona-head">
              <div class="bc-persona-id"><b>{{ p.nombre }}</b><small>{{ p.email }}</small></div>
              <button class="bc-btn-sm" @click="abrirAsignar(p)"><i class="bi bi-plus-lg"></i> Empresa</button>
            </div>
            <div class="bc-accesos">
              <div v-for="e in p.empresas" :key="e.user_id" class="bc-acceso" :class="{ 'bc-acceso--off': !e.activo }">
                <i class="bi" :class="e.es_bodega ? 'bi-boxes' : 'bi-shop'"></i>
                <div class="bc-acceso-txt"><span>{{ e.empresa }}</span><small>{{ e.rol || 'Sin rol' }}{{ e.activo ? '' : ' · inactivo' }}</small></div>
                <button v-if="!e.yo" class="bc-mini" :title="e.activo ? 'Desactivar en esta empresa' : 'Activar en esta empresa'"
                        :disabled="usr.guardando" @click="cambiarEstado(p, e)">
                  <i class="bi" :class="e.activo ? 'bi-toggle-on' : 'bi-toggle-off'"></i>
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <!-- ── Movimientos ── -->
      <section v-if="tab === 'movimientos'" class="bc-card">
        <div v-if="cargandoMov" class="bc-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
        <div v-else-if="!movimientos.length" class="bc-vacio"><i class="bi bi-journal"></i><p>Sin movimientos todavía.</p></div>
        <div v-else class="bc-movs">
          <div v-for="m in movimientos" :key="m.id" class="bc-mov">
            <span class="bc-mov-tipo" :class="`bc-mov-tipo--${m.tipo.toLowerCase()}`">{{ m.tipo }}</span>
            <div class="bc-mov-main">
              <b>{{ m.producto || m.detalle || '—' }}</b>
              <small>
                <template v-if="m.codigo">{{ m.codigo }} · </template>
                <template v-if="m.sede">{{ m.sede }} · </template>
                {{ m.usuario }} · {{ fechaHora(m.created_at) }}
              </small>
              <small v-if="m.producto && m.detalle && m.detalle !== m.producto" class="bc-mov-det">{{ m.detalle }}</small>
            </div>
            <b v-if="m.cantidad" class="bc-mov-cant">+{{ fmtCant(m.cantidad) }}</b>
          </div>
        </div>
      </section>
    </template>

    <!-- ── Modal: nuevo producto ── -->
    <div v-if="modal === 'nuevo'" class="bc-overlay" @click.self="cerrar">
      <div class="bc-modal">
        <div class="bc-modal-head"><b>Nuevo producto</b><button class="bc-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="bc-modal-body">
          <div class="bc-field">
            <label>Nombre *</label>
            <input v-model.trim="nuevo.name" class="bc-inp" maxlength="250" />
          </div>
          <div class="bc-row">
            <div class="bc-field">
              <label>{{ info.cargue_unitario ? 'Código / IMEI' : 'Código' }}</label>
              <input v-model.trim="nuevo.product_code" class="bc-inp" maxlength="60" placeholder="Automático si se deja vacío" />
            </div>
            <div class="bc-field">
              <label>Categoría *</label>
              <select v-model.number="nuevo.category_id" class="bc-inp">
                <option :value="0">— Seleccionar —</option>
                <option v-for="c in $ordenAlfa(info.categorias, 'name')" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
          </div>
          <div class="bc-field">
            <label>Proveedor {{ info.cargue_unitario ? '*' : '' }}</label>
            <select v-model.number="nuevo.id_proveedor" class="bc-inp">
              <option :value="0">{{ info.cargue_unitario ? '— Seleccionar —' : 'VARIOS (por defecto)' }}</option>
              <option v-for="p in $ordenAlfa(info.proveedores, 'name')" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="bc-row">
            <div class="bc-field"><label>Precio venta</label><CurrencyInput v-model="nuevo.price" class="bc-inp bc-num" /></div>
            <div class="bc-field"><label>Precio mínimo</label><CurrencyInput v-model="nuevo.wholesale_price" class="bc-inp bc-num" /></div>
          </div>
          <div class="bc-row">
            <div class="bc-field"><label>Costo</label><CurrencyInput v-model="nuevo.product_cost" class="bc-inp bc-num" /></div>
            <div class="bc-field"><label>IVA %</label><input v-model.number="nuevo.tax" type="number" min="0" max="100" class="bc-inp bc-num" /></div>
          </div>
          <div class="bc-row">
            <div class="bc-field"><label>Stock mínimo</label><input v-model.number="nuevo.minimum_stock" type="number" min="0" class="bc-inp bc-num" /></div>
            <div class="bc-field">
              <label>Cantidad inicial</label>
              <input v-if="!info.cargue_unitario" v-model.number="nuevo.cantidad_inicial" type="number" min="0" step="1" class="bc-inp bc-num" />
              <div v-else class="bc-fijo">1 (cargue unitario)</div>
            </div>
          </div>
          <label class="bc-switch">
            <input v-model="nuevo.extra_print" type="checkbox" :disabled="info.cargue_unitario" />
            Desactivar el producto al venderlo
          </label>
          <label class="bc-switch">
            <input v-model="nuevo.ask_product_description" type="checkbox" />
            Pedir descripción al vender
          </label>
        </div>
        <div class="bc-modal-foot">
          <button class="bc-btn bc-btn--sec" @click="cerrar">Cancelar</button>
          <button class="bc-btn" :disabled="enviando" @click="guardarNuevo">
            <span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Guardar
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal: entrada ── -->
    <div v-if="modal === 'entrada'" class="bc-overlay" @click.self="cerrar">
      <div class="bc-modal bc-modal--sm">
        <div class="bc-modal-head"><b>Entrada a bodega</b><button class="bc-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="bc-modal-body">
          <div class="bc-prod-ref">{{ sel.name }}<small>{{ sel.product_code }} · stock actual {{ fmtCant(sel.stock) }}</small></div>
          <div class="bc-field"><label>Cantidad *</label><input v-model.number="entrada.cantidad" type="number" min="1" step="1" class="bc-inp bc-num" /></div>
          <div class="bc-field"><label>Observación</label><input v-model.trim="entrada.observacion" class="bc-inp" maxlength="200" /></div>
        </div>
        <div class="bc-modal-foot">
          <button class="bc-btn bc-btn--sec" @click="cerrar">Cancelar</button>
          <button class="bc-btn" :disabled="enviando" @click="guardarEntrada">
            <span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Registrar
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal: invitar usuario ── -->
    <div v-if="modal === 'invitar'" class="bc-overlay" @click.self="cerrar">
      <div class="bc-modal">
        <div class="bc-modal-head"><b>Invitar usuario</b><button class="bc-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="bc-modal-body">
          <template v-if="!inv.link">
            <p class="bc-help">Marque las empresas a las que tendrá acceso y su rol en cada una. Se genera un link (válido 48 horas) para que la persona ponga su nombre, correo y contraseña.</p>
            <div class="bc-datos">
              <div v-for="e in rolesEmpresas" :key="e.company_id" class="bc-inv-fila">
                <label class="bc-inv-emp">
                  <input v-model="inv.marcadas" type="checkbox" :value="e.company_id" />
                  <span><i class="bi" :class="e.es_bodega ? 'bi-boxes' : 'bi-shop'"></i> {{ e.nombre }}</span>
                </label>
                <select v-model.number="inv.roles[e.company_id]" class="bc-inp bc-inp--sm" :disabled="!inv.marcadas.includes(e.company_id)">
                  <option :value="0">— Rol —</option>
                  <option v-for="r in $ordenAlfa(e.roles, 'name')" :key="r.id" :value="r.id">{{ r.name }}</option>
                </select>
              </div>
            </div>
          </template>
          <template v-else>
            <p class="bc-help"><i class="bi bi-check-circle-fill text-success"></i> Link generado, válido por 48 horas. Compártalo por WhatsApp o correo.</p>
            <div class="bc-link-box"><span>{{ inv.link }}</span>
              <button class="bc-mini" @click="copiarLink"><i class="bi" :class="inv.copiado ? 'bi-check-lg' : 'bi-clipboard'"></i></button>
            </div>
          </template>
        </div>
        <div class="bc-modal-foot">
          <button class="bc-btn bc-btn--sec" @click="cerrar">{{ inv.link ? 'Cerrar' : 'Cancelar' }}</button>
          <button v-if="!inv.link" class="bc-btn" :disabled="enviando || !inv.marcadas.length" @click="generarInvitacion">
            <span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Generar link
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal: dar acceso a otra empresa ── -->
    <div v-if="modal === 'asignar'" class="bc-overlay" @click.self="cerrar">
      <div class="bc-modal bc-modal--sm">
        <div class="bc-modal-head"><b>Acceso a empresa</b><button class="bc-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="bc-modal-body">
          <div class="bc-prod-ref">{{ asig.persona.nombre }}<small>{{ asig.persona.email }} · entra con su misma contraseña</small></div>
          <div class="bc-field">
            <label>Empresa</label>
            <select v-model.number="asig.empresa" class="bc-inp" @change="asig.rol = 0">
              <option :value="0">— Seleccionar —</option>
              <option v-for="e in rolesEmpresas" :key="e.company_id" :value="e.company_id">{{ e.nombre }}{{ tieneAcceso(asig.persona, e.company_id) ? ' (cambiar rol)' : '' }}</option>
            </select>
          </div>
          <div class="bc-field">
            <label>Rol en esa empresa</label>
            <select v-model.number="asig.rol" class="bc-inp" :disabled="!asig.empresa">
              <option :value="0">— Rol —</option>
              <option v-for="r in $ordenAlfa(rolesDe(asig.empresa), 'name')" :key="r.id" :value="r.id">{{ r.name }}</option>
            </select>
          </div>
        </div>
        <div class="bc-modal-foot">
          <button class="bc-btn bc-btn--sec" @click="cerrar">Cancelar</button>
          <button class="bc-btn" :disabled="enviando || !asig.empresa || !asig.rol" @click="guardarAsignacion">
            <span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Guardar
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal: replicar por IMEI ── -->
    <div v-if="modal === 'replicar'" class="bc-overlay" @click.self="cerrar">
      <div class="bc-modal">
        <div class="bc-modal-head"><b>Replicar producto</b><button class="bc-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="bc-modal-body">
          <div class="bc-prod-ref">{{ sel.name }}<small>{{ sel.product_code }} · {{ fmt(sel.price) }}</small></div>
          <p class="bc-help">Cada réplica es un producto nuevo con el mismo precio, categoría y proveedor, su propio código (IMEI) y cantidad 1.</p>
          <div class="bc-field"><label>Nombre del producto a replicar</label><input v-model.trim="rep.nombre_base" class="bc-inp" maxlength="200" /></div>
          <div v-if="!rep.codigos.length" class="bc-row bc-row--end">
            <div class="bc-field"><label>Cantidad de réplicas</label><input v-model.number="rep.cantidad" type="number" min="1" max="200" step="1" class="bc-inp bc-num" /></div>
            <button class="bc-btn" @click="iniciarReplica"><i class="bi bi-play-fill me-1"></i>Iniciar</button>
          </div>
          <template v-else>
            <div class="bc-resumen">{{ codigosListos }} de {{ rep.codigos.length }} códigos digitados</div>
            <div class="bc-imeis">
              <div v-for="(c, i) in rep.codigos" :key="i" class="bc-imei" :class="{ 'bc-imei--dup': duplicados.has(c.trim()) && c.trim() }">
                <span>{{ i + 1 }}</span>
                <input :ref="el => (imeiRefs[i] = el)" v-model="rep.codigos[i]" class="bc-inp" maxlength="60"
                       :placeholder="`Código replica ${i + 1}`" autocomplete="off" @keydown.enter.prevent="siguienteImei(i)" />
              </div>
            </div>
          </template>
        </div>
        <div class="bc-modal-foot">
          <button class="bc-btn bc-btn--sec" @click="rep.codigos.length ? (rep.codigos = []) : cerrar()">
            {{ rep.codigos.length ? 'Cancelar replicar' : 'Cerrar' }}
          </button>
          <button v-if="rep.codigos.length" class="bc-btn" :disabled="enviando || codigosListos !== rep.codigos.length || duplicados.size > 0" @click="guardarReplica">
            <span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Replicar {{ rep.codigos.length }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'
import CurrencyInput from '@/components/CurrencyInput.vue'

const { moduleName } = useModuleName()
const BASE = '/api/bodega-central'
const MAX_REPLICAS = 200

const loading = ref(true)
const bloqueo = ref('')
const info = ref(null)
// Cada opción del menú "Bodega Central" es una ruta hija (/bodega-central/<sección>), con su propio permiso
const route = useRoute()
const router = useRouter()
const SECCIONES = ['productos', 'importar', 'enviar', 'usuarios', 'movimientos']
const tab = computed(() => (SECCIONES.includes(route.params.seccion) ? route.params.seccion : ''))

function primeraSeccionPermitida() {
  try {
    const menu = JSON.parse(localStorage.getItem('menu') || '[]')
    const rutas = []
    const recorrer = (items) => (items || []).forEach(i => { if (i.route) rutas.push(i.route); recorrer(i.children) })
    recorrer(menu)
    return SECCIONES.find(s => rutas.includes(`/bodega-central/${s}`)) || 'productos'
  } catch { return 'productos' }
}

const productos = ref([])
const cargandoProductos = ref(false)
const buscar = ref('')
const movimientos = ref([])
const cargandoMov = ref(false)
const importarSede = ref(0)
const importando = ref(false)
const resultadoImportar = ref(null)
const resumenSede = ref([])
const cargandoResumen = ref(false)
const datosMarcados = ref([])

// ── Enviar a sedes ──
const tiposEnvio = [
  { clave: 'proveedores', nombre: 'Proveedores', icon: 'bi bi-truck', ruta: '/inventory/suppliers' },
  { clave: 'categorias', nombre: 'Categorías de productos', icon: 'bi bi-tags', ruta: '/pos/categorias' },
  { clave: 'categorias_insumos', nombre: 'Categorías de insumos', icon: 'bi bi-diagram-3', ruta: '/pos/categorias-productos' },
  { clave: 'roles', nombre: 'Roles y permisos', icon: 'bi bi-shield-lock', ruta: '/configuration/roles' },
  { clave: 'formas_pago', nombre: 'Formas de pago', icon: 'bi bi-credit-card-2-front', ruta: '/payment-types' },
]
const envio = ref({ tipo: 'proveedores', registros: [], ids: [], sedes: [], buscar: '', cargando: false, enviando: false, resultado: null })

// ── Usuarios del grupo ──
const usr = ref({ lista: [], buscar: '', cargando: false, guardando: false })
const rolesEmpresas = ref([])
const inv = ref({ marcadas: [], roles: {}, link: '', copiado: false })
const asig = ref({ persona: null, empresa: 0, rol: 0 })

const modal = ref('')
const enviando = ref(false)
const sel = ref(null)
const nuevo = ref({})
const entrada = ref({ cantidad: 1, observacion: '' })
const rep = ref({ nombre_base: '', cantidad: 1, codigos: [], clave: '' })
const imeiRefs = ref([])

// ── Formatos (moneda del asociado) ──
const usuario = (() => { try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} } })()
const fmtMoneda = new Intl.NumberFormat(usuario.locale || 'es-CO', { style: 'currency', currency: usuario.currency_code || 'COP', maximumFractionDigits: 0 })
const fmt = (v) => fmtMoneda.format(Number(v) || 0)
const fmtCant = (v) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 }).format(Number(v) || 0)
const fechaHora = (v) => (v ? new Date(v).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '')
const errorDe = (e, porDefecto) => {
  const d = e?.response?.data?.detail
  return Array.isArray(d) ? 'Revise los valores ingresados' : (d || porDefecto)
}
// Clave de idempotencia: repetir el envío (doble clic, red lenta) no duplica nada en el servidor
const nuevaClave = () => (window.crypto?.randomUUID ? window.crypto.randomUUID()
  : Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join(''))

const filtrados = computed(() => {
  const q = buscar.value.toLowerCase()
  if (!q) return productos.value
  return productos.value.filter(p => [p.name, p.product_code, p.categoria].some(v => (v || '').toLowerCase().includes(q)))
})
const totalUnidades = computed(() => filtrados.value.reduce((s, p) => s + (p.stock > 0 ? p.stock : 0), 0))
const todosMarcados = computed(() => {
  const con = resumenSede.value.filter(d => d.registros)
  return con.length > 0 && con.every(d => datosMarcados.value.includes(d.clave))
})
const tipoEnvio = computed(() => tiposEnvio.find(t => t.clave === envio.value.tipo))
const envioFiltrados = computed(() => {
  const q = envio.value.buscar.toLowerCase()
  return q ? envio.value.registros.filter(r => [r.name, r.nit].some(v => (v || '').toLowerCase().includes(q))) : envio.value.registros
})
const registrosTodos = computed(() => {
  const marcables = envioFiltrados.value.filter(r => !r.es_admin && !r.bloqueado)
  return marcables.length > 0 && marcables.every(r => envio.value.ids.includes(r.id))
})
const sedesTodas = computed(() => info.value?.sedes.length > 0 && info.value.sedes.every(s => envio.value.sedes.includes(s.id)))
const usuariosFiltrados = computed(() => {
  const q = usr.value.buscar.toLowerCase()
  return q ? usr.value.lista.filter(p => [p.nombre, p.email].some(v => (v || '').toLowerCase().includes(q))) : usr.value.lista
})
const codigosListos = computed(() => rep.value.codigos.filter(c => c.trim()).length)
const duplicados = computed(() => {
  const vistos = new Set(), dup = new Set()
  rep.value.codigos.forEach(c => { const k = c.trim(); if (!k) return; if (vistos.has(k)) dup.add(k); vistos.add(k) })
  return dup
})

async function cargar() {
  loading.value = true
  try {
    info.value = (await api.get(BASE)).data
    bloqueo.value = ''
    cargarSeccion()
  } catch (e) {
    if (e?.response?.status === 403) bloqueo.value = errorDe(e, 'La empresa no está habilitada como bodega central')
    else showToast(errorDe(e, 'Error cargando la bodega'), 'error')
  }
  loading.value = false
}

async function cargarProductos() {
  cargandoProductos.value = true
  try { productos.value = (await api.get(`${BASE}/productos`)).data }
  catch (e) { showToast(errorDe(e, 'Error cargando los productos'), 'error') }
  cargandoProductos.value = false
}

async function cargarMovimientos() {
  cargandoMov.value = true
  try { movimientos.value = (await api.get(`${BASE}/movimientos`)).data }
  catch (e) { showToast(errorDe(e, 'Error cargando los movimientos'), 'error') }
  cargandoMov.value = false
}

function cargarSeccion() {
  const k = tab.value
  if (!k || !info.value) return
  if (k === 'productos') cargarProductos()
  if (k === 'movimientos') cargarMovimientos()
  if (k === 'enviar') cargarEnvio()
  if (k === 'usuarios') cargarUsuarios()
}
watch(tab, cargarSeccion)

// ── Usuarios del grupo ──
async function cargarUsuarios() {
  usr.value.cargando = true
  try {
    const [u, r] = await Promise.all([api.get(`${BASE}/usuarios`), api.get(`${BASE}/roles-empresas`)])
    usr.value.lista = u.data
    rolesEmpresas.value = r.data
  } catch (e) { showToast(errorDe(e, 'Error cargando los usuarios'), 'error') }
  usr.value.cargando = false
}

const rolesDe = (cid) => rolesEmpresas.value.find(e => e.company_id === cid)?.roles || []
const tieneAcceso = (p, cid) => !!p?.empresas.some(e => e.company_id === cid)

function abrirInvitar() {
  inv.value = { marcadas: [], roles: Object.fromEntries(rolesEmpresas.value.map(e => [e.company_id, 0])), link: '', copiado: false }
  modal.value = 'invitar'
}

async function generarInvitacion() {
  const asignaciones = inv.value.marcadas.map(c => ({ empresa_id: c, role_id: inv.value.roles[c] || 0 }))
  if (asignaciones.some(a => !a.role_id)) return showToast('Escoja el rol en cada empresa marcada', 'warning')
  enviando.value = true
  try {
    const { data } = await api.post(`${BASE}/invitar`, { asignaciones })
    inv.value.link = `${window.location.origin}/invite/${data.token}`
  } catch (e) { showToast(errorDe(e, 'Error generando la invitación'), 'error') }
  enviando.value = false
}

async function copiarLink() {
  try { await navigator.clipboard.writeText(inv.value.link); inv.value.copiado = true; setTimeout(() => { inv.value.copiado = false }, 2000) }
  catch { showToast('No se pudo copiar, cópielo manualmente', 'warning') }
}

function abrirAsignar(p) {
  asig.value = { persona: p, empresa: 0, rol: 0 }
  modal.value = 'asignar'
}

async function guardarAsignacion() {
  enviando.value = true
  try {
    const { data } = await api.post(`${BASE}/usuarios/asignar`, { email: asig.value.persona.email, empresa_id: asig.value.empresa, role_id: asig.value.rol })
    showToast(data.accion === 'agregado' ? 'Acceso agregado' : 'Rol actualizado', 'success')
    enviando.value = false
    modal.value = ''
    await cargarUsuarios()
  } catch (e) { showToast(errorDe(e, 'Error al guardar el acceso'), 'error') }
  enviando.value = false
}

async function cambiarEstado(p, e) {
  if (e.activo) {
    const { isConfirmed } = await window.Swal.fire({
      title: '¿Desactivar el acceso?', text: `${p.nombre} no podrá entrar a ${e.empresa}. En las demás empresas sigue igual.`,
      icon: 'warning', showCancelButton: true, confirmButtonText: 'Desactivar', cancelButtonText: 'Cancelar',
    })
    if (!isConfirmed) return
  }
  usr.value.guardando = true
  try {
    await api.post(`${BASE}/usuarios/estado`, { user_id: e.user_id, activo: !e.activo })
    e.activo = !e.activo
  } catch (err) { showToast(errorDe(err, 'Error al cambiar el acceso'), 'error') }
  usr.value.guardando = false
}

// ── Enviar a sedes ──
async function cargarEnvio() {
  envio.value.cargando = true
  envio.value.resultado = null
  try { envio.value.registros = (await api.get(`${BASE}/enviar/${envio.value.tipo}`)).data }
  catch (e) { envio.value.registros = []; showToast(errorDe(e, 'Error cargando los datos de la bodega'), 'error') }
  envio.value.cargando = false
}

function cambiarTipoEnvio(clave) {
  envio.value.tipo = clave
  envio.value.ids = []
  envio.value.buscar = ''
  cargarEnvio()
}

function marcarRegistros(marcar) {
  const visibles = envioFiltrados.value.filter(r => !r.es_admin && !r.bloqueado).map(r => r.id)
  envio.value.ids = marcar ? [...new Set([...envio.value.ids, ...visibles])] : envio.value.ids.filter(id => !visibles.includes(id))
}

async function enviarSedes() {
  const e = envio.value
  const nombresSedes = info.value.sedes.filter(s => e.sedes.includes(s.id)).map(s => s.nombre).join(', ')
  const { isConfirmed } = await window.Swal.fire({
    title: '¿Enviar a las sedes?',
    text: `${e.ids.length} ${tipoEnvio.value.nombre.toLowerCase()} a: ${nombresSedes}. Lo que ya exista en la sede se sobrescribe.`,
    icon: 'question', showCancelButton: true, confirmButtonText: 'Enviar', cancelButtonText: 'Cancelar',
  })
  if (!isConfirmed) return
  e.enviando = true
  e.resultado = null
  try {
    const { data } = await api.post(`${BASE}/enviar`, { tipo: e.tipo, ids: e.ids, sedes: e.sedes, clave: nuevaClave() })
    e.resultado = data.resultado
    showToast(data.repetida ? 'Este envío ya se había hecho' : 'Envío terminado', 'success')
  } catch (err) { showToast(errorDe(err, 'Error al enviar a las sedes'), 'error') }
  e.enviando = false
}

function cerrar() { if (!enviando.value) modal.value = '' }

// ── Nuevo producto ──
function abrirNuevo() {
  nuevo.value = {
    name: '', product_code: '', category_id: 0, id_proveedor: 0, price: 0, wholesale_price: 0, product_cost: 0,
    tax: 0, minimum_stock: 0, cantidad_inicial: 0, extra_print: !!info.value.cargue_unitario,
    ask_product_description: false, clave: nuevaClave(),
  }
  modal.value = 'nuevo'
}

async function guardarNuevo() {
  const n = nuevo.value
  if (!n.name) return showToast('Digite el nombre del producto', 'warning')
  if (!n.category_id) return showToast('Escoja la categoría', 'warning')
  if (info.value.cargue_unitario && !n.id_proveedor) return showToast('Escoja el proveedor (obligatorio en cargue unitario)', 'warning')
  if (n.wholesale_price && n.price && n.wholesale_price > n.price) return showToast('El precio mínimo no puede ser mayor que el precio de venta', 'warning')
  enviando.value = true
  try {
    await api.post(`${BASE}/productos`, { ...n, cantidad_inicial: Math.max(0, Math.floor(n.cantidad_inicial || 0)) })
    showToast('Producto creado', 'success')
    enviando.value = false
    modal.value = ''
    await cargarProductos()
  } catch (e) { showToast(errorDe(e, 'Error al crear el producto'), 'error') }
  enviando.value = false
}

// ── Entrada ──
function abrirEntrada(p) {
  sel.value = p
  entrada.value = { cantidad: 1, observacion: '', clave: nuevaClave() }
  modal.value = 'entrada'
}

async function guardarEntrada() {
  const cant = Math.floor(entrada.value.cantidad || 0)
  if (cant < 1) return showToast('La cantidad debe ser mayor a 0', 'warning')
  enviando.value = true
  try {
    await api.post(`${BASE}/entradas`, { dish_id: sel.value.id, cantidad: cant, observacion: entrada.value.observacion, clave: entrada.value.clave })
    showToast('Entrada registrada', 'success')
    enviando.value = false
    modal.value = ''
    await cargarProductos()
  } catch (e) { showToast(errorDe(e, 'Error al registrar la entrada'), 'error') }
  enviando.value = false
}

// ── Replicar (IMEI) ──
function abrirReplicar(p) {
  sel.value = p
  rep.value = { nombre_base: p.name, cantidad: 1, codigos: [], clave: '' }
  modal.value = 'replicar'
}

async function iniciarReplica() {
  const n = Math.floor(rep.value.cantidad || 0)
  if (n < 1 || n > MAX_REPLICAS) return showToast(`La cantidad debe estar entre 1 y ${MAX_REPLICAS}`, 'warning')
  rep.value.codigos = Array.from({ length: n }, () => '')
  rep.value.clave = nuevaClave()
  imeiRefs.value = []
  await nextTick()
  imeiRefs.value[0]?.focus()
}

function siguienteImei(i) {
  const sig = imeiRefs.value[i + 1]
  if (sig) sig.focus()
  else if (codigosListos.value === rep.value.codigos.length && !duplicados.value.size) guardarReplica()
}

async function guardarReplica() {
  enviando.value = true
  try {
    const { data } = await api.post(`${BASE}/replicar/${sel.value.id}`, {
      nombre_base: rep.value.nombre_base, codigos: rep.value.codigos.map(c => c.trim()), clave: rep.value.clave,
    })
    showToast(data.repetida ? 'Esta réplica ya se había registrado' : `${data.creados.length} producto(s) creados con cantidad 1`, 'success')
    enviando.value = false
    modal.value = ''
    await cargarProductos()
  } catch (e) { showToast(errorDe(e, 'Error al replicar'), 'error') }
  enviando.value = false
}

// ── Importar datos de una sede ──
async function cargarResumenSede() {
  resumenSede.value = []
  datosMarcados.value = []
  resultadoImportar.value = null
  if (!importarSede.value) return
  cargandoResumen.value = true
  try { resumenSede.value = (await api.get(`${BASE}/resumen-sede/${importarSede.value}`)).data }
  catch (e) { showToast(errorDe(e, 'Error consultando los datos de la sede'), 'error') }
  cargandoResumen.value = false
}

function marcarTodos(marcar) {
  datosMarcados.value = marcar ? resumenSede.value.filter(d => d.registros).map(d => d.clave) : []
}

async function importar() {
  const sede = info.value.sedes.find(s => s.id === importarSede.value)
  if (!sede || !datosMarcados.value.length) return
  const nombres = resumenSede.value.filter(d => datosMarcados.value.includes(d.clave)).map(d => d.nombre).join(', ')
  const { isConfirmed } = await window.Swal.fire({
    title: '¿Importar a la bodega?',
    text: `De ${sede.nombre}: ${nombres}.`,
    icon: 'question', showCancelButton: true, confirmButtonText: 'Importar', cancelButtonText: 'Cancelar',
  })
  if (!isConfirmed) return
  importando.value = true
  resultadoImportar.value = null
  try {
    const { data } = await api.post(`${BASE}/importar`, { sede_id: sede.id, datos: datosMarcados.value, clave: nuevaClave() })
    resultadoImportar.value = data.resultado
    showToast(data.repetida ? 'Esta importación ya se había hecho' : 'Importación terminada', 'success')
    info.value = (await api.get(BASE)).data
  } catch (e) { showToast(errorDe(e, 'Error al importar'), 'error') }
  importando.value = false
}

onMounted(() => {
  if (!tab.value) { router.replace(`/bodega-central/${primeraSeccionPermitida()}`); }
  cargar()
})
</script>

<style scoped>
.bc-page { padding: 20px 24px 32px; }
.bc-head { margin-bottom: 14px; }
.bc-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.bc-sub { font-size: 13px; color: #64748b; margin: 2px 0 0; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.bc-sedes { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-top: 8px; }
.bc-sedes-lbl { font-size: 12px; font-weight: 700; color: #475569; }
.bc-nota { font-size: 12px; color: #94a3b8; }
.bc-chip { display: inline-flex; align-items: center; gap: 4px; font-size: 11.5px; font-weight: 700; padding: 3px 8px;
  border-radius: 999px; background: #eef2ff; color: #3730a3; white-space: nowrap; }
.bc-chip--imei { background: #fef3c7; color: #92400e; }
.bc-chip--vinculado { background: #dcfce7; color: #166534; }
.bc-chip--pendiente { background: #fef9c3; color: #854d0e; }
.bc-chip--error { background: #fee2e2; color: #991b1b; }
.bc-state { display: flex; justify-content: center; padding: 40px; }
.bc-bloqueo { display: flex; gap: 12px; align-items: flex-start; background: #fffbeb; border: 1px solid #fde68a; color: #92400e;
  border-radius: 12px; padding: 16px; max-width: 640px; }
.bc-bloqueo i { font-size: 22px; }
.bc-bloqueo p { margin: 4px 0 0; font-size: 13px; }

.bc-tab { display: inline-flex; align-items: center; gap: 6px; border: 1.5px solid #cbd5e1; background: #fff; color: #475569;
  border-radius: 10px; padding: 8px 14px; font-weight: 700; font-size: 13.5px; cursor: pointer; white-space: nowrap; }
.bc-tab--on { background: #1e3a5f; border-color: #1e3a5f; color: #fff; }

.bc-card { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.bc-card--angosta { max-width: 640px; }
.bc-card-ttl { font-size: 15px; font-weight: 800; color: #1e3a5f; margin: 0; display: flex; gap: 8px; align-items: center; }
.bc-help { font-size: 13px; color: #475569; margin: 0; line-height: 1.45; }
.bc-toolbar { display: flex; gap: 10px; align-items: center; }
.bc-search { position: relative; flex: 1; }
.bc-search i { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: #94a3b8; }
.bc-search .bc-inp { padding-left: 32px; }
.bc-resumen { font-size: 12.5px; color: #64748b; }
.bc-vacio { text-align: center; color: #94a3b8; padding: 30px 10px; }
.bc-vacio i { font-size: 34px; }

.bc-field { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.bc-field label { font-size: 12px; font-weight: 700; color: #475569; }
.bc-row { display: flex; gap: 10px; }
.bc-row--end { align-items: flex-end; }
.bc-inp { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; color: #1e293b; background: #fff; width: 100%; }
.bc-inp:focus { outline: none; border-color: #1d4ed8; }
.bc-num { text-align: right; }
.bc-fijo { padding: 8px 10px; background: #f8fafc; border-radius: 8px; font-size: 14px; color: #64748b; }
.bc-switch { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #334155; cursor: pointer; }
.bc-switch input { width: 18px; height: 18px; accent-color: #1d4ed8; flex-shrink: 0; }

.bc-btn { display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(90deg,#1e3a5f,#1d4ed8);
  color: #fff; border: none; border-radius: 10px; padding: 9px 16px; font-weight: 700; font-size: 14px; cursor: pointer; white-space: nowrap; }
.bc-btn:disabled { opacity: .55; cursor: not-allowed; }
.bc-btn--sec { background: #e2e8f0; color: #334155; }
.bc-btn--full { width: 100%; }
.bc-btn-sm { display: inline-flex; align-items: center; gap: 5px; border: 1.5px solid #bfdbfe; background: #eff6ff; color: #1d4ed8;
  border-radius: 8px; padding: 6px 10px; font-size: 12.5px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.bc-btn-sm--imei { border-color: #fde68a; background: #fffbeb; color: #92400e; }

.bc-lista { display: flex; flex-direction: column; gap: 8px; }
.bc-prod { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 12px; align-items: center;
  border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; }
.bc-prod--inactivo { opacity: .55; }
.bc-prod-nombre { font-weight: 800; color: #1e293b; font-size: 14px; word-break: break-word; }
.bc-prod-meta { display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 12px; color: #64748b; margin-top: 2px; }
.bc-prod-sedes { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.bc-prod-nums { display: grid; grid-template-columns: repeat(4, minmax(80px, auto)); gap: 10px; text-align: right; }
.bc-prod-nums small { display: block; font-size: 10.5px; color: #94a3b8; font-weight: 700; text-transform: uppercase; }
.bc-prod-nums b { font-size: 13.5px; color: #1e293b; }
.bc-stock b { color: #15803d; }
.bc-stock--cero b { color: #b91c1c; }
.bc-prod-acc { display: flex; flex-direction: column; gap: 6px; }
.bc-prod-ref { font-weight: 800; color: #1e293b; display: flex; flex-direction: column; background: #f8fafc; border-radius: 10px; padding: 8px 10px; }
.bc-prod-ref small { font-weight: 500; color: #64748b; }

.bc-datos { display: flex; flex-direction: column; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; }
.bc-dato { display: grid; grid-template-columns: 20px minmax(0, 1fr) auto; gap: 2px 10px; align-items: center;
  padding: 10px 12px; border-top: 1px solid #f1f5f9; cursor: pointer; font-size: 14px; color: #1e293b; margin: 0; }
.bc-dato:first-child { border-top: none; }
.bc-dato input { width: 18px; height: 18px; accent-color: #1d4ed8; }
.bc-dato--todo { background: #f8fafc; font-weight: 800; grid-template-columns: 20px 1fr; }
.bc-dato--vacio { color: #94a3b8; cursor: default; }
.bc-dato-n { font-weight: 800; color: #1e3a5f; }
.bc-dato--vacio .bc-dato-n { color: #cbd5e1; }
.bc-dato-nota { grid-column: 2 / -1; font-size: 11.5px; color: #94a3b8; }
.bc-chips { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.bc-link { margin-left: auto; font-size: 13px; font-weight: 700; color: #1d4ed8; text-decoration: none; display: inline-flex; gap: 5px; align-items: center; }
.bc-envio { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 14px; align-items: start; }
.bc-envio-col { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.bc-datos--scroll { max-height: 420px; overflow-y: auto; }
.bc-persona { border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; }
.bc-persona-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.bc-persona-id { display: flex; flex-direction: column; min-width: 0; }
.bc-persona-id b { color: #1e293b; font-size: 14px; }
.bc-persona-id small { color: #64748b; font-size: 12px; word-break: break-all; }
.bc-accesos { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 6px; }
.bc-acceso { display: flex; align-items: center; gap: 8px; background: #f8fafc; border-radius: 10px; padding: 6px 8px; }
.bc-acceso > i { color: #1e3a5f; }
.bc-acceso--off { opacity: .55; }
.bc-acceso-txt { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.bc-acceso-txt span { font-size: 12.5px; font-weight: 700; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bc-acceso-txt small { font-size: 11.5px; color: #64748b; }
.bc-mini { border: none; background: none; font-size: 20px; color: #1d4ed8; cursor: pointer; padding: 0 2px; line-height: 1; }
.bc-acceso--off .bc-mini { color: #94a3b8; }
.bc-inv-fila { display: grid; grid-template-columns: minmax(0, 1fr) 180px; gap: 8px; align-items: center; padding: 8px 12px; border-top: 1px solid #f1f5f9; }
.bc-inv-fila:first-child { border-top: none; }
.bc-inv-emp { display: flex; align-items: center; gap: 8px; margin: 0; font-size: 14px; cursor: pointer; min-width: 0; }
.bc-inv-emp input { width: 18px; height: 18px; accent-color: #1d4ed8; flex-shrink: 0; }
.bc-inp--sm { padding: 6px 8px; font-size: 13px; }
.bc-link-box { display: flex; align-items: center; gap: 8px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px 10px; }
.bc-link-box span { flex: 1; font-size: 12.5px; word-break: break-all; color: #1e293b; }
.bc-res-error { padding: 4px 12px 8px; font-size: 12px; color: #b45309; }
.bc-res-fila--3 { grid-template-columns: minmax(0, 1fr) repeat(2, 90px); }
.bc-res { border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; font-size: 13.5px; }
.bc-res-fila { display: grid; grid-template-columns: minmax(0, 1fr) repeat(3, 80px); gap: 8px; padding: 8px 12px;
  border-top: 1px solid #f1f5f9; text-align: right; }
.bc-res-fila span:first-child { text-align: left; }
.bc-res-fila--head { background: #f8fafc; font-size: 11.5px; font-weight: 800; color: #64748b; border-top: none; }
.bc-res-fila b { color: #15803d; }
.bc-resultado { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.bc-resultado div { background: #f8fafc; border-radius: 10px; padding: 10px; text-align: center; display: flex; flex-direction: column; }
.bc-resultado b { font-size: 20px; color: #1e3a5f; }
.bc-resultado small { font-size: 11.5px; color: #64748b; }

.bc-movs { display: flex; flex-direction: column; }
.bc-mov { display: flex; gap: 10px; align-items: center; padding: 8px 0; border-bottom: 1px solid #f1f5f9; }
.bc-mov-tipo { font-size: 10.5px; font-weight: 800; padding: 3px 7px; border-radius: 6px; background: #e2e8f0; color: #334155; flex-shrink: 0; }
.bc-mov-tipo--entrada, .bc-mov-tipo--replica { background: #dcfce7; color: #166534; }
.bc-mov-tipo--importacion { background: #e0e7ff; color: #3730a3; }
.bc-mov-main { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.bc-mov-main b { font-size: 13.5px; color: #1e293b; word-break: break-word; }
.bc-mov-main small { font-size: 12px; color: #64748b; }
.bc-mov-det { color: #94a3b8 !important; }
.bc-mov-cant { color: #15803d; }

.bc-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.5); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 16px; }
.bc-modal { background: #fff; border-radius: 14px; width: 100%; max-width: 560px; max-height: 92vh; display: flex; flex-direction: column; }
.bc-modal--sm { max-width: 420px; }
.bc-modal-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; border-bottom: 1px solid #e2e8f0; }
.bc-modal-head b { font-size: 16px; color: #1e293b; }
.bc-x { border: none; background: none; font-size: 18px; color: #64748b; cursor: pointer; }
.bc-modal-body { padding: 14px 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.bc-modal-foot { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 16px; border-top: 1px solid #e2e8f0; }

.bc-imeis { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
.bc-imei { display: flex; align-items: center; gap: 6px; }
.bc-imei span { width: 26px; text-align: right; font-size: 12px; color: #94a3b8; font-weight: 700; flex-shrink: 0; }
.bc-imei--dup .bc-inp { border-color: #dc2626; background: #fef2f2; }

@media (max-width: 1024px) {
  .bc-prod { grid-template-columns: minmax(0, 1fr) auto; }
  .bc-prod-nums { grid-column: 1 / -1; grid-template-columns: repeat(4, 1fr); text-align: left; }
  .bc-prod-acc { grid-row: 1; grid-column: 2; }
}
@media (max-width: 768px) {
  .bc-page { padding: 14px 12px 80px; }
  .bc-envio { grid-template-columns: 1fr; }
  .bc-link { margin-left: 0; }
  .bc-datos--scroll { max-height: 320px; }
  .bc-toolbar { flex-direction: column; align-items: stretch; }
  .bc-card--angosta { max-width: none; }
  .bc-imeis { grid-template-columns: 1fr; }
  .bc-overlay { align-items: flex-end; padding: 0; }
  .bc-modal { max-width: none; border-radius: 14px 14px 0 0; max-height: 94vh; }
}
@media (max-width: 576px) {
  .bc-title { font-size: 18px; }
  .bc-inv-fila { grid-template-columns: 1fr; }
  .bc-accesos { grid-template-columns: 1fr; }
  .bc-row { flex-direction: column; gap: 10px; }
  .bc-row--end { align-items: stretch; }
  .bc-prod { grid-template-columns: 1fr; }
  .bc-prod-acc { grid-row: auto; grid-column: auto; flex-direction: row; }
  .bc-prod-acc .bc-btn-sm { flex: 1; justify-content: center; }
  .bc-prod-nums { grid-template-columns: repeat(2, 1fr); }
  .bc-resultado { grid-template-columns: repeat(2, 1fr); }
  .bc-res-fila { grid-template-columns: minmax(0, 1fr) repeat(3, 58px); font-size: 12.5px; padding: 8px 10px; }
  .bc-tab span { font-size: 12.5px; }
  .bc-card { padding: 12px; }
}
</style>
