' ============================================================
' SincronizarConsecutivoFacturaManual
' Endpoint: POST /api/pos/sync/push/consecutivo-factura-manual
' Tabla local VB6: consecutivo_factura_manual
' Tabla servidor:  consecutivo_factura_manual
' Grupo sync:      A — tabla maestra de resoluciones, sin dependencias críticas
' Depende de:      ninguna
' Columnas locales:
'   Id_Consecutivo, Nro_Pedido, Fecha, Id_Resolucion, Enviada_MySql
' PK servidor: UNIQUE (company_id, Id_Consecutivo)
' ============================================================
Public Sub SincronizarConsecutivoFacturaManual(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)
    Var_Tabla_Error = "SincronizarConsecutivoFacturaManual"

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM consecutivo_factura_manual WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON + acumular Id_Consecutivo enviados --
    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""

    Do While Not rs.EOF
        Dim idCons As Long
        idCons = CLng(Nz(rs("Id_Consecutivo"), 0))

        json = json & sep & "{"
        json = json & """company_id"":"     & Var_Id_Company_Envio                                  & ","
        json = json & """Id_Consecutivo"":"  & idCons                                                & ","
        json = json & """Nro_Pedido"":"     & """" & EscapeJson(Nz(rs("Nro_Pedido"), ""))           & ""","
        json = json & """Fecha"":"          & """" & Format(rs("Fecha"), "YYYY-MM-DD")              & ""","
        json = json & """Id_Resolucion"":"  & Nz(rs("Id_Resolucion"), 0)                             & ","
        json = json & """Enviada_MySql"":"  & CInt(Nz(rs("Enviada_MySql"), 0))
        json = json & "}"

        idList = idList & idSep & idCons
        sep = ",": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/consecutivo-factura-manual", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar como enviados por Id_Consecutivo --------
    If idList <> "" Then
        conn.Execute "UPDATE consecutivo_factura_manual SET Enviada_MySql = 1 " & _
                     "WHERE Id_Consecutivo IN (" & idList & ")"
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
    Var_Caption_Error = "ConsecManual Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
