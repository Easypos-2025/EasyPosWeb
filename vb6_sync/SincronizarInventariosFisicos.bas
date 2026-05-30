' ============================================================
' SincronizarInventariosFisicos
' Endpoint: POST /api/pos/sync/push/inventory-physical
' Tabla local VB6: inventarios_fisicos
' Tabla servidor:  inventory_physical
' Grupo sync:      B — después de SincronizarInventarioPorciones (Grupo B)
' Depende de:      supply_items (id_item)
' Columnas locales:
'   Id_Fisico, Id_Item, Fecha, Cantidad, cod_Usuario,
'   Hora, Observacion, Autorizada, Revisada, Cobrar,
'   Agrupar, Enviada_MySql
' PK servidor: (company_id, id_fisico)
' Nota: el servidor aplica movimiento de stock solo si Autorizada=1
' ============================================================
Public Sub SincronizarInventariosFisicos(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)
    Var_Tabla_Error = "SincronizarInventariosFisicos"

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM inventarios_fisicos_manuales WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    Dim ids As String, sepI As String
    json = "[": sep = ""
    ids = "": sepI = ""

    Do While Not rs.EOF
        Dim idFisico As Long
        idFisico = Nz(rs("Id_Fisico"), 0)

        Dim hora As String
        hora = Nz(rs("Hora"), "")
        If hora = "" Then hora = "00:00:00"

        json = json & sep & "{"
        json = json & """id_fisico"":"   & idFisico                                                      & ","
        json = json & """id_item"":"     & Nz(rs("Id_Item"), 0)                                          & ","
        json = json & """company_id"":"  & Var_Id_Company_Envio                                           & ","
        json = json & """fecha"":"       & """" & Format(rs("Fecha"), "yyyy-mm-dd")                      & ""","
        json = json & """cantidad"":"    & Replace(CStr(Nz(rs("Cantidad"), 0)), ",", ".")                 & ","
        json = json & """cod_usuario"":"  & """" & EscapeJson(Nz(rs("cod_Usuario"), ""))                 & ""","
        json = json & """hora"":"        & """" & hora                                                    & ""","
        json = json & """observacion"":"  & """" & EscapeJson(Nz(rs("Observacion"), ""))                 & ""","
        json = json & """autorizada"":"  & CInt(Nz(rs("Autorizada"), 0))                                 & ","
        json = json & """revisada"":"    & CInt(Nz(rs("Revisada"), 0))                                   & ","
        json = json & """cobrar"":"      & CInt(Nz(rs("Cobrar"), 0))                                     & ","
        json = json & """agrupar"":"     & Nz(rs("Agrupar"), 0)
        json = json & "}"
        sep = ","

        ids = ids & sepI & idFisico
        sepI = ","

        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/inventory-physical", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    If InStr(respuesta, "total_saved") = 0 Then
        Var_Caption_Error = "Error servidor: " & Left(respuesta, 200)
        conn.Close: Exit Sub
    End If

    If ids <> "" Then
        conn.Execute "UPDATE inventarios_fisicos SET Enviada_MySql = 1 " & _
                     "WHERE Id_Fisico IN (" & ids & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Inv.Fisico Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
