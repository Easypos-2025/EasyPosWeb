Attribute VB_Name = "modSyncAll"
Option Explicit

' ============================================================
' modSyncAll.bas
' Sincronización completa VB6 -> EasyPosWeb API
' Llama a SincronizarTodo() desde el timer del formulario
' ============================================================

' ── Configuración ────────────────────────────────────────────
Public Const API_BASE   As String = "https://easyposweb.com/api/pos"
Public Const API_KEY    As String = "easypos-sync-key-2024"
Public Const COMPANY_ID As Long   = 3      ' ID de tu empresa en EasyPosWeb
Public Const BATCH_SIZE As Integer = 50    ' Registros por lote


' ════════════════════════════════════════════════════════════
' FUNCIÓN PRINCIPAL — llámala desde el timer
' ════════════════════════════════════════════════════════════
Public Sub SincronizarTodo(lblEstado As Label)
    ' Tablas transaccionales (tienen Enviada_MySql)
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

    ' Tablas transaccionales de productos en comandas
    SyncDetalleComandaProducto lblEstado
    SyncRecibosDetalleComandaProducto lblEstado

    ' Tablas catálogo (se sincronizan completas, sin filtro)
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

    lblEstado.Caption = "Sync completo: " & Now()
End Sub


' ════════════════════════════════════════════════════════════
' HTTP HELPERS
' ════════════════════════════════════════════════════════════
Public Function ApiPost(ByVal endpoint As String, ByVal jsonBody As String) As String
    On Error GoTo ErrHandler
    Dim http As Object
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.Open "POST", API_BASE & endpoint, False
    http.SetRequestHeader "X-Api-Key", API_KEY
    http.SetRequestHeader "Content-Type", "application/json"
    http.Send jsonBody
    If http.Status = 200 Then ApiPost = http.ResponseText
    Exit Function
ErrHandler:
    ApiPost = ""
End Function

Public Function ApiGet(ByVal endpoint As String) As String
    On Error GoTo ErrHandler
    Dim http As Object
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.Open "GET", API_BASE & endpoint, False
    http.SetRequestHeader "X-Api-Key", API_KEY
    http.Send
    If http.Status = 200 Then ApiGet = http.ResponseText
    Exit Function
ErrHandler:
    ApiGet = ""
End Function

' Retorna lista de IDs guardados: 'A','B','C'
Public Function ParseSaved(ByVal json As String) As String
    On Error GoTo ErrHandler
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"
    sc.ExecuteStatement "var r = " & json & ";"
    Dim total As Integer
    total = sc.Eval("r.saved.length")
    Dim i As Integer, result As String
    For i = 0 To total - 1
        If result <> "" Then result = result & ","
        result = result & "'" & sc.Eval("r.saved[" & i & "]") & "'"
    Next i
    ParseSaved = result
    Exit Function
ErrHandler:
    ParseSaved = ""
End Function

' Retorna total_saved del JSON de respuesta
Public Function TotalSaved(ByVal json As String) As Integer
    On Error GoTo ErrHandler
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"
    sc.ExecuteStatement "var r = " & json & ";"
    TotalSaved = CInt(sc.Eval("r.total_saved"))
    Exit Function
ErrHandler:
    TotalSaved = 0
End Function

' Escapa caracteres especiales para JSON
Public Function EscJson(ByVal s As Variant) As String
    If IsNull(s) Or IsEmpty(s) Then
        EscJson = ""
        Exit Function
    End If
    Dim r As String
    r = CStr(s)
    r = Replace(r, "\", "\\")
    r = Replace(r, """", "\""")
    r = Replace(r, Chr(13), "\r")
    r = Replace(r, Chr(10), "\n")
    EscJson = r
End Function

Public Function Nz(ByVal val As Variant, ByVal def As Variant) As Variant
    If IsNull(val) Or IsEmpty(val) Then Nz = def Else Nz = val
End Function

Public Function FechaSQL(ByVal d As Variant) As String
    If IsNull(d) Or IsEmpty(d) Then
        FechaSQL = ""
    Else
        FechaSQL = Format(d, "YYYY-MM-DD")
    End If
End Function


' ════════════════════════════════════════════════════════════
' 1. FACTURAS
' ════════════════════════════════════════════════════════════
Private Sub SyncFacturas(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando facturas..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM facturas WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """invoice_number"":""" & EscJson(rs("Nro_Factura")) & ""","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """date"":""" & FechaSQL(rs("Fecha")) & ""","
        json = json & """cash_amount"":" & Nz(rs("Valor_Efectivo"), 0) & ","
        json = json & """discount"":" & Nz(rs("Descuento"), 0) & ","
        json = json & """customer_id"":" & Nz(rs("Id_Cliente"), 0) & ","
        json = json & """employee_id"":" & Nz(rs("Empleado"), 0) & ","
        json = json & """voided"":" & Nz(rs("Anulada"), 0) & ","
        json = json & """paid_vat"":" & Nz(rs("Pago_Iva"), 0) & ","
        json = json & """credit_card_amount"":" & Nz(rs("Valor_T_Credito"), 0) & ","
        json = json & """debit_card_amount"":" & Nz(rs("Valor_T_Debito"), 0) & ","
        json = json & """tip"":" & Nz(rs("Propina"), 0) & ","
        json = json & """shift"":" & Nz(rs("Turno"), 0) & ","
        json = json & """extra_tip"":" & Nz(rs("Propina_Extra"), 0) & ","
        json = json & """amount_without_tip"":" & Nz(rs("Valor_Sin_Propina"), 0) & ","
        json = json & """currency_type_id"":" & Nz(rs("Tipo_Moneda"), 0) & ","
        json = json & """delivery_invoice"":" & Nz(rs("Factura_Domicilio"), 0)
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/invoices", json)
    If resp = "" Then GoTo Salir

    Dim saved As String: saved = ParseSaved(resp)
    If saved <> "" Then
        conn.Execute "UPDATE facturas SET Enviada_MySql=1 WHERE Nro_Factura IN (" & saved & ")"
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 2. RECIBOS
' ════════════════════════════════════════════════════════════
Private Sub SyncRecibos(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando recibos..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """receipt_number"":""" & EscJson(rs("Nro_Factura")) & ""","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """date"":""" & FechaSQL(rs("Fecha")) & ""","
        json = json & """cash_amount"":" & Nz(rs("Valor_Efectivo"), 0) & ","
        json = json & """discount"":" & Nz(rs("Descuento"), 0) & ","
        json = json & """customer_id"":" & Nz(rs("Id_Cliente"), 0) & ","
        json = json & """employee_id"":" & Nz(rs("Empleado"), 0) & ","
        json = json & """voided"":" & Nz(rs("Anulada"), 0) & ","
        json = json & """credit_card_amount"":" & Nz(rs("Valor_T_Credito"), 0) & ","
        json = json & """debit_card_amount"":" & Nz(rs("Valor_T_Debito"), 0) & ","
        json = json & """tip"":" & Nz(rs("Propina"), 0) & ","
        json = json & """shift"":" & Nz(rs("Turno"), 0) & ","
        json = json & """extra_tip"":" & Nz(rs("Propina_Extra"), 0) & ","
        json = json & """amount_without_tip"":" & Nz(rs("Valor_Sin_Propina"), 0) & ","
        json = json & """currency_type_id"":" & Nz(rs("Tipo_Moneda"), 0) & ","
        json = json & """delivery_receipt"":" & Nz(rs("Factura_Domicilio"), 0)
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/receipts", json)
    If resp = "" Then GoTo Salir

    Dim saved As String: saved = ParseSaved(resp)
    If saved <> "" Then
        conn.Execute "UPDATE recibos SET Enviada_MySql=1 WHERE Nro_Factura IN (" & saved & ")"
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 3. COMANDAS (orders)
' ════════════════════════════════════════════════════════════
Private Sub SyncComandas(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando comandas..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM comanda WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Dim keys As String
    Do While Not rs.EOF
        Dim nroPedido As String: nroPedido = EscJson(rs("Nro_Pedido"))
        Dim fecha As String:     fecha = FechaSQL(rs("Fecha"))
        Dim nroFac As String:    nroFac = EscJson(rs("Nro_Factura"))

        json = json & sep & "{"
        json = json & """order_number"":""" & nroPedido & ""","
        json = json & """date"":""" & fecha & ""","
        json = json & """invoice_number"":""" & nroFac & ""","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """table_name"":""" & EscJson(Nz(rs("Mesa"), "0")) & ""","
        json = json & """time"":""" & EscJson(Nz(rs("Hora"), "")) & ""","
        json = json & """waiter_id"":" & Nz(rs("Mesero"), 0) & ","
        json = json & """cancelled"":" & Nz(rs("Cancelado"), 0) & ","
        json = json & """amount"":" & Nz(rs("Valor"), 0) & ","
        json = json & """notes"":""" & EscJson(Nz(rs("Novedad"), "")) & ""","
        json = json & """complimentary"":" & Nz(rs("Cortesia"), 0) & ","
        json = json & """guests_count"":" & Nz(rs("Nro_Comenzales"), 0) & ","
        json = json & """delivery"":" & Nz(rs("Domicilio"), 0) & ","
        json = json & """customer_id"":" & Nz(rs("Id_Cliente"), 0) & ","
        json = json & """table_id"":" & Nz(rs("Id_Mesa"), 0)
        json = json & "}": sep = ","

        ' Guardar clave compuesta para UPDATE posterior
        If keys <> "" Then keys = keys & " OR "
        keys = keys & "(Nro_Pedido='" & nroPedido & "' AND Fecha='" & fecha & "' AND Nro_Factura='" & nroFac & "')"
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/orders", json)
    If resp = "" Then GoTo Salir

    If TotalSaved(resp) > 0 And keys <> "" Then
        conn.Execute "UPDATE comanda SET Enviada_MySql=1 WHERE " & keys
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 4. DETALLE COMANDA (order_details)
' ════════════════════════════════════════════════════════════
Private Sub SyncDetalleComanda(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando detalle comanda..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM detalle_comanda WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, keys As String
    json = "[": sep = ""
    Do While Not rs.EOF
        Dim nroPedido As String: nroPedido = EscJson(rs("Nro_pedido"))
        Dim fecha As String:     fecha = FechaSQL(rs("Fecha"))
        Dim nroFac As String:    nroFac = EscJson(rs("Nro_Factura"))
        Dim dishId As Long:      dishId = Nz(rs("Id_Plato"), 0)
        Dim itm As Long:         itm = Nz(rs("Item"), 0)
        Dim dep As Long:         dep = Nz(rs("Depende"), 0)

        json = json & sep & "{"
        json = json & """order_number"":""" & nroPedido & ""","
        json = json & """date"":""" & fecha & ""","
        json = json & """invoice_number"":""" & nroFac & ""","
        json = json & """dish_id"":" & dishId & ","
        json = json & """item"":" & itm & ","
        json = json & """depends_on"":" & dep & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """quantity"":" & Nz(rs("Cantidad"), 0) & ","
        json = json & """amount"":" & Nz(rs("Valor"), 0) & ","
        json = json & """notes"":""" & EscJson(Nz(rs("Novedad"), "")) & ""","
        json = json & """complimentary"":" & Nz(rs("Cortesia"), 0) & ","
        json = json & """dish_discount_pct"":" & Nz(rs("Porc_Descuento_Plato"), 0) & ","
        json = json & """general_discount_pct"":" & Nz(rs("Porc_Descuento_General"), 0) & ","
        json = json & """seat_number"":" & Nz(rs("Nro_Puesto"), 0) & ","
        json = json & """pays_tax"":" & Nz(rs("Paga_Impuesto"), 0) & ","
        json = json & """tax"":" & Nz(rs("Impuesto"), 0) & ","
        json = json & """original_tax"":" & Nz(rs("Impuesto_Original"), 0) & ","
        json = json & """pays_dish"":" & Nz(rs("Paga_Plato"), 0)
        json = json & "}": sep = ","

        If keys <> "" Then keys = keys & " OR "
        keys = keys & "(Nro_pedido='" & nroPedido & "' AND Fecha='" & fecha & "' AND Nro_Factura='" & nroFac & "' AND Id_Plato=" & dishId & " AND Item=" & itm & " AND Depende=" & dep & ")"
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/order-details", json)
    If TotalSaved(resp) > 0 And keys <> "" Then
        conn.Execute "UPDATE detalle_comanda SET Enviada_MySql=1 WHERE " & keys
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 5. DETALLE FACTURA (invoice_details)
' ════════════════════════════════════════════════════════════
Private Sub SyncDetalleFactura(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando detalle factura..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM detalle_factura WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, keys As String
    json = "[": sep = ""
    Do While Not rs.EOF
        Dim nroFac As String:    nroFac = EscJson(rs("Nro_Factura"))
        Dim nroPed As String:    nroPed = EscJson(rs("Nro_Pedido"))
        Dim fecha As String:     fecha = FechaSQL(rs("Fecha"))
        Dim dishId As Long:      dishId = Nz(rs("Id_Plato"), 0)
        Dim itm As Long:         itm = Nz(rs("Item"), 0)
        Dim dep As Long:         dep = Nz(rs("Depende"), 0)

        json = json & sep & "{"
        json = json & """invoice_number"":""" & nroFac & ""","
        json = json & """order_number"":""" & nroPed & ""","
        json = json & """date"":""" & fecha & ""","
        json = json & """dish_id"":" & dishId & ","
        json = json & """item"":" & itm & ","
        json = json & """depends_on"":" & dep & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """quantity"":" & Nz(rs("Cantidad"), 0) & ","
        json = json & """notes"":""" & EscJson(Nz(rs("Novedad"), "")) & ""","
        json = json & """dish_amount"":" & Nz(rs("Valor_Plato"), 0) & ","
        json = json & """complimentary"":" & Nz(rs("Cortesia"), 0) & ","
        json = json & """discount_pct"":" & Nz(rs("Porc_Descuento"), 0)
        json = json & "}": sep = ","

        If keys <> "" Then keys = keys & " OR "
        keys = keys & "(Nro_Factura='" & nroFac & "' AND Nro_Pedido='" & nroPed & "' AND Fecha='" & fecha & "' AND Id_Plato=" & dishId & " AND Item=" & itm & " AND Depende=" & dep & ")"
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/invoice-details", json)
    If TotalSaved(resp) > 0 And keys <> "" Then
        conn.Execute "UPDATE detalle_factura SET Enviada_MySql=1 WHERE " & keys
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 6. FACTURA FORMA PAGO (invoice_payments)
' ════════════════════════════════════════════════════════════
Private Sub SyncFacturaFormaPago(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando formas de pago factura..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM factura_forma_pago WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, keys As String
    json = "[": sep = ""
    Do While Not rs.EOF
        Dim itm As Long:     itm = Nz(rs("Item"), 0)
        Dim pmId As Long:    pmId = Nz(rs("Id_Forma_Pago"), 0)
        Dim cardId As Long:  cardId = Nz(rs("Id_Tarjeta"), 0)
        Dim nroFac As String: nroFac = EscJson(rs("Nro_Factura"))

        json = json & sep & "{"
        json = json & """item"":" & itm & ","
        json = json & """payment_method_id"":" & pmId & ","
        json = json & """card_id"":" & cardId & ","
        json = json & """invoice_number"":""" & nroFac & ""","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """amount"":" & Nz(rs("Valor"), 0) & ","
        json = json & """date"":""" & FechaSQL(rs("Fecha")) & ""","
        json = json & """authorization"":" & Nz(rs("Autorizacion"), 0) & ","
        json = json & """notes"":""" & EscJson(Nz(rs("Observacion"), "")) & ""","
        json = json & """delivery_amount"":" & Nz(rs("Valor_Domicilio"), 0) & ","
        json = json & """prefix"":""" & EscJson(Nz(rs("Prefix"), "")) & ""","
        json = json & """order_number"":""" & EscJson(Nz(rs("Nro_Pedido"), "")) & """"
        json = json & "}": sep = ","

        If keys <> "" Then keys = keys & " OR "
        keys = keys & "(Item=" & itm & " AND Id_Forma_Pago=" & pmId & " AND Id_Tarjeta=" & cardId & " AND Nro_Factura='" & nroFac & "')"
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/invoice-payments", json)
    If TotalSaved(resp) > 0 And keys <> "" Then
        conn.Execute "UPDATE factura_forma_pago SET Enviada_MySql=1 WHERE " & keys
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 7. RECIBOS COMANDA (receipt_orders)
' ════════════════════════════════════════════════════════════
Private Sub SyncRecibosComanda(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando recibos comanda..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos_comanda WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, keys As String
    json = "[": sep = ""
    Do While Not rs.EOF
        Dim nroPed As String: nroPed = EscJson(rs("Nro_Pedido"))
        Dim fecha As String:  fecha = FechaSQL(rs("Fecha"))
        Dim nroFac As String: nroFac = EscJson(rs("Nro_Factura"))

        json = json & sep & "{"
        json = json & """order_number"":""" & nroPed & ""","
        json = json & """date"":""" & fecha & ""","
        json = json & """receipt_number"":""" & nroFac & ""","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """table_name"":""" & EscJson(Nz(rs("Mesa"), "0")) & ""","
        json = json & """time"":""" & EscJson(Nz(rs("Hora"), "")) & ""","
        json = json & """waiter_id"":" & Nz(rs("Mesero"), 0) & ","
        json = json & """cancelled"":" & Nz(rs("Cancelado"), 0) & ","
        json = json & """amount"":" & Nz(rs("Valor"), 0) & ","
        json = json & """notes"":""" & EscJson(Nz(rs("Novedad"), "")) & ""","
        json = json & """complimentary"":" & Nz(rs("Cortesia"), 0) & ","
        json = json & """guests_count"":" & Nz(rs("Nro_Comenzales"), 0) & ","
        json = json & """delivery"":" & Nz(rs("Domicilio"), 0) & ","
        json = json & """customer_id"":" & Nz(rs("Id_Cliente"), 0) & ","
        json = json & """table_id"":" & Nz(rs("Id_Mesa"), 0)
        json = json & "}": sep = ","

        If keys <> "" Then keys = keys & " OR "
        keys = keys & "(Nro_Pedido='" & nroPed & "' AND Fecha='" & fecha & "' AND Nro_Factura='" & nroFac & "')"
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/receipt-orders", json)
    If TotalSaved(resp) > 0 And keys <> "" Then
        conn.Execute "UPDATE recibos_comanda SET Enviada_MySql=1 WHERE " & keys
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 8. RECIBOS DETALLE COMANDA (receipt_order_details)
' ════════════════════════════════════════════════════════════
Private Sub SyncRecibosDetalleComanda(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando recibos detalle comanda..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos_detalle_comanda WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, keys As String
    json = "[": sep = ""
    Do While Not rs.EOF
        Dim nroPed As String: nroPed = EscJson(rs("Nro_pedido"))
        Dim fecha As String:  fecha = FechaSQL(rs("Fecha"))
        Dim nroFac As String: nroFac = EscJson(rs("Nro_Factura"))
        Dim dishId As Long:   dishId = Nz(rs("Id_Plato"), 0)
        Dim itm As Long:      itm = Nz(rs("Item"), 0)
        Dim dep As Long:      dep = Nz(rs("Depende"), 0)

        json = json & sep & "{"
        json = json & """order_number"":""" & nroPed & ""","
        json = json & """date"":""" & fecha & ""","
        json = json & """receipt_number"":""" & nroFac & ""","
        json = json & """dish_id"":" & dishId & ","
        json = json & """item"":" & itm & ","
        json = json & """depends_on"":" & dep & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """quantity"":" & Nz(rs("Cantidad"), 0) & ","
        json = json & """amount"":" & Nz(rs("Valor"), 0) & ","
        json = json & """notes"":""" & EscJson(Nz(rs("Novedad"), "")) & ""","
        json = json & """complimentary"":" & Nz(rs("Cortesia"), 0) & ","
        json = json & """dish_discount_pct"":" & Nz(rs("Porc_Descuento_Plato"), 0) & ","
        json = json & """general_discount_pct"":" & Nz(rs("Porc_Descuento_General"), 0) & ","
        json = json & """pays_tax"":" & Nz(rs("Paga_Impuesto"), 0) & ","
        json = json & """tax"":" & Nz(rs("Impuesto"), 0)
        json = json & "}": sep = ","

        If keys <> "" Then keys = keys & " OR "
        keys = keys & "(Nro_pedido='" & nroPed & "' AND Fecha='" & fecha & "' AND Nro_Factura='" & nroFac & "' AND Id_Plato=" & dishId & " AND Item=" & itm & " AND Depende=" & dep & ")"
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/receipt-order-details", json)
    If TotalSaved(resp) > 0 And keys <> "" Then
        conn.Execute "UPDATE recibos_detalle_comanda SET Enviada_MySql=1 WHERE " & keys
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 9. RECIBOS DETALLE FACTURA (receipt_invoice_details)
' ════════════════════════════════════════════════════════════
Private Sub SyncRecibosDetalleFactura(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando recibos detalle factura..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos_detalle_factura WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, keys As String
    json = "[": sep = ""
    Do While Not rs.EOF
        Dim nroFac As String: nroFac = EscJson(rs("Nro_Factura"))
        Dim nroPed As String: nroPed = EscJson(rs("Nro_Pedido"))
        Dim fecha As String:  fecha = FechaSQL(rs("Fecha"))
        Dim dishId As Long:   dishId = Nz(rs("Id_Plato"), 0)
        Dim itm As Long:      itm = Nz(rs("Item"), 0)
        Dim dep As Long:      dep = Nz(rs("Depende"), 0)

        json = json & sep & "{"
        json = json & """receipt_number"":""" & nroFac & ""","
        json = json & """order_number"":""" & nroPed & ""","
        json = json & """date"":""" & fecha & ""","
        json = json & """dish_id"":" & dishId & ","
        json = json & """item"":" & itm & ","
        json = json & """depends_on"":" & dep & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """quantity"":" & Nz(rs("Cantidad"), 0) & ","
        json = json & """notes"":""" & EscJson(Nz(rs("Novedad"), "")) & ""","
        json = json & """dish_amount"":" & Nz(rs("Valor_Plato"), 0) & ","
        json = json & """complimentary"":" & Nz(rs("Cortesia"), 0) & ","
        json = json & """discount_pct"":" & Nz(rs("Porc_Descuento"), 0)
        json = json & "}": sep = ","

        If keys <> "" Then keys = keys & " OR "
        keys = keys & "(Nro_Factura='" & nroFac & "' AND Nro_Pedido='" & nroPed & "' AND Fecha='" & fecha & "' AND Id_Plato=" & dishId & " AND Item=" & itm & " AND Depende=" & dep & ")"
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/receipt-invoice-details", json)
    If TotalSaved(resp) > 0 And keys <> "" Then
        conn.Execute "UPDATE recibos_detalle_factura SET Enviada_MySql=1 WHERE " & keys
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 10. RECIBOS FORMA PAGO (receipt_payments)
' ════════════════════════════════════════════════════════════
Private Sub SyncRecibosFormaPago(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando formas de pago recibo..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos_forma_pago WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, keys As String
    json = "[": sep = ""
    Do While Not rs.EOF
        Dim itm As Long:     itm = Nz(rs("Item"), 0)
        Dim pmId As Long:    pmId = Nz(rs("Id_Forma_Pago"), 0)
        Dim cardId As Long:  cardId = Nz(rs("Id_Tarjeta"), 0)
        Dim nroFac As String: nroFac = EscJson(rs("Nro_Factura"))

        json = json & sep & "{"
        json = json & """item"":" & itm & ","
        json = json & """payment_method_id"":" & pmId & ","
        json = json & """card_id"":" & cardId & ","
        json = json & """receipt_number"":""" & nroFac & ""","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """amount"":" & Nz(rs("Valor"), 0) & ","
        json = json & """date"":""" & EscJson(Nz(rs("Fecha"), "")) & ""","
        json = json & """authorization"":" & Nz(rs("Autorizacion"), 0) & ","
        json = json & """notes"":""" & EscJson(Nz(rs("Observacion"), "")) & ""","
        json = json & """delivery_amount"":" & Nz(rs("Valor_Domicilio"), 0) & ","
        json = json & """order_number"":""" & EscJson(Nz(rs("Nro_Pedido"), "")) & """"
        json = json & "}": sep = ","

        If keys <> "" Then keys = keys & " OR "
        keys = keys & "(Item=" & itm & " AND Id_Forma_Pago=" & pmId & " AND Id_Tarjeta=" & cardId & " AND Nro_Factura='" & nroFac & "')"
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/receipt-payments", json)
    If TotalSaved(resp) > 0 And keys <> "" Then
        conn.Execute "UPDATE recibos_forma_pago SET Enviada_MySql=1 WHERE " & keys
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 11. CAJAS CIERRES (cash_closings)
' ════════════════════════════════════════════════════════════
Private Sub SyncCajasCierres(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando cierres de caja..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM cajas_cierres WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""
    Do While Not rs.EOF
        Dim idCaja As Long: idCaja = Nz(rs("Id_Caja"), 0)
        json = json & sep & "{"
        json = json & """id_registro"":" & idCaja & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """register_number"":" & Nz(rs("Nro_Caja"), 0) & ","
        json = json & """shift"":" & Nz(rs("Turno"), 0) & ","
        json = json & """date"":""" & FechaSQL(rs("Fecha")) & ""","
        json = json & """base_amount"":" & Nz(rs("Base"), 0) & ","
        json = json & """total_sales"":" & Nz(rs("Venta_Total"), 0) & ","
        json = json & """cash_sales"":" & Nz(rs("Venta_Efectivo"), 0) & ","
        json = json & """voucher_sales"":" & Nz(rs("Venta_Baucher"), 0) & ","
        json = json & """tips"":" & Nz(rs("Propinas"), 0) & ","
        json = json & """extra_tips"":" & Nz(rs("Propinas_Extra"), 0) & ","
        json = json & """expenses"":" & Nz(rs("Gastos"), 0) & ","
        json = json & """vouchers"":" & Nz(rs("Vales"), 0) & ","
        json = json & """manager_consumption"":" & Nz(rs("Consumo_Jefes"), 0) & ","
        json = json & """final_base"":" & Nz(rs("Base_Final"), 0) & ","
        json = json & """total_invoices"":" & Nz(rs("F_Totales"), 0) & ","
        json = json & """voucher_invoices"":" & Nz(rs("F_Baucher"), 0) & ","
        json = json & """copy_invoices"":" & Nz(rs("F_Copias"), 0) & ","
        json = json & """voided_invoices"":" & Nz(rs("F_Anuladas"), 0) & ","
        json = json & """bills"":" & Nz(rs("Billetes"), 0) & ","
        json = json & """coins"":" & Nz(rs("Monedas"), 0) & ","
        json = json & """purchases"":" & Nz(rs("Compras"), 0) & ","
        json = json & """customer_sales"":" & Nz(rs("Venta_Clientes"), 0) & ","
        json = json & """closed"":" & Nz(rs("Cierre"), 0) & ","
        json = json & """invoice_start"":""" & EscJson(Nz(rs("Factura_Inicio"), "")) & ""","
        json = json & """invoice_end"":""" & EscJson(Nz(rs("Factura_Fin"), "")) & ""","
        json = json & """invoice_start_manual"":""" & EscJson(Nz(rs("Factura_Inicio_Manual"), "")) & ""","
        json = json & """invoice_end_manual"":""" & EscJson(Nz(rs("Factura_Fin_Manual"), "")) & ""","
        json = json & """delivery_income"":" & Nz(rs("Ingreso_Domicilio"), 0) & ","
        json = json & """delivery_expense"":" & Nz(rs("Egreso_Domicilio"), 0) & ","
        json = json & """opened_pc"":""" & EscJson(Nz(rs("Pc_Abierta"), "")) & ""","
        json = json & """closing_notes"":""" & EscJson(Nz(rs("Observaciones_Cierre"), "")) & ""","
        json = json & """opening_datetime"":""" & EscJson(Nz(rs("Fecha_Hora_Apertura"), "")) & ""","
        json = json & """closing_datetime"":""" & EscJson(Nz(rs("Fecha_Hora_Cierre"), "")) & """"
        json = json & "}": sep = ","
        idList = idList & idSep & idCaja: idSep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/cash-closings-v2", json)
    If resp = "" Then GoTo Salir

    If idList <> "" Then
        conn.Execute "UPDATE cajas_cierres SET Enviada_MySql=1 WHERE Id_Caja IN (" & idList & ")"
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 12. PLATOS — catálogo completo (sin filtro Enviada_MySql)
' ════════════════════════════════════════════════════════════
Private Sub SyncPlatos(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando platos..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM platos", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":" & rs("Id_Plato") & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """name"":""" & EscJson(Nz(rs("Nombre"), "")) & ""","
        json = json & """product_code"":""" & EscJson(Nz(rs("Codigo_Producto"), "")) & ""","
        json = json & """price"":" & Nz(rs("Valor"), 0) & ","
        json = json & """preparation_time"":" & Nz(rs("Tiempo"), 0) & ","
        json = json & """active"":" & Nz(rs("Activo"), 0) & ","
        json = json & """category_id"":" & Nz(rs("Cod_Categoria"), 0) & ","
        json = json & """tax"":" & Nz(rs("Impuesto"), 0) & ","
        json = json & """wholesale_price"":" & Nz(rs("Precio_x_Mayor"), 0) & ","
        json = json & """product_cost"":" & Nz(rs("Costo_Producto"), 0) & ","
        json = json & """minimum_stock"":" & Nz(rs("Stock_Minimo"), 0) & ","
        json = json & """description"":""" & EscJson(Nz(rs("Descripcion_Plato"), "")) & """"
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/dishes", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 13. EMPLEADOS — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncEmpleados(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando empleados..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM empleados", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":" & rs("cod_empleado") & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """name"":""" & EscJson(Nz(rs("nombres"), "")) & ""","
        json = json & """phone"":""" & EscJson(Nz(rs("telefonos"), "")) & ""","
        json = json & """address"":""" & EscJson(Nz(rs("direccion"), "")) & ""","
        json = json & """login"":""" & EscJson(Nz(rs("login"), "")) & ""","
        json = json & """password"":""" & EscJson(Nz(rs("clave"), "")) & ""","
        json = json & """status"":" & Nz(rs("estado"), 0) & ","
        json = json & """employee_type"":" & Nz(rs("tipo_empleado"), 0)
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/employees", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 14. MESEROS — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncMeseros(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando meseros..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM meseros", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":" & rs("cod_empleado") & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """name"":""" & EscJson(Nz(rs("nombres"), "")) & ""","
        json = json & """phone"":""" & EscJson(Nz(rs("telefonos"), "")) & ""","
        json = json & """address"":""" & EscJson(Nz(rs("direccion"), "")) & ""","
        json = json & """password"":""" & EscJson(Nz(rs("Clave"), "")) & ""","
        json = json & """status"":" & Nz(rs("estado"), 0) & ","
        json = json & """employee_type"":" & Nz(rs("Tipo_Empleado"), 0)
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/waiters", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 16. DETALLE COMANDA PRODUCTO — transaccional (Enviada_MySql)
' ════════════════════════════════════════════════════════════
Private Sub SyncDetalleComandaProducto(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando detalle comanda productos..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM detalle_comanda_producto WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, keys As String
    json = "[": sep = ""
    Do While Not rs.EOF
        Dim nroPedido As String: nroPedido = EscJson(rs("Nro_pedido"))
        Dim fecha As String:     fecha = FechaSQL(rs("Fecha"))
        Dim nroFac As String:    nroFac = EscJson(rs("Nro_Factura"))
        Dim dishId As Long:      dishId = Nz(rs("Id_Plato"), 0)
        Dim itm As Long:         itm = Nz(rs("Item"), 0)
        Dim grpId As Long:       grpId = Nz(rs("Id_Grupo"), 0)
        Dim itmId As Long:       itmId = Nz(rs("Id_Item"), 0)

        json = json & sep & "{"
        json = json & """order_number"":""" & nroPedido & ""","
        json = json & """date"":""" & fecha & ""","
        json = json & """invoice_number"":""" & nroFac & ""","
        json = json & """dish_id"":" & dishId & ","
        json = json & """item"":" & itm & ","
        json = json & """group_id"":" & grpId & ","
        json = json & """item_id"":" & itmId & ","
        json = json & """quantity"":" & Nz(rs("Cantidad"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID
        json = json & "}": sep = ","

        If keys <> "" Then keys = keys & " OR "
        keys = keys & "(Nro_pedido='" & nroPedido & "' AND Fecha='" & fecha & "' AND Nro_Factura='" & nroFac & "' AND Id_Plato=" & dishId & " AND Item=" & itm & " AND Id_Grupo=" & grpId & " AND Id_Item=" & itmId & ")"
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/order-detail-products", json)
    If TotalSaved(resp) > 0 And keys <> "" Then
        conn.Execute "UPDATE detalle_comanda_producto SET Enviada_MySql=1 WHERE " & keys
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 17. RECIBOS DETALLE COMANDA PRODUCTO — transaccional
' ════════════════════════════════════════════════════════════
Private Sub SyncRecibosDetalleComandaProducto(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando recibos detalle comanda productos..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos_detalle_comanda_producto WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, keys As String
    json = "[": sep = ""
    Do While Not rs.EOF
        Dim nroPedido As String: nroPedido = EscJson(rs("Nro_pedido"))
        Dim fecha As String:     fecha = FechaSQL(rs("Fecha"))
        Dim nroFac As String:    nroFac = EscJson(rs("Nro_Factura"))
        Dim dishId As Long:      dishId = Nz(rs("Id_Plato"), 0)
        Dim itm As Long:         itm = Nz(rs("Item"), 0)
        Dim grpId As Long:       grpId = Nz(rs("Id_Grupo"), 0)
        Dim itmId As Long:       itmId = Nz(rs("Id_Item"), 0)

        json = json & sep & "{"
        json = json & """order_number"":""" & nroPedido & ""","
        json = json & """date"":""" & fecha & ""","
        json = json & """receipt_number"":""" & nroFac & ""","
        json = json & """dish_id"":" & dishId & ","
        json = json & """item"":" & itm & ","
        json = json & """group_id"":" & grpId & ","
        json = json & """item_id"":" & itmId & ","
        json = json & """quantity"":" & Nz(rs("Cantidad"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID
        json = json & "}": sep = ","

        If keys <> "" Then keys = keys & " OR "
        keys = keys & "(Nro_pedido='" & nroPedido & "' AND Fecha='" & fecha & "' AND Nro_Factura='" & nroFac & "' AND Id_Plato=" & dishId & " AND Item=" & itm & " AND Id_Grupo=" & grpId & " AND Id_Item=" & itmId & ")"
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/receipt-order-detail-products", json)
    If TotalSaved(resp) > 0 And keys <> "" Then
        conn.Execute "UPDATE recibos_detalle_comanda_producto SET Enviada_MySql=1 WHERE " & keys
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 18. PLATO PRODUCTO — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncPlatoProducto(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando plato_producto..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM plato_producto", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """dish_id"":" & Nz(rs("Id_Plato"), 0) & ","
        json = json & """measure_id"":" & Nz(rs("Id_Forma_Medida"), 0) & ","
        json = json & """supplier_id"":" & Nz(rs("id_proveedor"), 0) & ","
        json = json & """minimum_units"":" & Nz(rs("Unidades_Minimas"), 0) & ","
        json = json & """presentation_value"":" & Nz(rs("Valor_Presentacion"), 0) & ","
        json = json & """description"":""" & EscJson(Nz(rs("Descripcion"), "")) & ""","
        json = json & """active"":" & Nz(rs("Activo"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/dish-products", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 19. PLATO IMPRESORAS — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncPlatoImpresoras(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando plato_impresoras..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM plato_impresoras", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """item_id"":" & Nz(rs("Id_Plato"), 0) & ","
        json = json & """printer_id"":" & Nz(rs("Id_Impresora"), 0) & ","
        json = json & """print_copies"":" & Nz(rs("Cant_Impresiones"), 1) & ","
        json = json & """company_id"":" & COMPANY_ID
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/dish-printers", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 20. PLATO ARMAR — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncPlatoArmar(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando plato_armar..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM plato_armar", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """dish_id"":" & Nz(rs("Id_Plato"), 0) & ","
        json = json & """category_code"":" & Nz(rs("Cod_Categoria"), 0) & ","
        json = json & """max_choices"":" & Nz(rs("Cantidad_Elegir"), 0) & ","
        json = json & """is_active"":" & Nz(rs("Activa"), 0) & ","
        json = json & """is_required"":" & Nz(rs("Exgir_Seleccion"), 0) & ","
        json = json & """print_on_change_only"":" & Nz(rs("Imprimir_Armar_Solo_Cambio"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/dish-assembly", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 21. PLATO ARMAR DETALLE — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncPlatoArmarDetalle(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando plato_armar_detalle..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM plato_armar_detalle", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """dish_id"":" & Nz(rs("Id_Plato"), 0) & ","
        json = json & """category_code"":" & Nz(rs("Cod_Categoria"), 0) & ","
        json = json & """item"":" & Nz(rs("Item"), 0) & ","
        json = json & """position"":" & Nz(rs("Posicion"), 0) & ","
        json = json & """supply_price"":" & Nz(rs("Precio_Insumo"), 0) & ","
        json = json & """discount_qty"":" & Nz(rs("Cantidad_Descontar"), 0) & ","
        json = json & """is_default"":" & Nz(rs("Por_Default"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/dish-assembly-detail", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 22. MENU DIARIO — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncMenuDiario(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando menú diario..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM menu_diario", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """menu_id"":" & Nz(rs("Id_Menu"), 0) & ","
        json = json & """item_id"":" & Nz(rs("Id_Item"), 0) & ","
        json = json & """date"":""" & EscJson(Nz(rs("Fecha"), "")) & ""","
        json = json & """category"":""" & EscJson(Nz(rs("Categoria"), "")) & ""","
        json = json & """description"":""" & EscJson(Nz(rs("Descripcion"), "")) & ""","
        json = json & """group_by"":" & Nz(rs("Agrupar"), 0) & ","
        json = json & """selected"":" & Nz(rs("Seleccionado"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/daily-menu", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 15. MESAS — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncMesas(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando mesas..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM mesas", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":" & rs("Id_Mesa") & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """branch_id"":" & Nz(rs("Id_Sede"), 0) & ","
        json = json & """name"":""" & EscJson(Nz(rs("Mesa"), "")) & ""","
        json = json & """location"":""" & EscJson(Nz(rs("Ubicacion"), "")) & ""","
        json = json & """seats"":" & Nz(rs("Nro_Puestos"), 0) & ","
        json = json & """active"":" & Nz(rs("Activa"), 0) & ","
        json = json & """zone_id"":" & Nz(rs("Id_Zona"), 0)
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/tables", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 23. CAJA FACTURAS — transaccional (Enviada_MySql)
' ════════════════════════════════════════════════════════════
Private Sub SyncCajaFacturas(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando caja facturas..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM caja_facturas WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""
    Do While Not rs.EOF
        Dim nroFac As String: nroFac = EscJson(rs("Nro_Factura"))
        json = json & sep & "{"
        json = json & """register_number"":" & Nz(rs("Nro_Caja"), 0) & ","
        json = json & """closing_id"":" & Nz(rs("Id_Caja"), 0) & ","
        json = json & """invoice_number"":""" & nroFac & ""","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """date"":""" & FechaSQL(rs("Fecha")) & ""","
        json = json & """order_number"":""" & EscJson(Nz(rs("Nro_Pedido"), "")) & ""","
        json = json & """amount"":" & Nz(rs("Valor"), 0) & ","
        json = json & """base_amount"":" & Nz(rs("Base"), 0) & ","
        json = json & """tax_vat"":" & Nz(rs("Impuesto_Iva"), 0) & ","
        json = json & """tax_consumption"":" & Nz(rs("Impuesto_Impoconsumo"), 0) & ","
        json = json & """employee_id"":" & Nz(rs("Empleado"), 0) & ","
        json = json & """shift"":" & Nz(rs("Turno"), 0) & ","
        json = json & """source_pc"":""" & EscJson(Nz(rs("Pc_Desde"), "")) & ""","
        json = json & """delivery_person_id"":" & Nz(rs("Cod_Domiciliario"), 0) & ","
        json = json & """invoice_notes"":""" & EscJson(Nz(rs("Observacion_Factura"), "")) & ""","
        json = json & """prefix"":""" & EscJson(Nz(rs("prefix"), "")) & ""","
        json = json & """fac_pe"":""" & EscJson(Nz(rs("fac_pe"), "")) & """"
        json = json & "}": sep = ","
        idList = idList & idSep & "'" & nroFac & "'": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/cash-register-invoices", json)
    If resp = "" Then GoTo Salir

    If idList <> "" Then
        conn.Execute "UPDATE caja_facturas SET Enviada_MySql=1 WHERE Nro_Factura IN (" & idList & ")"
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 24. CAJA RECIBOS — transaccional (Enviada_MySql)
' ════════════════════════════════════════════════════════════
Private Sub SyncCajaRecibos(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando caja recibos..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM caja_recibos WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""
    Do While Not rs.EOF
        Dim nroRec As String: nroRec = EscJson(rs("Nro_Factura"))
        json = json & sep & "{"
        json = json & """register_number"":" & Nz(rs("Nro_Caja"), 0) & ","
        json = json & """closing_id"":" & Nz(rs("Id_Caja"), 0) & ","
        json = json & """receipt_number"":""" & nroRec & ""","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """date"":""" & FechaSQL(rs("Fecha")) & ""","
        json = json & """order_number"":""" & EscJson(Nz(rs("Nro_Pedido"), "")) & ""","
        json = json & """amount"":" & Nz(rs("Valor"), 0) & ","
        json = json & """base_amount"":" & Nz(rs("Base"), 0) & ","
        json = json & """tax_vat"":" & Nz(rs("Impuesto_Iva"), 0) & ","
        json = json & """tax_consumption"":" & Nz(rs("Impuesto_Impoconsumo"), 0) & ","
        json = json & """employee_id"":" & Nz(rs("Empleado"), 0) & ","
        json = json & """shift"":" & Nz(rs("Turno"), 0) & ","
        json = json & """source_pc"":""" & EscJson(Nz(rs("Pc_Desde"), "")) & ""","
        json = json & """delivery_person_id"":" & Nz(rs("Cod_Domiciliario"), 0) & ","
        json = json & """notes"":""" & EscJson(Nz(rs("Observacion_Factura"), "")) & ""","
        json = json & """prefix"":""" & EscJson(Nz(rs("Prefix"), "")) & ""","
        json = json & """fac_pe"":""" & EscJson(Nz(rs("Fac_PE"), "")) & """"
        json = json & "}": sep = ","
        idList = idList & idSep & "'" & nroRec & "'": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/cash-register-receipts", json)
    If resp = "" Then GoTo Salir

    If idList <> "" Then
        conn.Execute "UPDATE caja_recibos SET Enviada_MySql=1 WHERE Nro_Factura IN (" & idList & ")"
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 25. GASTOS — transaccional (Enviada_MySql)
' ════════════════════════════════════════════════════════════
Private Sub SyncGastos(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando gastos..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM gastos WHERE Enviada_MySql = 0 AND year(Fecha_Gasto) >= 2025 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""
    Do While Not rs.EOF
        Dim idReg As Long: idReg = Nz(rs("Nro_Gasto"), 0)
        json = json & sep & "{"
        json = json & """id_registro"":" & idReg & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """register_id"":" & Nz(rs("Id_Caja"), 0) & ","
        json = json & """date"":""" & FechaSQL(rs("Fecha_Gasto")) & ""","
        json = json & """amount"":" & Nz(rs("Valor_Gasto"), 0) & ","
        json = json & """employee_code"":""" & EscJson(Nz(rs("Cod_Empleado"), "")) & ""","
        json = json & """concept_id"":" & Nz(rs("Cod_Concepto"), 0) & ","
        json = json & """sub_concept_id"":" & Nz(rs("Cod_Sub_Concepto"), 0) & ","
        json = json & """shift"":" & Nz(rs("Turno"), 0) & ","
        json = json & """movement_number"":" & Nz(rs("Nro_Movimiento"), 0) & ","
        json = json & """detail"":""" & EscJson(Nz(rs("Detalle"), "")) & """"
        json = json & "}": sep = ","
        idList = idList & idSep & idReg: idSep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/expenses", json)
    If resp = "" Then GoTo Salir

    If idList <> "" Then
        conn.Execute "UPDATE gastos SET Enviada_MySql=1 WHERE Nro_Gasto IN (" & idList & ")"
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 26. COMPRAS — transaccional (Enviada_MySql)
' ════════════════════════════════════════════════════════════
Private Sub SyncCompras(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando compras..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM compras WHERE Enviada_MySql = 0 AND year(Fecha_Gasto) >= 2025 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""
    Do While Not rs.EOF
        Dim idReg As Long: idReg = Nz(rs("Nro_Gasto"), 0)
        json = json & sep & "{"
        json = json & """id_registro"":" & idReg & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """register_id"":" & Nz(rs("Id_Caja"), 0) & ","
        json = json & """date"":""" & FechaSQL(rs("Fecha_Gasto")) & ""","
        json = json & """amount"":" & Nz(rs("Valor_Gasto"), 0) & ","
        json = json & """employee_code"":""" & EscJson(Nz(rs("Cod_Empleado"), "")) & ""","
        json = json & """concept_id"":" & Nz(rs("Cod_Concepto"), 0) & ","
        json = json & """sub_concept_id"":" & Nz(rs("Cod_Sub_Concepto"), 0) & ","
        json = json & """shift"":" & Nz(rs("Turno"), 0) & ","
        json = json & """movement_number"":" & Nz(rs("Nro_Movimiento"), 0) & ","
        json = json & """detail"":""" & EscJson(Nz(rs("Detalle"), "")) & """"
        json = json & "}": sep = ","
        idList = idList & idSep & idReg: idSep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/purchases", json)
    If resp = "" Then GoTo Salir

    If idList <> "" Then
        conn.Execute "UPDATE compras SET Enviada_MySql=1 WHERE Nro_Gasto IN (" & idList & ")"
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 27. DESCUENTOS — transaccional (Enviada_MySql)
' ════════════════════════════════════════════════════════════
Private Sub SyncDescuentos(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando descuentos..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM descuentos WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""
    Do While Not rs.EOF
        Dim idReg As Long: idReg = Nz(rs("Id_Descuento"), 0)
        json = json & sep & "{"
        json = json & """id_registro"":" & idReg & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """date"":""" & EscJson(Nz(rs("Fecha"), "")) & ""","
        json = json & """prefix"":""" & EscJson(Nz(rs("Prefix"), "")) & ""","
        json = json & """invoice_number"":""" & EscJson(Nz(rs("Factura"), "")) & ""","
        json = json & """dish_id"":" & Nz(rs("Id_Plato"), 0) & ","
        json = json & """item"":" & Nz(rs("Item"), 0) & ","
        json = json & """typification_id"":" & Nz(rs("Id_Tipificacion"), 0) & ","
        json = json & """original_price"":" & Nz(rs("Valor_Original_Producto"), 0) & ","
        json = json & """sale_price"":" & Nz(rs("Valor_Venta_Producto"), 0) & ","
        json = json & """base_value"":" & Nz(rs("Valor_Base"), 0) & ","
        json = json & """tax_value"":" & Nz(rs("Valor_Impuesto"), 0) & ","
        json = json & """discount_amount"":" & Nz(rs("Valor_Descuento_Pesos"), 0) & ","
        json = json & """percentage"":" & Nz(rs("Porcentaje"), 0) & ","
        json = json & """reason"":""" & EscJson(Nz(rs("Motivo"), "")) & ""","
        json = json & """order_number"":""" & EscJson(Nz(rs("Nro_Pedido"), "")) & """"
        json = json & "}": sep = ","
        idList = idList & idSep & idReg: idSep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/discounts", json)
    If resp = "" Then GoTo Salir

    If idList <> "" Then
        conn.Execute "UPDATE descuentos SET Enviada_MySql=1 WHERE Id_Descuento IN (" & idList & ")"
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 28. RECIBOS DESCUENTOS — transaccional (Enviada_MySql)
' ════════════════════════════════════════════════════════════
Private Sub SyncRecibosDescuentos(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando recibos descuentos..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos_descuentos WHERE Enviada_MySql = 0 LIMIT " & BATCH_SIZE, conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""
    Do While Not rs.EOF
        Dim idReg As Long: idReg = Nz(rs("Id_Descuento"), 0)
        json = json & sep & "{"
        json = json & """id_registro"":" & idReg & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """date"":""" & EscJson(Nz(rs("Fecha"), "")) & ""","
        json = json & """prefix"":""" & EscJson(Nz(rs("Prefix"), "")) & ""","
        json = json & """receipt_number"":""" & EscJson(Nz(rs("Factura"), "")) & ""","
        json = json & """dish_id"":" & Nz(rs("Id_Plato"), 0) & ","
        json = json & """item"":" & Nz(rs("Item"), 0) & ","
        json = json & """typification_id"":" & Nz(rs("Id_Tipificacion"), 0) & ","
        json = json & """original_price"":" & Nz(rs("Valor_Original_Producto"), 0) & ","
        json = json & """sale_price"":" & Nz(rs("Valor_Venta_Producto"), 0) & ","
        json = json & """base_value"":" & Nz(rs("Valor_Base"), 0) & ","
        json = json & """tax_value"":" & Nz(rs("Valor_Impuesto"), 0) & ","
        json = json & """discount_amount"":" & Nz(rs("Valor_Descuento_Pesos"), 0) & ","
        json = json & """percentage"":" & Nz(rs("Porcentaje"), 0) & ","
        json = json & """reason"":""" & EscJson(Nz(rs("Motivo"), "")) & ""","
        json = json & """order_number"":""" & EscJson(Nz(rs("Nro_Pedido"), "")) & """"
        json = json & "}": sep = ","
        idList = idList & idSep & idReg: idSep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/receipt-discounts", json)
    If resp = "" Then GoTo Salir

    If idList <> "" Then
        conn.Execute "UPDATE recibos_descuentos SET Enviada_MySql=1 WHERE Id_Descuento IN (" & idList & ")"
    End If

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 29. FORMA PAGO — catálogo completo (sin Enviada_MySql)
' ════════════════════════════════════════════════════════════
Private Sub SyncFormaPago(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando forma pago..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM forma_pago", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":" & Nz(rs("Id_Forma_Pago"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """name"":""" & EscJson(Nz(rs("Descripcion_Forma_Pago"), "")) & ""","
        json = json & """validate_amount"":" & Nz(rs("Validar"), 0) & ","
        json = json & """is_active"":" & Nz(rs("Activo"), 0) & ","
        json = json & """select_card"":" & Nz(rs("Seleccionar_Tarjeta"), 0) & ","
        json = json & """value"":" & Nz(rs("Valor"), 0) & ","
        json = json & """ask_notes"":" & Nz(rs("Pedir_Observacion"), 0) & ","
        json = json & """ask_customer"":" & Nz(rs("Pedir_Cliente"), 0) & ","
        json = json & """adds_to_cash"":" & Nz(rs("Suma_Efectivo"), 0) & ","
        json = json & """validate_number"":" & Nz(rs("Validar_Numero"), 0) & ","
        json = json & """is_default"":" & Nz(rs("Forma_Pago_Default"), 0)
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/payment-types", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 30. FORMA MEDIDA — catálogo completo (sin Enviada_MySql)
' ════════════════════════════════════════════════════════════
Private Sub SyncFormaMedida(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando forma medida..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM forma_medida", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":" & Nz(rs("Id_Forma_Medida"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """name"":""" & EscJson(Nz(rs("Descripcion"), "")) & ""","
        json = json & """is_active"":" & Nz(rs("Activa"), 1)
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/measure-forms", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 31. LISTA PRECIOS CLIENTE — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncListaPreciosCliente(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando lista precios cliente..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM lista_precios_cliente", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id_lista"":" & Nz(rs("id_lista"), 0) & ","
        json = json & """id_cliente"":" & Nz(rs("Id_Cliente"), 0) & ","
        json = json & """id_producto"":" & Nz(rs("Id_Producto"), 0) & ","
        json = json & """id_presentacion"":" & Nz(rs("Id_Presentacion"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """precio_producto"":" & Nz(rs("Precio_Producto"), 0) & ","
        json = json & """fecha"":""" & EscJson(Nz(rs("Fecha"), "")) & ""","
        json = json & """activa"":" & Nz(rs("Activa"), 0)
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/customer-price-list", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 32. NOVEDADES CATEGORIAS — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncNovedadesCategorias(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando novedades categorias..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM novedades_categorias", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id_consecutivo"":" & Nz(rs("Id_Consecutivo"), 0) & ","
        json = json & """cod_categoria"":" & Nz(rs("Cod_Categoria"), 0) & ","
        json = json & """id_novedad"":" & Nz(rs("Id_Novedad"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """name"":""" & EscJson(Nz(rs("Novedad"), "")) & """"
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/dish-note-categories", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 33. NOVEDADES COMENTARIOS — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncNovedadesComentarios(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando novedades comentarios..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM novedades_comentarios", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":" & Nz(rs("Id_Novedad"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """name"":""" & EscJson(Nz(rs("Novedad"), "")) & """"
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/order-notes", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 34. NOVEDADES PRODUCTOS — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncNovedadesProductos(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando novedades productos..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM novedades_productos", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":" & Nz(rs("Id_Novedad"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """name"":""" & EscJson(Nz(rs("Novedad"), "")) & """"
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/product-notes", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub


' ════════════════════════════════════════════════════════════
' 35. INVENTARIO PORCIONES (insumos) — catálogo completo
' ════════════════════════════════════════════════════════════
Private Sub SyncInventarioPorciones(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando inventario porciones..."
    Dim conn As Object: Set conn = GetConn()
    Dim rs As Object:   Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM inventario_porciones", conn

    If rs.EOF Then GoTo Salir

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id_grupo"":" & Nz(rs("Id_Grupo"), 0) & ","
        json = json & """id_item"":" & Nz(rs("Id_Item"), 0) & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """code"":""" & EscJson(Nz(rs("Codigo_Insumo"), "")) & ""","
        json = json & """name"":""" & EscJson(Nz(rs("Descripcion"), "")) & ""","
        json = json & """cost_price"":" & Nz(rs("Costo"), 0) & ","
        json = json & """unit_id"":" & Nz(rs("Und_Compra"), 0) & ","
        json = json & """min_stock"":" & Nz(rs("Stock_MInimo"), 0) & ","
        json = json & """waste_pct"":" & Nz(rs("Porcentaje_Merma"), 0) & ","
        json = json & """control_stock"":" & Nz(rs("Controlar"), 0)
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    ApiPost "/sync/push/supply-items", json

Salir:
    On Error Resume Next: conn.Close: Exit Sub
ErrHandler:
    On Error Resume Next: conn.Close
End Sub
