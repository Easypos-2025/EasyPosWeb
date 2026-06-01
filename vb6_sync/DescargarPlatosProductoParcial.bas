' ============================================================
' DescargarPlatosProductoParcial.bas
' Endpoint: GET /api/pos/sync/pull/web-order-assembly
' Tabla destino local: datatemppos.Temp_plato_producto_Parcial
' Contiene las selecciones de armado (modificadores) de pedidos web
' ============================================================
Public Sub DescargarPlatosProductoParcial(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Descargando armado web..."

    Dim desde As String
    desde = ObtenerUltimoPull()

    Dim respuesta As String
    respuesta = ApiGet("/sync/pull/web-order-assembly?company_id=" & COMPANY_ID & _
                       "&desde=" & URLEncode(desde))

    If respuesta = "" Or respuesta = "[]" Then
        lblEstado.Caption = "Armado web: sin cambios " & Now()
        Exit Sub
    End If

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"
    On Error Resume Next
    sc.ExecuteStatement "var r = " & respuesta & ";"
    If Err.Number <> 0 Then
        Var_Caption_Error = "DescargarPlatosProductoParcial: JSON invalido"
        Exit Sub
    End If
    On Error GoTo ErrHandler

    Dim total As Integer
    total = CInt(sc.Eval("r.length"))
    If total = 0 Then
        lblEstado.Caption = "Armado web: sin cambios " & Now()
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
        If Not IsDate(fecha) Then GoTo SigArmado

        Dim nroFac  As String: nroFac  = EscSql(CStr(sc.Eval("r[" & i & "].invoice_number || '0'")))
        Dim dishId  As Long:   dishId  = CLng(sc.Eval("r[" & i & "].dish_id || 0"))
        Dim item    As Long:   item    = CLng(sc.Eval("r[" & i & "].item || 0"))
        Dim grpId   As Long:   grpId   = CLng(sc.Eval("r[" & i & "].group_id || 0"))
        Dim itmId   As Long:   itmId   = CLng(sc.Eval("r[" & i & "].item_id || 0"))
        Dim cant    As Double: cant    = CDbl(sc.Eval("r[" & i & "].quantity || 0"))

        Dim pkWhere As String
        pkWhere = "Nro_Pedido='" & nroPedido & "' AND Fecha='" & fecha & "'" & _
                  " AND Nro_Factura='" & nroFac & "' AND Id_Plato=" & dishId & _
                  " AND Item=" & item & " AND Id_Grupo=" & grpId & " AND Id_Item=" & itmId

        Dim rs As Object
        Set rs = CreateObject("ADODB.Recordset")
        rs.Open "SELECT 1 FROM Temp_plato_producto_Parcial WHERE " & pkWhere, conn

        If rs.EOF Then
            conn.Execute "INSERT INTO Temp_plato_producto_Parcial " & _
                "(Nro_Pedido,Fecha,Nro_Factura,Id_Plato,Item,Id_Grupo,Id_Item," & _
                " Cantidad,Enviada_MySql) VALUES (" & _
                "'" & nroPedido & "','" & fecha & "','" & nroFac & "'," & _
                dishId & "," & item & "," & grpId & "," & itmId & "," & _
                Replace(CStr(cant), ",", ".") & ",0)"
            ins = ins + 1
        Else
            conn.Execute "UPDATE Temp_plato_producto_Parcial SET " & _
                "Cantidad=" & Replace(CStr(cant), ",", ".") & _
                " WHERE " & pkWhere
            upd = upd + 1
        End If
        rs.Close
SigArmado:
        Set rs = Nothing
    Next i

    conn.Close
    lblEstado.Caption = "Armado web: +" & ins & " | upd " & upd
    Exit Sub
ErrHandler:
    Var_Caption_Error = "DescargarPlatosProductoParcial: " & Err.Description
    On Error Resume Next: If Not conn Is Nothing Then conn.Close
End Sub
