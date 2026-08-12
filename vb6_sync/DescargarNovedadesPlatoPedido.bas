' ============================================================
' DescargarNovedadesPlatoPedido.bas
' Endpoint: GET /api/pos/sync/pull/web-order-notes
' Tabla destino local: datatemppos.temp_novedades_plato_pedido
' Filtro servidor: pedidos WEB activos (Salio=0) de hoy
' Estrategia: REPLACE por pedido (DELETE + INSERT)
'   - El servidor devuelve el estado completo de cada pedido WEB
'   - Se borra lo anterior de esos pedidos y se inserta el actual
'   - Cubre: agregar novedad, eliminar novedad, cambiar novedad
' Nota: temp_novedades_plato_pedido no tiene updated_at →
'   el endpoint filtra por Fecha=CURDATE() en temp_comanda
' ============================================================
Public Sub DescargarNovedadesPlatoPedido(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Descargando novedades web..."

    Dim respuesta As String
    respuesta = ApiGet("/sync/pull/web-order-notes?company_id=" & COMPANY_ID)

    If respuesta = "" Or respuesta = "[]" Then
        lblEstado.Caption = "Novedades web: sin cambios " & Now()
        Exit Sub
    End If

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"
    On Error Resume Next
    sc.ExecuteStatement "var r = " & respuesta & ";"
    If Err.Number <> 0 Then
        Var_Caption_Error = "DescargarNovedadesPlatoPedido: JSON invalido"
        Exit Sub
    End If
    On Error GoTo ErrHandler

    Dim total As Long
    total = CLng(sc.Eval("r.length"))
    If total = 0 Then
        lblEstado.Caption = "Novedades web: sin cambios " & Now()
        Exit Sub
    End If

    Dim conn As Object
    Set conn = GetConnDatatemppos()

    ' -- Recopilar Nro_Pedido unicos de la respuesta ------------
    Dim pedidosVistos As String
    Dim i As Long
    For i = 0 To total - 1
        Dim np As String
        np = EscSql(CStr(sc.Eval("r[" & i & "].order_number")))
        If InStr("," & pedidosVistos & ",", "," & np & ",") = 0 Then
            If pedidosVistos = "" Then
                pedidosVistos = "'" & np & "'"
            Else
                pedidosVistos = pedidosVistos & ",'" & np & "'"
            End If
        End If
    Next i

    ' -- Borrar estado anterior de esos pedidos -----------------
    If pedidosVistos <> "" Then
        conn.Execute "DELETE FROM temp_novedades_plato_pedido " & _
                     "WHERE Nro_Pedido IN (" & pedidosVistos & ")"
    End If

    ' -- Insertar estado actual recibido del servidor -----------
    Dim ins As Long: ins = 0
    For i = 0 To total - 1
        Dim nroPedido As String: nroPedido = EscSql(CStr(sc.Eval("r[" & i & "].order_number")))
        Dim consec    As Long:   consec    = CLng(sc.Eval("r[" & i & "].consecutive_id || 0"))
        Dim item      As Long:   item      = CLng(sc.Eval("r[" & i & "].item || 0"))
        Dim depende   As Long:   depende   = CLng(sc.Eval("r[" & i & "].depends_on || 0"))
        Dim codCat    As Long:   codCat    = CLng(sc.Eval("r[" & i & "].category_id || 0"))
        Dim idNov     As Long:   idNov     = CLng(sc.Eval("r[" & i & "].note_id || 0"))
        Dim novedad   As String: novedad   = EscSql(CStr(sc.Eval("r[" & i & "].note || ''")))

        conn.Execute "INSERT IGNORE INTO temp_novedades_plato_pedido " & _
            "(Id_Consecutivo,Nro_Pedido,Item,Depende,Cod_Categoria,Id_Novedad,Novedad) VALUES (" & _
            consec & ",'" & nroPedido & "'," & item & "," & depende & "," & _
            codCat & "," & idNov & ",'" & novedad & "')"
        ins = ins + 1
    Next i

    conn.Close
    lblEstado.Caption = "Novedades web: +" & ins & " " & Now()
    Exit Sub

ErrHandler:
    Var_Caption_Error = "DescargarNovedadesPlatoPedido: " & Err.Description
    On Error Resume Next: If Not conn Is Nothing Then conn.Close
End Sub
