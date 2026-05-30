' ============================================================
' SincronizarZonasAsientos
' Endpoint: POST /api/pos/sync/push/zones
' Tabla local VB6: zonas_asientos
' Tabla servidor: pos_zones
' Grupo sync:     A — sin dependencias, tabla maestra base
' Depende de:     ninguna
' Mapeo:
'   Id_Sede   -> branch_id  (sede/sucursal en VB6)
'   Id_Zona   -> id         (ID de la zona)
'   Ubicacion -> name
'   Nro_Asientos -> seats_count
'   Activa    -> is_active
'   Zona_Dinamica -> dynamic_zone
'   Color     -> color
'   Altura    -> height
' Envia TODAS las zonas activas (tabla peque~a, sin flag Enviada_MySql)
' ============================================================
Public Sub SincronizarZonasAsientos(Var_Id_Company_Envio As Integer)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer todas las zonas activas (sin filtrar por sede) --
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM zonas_asientos WHERE Activa = 1", conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ------------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"            & Nz(rs("Id_Zona"), 0)                              & ","
        json = json & """company_id"":"    & Var_Id_Company_Envio                               & ","
        json = json & """branch_id"":"     & Nz(rs("Id_Sede"), 1)                              & ","
        json = json & """name"":"          & """" & EscapeJson(Nz(rs("Ubicacion"), ""))        & ""","
        json = json & """seats_count"":"   & Nz(rs("Nro_Asientos"), 0)                         & ","
        json = json & """is_active"":"     & Nz(rs("Activa"), 1)                               & ","
        json = json & """dynamic_zone"":"  & Nz(rs("Zona_Dinamica"), 0)                        & ","
        json = json & """color"":"         & """" & Nz(rs("Color"), "#1d4ed8")                 & ""","
        json = json & """height"":"        & Nz(rs("Altura"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close
    conn.Close

    ' -- 3. Enviar al servidor --------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/zones", json)

    If respuesta = "" Then Exit Sub

    ' -- 4. Mostrar estado ------------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Zonas Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
