' ============================================================
' SincronizarCierresCaja
' Endpoint: POST /api/pos/sync/push/cash-closings-v2
' Tabla local VB6: cajas_cierres
' Tabla servidor: pos_cash_register_closings
' Grupo sync:     J — después de SincronizarCajas (Grupo A)
' Depende de:     pos_cash_registers
' Columnas locales:
'   Id_Caja, Nro_Caja, Turno, Fecha, Base,
'   Venta_Total, Venta_Efectivo, Venta_Baucher,
'   Propinas, Propinas_Extra, Gastos, Vales,
'   Consumo_Jefes, Base_Final, F_Totales, F_Baucher,
'   F_Copias, F_Anuladas, Factura_Inicio, Factura_Fin,
'   Billetes, Monedas, Compras, Venta_Clientes, Cierre,
'   Factura_Inicio_Manual, Factura_Fin_Manual, Enviada_MySql,
'   Ingreso_Domicilio, Egreso_Domicilio, Pc_Abierta,
'   Observaciones_Cierre, Fecha_Hora_Apertura, Fecha_Hora_Cierre
' PK servidor: UNIQUE(id_registro, company_id) — id_registro = Id_Caja en VB6
' ============================================================
Public Sub SincronizarCierresCaja(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM cajas_cierres WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON + acumular Id_Caja enviados -----
    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""

    Do While Not rs.EOF
        Dim idCaja As Long
        idCaja = Nz(rs("Id_Caja"), 0)

        json = json & sep & "{"
        json = json & """id_registro"":"              & idCaja                                          & ","
        json = json & """company_id"":"            & Var_Id_Company_Envio                              & ","
        json = json & """register_number"":"       & Nz(rs("Nro_Caja"), 0)                            & ","
        json = json & """shift"":"                 & Nz(rs("Turno"), 0)                                & ","
        json = json & """date"":"                  & """" & Format(rs("Fecha"), "YYYY-MM-DD")          & ""","
        json = json & """base_amount"":"           & Nz(rs("Base"), 0)                                 & ","
        json = json & """total_sales"":"           & Nz(rs("Venta_Total"), 0)                          & ","
        json = json & """cash_sales"":"            & Nz(rs("Venta_Efectivo"), 0)                       & ","
        json = json & """voucher_sales"":"         & Nz(rs("Venta_Baucher"), 0)                        & ","
        json = json & """tips"":"                  & Nz(rs("Propinas"), 0)                             & ","
        json = json & """extra_tips"":"            & Nz(rs("Propinas_Extra"), 0)                       & ","
        json = json & """expenses"":"              & Nz(rs("Gastos"), 0)                               & ","
        json = json & """vouchers"":"              & Nz(rs("Vales"), 0)                                & ","
        json = json & """manager_consumption"":"   & Nz(rs("Consumo_Jefes"), 0)                        & ","
        json = json & """final_base"":"            & Nz(rs("Base_Final"), 0)                           & ","
        json = json & """total_invoices"":"        & Nz(rs("F_Totales"), 0)                            & ","
        json = json & """voucher_invoices"":"      & Nz(rs("F_Baucher"), 0)                            & ","
        json = json & """copy_invoices"":"         & Nz(rs("F_Copias"), 0)                             & ","
        json = json & """voided_invoices"":"       & Nz(rs("F_Anuladas"), 0)                           & ","
        json = json & """invoice_start"":"         & """" & ("" & rs("Factura_Inicio"))                & ""","
        json = json & """invoice_end"":"           & """" & ("" & rs("Factura_Fin"))                   & ""","
        json = json & """bills"":"                 & Nz(rs("Billetes"), 0)                             & ","
        json = json & """coins"":"                 & Nz(rs("Monedas"), 0)                              & ","
        json = json & """purchases"":"             & Nz(rs("Compras"), 0)                              & ","
        json = json & """customer_sales"":"        & Nz(rs("Venta_Clientes"), 0)                       & ","
        json = json & """closed"":"                & Nz(rs("Cierre"), 0)                               & ","
        json = json & """invoice_start_manual"":"  & """" & ("" & rs("Factura_Inicio_Manual"))         & ""","
        json = json & """invoice_end_manual"":"    & """" & ("" & rs("Factura_Fin_Manual"))            & ""","
        json = json & """delivery_income"":"       & Nz(rs("Ingreso_Domicilio"), 0)                    & ","
        json = json & """delivery_expense"":"      & Nz(rs("Egreso_Domicilio"), 0)                     & ","
        json = json & """opened_pc"":"             & """" & ("" & rs("Pc_Abierta"))                    & ""","
        json = json & """closing_notes"":"         & """" & EscapeJson("" & rs("Observaciones_Cierre")) & ""","
        json = json & """opening_datetime"":"      & """" & ("" & rs("Fecha_Hora_Apertura"))           & ""","
        json = json & """closing_datetime"":"      & """" & ("" & rs("Fecha_Hora_Cierre"))             & """"
        json = json & "}"

        idList = idList & idSep & idCaja
        sep = ",": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/cash-closings-v2", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar como enviados por Id_Caja ---------------
    If idList <> "" Then
        conn.Execute "UPDATE cajas_cierres SET Enviada_MySql = 1 " & _
                     "WHERE Id_Caja IN (" & idList & ")"
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
