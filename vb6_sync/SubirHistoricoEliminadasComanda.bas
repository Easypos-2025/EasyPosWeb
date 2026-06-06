' ============================================================
' SubirHistoricoEliminadasComanda
' Endpoint: POST /api/pos/sync/push/historico-comanda-eliminada
' Tabla local VB6: historico_comandas_eliminadas
' Tabla servidor:  easyposweb.historico_comandas_eliminadas
' Grupo sync:      ejecutar ANTES de SubirHistoricoEliminadasDetalle
' Columnas locales:
'   Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora, Mesero,
'   Cancelado, Valor, Salio, Novedad, Cortesia, Imprimio_Precuenta,
'   Nro_Comenzales, Mostrar, Nro_Puestos, Motivo_Eliminacion,
'   Quien_Elimino, Enviada_MySql, Domicilio, Id_Cliente
' PK servidor: (company_id, Nro_Pedido, Fecha)
' Nota: saved retorna clave compuesta; se marca por Nro_Pedido
' ============================================================
Public Sub SubirHistoricoEliminadasComanda(Var_Id_Company_Envio As Integer)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn()

    ' -- 1. Leer pendientes ------------------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora, " & _
            "       Mesero, Cancelado, Valor, Salio, Novedad, " & _
            "       Cortesia, Imprimio_Precuenta, Nro_Comenzales, " & _
            "       Mostrar, Nro_Puestos, Motivo_Eliminacion, " & _
            "       Quien_Elimino, Enviada_MySql, Domicilio, Id_Cliente " & _
            "FROM historico_comandas_eliminadas " & _
            "WHERE Enviada_MySql = 0", conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON -------------------------------------
    Dim json As String, sep As String
    Dim pedidos As String, sepP As String
    json = "[": sep = ""
    pedidos = "": sepP = ""

    Do While Not rs.EOF
        Dim nroPedido As String
        nroPedido = CStr(Nz(rs("Nro_Pedido"), ""))

        json = json & sep & "{"
        json = json & """company_id"":"          & Var_Id_Company_Envio                                                            & ","
        json = json & """order_number"":"         & """" & EscapeJson(nroPedido)                                                   & ""","
        json = json & """date"":"                 & """" & Format(rs("Fecha"), "YYYY/MM/DD")                                     & ""","
        json = json & """invoice_number"":"       & """" & EscapeJson(CStr(Nz(rs("Nro_Factura"),         "0")))                    & ""","
        json = json & """table_name"":"           & """" & EscapeJson(CStr(Nz(rs("Mesa"),                "")))                     & ""","
        json = json & """time"":"                 & """" & EscapeJson(CStr(Nz(rs("Hora"),                "")))                     & ""","
        json = json & """waiter_id"":"            & CLng(Nz(rs("Mesero"),                                0))                       & ","
        json = json & """cancelled"":"            & CInt(Nz(rs("Cancelado"),                             0))                       & ","
        json = json & """amount"":"               & CLng(Nz(rs("Valor"),                                 0))                       & ","
        json = json & """salio"":"                & CInt(Nz(rs("Salio"),                                 0))                       & ","
        json = json & """notes"":"                & """" & EscapeJson(CStr(Nz(rs("Novedad"),             "")))                     & ""","
        json = json & """complimentary"":"        & CInt(Nz(rs("Cortesia"),                              0))                       & ","
        json = json & """printed_precuenta"":"    & CLng(Nz(rs("Imprimio_Precuenta"),                    0))                       & ","
        json = json & """guests_count"":"         & CInt(Nz(rs("Nro_Comenzales"),                        0))                       & ","
        json = json & """mostrar"":"              & CInt(Nz(rs("Mostrar"),                               0))                       & ","
        json = json & """seats_count"":"          & CInt(Nz(rs("Nro_Puestos"),                           0))                       & ","
        json = json & """motivo_eliminacion"":"   & """" & EscapeJson(CStr(Nz(rs("Motivo_Eliminacion"),  "")))                     & ""","
        json = json & """quien_elimino"":"        & """" & EscapeJson(CStr(Nz(rs("Quien_Elimino"),       "")))                     & ""","
        json = json & """enviada_mysql"":"        & CInt(Nz(rs("Enviada_MySql"),                         0))                       & ","
        json = json & """delivery"":"             & CInt(Nz(rs("Domicilio"),                             0))                       & ","
        json = json & """customer_id"":"          & CLng(Nz(rs("Id_Cliente"),                            0))
        json = json & "}"
        sep = ","

        If InStr("," & pedidos & ",", "," & nroPedido & ",") = 0 Then
            pedidos = pedidos & sepP & """" & nroPedido & """"
            sepP = ","
        End If

        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ---------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/historico-comanda-eliminada", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Validar respuesta del servidor ---------------------
    If InStr(respuesta, "total_saved") = 0 Then
        Var_Caption_Error = "Hist.Elim. Error: " & Left(respuesta, 200)
        conn.Close: Exit Sub
    End If

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"

    If CInt(sc.Eval("r.total_failed")) > 0 Then
        Var_Caption_Error = "Hist.Elim. Fallidos: " & sc.Eval("r.total_failed") & " - " & sc.Eval("r.errors[0]")
        conn.Close: Exit Sub
    End If

    ' -- 5. Marcar sincronizadas (por Nro_Pedido) -------------
    If pedidos <> "" Then
        conn.Execute "UPDATE historico_comandas_eliminadas SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Pedido IN (" & pedidos & ")"
    End If

    ' -- 6. Mostrar estado -------------------------------------
    Var_Caption_Error = "Hist.Elim.: " & sc.Eval("r.total_saved") & " | TV: " & sc.Eval("r.tv_fired")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirHistoricoEliminadasComanda: " & Err.Description
    On Error Resume Next
    If Not rs   Is Nothing Then rs.Close
    If Not conn Is Nothing Then conn.Close
End Sub
