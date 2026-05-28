' ============================================================
' SincronizarCajaFacturas
' Endpoint: POST /api/pos/sync/push/cash-register-invoices
' Tabla local VB6: caja_facturas
' Tabla servidor: pos_cash_register_invoices
' Columnas locales:
'   Nro_Caja, Id_Caja, Nro_Factura, Fecha, Nro_Pedido,
'   Valor, Base, Impuesto_Iva, Impuesto_Impoconsumo,
'   Empleado, Turno, Pc_Desde, Cod_Domiciliario,
'   Observacion_Factura, prefix, fac_pe, Enviada_MySql
' ============================================================
Public Sub SincronizarCajaFacturas(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM caja_facturas WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON + acumular Nro_Factura enviados --
    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""

    Do While Not rs.EOF
        Dim nroFac As String
        nroFac = Nz(rs("Nro_Factura"), "")

        json = json & sep & "{"
        json = json & """register_number"":"    & Nz(rs("Nro_Caja"), 0)                              & ","
        json = json & """closing_id"":"         & Nz(rs("Id_Caja"), 0)                               & ","
        json = json & """invoice_number"":"     & """" & nroFac                                      & ""","
        json = json & """company_id"":"         & Var_Id_Company_Envio                               & ","
        json = json & """date"":"               & """" & Format(rs("Fecha"), "YYYY-MM-DD")           & ""","
        json = json & """order_number"":"       & """" & Nz(rs("Nro_Pedido"), "")                   & ""","
        json = json & """amount"":"             & Nz(rs("Valor"), 0)                                 & ","
        json = json & """base_amount"":"        & Nz(rs("Base"), 0)                                  & ","
        json = json & """tax_vat"":"            & Nz(rs("Impuesto_Iva"), 0)                          & ","
        json = json & """tax_consumption"":"    & Nz(rs("Impuesto_Impoconsumo"), 0)                  & ","
        json = json & """employee_id"":"        & Nz(rs("Empleado"), 0)                              & ","
        json = json & """shift"":"              & Nz(rs("Turno"), 0)                                 & ","
        json = json & """source_pc"":"          & """" & Nz(rs("Pc_Desde"), "")                     & ""","
        json = json & """delivery_person_id"":"  & Nz(rs("Cod_Domiciliario"), 0)                     & ","
        json = json & """invoice_notes"":"      & """" & EscapeJson(Nz(rs("Observacion_Factura"), "")) & ""","
        json = json & """prefix"":"             & """" & Nz(rs("prefix"), "")                       & ""","
        json = json & """fac_pe"":"             & """" & Nz(rs("fac_pe"), "")                       & """"
        json = json & "}"

        idList = idList & idSep & "'" & nroFac & "'"
        sep = ",": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/cash-register-invoices", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar como enviados por Nro_Factura -----------
    If idList <> "" Then
        conn.Execute "UPDATE caja_facturas SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Factura IN (" & idList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Caja Fact. Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
