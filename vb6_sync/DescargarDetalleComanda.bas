' ============================================================
' DescargarDetalleComanda.bas
' Endpoint: GET /api/pos/sync/pull/web-order-details
' Tabla destino local: datatemppos.temp_detalle_comanda
'                      datatemppos.temp_detalle_comanda_parcial (copia espejo)
' Enviada_MySql=0 en destino (el uploader no la re-sube al servidor)
' ============================================================
Public Sub DescargarDetalleComanda(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Descargando detalle comanda web..."

    Dim desde As String
    desde = ObtenerUltimoPull()

    Dim respuesta As String
    respuesta = ApiGet("/sync/pull/web-order-details?company_id=" & COMPANY_ID & _
                       "&desde=" & URLEncode(desde))

    If respuesta = "" Or respuesta = "[]" Then
        lblEstado.Caption = "Detalle web: sin cambios " & Now()
        Exit Sub
    End If

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"
    On Error Resume Next
    sc.ExecuteStatement "var r = " & respuesta & ";"
    If Err.Number <> 0 Then
        Var_Caption_Error = "DescargarDetalleComanda: JSON invalido"
        Exit Sub
    End If
    On Error GoTo ErrHandler

    Dim total As Integer
    total = CInt(sc.Eval("r.length"))
    If total = 0 Then
        lblEstado.Caption = "Detalle web: sin cambios " & Now()
        Exit Sub
    End If

    Dim conn As Object
    Set conn = GetConnDatatemppos()
    Dim ins As Integer, upd As Integer
    ins = 0: upd = 0

    Dim i As Integer
    For i = 0 To total - 1
        Dim nroPedido As String: nroPedido = EscSql(CStr(sc.Eval("r[" & i & "].order_number")))
        Dim fecha     As String: fecha     = CStr(sc.Eval("r[" & i & "].date"))
        If Not IsDate(fecha) Then GoTo SigDetalle

        Dim nroFac  As String:  nroFac  = EscSql(CStr(sc.Eval("r[" & i & "].invoice_number || '0'")))
        Dim dishId  As Long:    dishId  = CLng(sc.Eval("r[" & i & "].dish_id || 0"))
        Dim item    As Long:    item    = CLng(sc.Eval("r[" & i & "].item || 0"))
        Dim depende As Long:    depende = CLng(sc.Eval("r[" & i & "].depends_on || 0"))
        Dim cant    As Double:  cant    = CDbl(sc.Eval("r[" & i & "].quantity || 0"))
        Dim valor   As Long:    valor   = CLng(sc.Eval("r[" & i & "].amount || 0"))
        Dim novedad As String:  novedad = EscSql(CStr(sc.Eval("r[" & i & "].notes || ''")))
        Dim cambios As String:  cambios = EscSql(CStr(sc.Eval("r[" & i & "].changes || ''")))
        Dim cortes  As Integer: cortes  = CInt(sc.Eval("r[" & i & "].complimentary || 0"))
        Dim dscPlato As Double: dscPlato = CDbl(sc.Eval("r[" & i & "].dish_discount_pct || 0"))
        Dim dscGen  As Double:  dscGen  = CDbl(sc.Eval("r[" & i & "].general_discount_pct || 0"))
        Dim puesto  As Integer: puesto  = CInt(sc.Eval("r[" & i & "].seat_number || 0"))
        Dim pagImp  As Integer: pagImp  = CInt(sc.Eval("r[" & i & "].pays_tax || 0"))
        Dim impuest As Long:    impuest = CLng(sc.Eval("r[" & i & "].tax || 0"))
        Dim impOrig As Long:    impOrig = CLng(sc.Eval("r[" & i & "].original_tax || 0"))
        Dim pagPlat As Integer: pagPlat = CInt(sc.Eval("r[" & i & "].pays_dish || 0"))
        Dim horaPlat As String: horaPlat = EscSql(CStr(sc.Eval("r[" & i & "].dish_time || ''")))

        Dim pkWhere As String
        pkWhere = "Nro_pedido='" & nroPedido & "' AND Fecha='" & fecha & "'" & _
                  " AND Id_Plato=" & dishId & " AND Item=" & item & " AND Depende=" & depende

        Dim rs As Object
        Set rs = CreateObject("ADODB.Recordset")
        rs.Open "SELECT 1 FROM temp_detalle_comanda WHERE " & pkWhere, conn

        Dim valSql As String
        valSql = "'" & nroPedido & "','" & fecha & "','" & nroFac & "'," & _
                 dishId & "," & item & "," & depende & "," & _
                 cant & "," & valor & ",'" & novedad & "'," & cortes & "," & _
                 Replace(CStr(dscPlato), ",", ".") & "," & _
                 Replace(CStr(dscGen), ",", ".") & "," & _
                 puesto & "," & pagImp & "," & impuest & "," & impOrig & "," & _
                 pagPlat & ",'" & cambios & "','" & horaPlat & "'"

        If rs.EOF Then
            ' INSERT en temp_detalle_comanda
            conn.Execute "INSERT INTO temp_detalle_comanda " & _
                "(Nro_pedido,Fecha,Nro_Factura,Id_Plato,Item,Depende," & _
                " Cantidad,Valor,Novedad,Cortesia,Porc_Descuento_Plato," & _
                " Porc_Descuento_General,Nro_Puesto,Paga_Impuesto," & _
                " Impuesto,Impuesto_Original,Paga_Plato,Cambios,Hora_Plato," & _
                " Enviada_MySql,Mostrar) VALUES (" & valSql & ",0,0)"

            ' Copia espejo en temp_detalle_comanda_parcial
            conn.Execute "INSERT IGNORE INTO temp_detalle_comanda_parcial " & _
                "(Nro_pedido,Fecha,Nro_Factura,Id_Plato,Item,Depende," & _
                " Cantidad,Valor,Novedad,Cortesia,Porc_Descuento_Plato," & _
                " Porc_Descuento_General,Nro_Puesto,Paga_Impuesto," & _
                " Impuesto,Impuesto_Original,Paga_Plato,Cambios,Hora_Plato," & _
                " Enviada_MySql) VALUES (" & valSql & ",0)"
            ins = ins + 1
        Else
            conn.Execute "UPDATE temp_detalle_comanda SET " & _
                "Cantidad=" & cant & ",Valor=" & valor & "," & _
                "Novedad='" & novedad & "',Cambios='" & cambios & "'" & _
                " WHERE " & pkWhere
            upd = upd + 1
        End If
        rs.Close
SigDetalle:
        Set rs = Nothing
    Next i

    conn.Close
    lblEstado.Caption = "Detalle web: +" & ins & " | upd " & upd
    Exit Sub
ErrHandler:
    Var_Caption_Error = "DescargarDetalleComanda: " & Err.Description
    On Error Resume Next: If Not conn Is Nothing Then conn.Close
End Sub
