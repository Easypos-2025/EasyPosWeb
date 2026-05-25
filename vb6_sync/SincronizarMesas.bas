' ============================================================
' SincronizarMesas
' Endpoint: POST /api/pos/sync/push/tables
' Tabla local VB6: mesas
' Tabla servidor: pos_tables
' Columnas locales:
'   Id_Mesa, Id_Sede, Mesa, Ubicacion, Nro_Puestos,
'   Id_Cliente, Zona_Dinamica, Activa, Id_Zona, Enviada_MySql
' Columnas enviadas al servidor: id, company_id, zone_id,
'   name, capacity, is_active
' PK servidor: (id, company_id)
' ============================================================
Public Sub SincronizarMesas(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM mesas WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"           & Nz(rs("Id_Mesa"), 0)             & ","
        json = json & """company_id"":"   & Var_Id_Company_Envio             & ","
        json = json & """zone_id"":"      & Nz(rs("Id_Zona"), 0)             & ","
        json = json & """name"":"         & """" & EscapeJson("" & rs("Mesa"))  & ""","
        json = json & """capacity"":"     & Nz(rs("Nro_Puestos"), 0)         & ","
        json = json & """is_active"":"    & Nz(rs("Activa"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/tables", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE mesas SET Enviada_MySql = 1 " & _
                     "WHERE Id_Mesa IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Mesas Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
