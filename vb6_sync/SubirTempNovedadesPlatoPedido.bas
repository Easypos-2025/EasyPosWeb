' ============================================================
' SubirTempNovedadesPlatoPedido.bas
' Endpoint: POST /api/pos/sync/push/order-dish-notes
' Tabla fuente: datatemppos.temp_novedades_plato_pedido
' Sube comentarios/novedades de platos en pedidos activos
' JOIN con temp_comanda para filtrar por fecha y origen local
' ============================================================
Public Sub SubirTempNovedadesPlatoPedido(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConnDatatemppos()

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT n.* FROM temp_novedades_plato_pedido n " & _
            "JOIN temp_comanda c ON c.Nro_Pedido=n.Nro_Pedido " & _
            "WHERE n.Nro_Pedido NOT LIKE 'WEB-%' " & _
            "  AND c.Fecha=DATE(NOW()) AND c.Cancelado=0 " & _
            "LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """order_number"":"    & """" & EscapeJson(CStr(rs("Nro_Pedido")))        & ""","
        json = json & """company_id"":"      & Var_Id_Company_Envio                               & ","
        json = json & """consecutive_id"":"  & CLng(Nz(rs("Id_Consecutivo"), 0))                 & ","
        json = json & """item"":"            & CLng(Nz(rs("Item"), 0))                            & ","
        json = json & """depends_on"":"      & CLng(Nz(rs("Depende"), 0))                         & ","
        json = json & """category_id"":"     & CLng(Nz(rs("Cod_Categoria"), 0))                   & ","
        json = json & """note_id"":"         & CLng(Nz(rs("Id_Novedad"), 0))                      & ","
        json = json & """note"":"            & """" & EscapeJson(CStr(Nz(rs("Novedad"), "")))     & """"
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close: conn.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/order-dish-notes", json)

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "TempNovedades Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirTempNovedadesPlatoPedido: " & Err.Description
    On Error Resume Next: If Not conn Is Nothing Then conn.Close
End Sub
