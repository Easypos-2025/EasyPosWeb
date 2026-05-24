' ============================================================
' SincronizarDetalleFactura
' Endpoint: POST /api/pos/sync/push/invoice-details
' Tabla local VB6: detalle_factura
' Tabla servidor: pos_invoice_details
' PK servidor: (invoice_number, order_number, date, dish_id, item, depends_on)
' Nota: saved retorna claves compuestas; se marca por Nro_Factura
' ============================================================
Public Sub SincronizarDetalleFactura(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM detalle_factura WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    Dim facturas As String, sepF As String
    json = "[": sep = ""
    facturas = "": sepF = ""

    Do While Not rs.EOF
        Dim nroFactura As String
        nroFactura = rs("Nro_Factura")

        json = json & sep & "{"
        json = json & """invoice_number"":"  & """" & nroFactura                               & ""","
        json = json & """company_id"":"      & Var_Id_Company_Envio                            & ","
        json = json & """date"":"            & """" & Format(rs("Fecha"), "YYYY-MM-DD")        & ""","
        json = json & """order_number"":"    & """" & Nz(rs("Nro_Comanda"), "0")              & ""","
        json = json & """dish_id"":"         & Nz(rs("Id_Plato"), 0)                           & ","
        json = json & """item"":"            & Nz(rs("Item"), 0)                               & ","
        json = json & """depends_on"":"      & Nz(rs("Depende_De"), 0)                         & ","
        json = json & """quantity"":"        & Nz(rs("Cantidad"), 0)                           & ","
        json = json & """notes"":"           & """" & EscapeJson(Nz(rs("Notas"), ""))          & ""","
        json = json & """dish_amount"":"     & Nz(rs("Valor_Plato"), 0)                        & ","
        json = json & """complimentary"":"   & Nz(rs("Cortesia"), 0)                           & ","
        json = json & """discount_pct"":"    & Nz(rs("Dcto_Pct"), 0)
        json = json & "}"
        sep = ","

        If InStr("," & facturas & ",", "," & nroFactura & ",") = 0 Then
            facturas = facturas & sepF & """" & nroFactura & """"
            sepF = ","
        End If

        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/invoice-details", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar sincronizadas (por factura) -------------
    If facturas <> "" Then
        conn.Execute "UPDATE detalle_factura SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Factura IN (" & facturas & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Det.Factura Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
