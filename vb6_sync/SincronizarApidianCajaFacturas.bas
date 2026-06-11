' ============================================================
' SincronizarApidianCajaFacturas
' Endpoint: POST /api/pos/sync/push/apidian-caja-facturas
' Tabla local VB6: apidian_caja_facturas
' Tabla servidor:  apidian_caja_facturas
' Grupo sync:      I — después de SincronizarCajas (Grupo A)
' Depende de:      ninguna clave foránea crítica en servidor
' Columnas locales:
'   Nro_Caja, Nro_Factura, Fecha, Nro_Pedido,
'   Valor, Base, Impuesto_Iva, Impuesto_Impoconsumo,
'   Empleado, Turno, Pc_Desde, Cod_Domiciliario,
'   Observacion_Factura, Prefix, Fac_PE, Enviada_MySql
' PK servidor: UNIQUE (company_id, Nro_Caja, Nro_Factura)
' ============================================================
Public Sub SincronizarApidianCajaFacturas(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)
    Var_Tabla_Error = "SincronizarApidianCajaFacturas"

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM apidian_caja_facturas WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

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
        json = json & """company_id"":"         & Var_Id_Company_Envio                                          & ","
        json = json & """Nro_Caja"":"           & Nz(rs("Nro_Caja"), 0)                                         & ","
        json = json & """Nro_Factura"":"        & """" & EscapeJson(nroFac)                                     & ""","
        json = json & """Fecha"":"              & """" & Format(rs("Fecha"), "YYYY-MM-DD")                      & ""","
        json = json & """Nro_Pedido"":"         & """" & EscapeJson(Nz(rs("Nro_Pedido"), ""))                  & ""","
        json = json & """Valor"":"              & Replace(CStr(Nz(rs("Valor"), 0)), ",", ".")                    & ","
        json = json & """Base"":"               & Replace(CStr(Nz(rs("Base"), 0)), ",", ".")                     & ","
        json = json & """Impuesto_Iva"":"       & Replace(CStr(Nz(rs("Impuesto_Iva"), 0)), ",", ".")             & ","
        json = json & """Impuesto_Impoconsumo"":"  & Replace(CStr(Nz(rs("Impuesto_Impoconsumo"), 0)), ",", ".") & ","
        json = json & """Empleado"":"           & Nz(rs("Empleado"), 0)                                          & ","
        json = json & """Turno"":"              & Nz(rs("Turno"), 0)                                             & ","
        json = json & """Pc_Desde"":"           & """" & EscapeJson(Nz(rs("Pc_Desde"), ""))                    & ""","
        json = json & """Cod_Domiciliario"":"   & Nz(rs("Cod_Domiciliario"), 0)                                  & ","
        json = json & """Observacion_Factura"":"  & """" & EscapeJson(Nz(rs("Observacion_Factura"), ""))        & ""","
        json = json & """Prefix"":"             & """" & EscapeJson(Nz(rs("Prefix"), ""))                       & ""","
        json = json & """Fac_PE"":"             & """" & EscapeJson(Nz(rs("Fac_PE"), ""))                       & ""","
        json = json & """Enviada_MySql"":"      & CInt(Nz(rs("Enviada_MySql"), 0))
        json = json & "}"

        idList = idList & idSep & "'" & Replace(nroFac, "'", "''") & "'"
        sep = ",": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/apidian-caja-facturas", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar como enviados por Nro_Factura -----------
    If idList <> "" Then
        conn.Execute "UPDATE apidian_caja_facturas SET Enviada_MySql = 1 " & _
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
    Var_Caption_Error = "ApiCajaFact. Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
