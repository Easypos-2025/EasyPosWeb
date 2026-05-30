' ============================================================
' SincronizarListaPreciosCliente
' Endpoint: POST /api/pos/sync/push/customer-price-list
' Tabla local VB6: lista_precios_cliente
' Tabla servidor: pos_customer_price_list
' Grupo sync:     C — después de SincronizarPlatos (Grupo C)
' Depende de:     pos_dishes
' Columnas locales:
'   id_lista, Id_Cliente, Id_Producto, Id_Presentacion,
'   Precio_Producto, Fecha, Activa
' Nota: tabla sin Enviada_MySql — se envian todos los registros
' ============================================================
Public Sub SincronizarListaPreciosCliente(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer todos los registros -----------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM lista_precios_cliente LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id_lista"":"         & Nz(rs("id_lista"), 0)                              & ","
        json = json & """id_cliente"":"       & Nz(rs("Id_Cliente"), 0)                             & ","
        json = json & """id_producto"":"      & Nz(rs("Id_Producto"), 0)                            & ","
        json = json & """id_presentacion"":"  & Nz(rs("Id_Presentacion"), 0)                        & ","
        json = json & """company_id"":"       & Var_Id_Company_Envio                                 & ","
        json = json & """precio_producto"":"  & Nz(rs("Precio_Producto"), 0)                        & ","
        json = json & """fecha"":"            & """" & Nz(rs("Fecha"), "")                          & ""","
        json = json & """activa"":"           & Nz(rs("Activa"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/customer-price-list", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Mostrar estado (sin UPDATE — catálogo) ---------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Lista Precios Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
