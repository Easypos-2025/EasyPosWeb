' ============================================================
' SubirTempMesaAbierta.bas
' Endpoint: POST /api/pos/sync/push/temp-table-status
' Tabla fuente: datatemppos.temp_mesa_abierta
' Estrategia: REPLACE completo por company (Variante D)
'   - Envia el estado COMPLETO de temp_mesa_abierta (puede ser vacio)
'   - El servidor borra todos los bloqueos de la company e inserta los actuales
'   - Si la tabla local esta vacia => envia {"company_id":N,"tables":[]}
'     y el servidor limpia todos los bloqueos (mesas liberadas)
' IMPORTANTE: NO hacer Exit Sub si rs.EOF — siempre enviar aunque sea vacio
' ============================================================
Public Sub SubirTempMesaAbierta(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConnDatatemppos()

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM temp_mesa_abierta LIMIT " & Var_Limit_Registros, conn

    ' -- Construir wrapper: {"company_id":N,"tables":[...]} ----
    Dim json As String, sep As String
    json = "{""company_id"":" & Var_Id_Company_Envio & ",""tables"":["
    sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """table_id"":"   & CLng(Nz(rs("Id_Mesa"), 0))                         & ","
        json = json & """table_name"":" & """" & EscapeJson(CStr(Nz(rs("Mesa"), "")))         & ""","
        json = json & """is_open"":"    & CInt(Nz(rs("Abierta"), 1))
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop

    rs.Close: conn.Close
    json = json & "]}"

    ' -- Enviar siempre (vacio = limpiar bloqueos en servidor) --
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/temp-table-status", json)

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "TempMesas Env.: " & sc.Eval("r.total_saved")
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirTempMesaAbierta: " & Err.Description
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    If Not conn Is Nothing Then conn.Close
End Sub
