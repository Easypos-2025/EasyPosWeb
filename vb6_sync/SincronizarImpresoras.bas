' ============================================================
' SincronizarImpresoras
' Endpoint: POST /api/pos/sync/push/printers
' Tabla local VB6: impresoras
' Tabla servidor: pos_printers
' Grupo sync:     A — sin dependencias, tabla maestra base
' Depende de:     ninguna
' Columnas locales:
'   Id_Impresora -> id
'   Nombre       -> name
'   IP           -> ip
'   Puerto       -> port
'   Activa       -> is_active
' PK servidor: id (= Id_Impresora en VB6)
' ============================================================
Public Sub SincronizarImpresoras(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM impresoras WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"         & Nz(rs("Id_Impresora"), 0)                    & ","
        json = json & """company_id"":"  & Var_Id_Company_Envio                         & ","
        json = json & """name"":"       & """" & EscapeJson(Nz(rs("Nombre"), ""))      & ""","
        json = json & """ip"":"         & """" & Nz(rs("IP"), "")                      & ""","
        Dim strPort As String
        strPort = CStr(Nz(rs("Puerto"), ""))
        If strPort = "" Then strPort = "9100"
        json = json & """port"":"       & strPort                                          & ","
        json = json & """is_active"":"  & CInt(Nz(rs("Activa"), 1))
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/printers", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE impresoras SET Enviada_MySql = 1 " & _
                     "WHERE Id_Impresora IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    If InStr(respuesta, "total_saved") = 0 Then
        Var_Caption_Error = "Error servidor: " & Left(respuesta, 200)
        conn.Close: Exit Sub
    End If
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Impr. Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
