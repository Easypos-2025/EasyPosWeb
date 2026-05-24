' ============================================================
' SincronizarDetalleRecibosFactura
' Endpoint: POST /api/pos/sync/push/receipt-invoice-details
' Tabla local VB6: recibos_detalle_factura
' Tabla servidor: pos_receipt_invoice_details
' PK servidor: (receipt_number, order_number, date, dish_id, item, depends_on)
' Nota: saved retorna claves compuestas; se marca por Nro_Recibo
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
    Dim recibos As String, sepR As String
    json = "[": sep = ""
    recibos = "": sepR = ""

    Do While Not rs.EOF
        Dim nroRecibo As String
        nroRecibo = rs("Nro_Recibo")

        json = json & sep & "{"
        json = json & """receipt_number"":"  & """" & nroRecibo                                & ""","
        json = json & """company_id"":"      & Var_Id_Company_Envio                            & ","
        json = json & """date"":"            & """" & Format(rs("Fecha"), "YYYY-MM-DD")        & ""","
        json = json & """order_number"":"    & """" & Nz(rs("Nro_Comanda"), "0")              & ""","
        json = json & """dish_id"":"         & Nz(rs("Id_Plato"), 0)                           & ","
        json = json & """item"":"            & Nz(rs("Item"), 0)                               & ","
        json = json & """depends_on"":"      & Nz(rs("Depende_De"), 0)                         & ","
        json = json & """quantity"":"        & Nz(rs("Cantidad"), 0)                           & ","
        json = json & """notes"":"           & """" & EscapeJson(Nz(rs("Notas"), ""))          & ""","
        json = json & """dish_amount"":"     & Nz(rs("Valor_Plato"), 0)                        & ","
        json = json & """complimentary"":"   & Nz(rs("Cortesia"), 0)                           & ","
        json = json & """discount_pct"":"    & Nz(rs("Dcto_Pct"), 0)
        json = json & "}"
        sep = ","

        If InStr("," & recibos & ",", "," & nroRecibo & ",") = 0 Then
            recibos = recibos & sepR & """" & nroRecibo & """"
            sepR = ","
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

    ' -- 4. Marcar sincronizadas (por recibo) --------------
    If recibos <> "" Then
        conn.Execute "UPDATE recibos_detalle_factura SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Recibo IN (" & recibos & ")"
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
