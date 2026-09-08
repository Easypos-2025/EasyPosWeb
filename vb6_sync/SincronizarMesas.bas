' ============================================================
' SincronizarMesas
' Endpoints:
'   POST /api/pos/sync/push/tables      (solo fijas, Id_Mesa<1000)
'   POST /api/pos/sync/push/temp-mesas  (todas: fijas + dinamicas)
' Tabla local VB6: mesas
' Tabla servidor:  pos_tables_layout (catalogo curado, solo fijas)
'                  datatemppos.temp_mesas (espejo fiel, todas)
' Grupo sync:     B — después de SincronizarZonasAsientos (Grupo A)
' Depende de:     pos_zones
' Columnas locales:
'   Id_Mesa, Id_Sede, Mesa, Ubicacion, Nro_Puestos,
'   Id_Cliente, Zona_Dinamica, Activa, Id_Zona, Enviada_MySql
' Columnas enviadas a /sync/push/tables: id, company_id, zone_id,
'   name, capacity, is_active
' Columnas enviadas a /sync/push/temp-mesas: igual + is_dynamic,
'   customer_id (derivado de Id_Cliente)
' PK servidor pos_tables_layout: (id, company_id)
' PK servidor temp_mesas:        (company_id, Id_Mesa)
'
' Las mesas dinamicas (Id_Mesa >= 1000: domicilios, plazoleta, cuentas
' con nombre del cliente) NO se registran en pos_tables_layout — ese es
' el catalogo curado por el admin en "Configurar Mesas" y no deben
' contaminarlo con cuentas de un solo uso. Se suben SOLO a temp_mesas
' para que el dashboard web las pueda listar igual que las fijas.
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

    ' -- 2. Construir JSON: fijas (→pos_tables_layout) y todas (→temp_mesas) --
    Dim jsonFijas As String, sepFijas As String
    Dim jsonTodas As String, sepTodas As String
    jsonFijas = "[": sepFijas = ""
    jsonTodas = "[": sepTodas = ""

    Do While Not rs.EOF
        Dim esDinamica As Integer
        esDinamica = IIf(Nz(rs("Id_Mesa"), 0) >= 1000, 1, 0)

        If esDinamica = 0 Then
            jsonFijas = jsonFijas & sepFijas & "{"
            jsonFijas = jsonFijas & """id"":"         & Nz(rs("Id_Mesa"), 0)            & ","
            jsonFijas = jsonFijas & """company_id"":" & Var_Id_Company_Envio            & ","
            jsonFijas = jsonFijas & """zone_id"":"    & Nz(rs("Id_Zona"), 0)            & ","
            jsonFijas = jsonFijas & """name"":"       & """" & EscapeJson("" & rs("Mesa")) & ""","
            jsonFijas = jsonFijas & """capacity"":"   & Nz(rs("Nro_Puestos"), 0)        & ","
            jsonFijas = jsonFijas & """is_active"":"  & Nz(rs("Activa"), 0)
            jsonFijas = jsonFijas & "}"
            sepFijas = ","
        End If

        jsonTodas = jsonTodas & sepTodas & "{"
        jsonTodas = jsonTodas & """id"":"          & Nz(rs("Id_Mesa"), 0)             & ","
        jsonTodas = jsonTodas & """company_id"":"  & Var_Id_Company_Envio             & ","
        jsonTodas = jsonTodas & """zone_id"":"     & Nz(rs("Id_Zona"), 0)             & ","
        jsonTodas = jsonTodas & """name"":"        & """" & EscapeJson("" & rs("Mesa")) & ""","
        jsonTodas = jsonTodas & """capacity"":"    & Nz(rs("Nro_Puestos"), 0)         & ","
        jsonTodas = jsonTodas & """is_active"":"   & Nz(rs("Activa"), 0)              & ","
        jsonTodas = jsonTodas & """is_dynamic"":"  & esDinamica                       & ","
        jsonTodas = jsonTodas & """customer_id"":" & Nz(rs("Id_Cliente"), 0)
        jsonTodas = jsonTodas & "}"
        sepTodas = ","

        rs.MoveNext
    Loop
    jsonFijas = jsonFijas & "]"
    jsonTodas = jsonTodas & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuestaFijas As String
    respuestaFijas = "{""total_saved"":0,""total_failed"":0}"
    If sepFijas <> "" Then
        respuestaFijas = ApiPost("/sync/push/tables", jsonFijas)
        If respuestaFijas = "" Then respuestaFijas = "{""total_saved"":0,""total_failed"":0}"
    End If

    Dim respuestaTodas As String
    respuestaTodas = ApiPost("/sync/push/temp-mesas", jsonTodas)

    If respuestaTodas = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar confirmadas (una mesa se marca enviada solo si quedo
    '       confirmada en temp-mesas; para las fijas ademas debio quedar
    '       confirmada en tables) -----------------------------
    Dim savedList As String
    savedList = ParseSaved(respuestaTodas)

    If savedList <> "" Then
        conn.Execute "UPDATE mesas SET Enviada_MySql = 1 " & _
                     "WHERE Id_Mesa IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var rf = " & respuestaFijas & "; var rt = " & respuestaTodas & ";"
    Var_Caption_Error = "Mesas Env.: " & sc.Eval("rt.total_saved") & _
                        " | Fallidas: " & sc.Eval("rt.total_failed") & _
                        " | Fijas cat.: " & sc.Eval("rf.total_saved")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
