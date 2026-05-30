' ============================================================
' SincronizarDetalleRecibosComanda
' Endpoint: POST /api/pos/sync/push/receipt-order-details
' Tabla local VB6: recibos_detalle_comanda
' Tabla servidor: pos_receipt_order_details
' Grupo sync:     G — después de SincronizarRecibosComanda F1 + SincronizarRecibos F2
' Depende de:     pos_receipt_orders, pos_receipts
' Columnas locales (identicas a detalle_comanda):
'   Nro_Pedido, Fecha, Nro_Factura(*), Id_Plato, Item,
'   Cantidad, Valor, Novedad, Cortesia,
'   Porc_Descuento_Plato, Porc_Descuento_General,
'   Nro_Puesto, Cambios, Hora_Plato, Enviada_MySql,
'   Paga_Impuesto, Impuesto, Impuesto_Original,
'   Paga_Plato, Producto_Personalizado, Depende
' (*) Nro_Factura contiene el numero de recibo en este contexto
'     y se mapea a receipt_number en el servidor
' PK servidor: (order_number, date, receipt_number, dish_id, item, depends_on, company_id)
' Nota: saved retorna claves compuestas; se marca por Nro_Pedido
' ============================================================
Public Sub SincronizarDetalleRecibosComanda(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos_detalle_comanda WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    Dim pedidos As String, sepP As String
    json = "[": sep = ""
    pedidos = "": sepP = ""

    Do While Not rs.EOF
        Dim nroPedido As String
        nroPedido = rs("Nro_Pedido")

        json = json & sep & "{"
        json = json & """order_number"":"          & """" & nroPedido                                        & ""","
        json = json & """company_id"":"            & Var_Id_Company_Envio                                    & ","
        json = json & """date"":"                  & """" & Format(rs("Fecha"), "YYYY-MM-DD")                & ""","
        json = json & """receipt_number"":"        & """" & Nz(rs("Nro_Factura"), "0")                      & ""","
        json = json & """dish_id"":"               & Nz(rs("Id_Plato"), 0)                                   & ","
        json = json & """item"":"                  & Nz(rs("Item"), 0)                                       & ","
        json = json & """depends_on"":"            & Nz(rs("Depende"), 0)                                    & ","
        json = json & """quantity"":"              & Nz(rs("Cantidad"), 0)                                   & ","
        json = json & """amount"":"                & Nz(rs("Valor"), 0)                                      & ","
        json = json & """notes"":"                 & """" & EscapeJson("" & rs("Novedad"))                & ""","
        json = json & """complimentary"":"         & Nz(rs("Cortesia"), 0)                                   & ","
        json = json & """dish_discount_pct"":"     & Nz(rs("Porc_Descuento_Plato"), 0)                      & ","
        json = json & """general_discount_pct"":"  & Nz(rs("Porc_Descuento_General"), 0)                    & ","
        json = json & """seat_number"":"           & Nz(rs("Nro_Puesto"), 0)                                 & ","
        json = json & """changes"":"               & """" & EscapeJson("" & rs("Cambios"))                  & ""","
        json = json & """dish_time"":"             & """" & ("" & rs("Hora_Plato"))                          & ""","
        json = json & """pays_tax"":"              & Nz(rs("Paga_Impuesto"), 0)                              & ","
        json = json & """tax"":"                   & Nz(rs("Impuesto"), 0)                                   & ","
        json = json & """original_tax"":"          & Nz(rs("Impuesto_Original"), 0)                          & ","
        json = json & """pays_dish"":"             & Nz(rs("Paga_Plato"), 0)                                 & ","
        json = json & """custom_product"":"        & """" & EscapeJson("" & rs("Producto_Personalizado"))    & """"
        json = json & "}"
        sep = ","

        If InStr("," & pedidos & ",", "," & nroPedido & ",") = 0 Then
            pedidos = pedidos & sepP & """" & nroPedido & """"
            sepP = ","
        End If

        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/receipt-order-details", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar sincronizadas (por Nro_Pedido) ----------
    If pedidos <> "" Then
        conn.Execute "UPDATE recibos_detalle_comanda SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Pedido IN (" & pedidos & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Det.Rec.Com Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
