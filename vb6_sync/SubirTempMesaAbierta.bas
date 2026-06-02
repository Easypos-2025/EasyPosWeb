' ============================================================
' SubirTempMesaAbierta.bas
' Endpoint: POST /api/pos/sync/push/temp-table-status
' Tabla fuente: datatemppos.temp_mesa_abierta
' Sincroniza estado abierta/cerrada de todas las mesas al servidor
' Sin filtro de fecha — envia el estado actual completo cada ciclo
' ============================================================
Public Sub SubirTempMesaAbierta(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConnDatatemppos()

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM temp_mesa_abierta LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """company_id"":"   & Var_Id_Company_Envio                               & ","
        json = json & """table_id"":"     & CLng(Nz(rs("Id_Mesa"), 0))                          & ","
        json = json & """table_name"":"   & """" & EscapeJson(CStr(Nz(rs("Mesa"), "")))         & ""","
        json = json & """is_open"":"      & CInt(Nz(rs("Abierta"), 0))
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close: conn.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/temp-table-status", json)

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "TempMesas Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirTempMesaAbierta: " & Err.Description
    On Error Resume Next: If Not conn Is Nothing Then conn.Close
End Sub
