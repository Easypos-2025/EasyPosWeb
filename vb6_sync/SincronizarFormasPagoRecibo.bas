' ============================================================
' SincronizarFormasPagoRecibo
' Endpoint: POST /api/pos/sync/push/receipt-payments
' Tabla local VB6: formas_pago_recibo
' Tabla servidor: pos_receipt_payment_methods
' PK servidor: (item, payment_method_id, card_id, receipt_number)
' Nota: saved retorna claves compuestas; se marca por Nro_Recibo
' ============================================================
Public Sub SincronizarFormasPagoRecibo(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM formas_pago_recibo WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

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
        json = json & """item"":"              & Nz(rs("Item"), 0)                              & ","
        json = json & """payment_method_id"":"  & Nz(rs("Id_Forma_Pago"), 0)                   & ","
        json = json & """card_id"":"           & Nz(rs("Id_Tarjeta"), 0)                        & ","
        json = json & """receipt_number"":"    & """" & nroRecibo                               & ""","
        json = json & """company_id"":"        & Var_Id_Company_Envio                           & ","
        json = json & """amount"":"            & Nz(rs("Valor"), 0)                             & ","
        json = json & """date"":"              & """" & Format(rs("Fecha"), "YYYY-MM-DD")       & ""","
        json = json & """authorization"":"     & Nz(rs("Autorizacion"), 0)                      & ","
        json = json & """notes"":"             & """" & EscapeJson(Nz(rs("Notas"), ""))         & ""","
        json = json & """delivery_amount"":"   & Nz(rs("Valor_Domicilio"), 0)                   & ","
        json = json & """prefix"":"            & """" & Nz(rs("Prefijo"), "")                  & ""","
        json = json & """fac_pe"":"            & """" & Nz(rs("Fac_PE"), "")                   & ""","
        json = json & """order_number"":"      & """" & Nz(rs("Nro_Comanda"), "")              & """"
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
    respuesta = ApiPost("/sync/push/receipt-payments", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar sincronizadas (por recibo) --------------
    If recibos <> "" Then
        conn.Execute "UPDATE formas_pago_recibo SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Recibo IN (" & recibos & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "F.Pago.Rec Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
