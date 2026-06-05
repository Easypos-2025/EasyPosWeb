' ============================================================
' SubirTempNovedadesPlatoPedido.bas
' Endpoint: POST /api/pos/sync/push/temp-notes-replace
' Tabla fuente: datatemppos.temp_novedades_plato_pedido
' Estrategia: REPLACE por pedido (Variante C)
'   - Por cada pedido activo envia el estado COMPLETO de sus novedades
'   - El servidor borra lo que tenia e inserta el estado actual
' Nota: temp_novedades_plato_pedido no tiene campo Fecha —
'   se hace JOIN con temp_comanda para filtrar por dia y origen local
' ============================================================
Public Sub SubirTempNovedadesPlatoPedido(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConnDatatemppos()

    ' -- 1. Obtener pedidos activos del dia (origen desktop) ----
    Dim rsOrd As Object
    Set rsOrd = CreateObject("ADODB.Recordset")
    rsOrd.Open "SELECT Nro_Pedido FROM temp_comanda " & _
               "WHERE Movil=0 AND Fecha='" & Format(Date, "YYYY/MM/DD") & "' AND Cancelado=0 AND Salio=0 " & _
               "  AND Mesa NOT IN (SELECT Mesa FROM temp_mesa_abierta)", conn

    If rsOrd.EOF Then
        rsOrd.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON: array de pedidos con sus novedades --
    Dim json As String, sepOrd As String
    json = "[": sepOrd = ""
    Dim totalOrders As Integer
    totalOrders = 0

    Do While Not rsOrd.EOF
        Dim nroPedido As String
        nroPedido = CStr(rsOrd("Nro_Pedido"))

        Dim rsItems As Object
        Set rsItems = CreateObject("ADODB.Recordset")
        rsItems.Open "SELECT * FROM temp_novedades_plato_pedido " & _
                     "WHERE Nro_Pedido='" & Replace(nroPedido, "'", "''") & "'", conn

        Dim ordJson As String
        ordJson = "{"
        ordJson = ordJson & """order_number"":""" & EscapeJson(nroPedido) & ""","
        ordJson = ordJson & """company_id"":" & Var_Id_Company_Envio & ","
        ordJson = ordJson & """items"":["

        Dim sepItem As String: sepItem = ""

        Do While Not rsItems.EOF
            ordJson = ordJson & sepItem & "{"
            ordJson = ordJson & """consecutive_id"":"  & CLng(Nz(rsItems("Id_Consecutivo"), 0))                    & ","
            ordJson = ordJson & """item"":"             & CLng(Nz(rsItems("Item"), 0))                              & ","
            ordJson = ordJson & """depends_on"":"       & CLng(Nz(rsItems("Depende"), 0))                           & ","
            ordJson = ordJson & """category_id"":"      & CLng(Nz(rsItems("Cod_Categoria"), 0))                     & ","
            ordJson = ordJson & """note_id"":"          & CLng(Nz(rsItems("Id_Novedad"), 0))                        & ","
            ordJson = ordJson & """note"":"             & """" & EscapeJson(CStr(Nz(rsItems("Novedad"), "")))       & """"
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
    respuesta = ApiPost("/sync/push/temp-notes-replace", json)

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Novedades: " & sc.Eval("r.total_saved") & _
                        " items | " & sc.Eval("r.total_orders") & " pedidos"
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirTempNovedadesPlatoPedido: " & Err.Description
    On Error Resume Next
    If Not rsItems Is Nothing Then rsItems.Close
    If Not rsOrd Is Nothing Then rsOrd.Close
    If Not conn Is Nothing Then conn.Close
End Sub
