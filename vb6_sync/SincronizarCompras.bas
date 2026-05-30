' ============================================================
' SincronizarCompras
' Endpoint: POST /api/pos/sync/push/purchases
' Tabla local VB6: compras
' Tabla servidor: pos_purchases
' Grupo sync:     J — financiero independiente, sin orden crítico entre pares
' Depende de:     ninguna
' Columnas locales:
'   Nro_Gasto, Id_Caja, Fecha_Gasto, Valor_Gasto,
'   Cod_Empleado, Cod_Concepto, Cod_Sub_Concepto,
'   Turno, Nro_Movimiento, Detalle, Enviada_MySql
' ============================================================
Public Sub SincronizarCompras(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM compras WHERE Enviada_MySql = 0 AND year(Fecha_Gasto) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON + acumular Nro_Gasto enviados ---
    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""

    Do While Not rs.EOF
        Dim idReg As Long
        idReg = Nz(rs("Nro_Gasto"), 0)

        json = json & sep & "{"
        json = json & """id_registro"":"      & idReg                                              & ","
        json = json & """company_id"":"       & Var_Id_Company_Envio                               & ","
        json = json & """register_id"":"      & Nz(rs("Id_Caja"), 0)                               & ","
        json = json & """date"":"             & """" & Format(rs("Fecha_Gasto"), "YYYY-MM-DD")     & ""","
        json = json & """amount"":"           & Nz(rs("Valor_Gasto"), 0)                           & ","
        json = json & """employee_code"":"    & """" & Nz(rs("Cod_Empleado"), "")                  & ""","
        json = json & """concept_id"":"       & Nz(rs("Cod_Concepto"), 0)                          & ","
        json = json & """sub_concept_id"":"   & Nz(rs("Cod_Sub_Concepto"), 0)                      & ","
        json = json & """shift"":"            & Nz(rs("Turno"), 0)                                 & ","
        json = json & """movement_number"":"  & Nz(rs("Nro_Movimiento"), 0)                        & ","
        json = json & """detail"":"           & """" & EscapeJson(Nz(rs("Detalle"), ""))            & """"
        json = json & "}"

        idList = idList & idSep & idReg
        sep = ",": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/purchases", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar como enviados por Nro_Gasto -------------
    If idList <> "" Then
        conn.Execute "UPDATE compras SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Gasto IN (" & idList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Compras Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
