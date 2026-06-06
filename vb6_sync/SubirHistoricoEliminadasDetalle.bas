' ============================================================
' SubirHistoricoEliminadasDetalle.bas
' Endpoint: POST /api/pos/sync/push/historico-detalle-eliminada
' Tabla fuente: <BD_asociado>.historico_detalle_comanda_eliminadas
' Tabla destino (servidor): easyposweb.historico_detalle_comanda_eliminadas
'
' Envia TODOS los campos del local (misma estructura) + company_id.
' Debe llamarse DESPUES de SubirHistoricoEliminadasComanda en cada ciclo.
' ============================================================
Public Sub SubirHistoricoEliminadasDetalle(Var_Id_Company_Envio As Integer)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn()

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT d.Nro_pedido, d.Fecha, d.Nro_Factura, " & _
            "       d.Id_Plato, d.Item, d.Descripcion, " & _
            "       d.Cantidad, d.Valor, d.Min, d.Min_S, d.Hora, " & _
            "       d.Salio, d.Novedad, d.Cortesia, " & _
            "       d.Porc_Descuento_Plato, d.Porc_Descuento_General, " & _
            "       d.Impreso, d.Cambios, d.Mostrar, d.Impresora, " & _
            "       d.Depende, d.Enviada_MySql, d.Nro_Puesto, " & _
            "       d.Cod_Categoria_Plato, d.Hora_Plato, " & _
            "       d.Paga_Impuesto, d.Impuesto, d.Impuesto_Original, " & _
            "       d.Paga_Plato, d.Item_Original, d.Producto_Personalizado " & _
            "FROM historico_detalle_comanda_eliminadas d " & _
            "INNER JOIN historico_comandas_eliminadas c " & _
            "    ON c.Nro_Pedido = d.Nro_pedido AND c.Fecha = d.Fecha " & _
            "WHERE d.Fecha='" & Format(Date, "YYYY/MM/DD") & "'", conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """company_id"":"              & Var_Id_Company_Envio                                                                & ","
        json = json & """order_number"":"             & """" & EscapeJson(CStr(Nz(rs("Nro_pedido"),              "")))   & ""","
        json = json & """date"":"                     & """" & CStr(Nz(rs("Fecha"),                              ""))    & ""","
        json = json & """invoice_number"":"           & """" & EscapeJson(CStr(Nz(rs("Nro_Factura"),             "0")))  & ""","
        json = json & """dish_id"":"                  & CLng(Nz(rs("Id_Plato"),                                  0))     & ","
        json = json & """item"":"                     & CLng(Nz(rs("Item"),                                      0))     & ","
        json = json & """description"":"              & """" & EscapeJson(CStr(Nz(rs("Descripcion"),             "")))   & ""","
        json = json & """quantity"":"                 & CLng(Nz(rs("Cantidad"),                                  0))     & ","
        json = json & """amount"":"                   & CLng(Nz(rs("Valor"),                                     0))     & ","
        json = json & """min_val"":"                  & CLng(Nz(rs("Min"),                                       0))     & ","
        json = json & """min_s"":"                    & CLng(Nz(rs("Min_S"),                                     0))     & ","
        json = json & """hora"":"                     & """" & EscapeJson(CStr(Nz(rs("Hora"),                    "")))   & ""","
        json = json & """salio"":"                    & CInt(Nz(rs("Salio"),                                     0))     & ","
        json = json & """notes"":"                    & """" & EscapeJson(CStr(Nz(rs("Novedad"),                 "")))   & ""","
        json = json & """complimentary"":"            & CInt(Nz(rs("Cortesia"),                                  0))     & ","
        json = json & """dish_discount_pct"":"        & CDbl(Nz(rs("Porc_Descuento_Plato"),                      0))     & ","
        json = json & """general_discount_pct"":"     & CDbl(Nz(rs("Porc_Descuento_General"),                    0))     & ","
        json = json & """printed"":"                  & CInt(Nz(rs("Impreso"),                                   0))     & ","
        json = json & """changes"":"                  & """" & EscapeJson(CStr(Nz(rs("Cambios"),                 "")))   & ""","
        json = json & """mostrar"":"                  & CInt(Nz(rs("Mostrar"),                                   0))     & ","
        json = json & """printer"":"                  & """" & EscapeJson(CStr(Nz(rs("Impresora"),               "")))   & ""","
        json = json & """depends_on"":"               & """" & EscapeJson(CStr(Nz(rs("Depende"),                 "")))   & ""","
        json = json & """enviada_mysql"":"            & CInt(Nz(rs("Enviada_MySql"),                             0))     & ","
        json = json & """seat_number"":"              & CInt(Nz(rs("Nro_Puesto"),                                0))     & ","
        json = json & """category_id"":"              & CLng(Nz(rs("Cod_Categoria_Plato"),                       0))     & ","
        json = json & """dish_time"":"                & """" & EscapeJson(CStr(Nz(rs("Hora_Plato"),              "")))   & ""","
        json = json & """pays_tax"":"                 & CInt(Nz(rs("Paga_Impuesto"),                             0))     & ","
        json = json & """tax"":"                      & CDbl(Nz(rs("Impuesto"),                                  0))     & ","
        json = json & """original_tax"":"             & CDbl(Nz(rs("Impuesto_Original"),                         0))     & ","
        json = json & """pays_dish"":"                & CInt(Nz(rs("Paga_Plato"),                                0))     & ","
        json = json & """item_original"":"            & CLng(Nz(rs("Item_Original"),                             0))     & ","
        json = json & """custom_product"":"           & """" & EscapeJson(CStr(Nz(rs("Producto_Personalizado"),  "")))   & """"
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close: conn.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/historico-detalle-eliminada", json)

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Hist.Det.Elim.: " & sc.Eval("r.total_saved") & " items"
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirHistoricoEliminadasDetalle: " & Err.Description
    On Error Resume Next
    If Not rs   Is Nothing Then rs.Close
    If Not conn Is Nothing Then conn.Close
End Sub
