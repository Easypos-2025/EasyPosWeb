' ============================================================
' SincronizarPlatos
' Endpoint: POST /api/pos/sync/push/dishes
' Tabla local VB6: platos
' Tabla servidor: pos_dishes
' PK servidor: id (= Id_Plato en VB6)
' ============================================================
Public Sub SincronizarPlatos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM platos WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"                      & Nz(rs("Id_Plato"), 0)                           & ","
        json = json & """company_id"":"              & Var_Id_Company_Envio                             & ","
        json = json & """name"":"                    & """" & EscapeJson(Nz(rs("Nombre"), ""))         & ""","
        json = json & """product_code"":"            & """" & Nz(rs("Codigo_Producto"), "")            & ""","
        json = json & """price"":"                   & Nz(rs("Precio"), 0)                             & ","
        json = json & """preparation_time"":"        & Nz(rs("Tiempo_Preparacion"), 0)                 & ","
        json = json & """active"":"                  & Nz(rs("Activo"), 0)                             & ","
        json = json & """category_id"":"             & Nz(rs("Id_Categoria"), 0)                       & ","
        json = json & """photo_path"":"              & """" & Nz(rs("Ruta_Foto"), "")                  & ""","
        json = json & """description"":"             & """" & EscapeJson(Nz(rs("Descripcion"), ""))    & ""","
        json = json & """printer"":"                 & """" & Nz(rs("Impresora"), "")                  & ""","
        json = json & """comment"":"                 & """" & EscapeJson(Nz(rs("Comentario"), ""))     & ""","
        json = json & """extra_print"":"             & """" & Nz(rs("Impresion_Extra"), "")            & ""","
        json = json & """printer_2"":"               & """" & Nz(rs("Impresora_2"), "")               & ""","
        json = json & """pre_preparation"":"         & Nz(rs("Pre_Preparacion"), 0)                    & ","
        json = json & """offer"":"                   & Nz(rs("Oferta"), 0)                             & ","
        json = json & """offer_priority"":"          & Nz(rs("Prioridad_Oferta"), 0)                   & ","
        json = json & """tax"":"                     & Nz(rs("Impuesto"), 0)                           & ","
        json = json & """wholesale_price"":"         & Nz(rs("Precio_Mayor"), 0)                       & ","
        json = json & """product_cost"":"            & Nz(rs("Costo"), 0)                              & ","
        json = json & """minimum_stock"":"           & Nz(rs("Stock_Minimo"), 0)                       & ","
        json = json & """ask_sale_price"":"          & Nz(rs("Pedir_Precio_Venta"), 0)                 & ","
        json = json & """ask_product_description"":"  & Nz(rs("Pedir_Descripcion"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/dishes", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE platos SET Enviada_MySql = 1 " & _
                     "WHERE Id_Plato IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Platos Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
