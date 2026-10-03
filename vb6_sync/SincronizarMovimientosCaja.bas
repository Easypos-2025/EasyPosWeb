Attribute VB_Name = "SincronizarMovimientosCaja"
' ============================================================
' Movimientos de caja para el Cuadre de Caja web
'   SincronizarConceptos                 conceptos                   -> /sync/push/cash-concepts
'   SincronizarSubConceptos              sub_conceptos               -> /sync/push/cash-subconcepts
'   SincronizarOtrosIngresos             otros_ingresos              -> /sync/push/other-incomes
'   SincronizarOtrosEgresos              otros_egresos               -> /sync/push/other-expenses
'   SincronizarVales                     vales                       -> /sync/push/cash-advances
'   SincronizarIngresosEgresosFormaPago  ingresos_egresos_forma_pago -> /sync/push/cash-movement-payments
'
' - Todas las tablas usan Enviada_MySql (conceptos, sub_conceptos e ingresos_egresos_forma_pago
'   lo tienen agregado): se envían los pendientes y se marcan al confirmar.
' - Se marca Enviada_MySql = 1 solo si el servidor respondió sin fallas (si falla, el lote
'   se reintenta en el siguiente ciclo y el error queda en Grabar_Error).
' - Números siempre con punto decimal (NumMC) y textos escapados (TxtMC).
' ============================================================
Option Explicit

' -- Número con punto decimal (la configuración regional puede usar coma) --
Private Function NumMC(ByVal v As Variant) As String
    NumMC = Replace(CStr(Nz(v, 0)), ",", ".")
End Function

' -- Texto JSON entre comillas y escapado --
Private Function TxtMC(ByVal v As Variant) As String
    TxtMC = """" & EscapeJson("" & Nz(v, "")) & """"
End Function

' -- Fecha JSON (vacía -> null) --
Private Function FechaMC(ByVal v As Variant) As String
    If IsNull(v) Or IsEmpty(v) Then
        FechaMC = "null"
    Else
        FechaMC = """" & Format(v, "YYYY-MM-DD") & """"
    End If
End Function

' -- Lee total_saved / total_failed de la respuesta y deja el estado en Var_Caption_Error --
Private Function SinFallasMC(ByVal respuesta As String, ByVal titulo As String) As Boolean
    On Error GoTo ErrHandler
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = titulo & " Env.: " & sc.Eval("r.total_saved") & " | Fallidas: " & sc.Eval("r.total_failed")
    SinFallasMC = (CLng(sc.Eval("r.total_failed")) = 0)
    If Not SinFallasMC Then
        Call Grabar_Error(Var_Id_Company_Web, Date, Var_Tabla_Error, Left(respuesta, 250), "")
    End If
    Exit Function
ErrHandler:
    SinFallasMC = False
End Function


' ============================================================
' conceptos -> pos_cash_concepts
' Columnas: Cod_Concepto, descripcion, Tipo_Concepto, Activo, Enviada_MySql
' ============================================================
Public Sub SincronizarConceptos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler
    Var_Tabla_Error = "SincronizarConceptos"

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM conceptos WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn
    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String, idList As String
    json = "[": sep = "": idList = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """company_id"":" & Var_Id_Company_Envio & ","
        json = json & """concept_id"":" & NumMC(rs("Cod_Concepto")) & ","
        json = json & """description"":" & TxtMC(rs("descripcion")) & ","
        json = json & """concept_type"":" & NumMC(rs("Tipo_Concepto")) & ","
        json = json & """is_active"":" & NumMC(rs("Activo"))
        json = json & "}"
        idList = idList & sep & Nz(rs("Cod_Concepto"), 0)
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/cash-concepts", json)
    If respuesta = "" Then
        conn.Close: Exit Sub
    End If
    If SinFallasMC(respuesta, "Conceptos") Then
        conn.Execute "UPDATE conceptos SET Enviada_MySql = 1 WHERE Cod_Concepto IN (" & idList & ")"
    End If
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
    Call Grabar_Error(Var_Id_Company_Web, Date, Var_Tabla_Error, Var_Caption_Error, "")
End Sub


' ============================================================
' sub_conceptos -> pos_cash_subconcepts
' Columnas: Cod_Concepto, Cod_Sub_Concepto, Descripcion_Sub_Concepto, Activo, Enviada_MySql
' ============================================================
Public Sub SincronizarSubConceptos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler
    Var_Tabla_Error = "SincronizarSubConceptos"

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM sub_conceptos WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn
    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String, cond As String
    json = "[": sep = "": cond = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """company_id"":" & Var_Id_Company_Envio & ","
        json = json & """concept_id"":" & NumMC(rs("Cod_Concepto")) & ","
        json = json & """subconcept_id"":" & NumMC(rs("Cod_Sub_Concepto")) & ","
        json = json & """description"":" & TxtMC(rs("Descripcion_Sub_Concepto")) & ","
        json = json & """is_active"":" & NumMC(rs("Activo"))
        json = json & "}"
        If cond <> "" Then cond = cond & " OR "
        cond = cond & "(Cod_Concepto = " & Nz(rs("Cod_Concepto"), 0) & " AND Cod_Sub_Concepto = " & Nz(rs("Cod_Sub_Concepto"), 0) & ")"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/cash-subconcepts", json)
    If respuesta = "" Then
        conn.Close: Exit Sub
    End If
    If SinFallasMC(respuesta, "SubConceptos") Then
        conn.Execute "UPDATE sub_conceptos SET Enviada_MySql = 1 WHERE " & cond
    End If
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
    Call Grabar_Error(Var_Id_Company_Web, Date, Var_Tabla_Error, Var_Caption_Error, "")
End Sub


' ============================================================
' otros_ingresos / otros_egresos (misma estructura que gastos)
' Columnas: Nro_Gasto, Id_Caja, Fecha_Gasto, Valor_Gasto, Cod_Empleado, Cod_Concepto,
'           Cod_Sub_Concepto, Turno, Nro_Movimiento, Detalle, Enviada_MySql
' ============================================================
Private Sub SincronizarMovimientoMC(ByVal tabla As String, ByVal endpoint As String, ByVal titulo As String, _
                                    Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM " & tabla & " WHERE Enviada_MySql = 0 AND year(Fecha_Gasto) >= 2024 LIMIT " & Var_Limit_Registros, conn
    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String, idList As String
    json = "[": sep = "": idList = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id_registro"":" & NumMC(rs("Nro_Gasto")) & ","
        json = json & """company_id"":" & Var_Id_Company_Envio & ","
        json = json & """register_id"":" & NumMC(rs("Id_Caja")) & ","
        json = json & """date"":" & FechaMC(rs("Fecha_Gasto")) & ","
        json = json & """amount"":" & NumMC(rs("Valor_Gasto")) & ","
        json = json & """employee_code"":" & TxtMC(rs("Cod_Empleado")) & ","
        json = json & """concept_id"":" & NumMC(rs("Cod_Concepto")) & ","
        json = json & """sub_concept_id"":" & NumMC(rs("Cod_Sub_Concepto")) & ","
        json = json & """shift"":" & NumMC(rs("Turno")) & ","
        json = json & """movement_number"":" & NumMC(rs("Nro_Movimiento")) & ","
        json = json & """detail"":" & TxtMC(rs("Detalle"))
        json = json & "}"
        idList = idList & sep & Nz(rs("Nro_Gasto"), 0)
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    Dim respuesta As String
    respuesta = ApiPost(endpoint, json)
    If respuesta = "" Then
        conn.Close: Exit Sub
    End If
    If SinFallasMC(respuesta, titulo) Then
        conn.Execute "UPDATE " & tabla & " SET Enviada_MySql = 1 WHERE Nro_Gasto IN (" & idList & ")"
    End If
    conn.Close
End Sub

Public Sub SincronizarOtrosIngresos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler
    Var_Tabla_Error = "SincronizarOtrosIngresos"
    Call SincronizarMovimientoMC("otros_ingresos", "/sync/push/other-incomes", "Otros Ingresos", _
                                 Var_Id_Company_Envio, Var_Limit_Registros)
    Exit Sub
ErrHandler:
    Var_Caption_Error = Err.Description
    Call Grabar_Error(Var_Id_Company_Web, Date, Var_Tabla_Error, Var_Caption_Error, "")
End Sub

Public Sub SincronizarOtrosEgresos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler
    Var_Tabla_Error = "SincronizarOtrosEgresos"
    Call SincronizarMovimientoMC("otros_egresos", "/sync/push/other-expenses", "Otros Egresos", _
                                 Var_Id_Company_Envio, Var_Limit_Registros)
    Exit Sub
ErrHandler:
    Var_Caption_Error = Err.Description
    Call Grabar_Error(Var_Id_Company_Web, Date, Var_Tabla_Error, Var_Caption_Error, "")
End Sub


' ============================================================
' vales -> pos_cash_advances
' Columnas: Cod_Vale, Id_Caja, Fecha_Vale, Valor_Vale, Cod_Empleado, Estado,
'           Descripcion, Turno, Enviada_MySql
' ============================================================
Public Sub SincronizarVales(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler
    Var_Tabla_Error = "SincronizarVales"

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM vales WHERE Enviada_MySql = 0 AND year(Fecha_Vale) >= 2024 LIMIT " & Var_Limit_Registros, conn
    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String, idList As String
    json = "[": sep = "": idList = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id_registro"":" & NumMC(rs("Cod_Vale")) & ","
        json = json & """company_id"":" & Var_Id_Company_Envio & ","
        json = json & """register_id"":" & NumMC(rs("Id_Caja")) & ","
        json = json & """date"":" & FechaMC(rs("Fecha_Vale")) & ","
        json = json & """amount"":" & NumMC(rs("Valor_Vale")) & ","
        json = json & """employee_code"":" & TxtMC(rs("Cod_Empleado")) & ","
        json = json & """status"":" & NumMC(rs("Estado")) & ","
        json = json & """description"":" & TxtMC(rs("Descripcion")) & ","
        json = json & """shift"":" & NumMC(rs("Turno"))
        json = json & "}"
        idList = idList & sep & Nz(rs("Cod_Vale"), 0)
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/cash-advances", json)
    If respuesta = "" Then
        conn.Close: Exit Sub
    End If
    If SinFallasMC(respuesta, "Vales") Then
        conn.Execute "UPDATE vales SET Enviada_MySql = 1 WHERE Cod_Vale IN (" & idList & ")"
    End If
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
    Call Grabar_Error(Var_Id_Company_Web, Date, Var_Tabla_Error, Var_Caption_Error, "")
End Sub


' ============================================================
' ingresos_egresos_forma_pago -> pos_cash_movement_payments
' Columnas: Id_Registro, Id_Caja, Item, Id_Forma_Pago, Id_Tarjeta, Nro_Factura, Id_Tipo,
'           Turno, Valor, Fecha, Autorizacion, Observacion, Nro_Gasto, Enviada_MySql
' ============================================================
Public Sub SincronizarIngresosEgresosFormaPago(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler
    Var_Tabla_Error = "SincronizarIngresosEgresosFormaPago"

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM ingresos_egresos_forma_pago WHERE Enviada_MySql = 0 AND year(Fecha) >= 2024 LIMIT " & Var_Limit_Registros, conn
    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String, idList As String
    json = "[": sep = "": idList = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id_registro"":" & NumMC(rs("Id_Registro")) & ","
        json = json & """company_id"":" & Var_Id_Company_Envio & ","
        json = json & """register_id"":" & NumMC(rs("Id_Caja")) & ","
        json = json & """item"":" & NumMC(rs("Item")) & ","
        json = json & """payment_method_id"":" & NumMC(rs("Id_Forma_Pago")) & ","
        json = json & """card_id"":" & NumMC(rs("Id_Tarjeta")) & ","
        json = json & """invoice_number"":" & TxtMC(rs("Nro_Factura")) & ","
        json = json & """type_id"":" & NumMC(rs("Id_Tipo")) & ","
        json = json & """shift"":" & NumMC(rs("Turno")) & ","
        json = json & """amount"":" & NumMC(rs("Valor")) & ","
        json = json & """date"":" & FechaMC(rs("Fecha")) & ","
        json = json & """authorization"":" & NumMC(rs("Autorizacion")) & ","
        json = json & """notes"":" & TxtMC(rs("Observacion")) & ","
        json = json & """movement_id"":" & NumMC(rs("Nro_Gasto"))
        json = json & "}"
        idList = idList & sep & NumMC(rs("Id_Registro"))
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/cash-movement-payments", json)
    If respuesta = "" Then
        conn.Close: Exit Sub
    End If
    If SinFallasMC(respuesta, "F.Pago Movimientos") Then
        conn.Execute "UPDATE ingresos_egresos_forma_pago SET Enviada_MySql = 1 WHERE Id_Registro IN (" & idList & ")"
    End If
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
    Call Grabar_Error(Var_Id_Company_Web, Date, Var_Tabla_Error, Var_Caption_Error, "")
End Sub
