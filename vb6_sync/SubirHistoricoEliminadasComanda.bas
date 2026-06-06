' ============================================================
' SubirHistoricoEliminadasComanda.bas
' Endpoint: POST /api/pos/sync/push/historico-comanda-eliminada
' Tabla fuente: <BD_asociado>.historico_comandas_eliminadas
' Tabla destino (servidor): easyposweb.historico_comandas_eliminadas
'
' Flujo:
'   1. Lee todas las eliminadas del dia desde la BD del asociado
'   2. Envia al servidor con company_id (mismo conjunto de campos que local)
'   3. El servidor hace upsert + genera evento TV CANCELADO
'      + limpia el pedido de datatemppos
' ============================================================
Public Sub SubirHistoricoEliminadasComanda(Var_Id_Company_Envio As Integer)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn()

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora, " & _
            "       Mesero, Cancelado, Valor, Salio, Novedad, " & _
            "       Cortesia, Imprimio_Precuenta, Nro_Comenzales, " & _
            "       Mostrar, Nro_Puestos, Motivo_Eliminacion, " & _
            "       Quien_Elimino, Enviada_MySql, Domicilio, Id_Cliente " & _
            "FROM historico_comandas_eliminadas " & _
            "WHERE Fecha='" & Format(Date, "YYYY/MM/DD") & "'", conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """company_id"":"          & Var_Id_Company_Envio                                                            & ","
        json = json & """order_number"":"         & """" & EscapeJson(CStr(Nz(rs("Nro_Pedido"),          "")))  & ""","
        json = json & """date"":"                 & """" & CStr(Nz(rs("Fecha"),                          ""))   & ""","
        json = json & """invoice_number"":"       & """" & EscapeJson(CStr(Nz(rs("Nro_Factura"),         "0"))) & ""","
        json = json & """table_name"":"           & """" & EscapeJson(CStr(Nz(rs("Mesa"),                "")))  & ""","
        json = json & """time"":"                 & """" & EscapeJson(CStr(Nz(rs("Hora"),                "")))  & ""","
        json = json & """waiter_id"":"            & CLng(Nz(rs("Mesero"),                                0))    & ","
        json = json & """cancelled"":"            & CInt(Nz(rs("Cancelado"),                             0))    & ","
        json = json & """amount"":"               & CLng(Nz(rs("Valor"),                                 0))    & ","
        json = json & """salio"":"                & CInt(Nz(rs("Salio"),                                 0))    & ","
        json = json & """notes"":"                & """" & EscapeJson(CStr(Nz(rs("Novedad"),             "")))  & ""","
        json = json & """complimentary"":"        & CInt(Nz(rs("Cortesia"),                              0))    & ","
        json = json & """printed_precuenta"":"    & CLng(Nz(rs("Imprimio_Precuenta"),                    0))    & ","
        json = json & """guests_count"":"         & CInt(Nz(rs("Nro_Comenzales"),                        0))    & ","
        json = json & """mostrar"":"              & CInt(Nz(rs("Mostrar"),                               0))    & ","
        json = json & """seats_count"":"          & CInt(Nz(rs("Nro_Puestos"),                           0))    & ","
        json = json & """motivo_eliminacion"":"   & """" & EscapeJson(CStr(Nz(rs("Motivo_Eliminacion"),  "")))  & ""","
        json = json & """quien_elimino"":"        & """" & EscapeJson(CStr(Nz(rs("Quien_Elimino"),       "")))  & ""","
        json = json & """enviada_mysql"":"        & CInt(Nz(rs("Enviada_MySql"),                         0))    & ","
        json = json & """delivery"":"             & CInt(Nz(rs("Domicilio"),                             0))    & ","
        json = json & """customer_id"":"          & CLng(Nz(rs("Id_Cliente"),                            0))
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close: conn.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/historico-comanda-eliminada", json)

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Hist.Elim.: " & sc.Eval("r.total_saved") & " | TV: " & sc.Eval("r.tv_fired")
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SubirHistoricoEliminadasComanda: " & Err.Description
    On Error Resume Next
    If Not rs   Is Nothing Then rs.Close
    If Not conn Is Nothing Then conn.Close
End Sub
