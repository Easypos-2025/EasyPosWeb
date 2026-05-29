' ============================================================
' SincronizarRecibos
' Endpoint: POST /api/pos/sync/push/receipts
' Tabla local VB6: recibos
' Tabla servidor:  pos_receipts
' Grupo sync:      F2 — después de Comandas/RecibosComanda (Grupo F1)
' Depende de:      pos_receipt_orders (comanda debe existir antes)
' Columnas locales:
'   Nro_Recibo, Fecha, Valor_Efectivo, Descuento, Id_Cliente,
'   Id_Empleado, Anulada, Iva_Pagado, Ajuste, Tarjeta_Credito,
'   Tarjeta_Debito, Propina, Turno, Hora, Hora_Texto,
'   Propina_Extra, Valor_Sin_Propina, Analizada, Tipo_Moneda,
'   Valor_Extranjero, Recibo_Manual, Id_Resolucion,
'   Reservacion, Domicilio, Enviada_MySql
' PK servidor: (receipt_number, company_id)
' Nota: el campo local Nro_Recibo se envía como invoice_number
'       (el backend lo mapea a receipt_number en pos_receipts)
' ============================================================
Public Sub SincronizarRecibos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)
    Var_Tabla_Error = "SincronizarRecibos"

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

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

        Dim hora As String
        hora = Nz(rs("Hora"), "")
        If hora = "" Then hora = "00:00:00"

        json = json & sep & "{"
        json = json & """invoice_number"":"      & """" & EscapeJson(nroRecibo)                               & ""","
        json = json & """company_id"":"          & Var_Id_Company_Envio                                        & ","
        json = json & """date"":"                & """" & Format(rs("Fecha"), "yyyy-mm-dd")                   & ""","
        json = json & """cash_amount"":"         & Nz(rs("Valor_Efectivo"), 0)                                 & ","
        json = json & """discount"":"            & Nz(rs("Descuento"), 0)                                     & ","
        json = json & """customer_id"":"         & Nz(rs("Id_Cliente"), 0)                                    & ","
        json = json & """employee_id"":"         & Nz(rs("Id_Empleado"), 0)                                   & ","
        json = json & """voided"":"              & CInt(Nz(rs("Anulada"), 0))                                 & ","
        json = json & """paid_vat"":"            & Nz(rs("Iva_Pagado"), 0)                                    & ","
        json = json & """adjustment"":"          & Nz(rs("Ajuste"), 0)                                        & ","
        json = json & """credit_card_amount"":"  & Nz(rs("Tarjeta_Credito"), 0)                               & ","
        json = json & """debit_card_amount"":"   & Nz(rs("Tarjeta_Debito"), 0)                                & ","
        json = json & """tip"":"                 & Nz(rs("Propina"), 0)                                       & ","
        json = json & """shift"":"               & Nz(rs("Turno"), 0)                                         & ","
        json = json & """time"":"                & """" & hora                                                 & ""","
        json = json & """time_text"":"           & """" & EscapeJson(Nz(rs("Hora_Texto"), ""))                & ""","
        json = json & """extra_tip"":"           & Nz(rs("Propina_Extra"), 0)                                 & ","
        json = json & """amount_without_tip"":"  & Nz(rs("Valor_Sin_Propina"), 0)                             & ","
        json = json & """analyzed"":"            & CInt(Nz(rs("Analizada"), 0))                               & ","
        json = json & """currency_type_id"":"    & Nz(rs("Tipo_Moneda"), 0)                                   & ","
        json = json & """foreign_amount"":"      & Replace(CStr(Nz(rs("Valor_Extranjero"), 0)), ",", ".")     & ","
        json = json & """manual_receipt"":"      & CInt(Nz(rs("Recibo_Manual"), 0))                           & ","
        json = json & """resolution_id"":"       & Nz(rs("Id_Resolucion"), 0)                                 & ","
        json = json & """reservation_receipt"":"  & """" & Nz(rs("Reservacion"), "0")                         & ""","
        json = json & """delivery_invoice"":"    & CInt(Nz(rs("Domicilio"), 0))
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
    respuesta = ApiPost("/sync/push/receipts", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    If InStr(respuesta, "total_saved") = 0 Then
        Var_Caption_Error = "Error servidor: " & Left(respuesta, 200)
        conn.Close: Exit Sub
    End If

    If recibos <> "" Then
        conn.Execute "UPDATE recibos SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Recibo IN (" & recibos & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Recibos Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
