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
' Variante A: solo envía Enviada_MySql = 0 y marca por fila lo confirmado.
' Requiere columna Enviada_MySql (script 015_escritorio_...sql).
' ============================================================
Public Sub SincronizarListaPreciosCliente(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM lista_precios_cliente WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

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

    ' -- 4. Marcar solo las filas confirmadas ---------------
    '    saved = "id_lista|Id_Cliente|Id_Producto|Id_Presentacion"
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE lista_precios_cliente SET Enviada_MySql = 1 " & _
                     "WHERE Enviada_MySql = 0 AND " & _
                     "CONCAT(id_lista,'|',Id_Cliente,'|',Id_Producto,'|',Id_Presentacion) IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
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
