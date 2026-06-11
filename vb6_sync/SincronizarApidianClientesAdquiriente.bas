' ============================================================
' SincronizarApidianClientesAdquiriente
' Endpoint: POST /api/pos/sync/push/apidian-clientes
' Tabla local VB6: apidian_clientes_adquiriente
' Tabla servidor:  apidian_clientes_adquiriente
' Grupo sync:      A — tabla maestra, sin dependencias
' Depende de:      ninguna
' Columnas locales:
'   Id_Cliente, cedula, PersonaJuridica, Tipo_Documento, DV,
'   RegContributivo, nombres, direccion, telefono, Mail,
'   Observaciones, Enviada_MySql, Referencia,
'   Cod_Municipio, Ciudad, Departamento, CodPais
' PK servidor: UNIQUE (company_id, Id_Cliente)
' ============================================================
Public Sub SincronizarApidianClientesAdquiriente(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)
    Var_Tabla_Error = "SincronizarApidianClientesAdquiriente"

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM apidian_clientes_adquiriente WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON + acumular Id_Cliente enviados --
    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""

    Do While Not rs.EOF
        Dim idCliente As Long
        idCliente = CLng(Nz(rs("Id_Cliente"), 0))

        json = json & sep & "{"
        json = json & """company_id"":"     & Var_Id_Company_Envio                                     & ","
        json = json & """Id_Cliente"":"     & idCliente                                                 & ","
        json = json & """cedula"":"         & """" & EscapeJson(Nz(rs("cedula"), ""))                  & ""","
        json = json & """PersonaJuridica"":"  & CInt(Nz(rs("PersonaJuridica"), 0))                     & ","
        json = json & """Tipo_Documento"":"   & """" & EscapeJson(Nz(rs("Tipo_Documento"), ""))        & ""","
        json = json & """DV"":"             & """" & EscapeJson(Nz(rs("DV"), ""))                      & ""","
        json = json & """RegContributivo"":"  & """" & EscapeJson(Nz(rs("RegContributivo"), ""))       & ""","
        json = json & """nombres"":"        & """" & EscapeJson(Nz(rs("nombres"), ""))                 & ""","
        json = json & """direccion"":"      & """" & EscapeJson(Nz(rs("direccion"), ""))               & ""","
        json = json & """telefono"":"       & """" & EscapeJson(Nz(rs("telefono"), ""))                & ""","
        json = json & """Mail"":"           & """" & EscapeJson(Nz(rs("Mail"), ""))                    & ""","
        json = json & """Observaciones"":"  & """" & EscapeJson(Nz(rs("Observaciones"), ""))           & ""","
        json = json & """Referencia"":"     & """" & EscapeJson(Nz(rs("Referencia"), ""))              & ""","
        json = json & """Cod_Municipio"":"  & Nz(rs("Cod_Municipio"), 0)                               & ","
        json = json & """Ciudad"":"         & Nz(rs("Ciudad"), 0)                                      & ","
        json = json & """Departamento"":"   & Nz(rs("Departamento"), 0)                                & ","
        json = json & """CodPais"":"        & Nz(rs("CodPais"), 0)                                     & ","
        json = json & """Enviada_MySql"":"  & CInt(Nz(rs("Enviada_MySql"), 0))
        json = json & "}"

        idList = idList & idSep & idCliente
        sep = ",": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/apidian-clientes", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar como enviados por Id_Cliente -----------
    If idList <> "" Then
        conn.Execute "UPDATE apidian_clientes_adquiriente SET Enviada_MySql = 1 " & _
                     "WHERE Id_Cliente IN (" & idList & ")"
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
    Var_Caption_Error = "ApiClientes Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
