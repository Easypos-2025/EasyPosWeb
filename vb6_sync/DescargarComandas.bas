' ============================================================
' DescargarComandas.bas
' Endpoint: GET /api/pos/sync/pull/web-orders
' Tabla destino local: datatemppos.temp_comanda
' Filtro servidor: order_number LIKE 'WEB-%' AND updated_at > ultimo_pull
' Movil=1 en todos los registros descargados (identifica origen web)
' ============================================================
Public Sub DescargarComandas(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Descargando comandas web..."

    Dim desde As String
    desde = ObtenerUltimoPull()

    Dim respuesta As String
    respuesta = ApiGet("/sync/pull/web-orders?company_id=" & COMPANY_ID & _
                       "&desde=" & URLEncode(desde))

    If respuesta = "" Or respuesta = "[]" Then
        lblEstado.Caption = "Comandas web: sin cambios " & Now()
        Exit Sub
    End If

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"
    On Error Resume Next
    sc.ExecuteStatement "var r = " & respuesta & ";"
    If Err.Number <> 0 Then
        Var_Caption_Error = "DescargarComandas: JSON invalido"
        Exit Sub
    End If
    On Error GoTo ErrHandler

    Dim total As Integer
    total = CInt(sc.Eval("r.length"))
    If total = 0 Then
        lblEstado.Caption = "Comandas web: sin cambios " & Now()
        Exit Sub
    End If

    Dim conn As Object
    Set conn = GetConnDatatemppos()
    Dim ins As Integer, upd As Integer, omit As Integer
    ins = 0: upd = 0: omit = 0

    Dim i As Integer
    For i = 0 To total - 1
        Dim nroPedido As String
        nroPedido = EscSql(CStr(sc.Eval("r[" & i & "].order_number")))

        Dim fecha As String
        fecha = CStr(sc.Eval("r[" & i & "].date"))
        If Not IsDate(fecha) Then GoTo SigComanda

        Dim nroFac  As String:  nroFac  = EscSql(CStr(sc.Eval("r[" & i & "].invoice_number || '0'")))
        Dim mesa    As String:  mesa    = EscSql(CStr(sc.Eval("r[" & i & "].table_name || ''")))
        Dim hora    As String:  hora    = EscSql(CStr(sc.Eval("r[" & i & "].time || ''")))
        Dim mesero  As Long:    mesero  = CLng(sc.Eval("r[" & i & "].waiter_id || 0"))
        Dim cancel  As Integer: cancel  = CInt(sc.Eval("r[" & i & "].cancelled || 0"))
        Dim valor   As Long:    valor   = CLng(sc.Eval("r[" & i & "].amount || 0"))
        Dim novedad As String:  novedad = EscSql(CStr(sc.Eval("r[" & i & "].notes || ''")))
        Dim cortes  As Integer: cortes  = CInt(sc.Eval("r[" & i & "].complimentary || 0"))
        Dim comens  As Integer: comens  = CInt(sc.Eval("r[" & i & "].guests_count || 0"))
        Dim domici  As Integer: domici  = CInt(sc.Eval("r[" & i & "].delivery || 0"))
        Dim idCli   As Long:    idCli   = CLng(sc.Eval("r[" & i & "].customer_id || 0"))
        Dim idMesa  As Long:    idMesa  = CLng(sc.Eval("r[" & i & "].table_id || 0"))

        Dim rs As Object
        Set rs = CreateObject("ADODB.Recordset")
        rs.Open "SELECT Nro_Factura FROM temp_comanda " & _
                "WHERE Nro_Pedido='" & nroPedido & "' AND Fecha='" & fecha & "'", conn

        If rs.EOF Then
            conn.Execute "INSERT INTO temp_comanda " & _
                "(Nro_Pedido,Fecha,Nro_Factura,Mesa,Hora,Mesero," & _
                " Cancelado,Valor,Novedad,Cortesia,Nro_Comenzales," & _
                " Domicilio,Id_Cliente,Id_Mesa,Movil) VALUES (" & _
                "'" & nroPedido & "','" & fecha & "','" & nroFac & "'," & _
                "'" & mesa & "','" & hora & "'," & mesero & "," & _
                cancel & "," & valor & ",'" & novedad & "'," & cortes & "," & _
                comens & "," & domici & "," & idCli & "," & idMesa & ",1)"
            ins = ins + 1
        ElseIf Nz(rs("Nro_Factura"), "0") = "0" Then
            conn.Execute "UPDATE temp_comanda SET " & _
                "Cancelado=" & cancel & ",Valor=" & valor & "," & _
                "Novedad='" & novedad & "',Mesero=" & mesero & _
                " WHERE Nro_Pedido='" & nroPedido & "' AND Fecha='" & fecha & "'"
            upd = upd + 1
        Else
            omit = omit + 1
        End If
        rs.Close
SigComanda:
        Set rs = Nothing
    Next i

    conn.Close
    lblEstado.Caption = "Comandas web: +" & ins & " | upd " & upd & " | omit " & omit
    Exit Sub
ErrHandler:
    Var_Caption_Error = "DescargarComandas: " & Err.Description
    On Error Resume Next: If Not conn Is Nothing Then conn.Close
End Sub
