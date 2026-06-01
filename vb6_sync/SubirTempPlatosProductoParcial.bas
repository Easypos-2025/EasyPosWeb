' ============================================================
' SubirTempPlatosProductoParcial.bas
' Endpoint: POST /api/pos/sync/push/order-detail-products
' Tabla fuente: datatemppos.temp_plato_producto_parcial
' Sube selecciones de armado (modificadores) de pedidos activos
' Filtro: no WEB, dia de hoy
' ============================================================
Public Sub SubirTempPlatosProductoParcial(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConnDatatemppos()

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM temp_plato_producto_parcial " & _
            "WHERE Nro_Pedido NOT LIKE 'WEB-%' " & _
            "  AND Fecha=DATE(NOW()) " & _
            "LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """order_number"":"   & """" & EscapeJson(CStr(rs("Nro_Pedido")))                        & ""","
        json = json & """company_id"":"     & Var_Id_Company_Envio                                               & ","
        json = json & """date"":"           & """" & EscapeJson(CStr(Nz(rs("Fecha"), "")))                      & ""","
        json = json & """invoice_number"":"  & """" & EscapeJson(CStr(Nz(rs("Nro_Factura"), "0")))              & ""","
        json = json & """dish_id"":"        & CLng(Nz(rs("Id_Plato"), 0))                                        & ","
        json = json & """item"":"           & CLng(Nz(rs("Item"), 0))                                            & ","
        json = json & """group_id"":"       & CLng(Nz(rs("Id_Grupo"), 0))                                        & ","
        json = json & """item_id"":"        & CLng(Nz(rs("Id_Item"), 0))                                         & ","
        json = json & """quantity"":"       & CDbl(Nz(rs("Cantidad"), 0))
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close: conn.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/order-detail-products", json)

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "TempArmado Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirTempPlatosProductoParcial: " & Err.Description
    On Error Resume Next: If Not conn Is Nothing Then conn.Close
End Sub
