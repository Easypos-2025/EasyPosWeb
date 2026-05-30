' ============================================================
' SincronizarNovedadesProductos
' Endpoint: POST /api/pos/sync/push/product-notes
' Tabla local VB6: novedades_productos
' Tabla servidor: pos_product_notes
' Grupo sync:     D — después de SincronizarPlatos (Grupo C)
' Depende de:     pos_dishes
' Columnas locales:
'   Id_Novedad, Novedad
' Nota: tabla sin Enviada_MySql — se envian todos los registros
' ============================================================
Public Sub SincronizarNovedadesProductos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer todos los registros -----------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM novedades_productos LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"          & Nz(rs("Id_Novedad"), 0)                             & ","
        json = json & """company_id"":"  & Var_Id_Company_Envio                                 & ","
        json = json & """name"":"        & """" & EscapeJson(Nz(rs("Novedad"), ""))            & """"
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/product-notes", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Mostrar estado (sin UPDATE — catálogo) ---------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Nov.Productos Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
