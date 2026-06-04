' ============================================================
' SubirTempComandas.bas
' Endpoint: POST /api/pos/sync/push/temp-comanda
' Tabla fuente: datatemppos.temp_comanda
' Sube pedidos activos del desktop al servidor (origen local)
' Filtro: Movil=0 (no WEB), dia de hoy, no cancelados
' Estrategia: re-envia todo el dia cada ciclo — servidor hace upsert
' ============================================================
Public Sub SubirTempComandas(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConnDatatemppos()

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM temp_comanda " & _
            "WHERE Movil=0 AND Fecha='" & Format(Date, "YYYY/MM/DD") & "' " & _
            "LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """order_number"":"   & """" & EscapeJson(CStr(rs("Nro_Pedido")))                       & ""","
        json = json & """company_id"":"     & Var_Id_Company_Envio                                              & ","
        json = json & """date"":"           & """" & CStr(Nz(rs("Fecha"), ""))                                  & ""","
        json = json & """invoice_number"":"  & """" & EscapeJson(CStr(Nz(rs("Nro_Factura"), "0")))             & ""","
        json = json & """table_name"":"     & """" & EscapeJson(CStr(Nz(rs("Mesa"), "")))                       & ""","
        json = json & """time"":"           & """" & EscapeJson(CStr(Nz(rs("Hora"), "")))                       & ""","
        json = json & """waiter_id"":"      & CLng(Nz(rs("Mesero"), 0))                                         & ","
        json = json & """cancelled"":"      & CInt(Nz(rs("Cancelado"), 0))                                      & ","
        json = json & """amount"":"         & CLng(Nz(rs("Valor"), 0))                                          & ","
        json = json & """notes"":"          & """" & EscapeJson(CStr(Nz(rs("Novedad"), "")))                    & ""","
        json = json & """complimentary"":"  & CInt(Nz(rs("Cortesia"), 0))                                       & ","
        json = json & """guests_count"":"   & CInt(Nz(rs("Nro_Comenzales"), 0))                                 & ","
        json = json & """delivery"":"       & CInt(Nz(rs("Domicilio"), 0))                                      & ","
        json = json & """customer_id"":"    & CLng(Nz(rs("Id_Cliente"), 0))                                     & ","
        json = json & """table_id"":"       & 0
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close: conn.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/temp-comanda", json)

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "TempComandas Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirTempComandas: " & Err.Description
    On Error Resume Next: If Not conn Is Nothing Then conn.Close
End Sub
