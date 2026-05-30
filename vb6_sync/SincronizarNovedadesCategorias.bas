' ============================================================
' SincronizarNovedadesCategorias
' Endpoint: POST /api/pos/sync/push/dish-note-categories
' Tabla local VB6: novedades_categorias
' Tabla servidor: pos_dish_note_categories
' Grupo sync:     A — sin dependencias, tabla maestra base
' Depende de:     ninguna
' Columnas locales:
'   Id_Consecutivo, Cod_Categoria, Id_Novedad, Novedad
' Nota: tabla sin Enviada_MySql — se envian todos los registros
' ============================================================
Public Sub SincronizarNovedadesCategorias(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer todos los registros -----------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM novedades_categorias LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id_consecutivo"":"  & Nz(rs("Id_Consecutivo"), 0)                       & ","
        json = json & """cod_categoria"":"   & Nz(rs("Cod_Categoria"), 0)                        & ","
        json = json & """id_novedad"":"      & Nz(rs("Id_Novedad"), 0)                           & ","
        json = json & """company_id"":"      & Var_Id_Company_Envio                               & ","
        json = json & """name"":"            & """" & EscapeJson(Nz(rs("Novedad"), ""))          & """"
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/dish-note-categories", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Mostrar estado (sin UPDATE — catálogo) ---------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Nov.Categ. Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
