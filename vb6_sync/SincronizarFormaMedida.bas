' ============================================================
' SincronizarFormaMedida
' Endpoint: POST /api/pos/sync/push/measure-forms
' Tabla local VB6: forma_medida
' Tabla servidor: pos_measure_forms
' Columnas locales:
'   Id_Forma_Medida, Descripcion, Activa
' Nota: tabla sin Enviada_MySql — se envian todos los registros
' ============================================================
Public Sub SincronizarFormaMedida(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer todos los registros -----------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM forma_medida LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"         & Nz(rs("Id_Forma_Medida"), 0)                           & ","
        json = json & """company_id"":"  & Var_Id_Company_Envio                                   & ","
        json = json & """name"":"        & """" & EscapeJson(Nz(rs("Descripcion"), ""))          & ""","
        json = json & """is_active"":"   & Nz(rs("Activa"), 1)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/measure-forms", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Mostrar estado (sin UPDATE — catálogo) ---------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Forma Medida Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
