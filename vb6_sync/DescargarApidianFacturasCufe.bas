' ============================================================
' DescargarApidianFacturasCufe.bas
' Endpoint: GET /api/pos/sync/pull/apidian-facturas-cufe
' Tabla destino local: apidian_facturas_cufe (BD principal)
' Filtro servidor: Enviada_MySql=0 OR FEExitosa=0
'
' Caso A — servidor Enviada_MySql=0 (web modificó la factura):
'   · Actualiza TODOS los campos del servidor en local
'   · Marca local Enviada_MySql=0 → push la re-envía al servidor
'
' Caso B — servidor FEExitosa=0 (DIAN falló en servidor):
'   · SOLO marca local Enviada_MySql=0 (NO toca FEExitosa local)
'   · El proceso local intentará procesar DIAN de nuevo
'   · Si local tiene FEExitosa=1, el push actualizará el servidor
'
' INSERT (no existe local): guarda todos los campos, Enviada_MySql=0
' Llamar desde el mismo ciclo que SincronizarApidianFacturasCufe
' ============================================================
Public Sub DescargarApidianFacturasCufe(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Var_Tabla_Error = "DescargarApidianFacturasCufe"

    ' -- 1. Llamar al endpoint de pull ---------------------------
    Dim respuesta As String
    respuesta = ApiGet("/sync/pull/apidian-facturas-cufe?company_id=" & Var_Id_Company_Envio & _
                       "&limit=" & CStr(Var_Limit_Registros))

    If respuesta = "" Then Exit Sub

    ' -- 2. Parsear JSON -----------------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"

    On Error Resume Next
    sc.ExecuteStatement "var resp = " & respuesta & ";"
    If Err.Number <> 0 Then
        Var_Caption_Error = "DescargarApidianFacturasCufe: JSON invalido"
        Exit Sub
    End If
    On Error GoTo ErrHandler

    Dim total As Long
    total = CLng(sc.Eval("resp.total"))
    If total = 0 Then
        Var_Caption_Error = "ApiFactCUFE Desc.: sin pendientes"
        Exit Sub
    End If

    ' -- 3. Conectar a BD local principal ------------------------
    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    Dim ins As Long, upd As Long
    ins = 0: upd = 0

    Dim i As Long
    For i = 0 To total - 1
        Dim nroCaja  As Long:    nroCaja  = CLng(sc.Eval("resp.records[" & i & "].Nro_Caja || 0"))
        Dim prefix   As String:  prefix   = Replace(CStr(sc.Eval("resp.records[" & i & "].Prefix || ''")), "'", "''")
        Dim nroFac   As String:  nroFac   = Replace(CStr(sc.Eval("resp.records[" & i & "].Nro_Factura")), "'", "''")
        Dim tipoPago As String:  tipoPago = Replace(CStr(sc.Eval("resp.records[" & i & "].Tipo_Pago || ''")), "'", "''")
        Dim cedula   As String:  cedula   = Replace(CStr(sc.Eval("resp.records[" & i & "].Cedula || ''")), "'", "''")
        Dim fecha    As String:  fecha    = CStr(sc.Eval("resp.records[" & i & "].Fecha || ''"))
        Dim nroPed   As String:  nroPed   = Replace(CStr(sc.Eval("resp.records[" & i & "].Nro_Pedido || ''")), "'", "''")
        Dim cufe     As String:  cufe     = Replace(CStr(sc.Eval("resp.records[" & i & "].cufe || ''")), "'", "''")
        Dim feExit   As Integer: feExit   = CInt(sc.Eval("resp.records[" & i & "].FEExitosa || 0"))
        Dim valor    As Double:  valor    = CDbl(sc.Eval("resp.records[" & i & "].Valor || 0"))
        Dim desc     As Double:  desc     = CDbl(sc.Eval("resp.records[" & i & "].Descuento || 0"))
        Dim empleado As Long:    empleado = CLng(sc.Eval("resp.records[" & i & "].Empleado || 0"))
        Dim pcDesde  As String:  pcDesde  = Replace(CStr(sc.Eval("resp.records[" & i & "].Pc_Desde || ''")), "'", "''")
        Dim estado   As String:  estado   = Replace(CStr(sc.Eval("resp.records[" & i & "].Estado || ''")), "'", "''")
        Dim vCerrada As Integer: vCerrada = CInt(sc.Eval("resp.records[" & i & "].VentaCerrada || 0"))
        Dim obsv     As String:  obsv     = Replace(CStr(sc.Eval("resp.records[" & i & "].Observacion_Factura || ''")), "'", "''")
        Dim hora     As String:  hora     = Replace(CStr(sc.Eval("resp.records[" & i & "].Hora || ''")), "'", "''")
        Dim enviada  As Integer: enviada  = CInt(sc.Eval("resp.records[" & i & "].Enviada_MySql || 0"))

        Dim pkWhere As String
        pkWhere = "Nro_Caja=" & nroCaja & " AND Prefix='" & prefix & "' AND Nro_Factura='" & nroFac & "'"

        Dim rs As Object
        Set rs = CreateObject("ADODB.Recordset")
        rs.Open "SELECT FEExitosa FROM apidian_facturas_cufe WHERE " & pkWhere, conn

        If rs.EOF Then
            ' Registro nuevo en local: guardar todo, Enviada_MySql=0 para trigger push
            conn.Execute "INSERT INTO apidian_facturas_cufe " & _
                "(Nro_Caja,Prefix,Nro_Factura,Tipo_Pago,Cedula,Fecha,Nro_Pedido," & _
                " cufe,FEExitosa,Valor,Descuento,Empleado,Pc_Desde,Estado," & _
                " VentaCerrada,Observacion_Factura,Hora,Enviada_MySql) VALUES (" & _
                nroCaja & ",'" & prefix & "','" & nroFac & "','" & tipoPago & "'," & _
                "'" & cedula & "','" & fecha & "','" & nroPed & "','" & cufe & "'," & _
                feExit & "," & Replace(CStr(valor), ",", ".") & "," & _
                Replace(CStr(desc), ",", ".") & "," & empleado & ",'" & pcDesde & "'," & _
                "'" & estado & "'," & vCerrada & ",'" & obsv & "','" & hora & "',0)"
            ins = ins + 1
        ElseIf enviada = 0 Then
            ' Caso A: web modificó la factura (Enviada_MySql=0 en servidor)
            ' Copiar todos los campos del servidor + marcar Enviada_MySql=0 para re-envío
            conn.Execute "UPDATE apidian_facturas_cufe SET " & _
                "cufe='" & cufe & "',FEExitosa=" & feExit & "," & _
                "Tipo_Pago='" & tipoPago & "',Cedula='" & cedula & "'," & _
                "Estado='" & estado & "',VentaCerrada=" & vCerrada & "," & _
                "Observacion_Factura='" & obsv & "',Hora='" & hora & "'," & _
                "Enviada_MySql=0" & _
                " WHERE " & pkWhere
            upd = upd + 1
        ElseIf feExit = 0 Then
            ' Caso B: DIAN falló en servidor (FEExitosa=0, Enviada_MySql=1)
            ' SOLO marcar Enviada_MySql=0 para trigger re-envío local
            ' NO tocar FEExitosa local (puede ser 1 si local procesó DIAN correctamente)
            conn.Execute "UPDATE apidian_facturas_cufe SET Enviada_MySql=0" & _
                " WHERE " & pkWhere
            upd = upd + 1
        End If
        rs.Close
        Set rs = Nothing
    Next i

    conn.Close
    Var_Caption_Error = "ApiFactCUFE Desc.: +" & ins & " nuevos | " & upd & " actualizados"
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
    Call Grabar_Error(Var_Id_Company_Web, Date, Var_Tabla_Error, Var_Caption_Error, "")
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    If Not conn Is Nothing Then conn.Close
End Sub
