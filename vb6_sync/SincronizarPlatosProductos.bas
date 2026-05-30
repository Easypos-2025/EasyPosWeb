' ============================================================
' SincronizarPlatosProductos
' Endpoint: POST /api/pos/sync/push/dish-products
' Tabla local VB6: plato_producto
' Tabla servidor: pos_dish_products
' Grupo sync:     D — después de SincronizarPlatos + SincronizarInventarioPorciones (Grupos B y C)
' Depende de:     pos_dishes, supply_items
' PK servidor: (dish_id, supplier_id, measure_id)
' Nota: saved retorna dish_id; se marca por Id_Plato
' ============================================================
Public Sub SincronizarPlatosProductos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM plato_producto WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """dish_id"":"             & Nz(rs("Id_Plato"), 0)                           & ","
        json = json & """company_id"":"          & Var_Id_Company_Envio                             & ","
        json = json & """measure_id"":"          & Nz(rs("Id_Medida"), 0)                           & ","
        json = json & """supplier_id"":"         & Nz(rs("Id_Proveedor"), 0)                        & ","
        json = json & """minimum_units"":"       & Nz(rs("Unidades_Minimas"), 0)                    & ","
        json = json & """presentation_value"":"  & Nz(rs("Valor_Presentacion"), 0)                  & ","
        json = json & """description"":"         & """" & EscapeJson(Nz(rs("Descripcion"), ""))    & ""","
        json = json & """active"":"              & Nz(rs("Activo"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/dish-products", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE plato_producto SET Enviada_MySql = 1 " & _
                     "WHERE Id_Plato IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Plato.Prod Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
