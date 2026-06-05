' ============================================================
' SubirTempPlatosProductoParcial.bas
' Endpoint: POST /api/pos/sync/push/temp-assembly-replace
' Tabla fuente: datatemppos.temp_plato_producto_parcial
' Estrategia: REPLACE por pedido (Variante C)
'   - Por cada pedido activo envia el estado COMPLETO de sus armados
'   - El servidor borra lo que tenia e inserta el estado actual
'   - Cubre: agregar modificador, eliminar modificador, cambiar cantidad
' ============================================================
Public Sub SubirTempPlatosProductoParcial(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
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

    ' -- 2. Construir JSON: array de pedidos con sus armados ----
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
        rsItems.Open "SELECT * FROM temp_plato_producto_parcial " & _
                     "WHERE Nro_Pedido='" & Replace(nroPedido, "'", "''") & "' " & _
                     "  AND Fecha='" & fecha & "'", conn

        Dim ordJson As String
        ordJson = "{"
        ordJson = ordJson & """order_number"":""" & EscapeJson(nroPedido) & ""","
        ordJson = ordJson & """company_id"":" & Var_Id_Company_Envio & ","
        ordJson = ordJson & """date"":""" & fecha & ""","
        ordJson = ordJson & """items"":["

        Dim sepItem As String: sepItem = ""

        Do While Not rsItems.EOF
            ordJson = ordJson & sepItem & "{"
            ordJson = ordJson & """dish_id"":"         & CLng(Nz(rsItems("Id_Plato"), 0))                              & ","
            ordJson = ordJson & """item"":"             & CLng(Nz(rsItems("Item"), 0))                                  & ","
            ordJson = ordJson & """group_id"":"         & CLng(Nz(rsItems("Id_Grupo"), 0))                              & ","
            ordJson = ordJson & """item_id"":"          & CLng(Nz(rsItems("Id_Item"), 0))                               & ","
            ordJson = ordJson & """invoice_number"":"   & """" & EscapeJson(CStr(Nz(rsItems("Nro_Factura"), "0")))     & ""","
            ordJson = ordJson & """quantity"":"         & CDbl(Nz(rsItems("Cantidad"), 0))
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
    respuesta = ApiPost("/sync/push/temp-assembly-replace", json)

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Armado: " & sc.Eval("r.total_saved") & _
                        " items | " & sc.Eval("r.total_orders") & " pedidos"
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirTempPlatosProductoParcial: " & Err.Description
    On Error Resume Next
    If Not rsItems Is Nothing Then rsItems.Close
    If Not rsOrd Is Nothing Then rsOrd.Close
    If Not conn Is Nothing Then conn.Close
End Sub
