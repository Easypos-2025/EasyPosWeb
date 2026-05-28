' ============================================================
' SincronizarInventarioPorciones
' Endpoint: POST /api/pos/sync/push/supply-items
' Tabla local VB6: inventario_porciones
' Tabla servidor: supply_items
' Columnas locales:
'   Id_Grupo, Id_Item, Codigo_Insumo, Descripcion, Costo,
'   Und_Compra, Stock_MInimo, Porcentaje_Merma, Controlar
' Nota: tabla sin Enviada_MySql — se envian todos los registros
' ============================================================
Public Sub SincronizarInventarioPorciones(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer todos los registros -----------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM inventario_porciones LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id_grupo"":"      & Nz(rs("Id_Grupo"), 0)                                  & ","
        json = json & """id_item"":"       & Nz(rs("Id_Item"), 0)                                   & ","
        json = json & """company_id"":"    & Var_Id_Company_Envio                                    & ","
        json = json & """code"":"          & """" & Nz(rs("Codigo_Insumo"), "")                     & ""","
        json = json & """name"":"          & """" & EscapeJson(Nz(rs("Descripcion"), ""))           & ""","
        json = json & """cost_price"":"    & Nz(rs("Costo"), 0)                                     & ","
        json = json & """unit_id"":"       & Nz(rs("Und_Compra"), 0)                                & ","
        json = json & """min_stock"":"     & Nz(rs("Stock_MInimo"), 0)                              & ","
        json = json & """waste_pct"":"     & Nz(rs("Porcentaje_Merma"), 0)                          & ","
        json = json & """control_stock"":"  & Nz(rs("Controlar"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/supply-items", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Mostrar estado (sin UPDATE — catálogo) ---------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Insumos Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
