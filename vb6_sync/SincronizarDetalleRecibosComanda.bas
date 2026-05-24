' ============================================================
' SincronizarDetalleRecibosComanda
' Endpoint: POST /api/pos/sync/push/receipt-order-details
' Tabla local VB6: recibos_detalle_comanda
' Tabla servidor: pos_receipt_order_details
' PK servidor: (order_number, date, receipt_number, dish_id, item, depends_on)
' Nota: saved retorna claves compuestas; se marca por Nro_Comanda
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
    Dim comandas As String, sepC As String
    json = "[": sep = ""
    comandas = "": sepC = ""

    Do While Not rs.EOF
        Dim nroComanda As String
        nroComanda = rs("Nro_Comanda")

        json = json & sep & "{"
        json = json & """order_number"":"    & """" & nroComanda                               & ""","
        json = json & """company_id"":"      & Var_Id_Company_Envio                            & ","
        json = json & """date"":"            & """" & Format(rs("Fecha"), "YYYY-MM-DD")        & ""","
        json = json & """receipt_number"":"  & """" & Nz(rs("Nro_Recibo"), "0")              & ""","
        json = json & """dish_id"":"         & Nz(rs("Id_Plato"), 0)                           & ","
        json = json & """item"":"            & Nz(rs("Item"), 0)                               & ","
        json = json & """depends_on"":"      & Nz(rs("Depende_De"), 0)                         & ","
        json = json & """quantity"":"        & Nz(rs("Cantidad"), 0)                           & ","
        json = json & """amount"":"          & Nz(rs("Valor"), 0)                              & ","
        json = json & """notes"":"           & """" & EscapeJson(Nz(rs("Notas"), ""))          & ""","
        json = json & """complimentary"":"   & Nz(rs("Cortesia"), 0)                           & ","
        json = json & """dish_discount_pct"":" & Nz(rs("Dcto_Plato_Pct"), 0)                  & ","
        json = json & """general_discount_pct"":" & Nz(rs("Dcto_Gral_Pct"), 0)               & ","
        json = json & """seat_number"":"     & Nz(rs("Silla"), 0)                              & ","
        json = json & """changes"":"         & """" & EscapeJson(Nz(rs("Cambios"), ""))        & ""","
        json = json & """dish_time"":"       & """" & Nz(rs("Hora_Plato"), "")                & ""","
        json = json & """pays_tax"":"        & Nz(rs("Cobra_Impuesto"), 0)                     & ","
        json = json & """tax"":"             & Nz(rs("Impuesto"), 0)                           & ","
        json = json & """original_tax"":"    & Nz(rs("Impuesto_Original"), 0)                  & ","
        json = json & """pays_dish"":"       & Nz(rs("Cobra_Plato"), 0)                        & ","
        json = json & """custom_product"":"  & """" & Nz(rs("Producto_Personalizado"), "")   & """"
        json = json & "}"
        sep = ","

        If InStr("," & comandas & ",", "," & nroComanda & ",") = 0 Then
            comandas = comandas & sepC & """" & nroComanda & """"
            sepC = ","
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

    ' -- 4. Marcar sincronizadas (por comanda) -------------
    If comandas <> "" Then
        conn.Execute "UPDATE recibos_detalle_comanda SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Comanda IN (" & comandas & ")"
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
