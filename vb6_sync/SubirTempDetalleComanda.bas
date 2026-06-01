' ============================================================
' SubirTempDetalleComanda.bas
' Endpoint: POST /api/pos/sync/push/order-details
' Tabla fuente: datatemppos.temp_detalle_comanda_parcial
' (esta es la tabla con la informacion completa de items)
' Sube items de pedidos activos del desktop al servidor
' Filtro: no WEB, dia de hoy, Mostrar=1
' ============================================================
Public Sub SubirTempDetalleComanda(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConnDatatemppos()

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM temp_detalle_comanda_parcial " & _
            "WHERE Nro_pedido NOT LIKE 'WEB-%' " & _
            "  AND Fecha=DATE(NOW()) AND Mostrar=1 " & _
            "LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """order_number"":"         & """" & EscapeJson(CStr(rs("Nro_pedido")))                      & ""","
        json = json & """company_id"":"           & Var_Id_Company_Envio                                             & ","
        json = json & """date"":"                 & """" & Format(rs("Fecha"), "YYYY-MM-DD")                         & ""","
        json = json & """invoice_number"":"       & """" & EscapeJson(CStr(Nz(rs("Nro_Factura"), "0")))             & ""","
        json = json & """dish_id"":"              & CLng(Nz(rs("Id_Plato"), 0))                                      & ","
        json = json & """item"":"                 & CLng(Nz(rs("Item"), 0))                                          & ","
        json = json & """depends_on"":"           & CLng(Nz(rs("Depende"), 0))                                       & ","
        json = json & """quantity"":"             & CDbl(Nz(rs("Cantidad"), 0))                                      & ","
        json = json & """amount"":"               & CLng(Nz(rs("Valor"), 0))                                         & ","
        json = json & """notes"":"                & """" & EscapeJson(CStr(Nz(rs("Novedad"), "")))                   & ""","
        json = json & """complimentary"":"        & CInt(Nz(rs("Cortesia"), 0))                                      & ","
        json = json & """dish_discount_pct"":"    & CDbl(Nz(rs("Porc_Descuento_Plato"), 0))                         & ","
        json = json & """general_discount_pct"":"  & CDbl(Nz(rs("Porc_Descuento_General"), 0))                       & ","
        json = json & """seat_number"":"          & CInt(Nz(rs("Nro_Puesto"), 0))                                    & ","
        json = json & """changes"":"              & """" & EscapeJson(CStr(Nz(rs("Cambios"), "")))                   & ""","
        json = json & """dish_time"":"            & """" & EscapeJson(CStr(Nz(rs("Hora_Plato"), "")))                & ""","
        json = json & """pays_tax"":"             & CInt(Nz(rs("Paga_Impuesto"), 0))                                 & ","
        json = json & """tax"":"                  & CLng(Nz(rs("Impuesto"), 0))                                      & ","
        json = json & """original_tax"":"         & CLng(Nz(rs("Impuesto_Original"), 0))                             & ","
        json = json & """pays_dish"":"            & CInt(Nz(rs("Paga_Plato"), 0))                                    & ","
        json = json & """custom_product"":"       & """" & EscapeJson(CStr(Nz(rs("Producto_Personalizado"), "")))   & """"
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close: conn.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/order-details", json)

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "TempDetComanda Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirTempDetalleComanda: " & Err.Description
    On Error Resume Next: If Not conn Is Nothing Then conn.Close
End Sub
