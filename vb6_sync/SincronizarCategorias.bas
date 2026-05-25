' ============================================================
' SincronizarCategorias
' Endpoint: POST /api/pos/sync/push/categories
' Tabla local VB6: categorias
' Tabla servidor: pos_categories
' Columnas locales:
'   cod_categoria -> id
'   descripcion   -> description
'   Nombre_foto   -> photo_name
'   Activa        -> is_active
' PK servidor: id (= cod_categoria en VB6)
' ============================================================
Public Sub SincronizarCategorias(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM categorias WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"           & Nz(rs("cod_categoria"), 0)                    & ","
        json = json & """company_id"":"   & Var_Id_Company_Envio                          & ","
        json = json & """description"":"  & """" & EscapeJson(Nz(rs("descripcion"), "")) & ""","
        json = json & """photo_name"":"   & """" & EscapeJson(Nz(rs("Nombre_foto"), ""))  & ""","
        json = json & """is_active"":"    & Nz(rs("Activa"), 1)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/categories", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE categorias SET Enviada_MySql = 1 " & _
                     "WHERE cod_categoria IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Categ. Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
