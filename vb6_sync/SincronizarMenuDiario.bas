' ============================================================
' SincronizarMenuDiario
' Endpoint: POST /api/pos/sync/push/daily-menu
' Tabla local VB6: menu_diario
' Tabla servidor: pos_daily_menu
' PK servidor: (company_id, menu_id, item_id)
' Nota: saved retorna menu_id; se marca por Id_Menu
' ============================================================
Public Sub SincronizarMenuDiario(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM menu_diario WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """menu_id"":"     & Nz(rs("Id_Menu"), 0)                                   & ","
        json = json & """company_id"":"  & Var_Id_Company_Envio                                   & ","
        json = json & """item_id"":"     & Nz(rs("Id_Item"), 0)                                   & ","
        json = json & """date"":"        & """" & Format(rs("Fecha"), "YYYY-MM-DD")               & ""","
        json = json & """category"":"    & """" & Nz(rs("Categoria"), "0")                        & ""","
        json = json & """description"":"  & """" & EscapeJson(Nz(rs("Descripcion"), "0"))         & ""","
        json = json & """group_by"":"    & Nz(rs("Agrupar_Por"), 0)                               & ","
        json = json & """selected"":"    & Nz(rs("Seleccionado"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/daily-menu", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE menu_diario SET Enviada_MySql = 1 " & _
                     "WHERE Id_Menu IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Menu.Diario Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
