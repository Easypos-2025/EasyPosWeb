' ============================================================
' SincronizarCategoriaProductos
' Endpoint: POST /api/pos/sync/push/product-categories
' Tabla local VB6: categoria_productos
' Tabla servidor: pos_product_categories
' Grupo sync:     B — después de SincronizarCategorias (Grupo A)
' Depende de:     pos_categories
' Nota: esta tabla es la CATEGORÍA DE INSUMOS/suministros
'       supply_items.agrupar = pos_product_categories.id
'       (GET /api/inventory/categories lee de pos_product_categories)
' Columnas locales:
'   Cod_Categoria              -> id
'   Nombre                     -> name
'   Porcentaje                 -> percentage
'   Activa                     -> is_active
'   Exgir_Seleccion            -> require_selection
'   Imprimir_Armar_Solo_Cambios -> print_assembly_changes_only
' PK servidor: id (= Cod_Categoria en VB6 = supply_items.agrupar)
' ============================================================
Public Sub SincronizarCategoriaProductos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM categoria_productos WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"                         & Nz(rs("Cod_Categoria"), 0)                              & ","
        json = json & """company_id"":"                 & Var_Id_Company_Envio                                    & ","
        json = json & """name"":"                       & """" & EscapeJson(Nz(rs("Nombre"), ""))               & ""","
        json = json & """percentage"":"                 & Replace(CStr(Nz(rs("Porcentaje"), 0)), ",", ".") & ","
        json = json & """is_active"":"                  & CInt(Nz(rs("Activa"), 1))                              & ","
        json = json & """require_selection"":"          & CInt(Nz(rs("Exgir_Seleccion"), 0))                     & ","
        json = json & """print_assembly_changes_only"":"  & CInt(Nz(rs("Imprimir_Armar_Solo_Cambios"), 0))
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/product-categories", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE categoria_productos SET Enviada_MySql = 1 " & _
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
    Var_Caption_Error = "Cat.Prod Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
