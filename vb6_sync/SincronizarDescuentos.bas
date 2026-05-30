' ============================================================
' SincronizarDescuentos
' Endpoint: POST /api/pos/sync/push/discounts
' Tabla local VB6: descuentos
' Tabla servidor: pos_discounts
' Grupo sync:     J — después de SincronizarComandas (Grupo F1)
' Depende de:     pos_orders
' Columnas locales:
'   Id_Descuento, Fecha, Prefix, Factura, Id_Plato, Item,
'   Id_Tipificacion, Valor_Original_Producto, Valor_Venta_Producto,
'   Valor_Base, Valor_Impuesto, Valor_Descuento_Pesos, Porcentaje,
'   Motivo, Nro_Pedido, Enviada_MySql
' ============================================================
Public Sub SincronizarDescuentos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM descuentos WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON + acumular Id_Descuento enviados -
    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""

    Do While Not rs.EOF
        Dim idReg As Long
        idReg = Nz(rs("Id_Descuento"), 0)

        json = json & sep & "{"
        json = json & """id_registro"":"       & idReg                                               & ","
        json = json & """company_id"":"        & Var_Id_Company_Envio                                & ","
        json = json & """date"":"              & """" & Nz(rs("Fecha"), "")                          & ""","
        json = json & """prefix"":"            & """" & Nz(rs("Prefix"), "")                        & ""","
        json = json & """invoice_number"":"    & """" & Nz(rs("Factura"), "")                       & ""","
        json = json & """dish_id"":"           & Nz(rs("Id_Plato"), 0)                               & ","
        json = json & """item"":"              & Nz(rs("Item"), 0)                                   & ","
        json = json & """typification_id"":"   & Nz(rs("Id_Tipificacion"), 0)                        & ","
        json = json & """original_price"":"    & Nz(rs("Valor_Original_Producto"), 0)                & ","
        json = json & """sale_price"":"        & Nz(rs("Valor_Venta_Producto"), 0)                   & ","
        json = json & """base_value"":"        & Nz(rs("Valor_Base"), 0)                             & ","
        json = json & """tax_value"":"         & Nz(rs("Valor_Impuesto"), 0)                         & ","
        json = json & """discount_amount"":"   & Nz(rs("Valor_Descuento_Pesos"), 0)                  & ","
        json = json & """percentage"":"        & Nz(rs("Porcentaje"), 0)                             & ","
        json = json & """reason"":"            & """" & EscapeJson(Nz(rs("Motivo"), ""))             & ""","
        json = json & """order_number"":"      & """" & Nz(rs("Nro_Pedido"), "")                    & """"
        json = json & "}"

        idList = idList & idSep & idReg
        sep = ",": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/discounts", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar como enviados por Id_Descuento ----------
    If idList <> "" Then
        conn.Execute "UPDATE descuentos SET Enviada_MySql = 1 " & _
                     "WHERE Id_Descuento IN (" & idList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Descuentos Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
