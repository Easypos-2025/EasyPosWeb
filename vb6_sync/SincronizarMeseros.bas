' ============================================================
' SincronizarMeseros
' Endpoint: POST /api/pos/sync/push/waiters
' Tabla local VB6: meseros
' Tabla servidor: pos_waiters
' PK servidor: id (= Id_Mesero en VB6)
' ============================================================
Public Sub SincronizarMeseros(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM meseros WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"              & Nz(rs("Id_Mesero"), 0)                            & ","
        json = json & """company_id"":"      & Var_Id_Company_Envio                              & ","
        json = json & """name"":"            & """" & EscapeJson(Nz(rs("Nombre"), ""))          & ""","
        json = json & """phone"":"           & """" & Nz(rs("Telefono"), "")                    & ""","
        json = json & """address"":"         & """" & EscapeJson(Nz(rs("Direccion"), ""))       & ""","
        json = json & """password"":"        & """" & Nz(rs("Password"), "")                    & ""","
        json = json & """status"":"          & Nz(rs("Estado"), 0)                              & ","
        json = json & """employee_type"":"   & Nz(rs("Tipo_Empleado"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/waiters", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE meseros SET Enviada_MySql = 1 " & _
                     "WHERE Id_Mesero IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Meseros Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
