' ============================================================
' SincronizarDetalleRecibosFactura
' Endpoint: POST /api/pos/sync/push/receipt-invoice-details
' Tabla local VB6: recibos_detalle_factura
' Tabla servidor: pos_receipt_invoice_details
' Grupo sync:     G — después de SincronizarRecibos (Grupo F2)
' Depende de:     pos_receipts
' Columnas locales (identicas a detalle_factura):
'   Nro_Factura(*), Nro_Pedido, Fecha, Id_Plato, Item,
'   Cantidad, Novedad, Valor_Plato, Cortesia,
'   Porc_Descuento, Enviada_MySql, Depende
' (*) Nro_Factura contiene el numero de recibo en este contexto
'     y se mapea a receipt_number en el servidor
' PK servidor: (receipt_number, order_number, date, dish_id, item, depends_on)
' Nota: saved retorna claves compuestas; se marca por Nro_Factura
' ============================================================
Public Sub SincronizarDetalleRecibosFactura(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos_detalle_factura WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    Dim facturas As String, sepF As String
    json = "[": sep = ""
    facturas = "": sepF = ""

    Do While Not rs.EOF
        Dim nroFactura As String
        nroFactura = rs("Nro_Factura")

        json = json & sep & "{"
        json = json & """receipt_number"":"  & """" & nroFactura                               & ""","
        json = json & """company_id"":"      & Var_Id_Company_Envio                            & ","
        json = json & """date"":"            & """" & Format(rs("Fecha"), "YYYY-MM-DD")        & ""","
        json = json & """order_number"":"    & """" & ("" & rs("Nro_Pedido"))                  & ""","
        json = json & """dish_id"":"         & Nz(rs("Id_Plato"), 0)                           & ","
        json = json & """item"":"            & Nz(rs("Item"), 0)                               & ","
        json = json & """depends_on"":"      & Nz(rs("Depende"), 0)                            & ","
        json = json & """quantity"":"        & Nz(rs("Cantidad"), 0)                           & ","
        json = json & """notes"":"           & """" & EscapeJson("" & rs("Novedad"))            & ""","
        json = json & """dish_amount"":"     & Nz(rs("Valor_Plato"), 0)                        & ","
        json = json & """complimentary"":"   & Nz(rs("Cortesia"), 0)                           & ","
        json = json & """discount_pct"":"    & Nz(rs("Porc_Descuento"), 0)
        json = json & "}"
        sep = ","

        If InStr("," & facturas & ",", "," & nroFactura & ",") = 0 Then
            facturas = facturas & sepF & """" & nroFactura & """"
            sepF = ","
        End If

        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/receipt-invoice-details", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar sincronizadas (por Nro_Factura) ---------
    If facturas <> "" Then
        conn.Execute "UPDATE recibos_detalle_factura SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Factura IN (" & facturas & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Det.Rec.Fac Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
