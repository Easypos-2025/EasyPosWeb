' ============================================================
' SincronizarCategoriaPlatos
' Endpoint: POST /api/pos/sync/push/dish-categories
' Tabla local VB6: categoria_platos
' Tabla servidor: pos_dish_categories
' Grupo sync:     B — después de SincronizarCategorias (Grupo A)
' Depende de:     pos_categories
' Columnas locales:
'   Cod_Categoria -> id
'   Categoria     -> parent_category_id
'   Nombre        -> name
'   Nombre_foto   -> photo_name
'   Porcentaje    -> percentage
'   Turno         -> shift
'   Lunes         -> monday
'   Martes        -> tuesday
'   Miercoles     -> wednesday
'   Jueves        -> thursday
'   Viernes       -> friday
'   Sabado        -> saturday
'   Domingo       -> sunday
'   Activa        -> is_active
' PK servidor: id (= Cod_Categoria en VB6)
' ============================================================
Public Sub SincronizarCategoriaPlatos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM categoria_platos WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"                  & Nz(rs("Cod_Categoria"), 0)                  & ","
        json = json & """company_id"":"          & Var_Id_Company_Envio                         & ","
        json = json & """parent_category_id"":"  & Nz(rs("Categoria"), 0)                       & ","
        json = json & """name"":"                & """" & EscapeJson(Nz(rs("Nombre"), ""))     & ""","
        json = json & """photo_name"":"          & """" & Nz(rs("Nombre_foto"), "")            & ""","
        json = json & """percentage"":"          & Replace(CStr(Nz(rs("Porcentaje"), 0)), ",", ".") & ","
        json = json & """shift"":"               & CInt(Nz(rs("Turno"), 0))                     & ","
        json = json & """monday"":"              & CInt(Nz(rs("Lunes"), 0))                     & ","
        json = json & """tuesday"":"             & CInt(Nz(rs("Martes"), 0))                    & ","
        json = json & """wednesday"":"           & CInt(Nz(rs("Miercoles"), 0))                 & ","
        json = json & """thursday"":"            & CInt(Nz(rs("Jueves"), 0))                    & ","
        json = json & """friday"":"              & CInt(Nz(rs("Viernes"), 0))                   & ","
        json = json & """saturday"":"            & CInt(Nz(rs("Sabado"), 0))                    & ","
        json = json & """sunday"":"              & CInt(Nz(rs("Domingo"), 0))                   & ","
        json = json & """is_active"":"           & CInt(Nz(rs("Activa"), 1))
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/dish-categories", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE categoria_platos SET Enviada_MySql = 1 " & _
                     "WHERE Cod_Categoria IN (" & savedList & ")"
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
    Var_Caption_Error = "Cat.Platos Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
