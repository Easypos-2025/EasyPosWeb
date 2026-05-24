' ============================================================
' SincronizarCierresCaja
' Endpoint: POST /api/pos/sync/push/cash-closings
' Tabla local VB6: cierres_caja
' Tabla servidor: pos_cash_register_closings
' PK servidor: id (= Id_Registro en VB6)
' ============================================================
Public Sub SincronizarCierresCaja(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM cierres_caja WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"                   & Nz(rs("Id_Registro"), 0)                       & ","
        json = json & """company_id"":"            & Var_Id_Company_Envio                           & ","
        json = json & """register_number"":"       & Nz(rs("Nro_Caja"), 0)                         & ","
        json = json & """shift"":"                 & Nz(rs("Turno"), 0)                             & ","
        json = json & """date"":"                  & """" & Format(rs("Fecha"), "YYYY-MM-DD")       & ""","
        json = json & """base_amount"":"           & Nz(rs("Base"), 0)                              & ","
        json = json & """total_sales"":"           & Nz(rs("Total_Ventas"), 0)                      & ","
        json = json & """cash_sales"":"            & Nz(rs("Ventas_Efectivo"), 0)                   & ","
        json = json & """voucher_sales"":"         & Nz(rs("Ventas_Bonos"), 0)                      & ","
        json = json & """tips"":"                  & Nz(rs("Propinas"), 0)                          & ","
        json = json & """extra_tips"":"            & Nz(rs("Propinas_Extra"), 0)                    & ","
        json = json & """expenses"":"              & Nz(rs("Gastos"), 0)                            & ","
        json = json & """vouchers"":"              & Nz(rs("Bonos"), 0)                             & ","
        json = json & """manager_consumption"":"   & Nz(rs("Consumo_Gerente"), 0)                   & ","
        json = json & """final_base"":"            & Nz(rs("Base_Final"), 0)                        & ","
        json = json & """total_invoices"":"        & Nz(rs("Total_Facturas"), 0)                    & ","
        json = json & """voucher_invoices"":"      & Nz(rs("Facturas_Bonos"), 0)                    & ","
        json = json & """copy_invoices"":"         & Nz(rs("Facturas_Copia"), 0)                    & ","
        json = json & """voided_invoices"":"       & Nz(rs("Facturas_Anuladas"), 0)                 & ","
        json = json & """invoice_start"":"         & """" & Nz(rs("Desde_Factura"), "0")            & ""","
        json = json & """invoice_end"":"           & """" & Nz(rs("Hasta_Factura"), "0")            & ""","
        json = json & """bills"":"                 & Nz(rs("Billetes"), 0)                          & ","
        json = json & """coins"":"                 & Nz(rs("Monedas"), 0)                           & ","
        json = json & """purchases"":"             & Nz(rs("Compras"), 0)                           & ","
        json = json & """customer_sales"":"        & Nz(rs("Ventas_Cliente"), 0)                    & ","
        json = json & """closed"":"                & Nz(rs("Cerrado"), 0)                           & ","
        json = json & """invoice_start_manual"":"  & """" & Nz(rs("Desde_Manual"), "")             & ""","
        json = json & """invoice_end_manual"":"    & """" & Nz(rs("Hasta_Manual"), "")             & ""","
        json = json & """delivery_income"":"       & Nz(rs("Ingreso_Domicilio"), 0)                 & ","
        json = json & """delivery_expense"":"      & Nz(rs("Gasto_Domicilio"), 0)                   & ","
        json = json & """opened_pc"":"             & """" & Nz(rs("PC_Apertura"), "")              & ""","
        json = json & """closing_notes"":"         & """" & EscapeJson(Nz(rs("Notas_Cierre"), "")) & ""","
        json = json & """opening_datetime"":"      & """" & Nz(rs("Fecha_Apertura"), "")           & ""","
        json = json & """closing_datetime"":"      & """" & Nz(rs("Fecha_Cierre"), "")             & """"
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/cash-closings", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE cierres_caja SET Enviada_MySql = 1 " & _
                     "WHERE Id_Registro IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Cierres Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
