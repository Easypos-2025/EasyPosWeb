' ============================================================
' SubirTempDetalleComanda.bas
' Endpoint: POST /api/pos/sync/push/temp-details-replace
' Tabla fuente: datatemppos.temp_detalle_comanda_parcial
' Estrategia: REPLACE por pedido (Variante C)
'   - Itera cada pedido activo del dia (origin local, Movil=0)
'   - Por cada pedido envia el estado COMPLETO de sus items (Mostrar=1)
'   - El servidor borra lo que tenia e inserta el estado actual
'   - Esto cubre automaticamente: agregar, eliminar y modificar items
' Nota: Mostrar=1 identifica el registro maestro de cada plato
'   (cuando un plato se imprime en varias impresoras, Mostrar=0
'    son las copias de ruteo — se omiten aqui)
' ============================================================
Public Sub SubirTempDetalleComanda(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConnDatatemppos()

    ' -- 1. Obtener pedidos activos del dia (origen desktop) ----
    Dim rsOrd As Object
    Set rsOrd = CreateObject("ADODB.Recordset")
    rsOrd.Open "SELECT Nro_Pedido, Fecha FROM temp_comanda " & _
               "WHERE Movil=0 AND Fecha='" & Format(Date, "YYYY/MM/DD") & "' AND Salio=1", conn

    If rsOrd.EOF Then
        rsOrd.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON: array de pedidos con sus items ------
    Dim json As String, sepOrd As String
    json = "[": sepOrd = ""
    Dim totalOrders As Integer
    totalOrders = 0

    Do While Not rsOrd.EOF
        Dim nroPedido As String
        nroPedido = CStr(rsOrd("Nro_Pedido"))
        Dim fecha As String
        fecha = CStr(rsOrd("Fecha"))

        Dim rsItems As Object
        Set rsItems = CreateObject("ADODB.Recordset")
        rsItems.Open "SELECT * FROM temp_detalle_comanda_parcial " & _
                     "WHERE Nro_pedido='" & Replace(nroPedido, "'", "''") & "' " & _
                     "  AND Fecha='" & fecha & "' AND Mostrar=1 AND Salio=1", conn

        Dim ordJson As String
        ordJson = "{"
        ordJson = ordJson & """order_number"":""" & EscapeJson(nroPedido) & ""","
        ordJson = ordJson & """company_id"":" & Var_Id_Company_Envio & ","
        ordJson = ordJson & """date"":""" & fecha & ""","
        ordJson = ordJson & """items"":["

        Dim sepItem As String: sepItem = ""

        Do While Not rsItems.EOF
            ordJson = ordJson & sepItem & "{"
            ordJson = ordJson & """dish_id"":"          & CLng(Nz(rsItems("Id_Plato"), 0))                              & ","
            ordJson = ordJson & """item"":"              & CLng(Nz(rsItems("Item"), 0))                                  & ","
            ordJson = ordJson & """depends_on"":"        & CLng(Nz(rsItems("Depende"), 0))                               & ","
            ordJson = ordJson & """invoice_number"":"    & """" & EscapeJson(CStr(Nz(rsItems("Nro_Factura"), "0")))     & ""","
            ordJson = ordJson & """quantity"":"          & CDbl(Nz(rsItems("Cantidad"), 0))                              & ","
            ordJson = ordJson & """amount"":"            & CLng(Nz(rsItems("Valor"), 0))                                 & ","
            ordJson = ordJson & """notes"":"             & """" & EscapeJson(CStr(Nz(rsItems("Novedad"), "")))           & ""","
            ordJson = ordJson & """complimentary"":"     & CInt(Nz(rsItems("Cortesia"), 0))                              & ","
            ordJson = ordJson & """dish_discount_pct"":"  & CDbl(Nz(rsItems("Porc_Descuento_Plato"), 0))                & ","
            ordJson = ordJson & """general_discount_pct"":"  & CDbl(Nz(rsItems("Porc_Descuento_General"), 0))           & ","
            ordJson = ordJson & """seat_number"":"       & CInt(Nz(rsItems("Nro_Puesto"), 0))                            & ","
            ordJson = ordJson & """changes"":"           & """" & EscapeJson(CStr(Nz(rsItems("Cambios"), "")))           & ""","
            ordJson = ordJson & """dish_time"":"         & """" & EscapeJson(CStr(Nz(rsItems("Hora_Plato"), "")))        & ""","
            ordJson = ordJson & """pays_tax"":"          & CInt(Nz(rsItems("Paga_Impuesto"), 0))                         & ","
            ordJson = ordJson & """tax"":"               & CLng(Nz(rsItems("Impuesto"), 0))                              & ","
            ordJson = ordJson & """original_tax"":"      & CLng(Nz(rsItems("Impuesto_Original"), 0))                     & ","
            ordJson = ordJson & """pays_dish"":"         & CInt(Nz(rsItems("Paga_Plato"), 0))                            & ","
            ordJson = ordJson & """custom_product"":"    & """" & EscapeJson(CStr(Nz(rsItems("Producto_Personalizado"), ""))) & """"
            ordJson = ordJson & "}"
            sepItem = ","
            rsItems.MoveNext
        Loop

        rsItems.Close
        Set rsItems = Nothing

        ordJson = ordJson & "]}"
        json = json & sepOrd & ordJson
        sepOrd = ","
        totalOrders = totalOrders + 1

        rsOrd.MoveNext
    Loop

    rsOrd.Close
    json = json & "]"
    conn.Close

    If totalOrders = 0 Then Exit Sub

    ' -- 3. Enviar al servidor (replace atomico por pedido) -----
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/temp-details-replace", json)

    If respuesta = "" Then Exit Sub

    ' -- 4. Mostrar estado ------------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "DetComanda: " & sc.Eval("r.total_saved") & _
                        " items | " & sc.Eval("r.total_orders") & " pedidos"
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirTempDetalleComanda: " & Err.Description
    On Error Resume Next
    If Not rsItems Is Nothing Then rsItems.Close
    If Not rsOrd Is Nothing Then rsOrd.Close
    If Not conn Is Nothing Then conn.Close
End Sub
