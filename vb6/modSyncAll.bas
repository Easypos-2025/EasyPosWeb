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

    ' Tablas catálogo (se sincronizan completas, sin filtro)
    SyncPlatos lblEstado
    SyncEmpleados lblEstado
    SyncMeseros lblEstado
    SyncMesas lblEstado

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

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":" & rs("Id_Caja") & ","
        json = json & """company_id"":" & COMPANY_ID & ","
        json = json & """register_number"":" & Nz(rs("Nro_Caja"), 0) & ","
        json = json & """shift"":" & Nz(rs("Turno"), 0) & ","
        json = json & """date"":""" & FechaSQL(rs("Fecha")) & ""","
        json = json & """base_amount"":" & Nz(rs("Base"), 0) & ","
        json = json & """total_sales"":" & Nz(rs("Venta_Total"), 0) & ","
        json = json & """cash_sales"":" & Nz(rs("Venta_Efectivo"), 0) & ","
        json = json & """voucher_sales"":" & Nz(rs("Venta_Baucher"), 0) & ","
        json = json & """tips"":" & Nz(rs("Propinas"), 0) & ","
        json = json & """expenses"":" & Nz(rs("Gastos"), 0) & ","
        json = json & """final_base"":" & Nz(rs("Base_Final"), 0) & ","
        json = json & """total_invoices"":" & Nz(rs("F_Totales"), 0) & ","
        json = json & """voided_invoices"":" & Nz(rs("F_Anuladas"), 0) & ","
        json = json & """closed"":" & Nz(rs("Cierre"), 0) & ","
        json = json & """invoice_start"":""" & EscJson(Nz(rs("Factura_Inicio"), "")) & ""","
        json = json & """invoice_end"":""" & EscJson(Nz(rs("Factura_Fin"), "")) & ""","
        json = json & """opening_datetime"":""" & EscJson(Nz(rs("Fecha_Hora_Apertura"), "")) & ""","
        json = json & """closing_datetime"":""" & EscJson(Nz(rs("Fecha_Hora_Cierre"), "")) & """"
        json = json & "}": sep = ","
        rs.MoveNext
    Loop
    json = json & "]": rs.Close

    Dim resp As String: resp = ApiPost("/sync/push/cash-closings", json)
    If resp = "" Then GoTo Salir

    Dim saved As String: saved = ParseSaved(resp)
    If saved <> "" Then
        conn.Execute "UPDATE cajas_cierres SET Enviada_MySql=1 WHERE Id_Caja IN (" & saved & ")"
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
