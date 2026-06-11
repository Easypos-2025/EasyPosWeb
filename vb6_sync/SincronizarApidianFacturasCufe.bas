' ============================================================
' SincronizarApidianFacturasCufe
' Endpoint: POST /api/pos/sync/push/apidian-facturas-cufe
' Tabla local VB6: apidian_facturas_cufe
' Tabla servidor:  apidian_facturas_cufe
' Grupo sync:      I — después de SincronizarCajas (Grupo A)
' Depende de:      ninguna clave foránea crítica en servidor
' Columnas locales:
'   Nro_Caja, Prefix, Nro_Factura, Tipo_Pago, Cedula, Fecha,
'   Nro_Pedido, cufe, FEExitosa, Valor, Descuento, Empleado,
'   Pc_Desde, Estado, VentaCerrada, Observacion_Factura, Hora, Enviada_MySql
' PK servidor: UNIQUE (company_id, Nro_Caja, Prefix, Nro_Factura)
' ============================================================
Public Sub SincronizarApidianFacturasCufe(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)
    Var_Tabla_Error = "SincronizarApidianFacturasCufe"

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM apidian_facturas_cufe WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

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
        json = json & """company_id"":"          & Var_Id_Company_Envio                                          & ","
        json = json & """Nro_Caja"":"            & Nz(rs("Nro_Caja"), 0)                                         & ","
        json = json & """Prefix"":"              & """" & EscapeJson(Nz(rs("Prefix"), ""))                       & ""","
        json = json & """Nro_Factura"":"         & """" & EscapeJson(nroFac)                                     & ""","
        json = json & """Tipo_Pago"":"           & """" & EscapeJson(Nz(rs("Tipo_Pago"), ""))                   & ""","
        json = json & """Cedula"":"              & """" & EscapeJson(Nz(rs("Cedula"), ""))                       & ""","
        json = json & """Fecha"":"               & """" & Format(rs("Fecha"), "YYYY-MM-DD")                      & ""","
        json = json & """Nro_Pedido"":"          & """" & EscapeJson(Nz(rs("Nro_Pedido"), ""))                  & ""","
        json = json & """cufe"":"                & """" & EscapeJson(Nz(rs("cufe"), ""))                         & ""","
        json = json & """FEExitosa"":"           & CInt(Nz(rs("FEExitosa"), 0))                                  & ","
        json = json & """Valor"":"               & Replace(CStr(Nz(rs("Valor"), 0)), ",", ".")                   & ","
        json = json & """Descuento"":"           & Replace(CStr(Nz(rs("Descuento"), 0)), ",", ".")               & ","
        json = json & """Empleado"":"            & Nz(rs("Empleado"), 0)                                         & ","
        json = json & """Pc_Desde"":"            & """" & EscapeJson(Nz(rs("Pc_Desde"), ""))                    & ""","
        json = json & """Estado"":"              & """" & EscapeJson(Nz(rs("Estado"), ""))                       & ""","
        json = json & """VentaCerrada"":"        & CInt(Nz(rs("VentaCerrada"), 0))                               & ","
        json = json & """Observacion_Factura"":"   & """" & EscapeJson(Nz(rs("Observacion_Factura"), ""))        & ""","
        json = json & """Hora"":"                & """" & EscapeJson(Nz(rs("Hora"), ""))                         & ""","
        json = json & """Enviada_MySql"":"       & CInt(Nz(rs("Enviada_MySql"), 0))
        json = json & "}"

        idList = idList & idSep & "'" & Replace(nroFac, "'", "''") & "'"
        sep = ",": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/apidian-facturas-cufe", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar como enviados por Nro_Factura -----------
    If idList <> "" Then
        conn.Execute "UPDATE apidian_facturas_cufe SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Factura IN (" & idList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    If InStr(respuesta, "total_saved") = 0 Then
        Var_Caption_Error = "Error servidor: " & Left(respuesta, 200)
        conn.Close: Exit Sub
    End If
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "ApiFactCUFE Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
