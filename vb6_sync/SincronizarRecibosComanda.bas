' ============================================================
' SincronizarRecibosComanda
' Endpoint: POST /api/pos/sync/push/receipt-orders
' Tabla local VB6: recibos_comanda
' Tabla servidor: pos_receipt_orders
' ============================================================
Public Sub SincronizarRecibosComanda(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos_comanda WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """order_number"":"""    & rs("Nro_Comanda")   & ""","
        json = json & """company_id"":"        & Var_Id_Company_Envio & ","
        json = json & """date"":"              & """" & Format(rs("Fecha"), "YYYY-MM-DD") & ""","
        json = json & """receipt_number"":""" & Nz(rs("Nro_Recibo"), "0") & ""","
        json = json & """table_name"":"        & """" & EscapeJson(Nz(rs("Nombre_Mesa"), "")) & ""","
        json = json & """time"":"              & """" & Nz(rs("Hora"), "") & ""","
        json = json & """waiter_id"":"         & Nz(rs("Id_Mesero"), 0) & ","
        json = json & """cancelled"":"         & Nz(rs("Cancelada"), 0) & ","
        json = json & """amount"":"            & Nz(rs("Valor"), 0) & ","
        json = json & """notes"":"             & """" & EscapeJson(Nz(rs("Notas"), "")) & ""","
        json = json & """complimentary"":"     & Nz(rs("Cortesia"), 0) & ","
        json = json & """guests_count"":"      & Nz(rs("Num_Personas"), 0) & ","
        json = json & """delivery"":"          & Nz(rs("Domicilio"), 0) & ","
        json = json & """customer_id"":"       & Nz(rs("Id_Cliente"), 0) & ","
        json = json & """table_id"":"          & Nz(rs("Id_Mesa"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/receipt-orders", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE recibos_comanda SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Comanda IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Rec.Comanda Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
