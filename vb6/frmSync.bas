' ============================================================
' frmSync.frm — Formulario de sincronización
'
' Controles requeridos:
'   tmrSync    Timer   — Interval=300000 (5 min), Enabled=True
'   tmrCatalogo Timer  — Interval=3600000 (1 hora), Enabled=True
'   lblEstado  Label   — muestra el estado actual
'   btnSync    CommandButton — sync manual inmediato
'   btnPrueba  CommandButton — prueba de conexión
' ============================================================
Option Explicit

Private Sub Form_Load()
    tmrSync.Interval    = 300000    ' 5 minutos — tablas transaccionales
    tmrSync.Enabled     = True
    tmrCatalogo.Interval = 3600000  ' 1 hora — catálogos (platos, mesas, etc.)
    tmrCatalogo.Enabled  = True
    lblEstado.Caption = "Sincronización activa - " & Now()

    ' Sync inicial al arrancar
    SyncTransaccional
End Sub

' ── Timer 5 min: tablas con Enviada_MySql ────────────────────
Private Sub tmrSync_Timer()
    SyncTransaccional
End Sub

' ── Timer 1 hora: catálogos sin Enviada_MySql ────────────────
Private Sub tmrCatalogo_Timer()
    SyncCatalogos
End Sub

' ── Botón sync manual completo ───────────────────────────────
Private Sub btnSync_Click()
    SincronizarTodo lblEstado
End Sub

' ── Botón prueba de conexión ─────────────────────────────────
Private Sub btnPrueba_Click()
    Dim resp As String
    resp = ApiGet("/test/users")
    If resp <> "" Then
        MsgBox "Conexion exitosa con EasyPosWeb", vbInformation
    Else
        MsgBox "Sin conexion. Verifica internet o API Key.", vbCritical
    End If
End Sub

' ── Solo tablas transaccionales (rapido, cada 5 min) ─────────
Private Sub SyncTransaccional()
    SyncFacturas lblEstado
    SyncRecibos lblEstado
    SyncComandas lblEstado
    SyncDetalleComanda lblEstado
    SyncDetalleFactura lblEstado
    SyncFacturaFormaPago lblEstado
    SyncRecibosComanda lblEstado
    SyncRecibosDetalleComanda lblEstado
    SyncRecibosDetalleFactura lblEstado
    SyncRecibosFormaPago lblEstado
    SyncCajasCierres lblEstado
    SyncCajaFacturas lblEstado
    SyncCajaRecibos lblEstado
    SyncGastos lblEstado
    SyncCompras lblEstado
    SyncDescuentos lblEstado
    SyncRecibosDescuentos lblEstado
    SyncDetalleComandaProducto lblEstado
    SyncRecibosDetalleComandaProducto lblEstado
    lblEstado.Caption = "Ultima sync: " & Now()
End Sub

' ── Solo catalogos (lento, cada hora) ────────────────────────
Private Sub SyncCatalogos()
    SyncPlatos lblEstado
    SyncPlatoProducto lblEstado
    SyncPlatoImpresoras lblEstado
    SyncPlatoArmar lblEstado
    SyncPlatoArmarDetalle lblEstado
    SyncEmpleados lblEstado
    SyncMeseros lblEstado
    SyncMesas lblEstado
    SyncMenuDiario lblEstado
    SyncFormaPago lblEstado
    SyncFormaMedida lblEstado
    SyncListaPreciosCliente lblEstado
    SyncNovedadesCategorias lblEstado
    SyncNovedadesComentarios lblEstado
    SyncNovedadesProductos lblEstado
    SyncInventarioPorciones lblEstado
    lblEstado.Caption = "Catalogos sync: " & Now()
End Sub
