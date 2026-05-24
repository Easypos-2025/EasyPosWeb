' ============================================================
' SincronizarPlatosArmar
' Endpoint: POST /api/pos/sync/push/dish-assembly
' Tabla local VB6: plato_armar
' Tabla servidor: pos_dish_assembly
' PK servidor: (company_id, dish_id, category_code)
' Nota: saved retorna dish_id; se marca por Id_Plato
' ============================================================
Public Sub SincronizarPlatosArmar(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM plato_armar WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """dish_id"":"               & Nz(rs("Id_Plato"), 0)             & ","
        json = json & """company_id"":"            & Var_Id_Company_Envio              & ","
        json = json & """category_code"":"         & Nz(rs("Codigo_Categoria"), 0)     & ","
        json = json & """max_choices"":"           & Nz(rs("Max_Opciones"), 0)         & ","
        json = json & """is_active"":"             & Nz(rs("Activo"), 0)               & ","
        json = json & """is_required"":"           & Nz(rs("Obligatorio"), 0)          & ","
        json = json & """print_on_change_only"":"  & Nz(rs("Solo_Cambios"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/dish-assembly", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE plato_armar SET Enviada_MySql = 1 " & _
                     "WHERE Id_Plato IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Plato.Armar Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
