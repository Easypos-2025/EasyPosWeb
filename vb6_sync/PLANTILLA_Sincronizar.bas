' ============================================================
' [NombreFuncion]
' Endpoint: POST /api/pos/sync/push/[endpoint-slug]
' Tabla local VB6: [tabla_vb6]
' Tabla servidor:  [tabla_servidor]
' Columnas locales:
'   [Col1] -> [campo_api]
'   [Col2] -> [campo_api]
'   ...
' PK servidor: id (= [Col_PK] en VB6)
'
' REGLA GENERAL: SIEMPRE usar Variante A.
'   - Filtrar por Enviada_MySql = 0 (no reenviar lo ya sincronizado)
'   - Marcar con Enviada_MySql = 1 solo los confirmados por el servidor
'
' EXCEPCION Variante B: UNICAMENTE si la tabla VB6 NO tiene columna
'   Enviada_MySql Y el equipo confirma que es aceptable re-enviar
'   todos los registros en cada sincronizacion (tablas maestras
'   muy pequeñas ya existentes como zonas_asientos).
'
' TIPOS DE CAMPO EN JSON:
'   ENTERO/ID:  & Nz(rs("[Col]"), 0)                              (sin comillas)
'   TINYINT:    & CInt(Nz(rs("[Col]"), 0))                        (evita True/False de ADODB)
'   DECIMAL:    & Replace(CStr(Nz(rs("[Col]"), 0)), ",", ".")     (evita coma decimal del locale)
'   TEXTO:      & """" & EscapeJson(Nz(rs("[Col]"), "")) & """"
'   FECHA:      & """" & Format(rs("[Col]"), "YYYY-MM-DD") & """"
'   DATETIME:   & """" & ("" & rs("[Col]")) & """"
' ============================================================

' ── VARIANTE A — PATRON ESTANDAR (usar siempre) ──────────────────────────────

Public Sub [NombreFuncion](Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM [tabla_vb6] WHERE Enviada_MySql = 0 [AND year([campo_fecha]) >= 2025] LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"          & Nz(rs("[Col_PK]"), 0)                                        & ","
        json = json & """company_id"":"  & Var_Id_Company_Envio                                         & ","
        ' ENTERO:   json = json & """[campo]"":"  & Nz(rs("[Col]"), 0)                                  & ","
        ' TINYINT:  json = json & """[campo]"":"  & CInt(Nz(rs("[Col]"), 0))                            & ","
        ' DECIMAL:  json = json & """[campo]"":"  & Replace(CStr(Nz(rs("[Col]"), 0)), ",", ".")         & ","
        ' TEXTO:    json = json & """[campo]"":"  & """" & EscapeJson(Nz(rs("[Col]"), ""))             & ""","
        ' FECHA:    json = json & """[campo]"":"  & """" & Format(rs("[Col]"), "YYYY-MM-DD")            & ""","
        ' DATETIME: json = json & """[campo]"":"  & """" & ("" & rs("[Col]"))                           & ""","
        ' ULTIMO campo sin coma:
        json = json & """[ultimo_campo]"":"  & CInt(Nz(rs("[Col_Final]"), 0))
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/[endpoint-slug]", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE [tabla_vb6] SET Enviada_MySql = 1 " & _
                     "WHERE [Col_PK] IN (" & savedList & ")"
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
    Var_Caption_Error = "[Etiqueta] Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub


' ── VARIANTE A con PK compuesta (tablas donde se agrupa por otro campo) ───────
' Ejemplo: comanda, detalle_comanda, formas_pago_factura, etc.
' En lugar de ParseSaved se acumula la clave de agrupacion (Nro_Pedido, Nro_Factura...)
' y se marca toda la factura/pedido confirmado.
'
'    Dim pedidos As String, sepP As String
'    pedidos = "": sepP = ""
'    ...
'    Dim clave As String
'    clave = rs("[Campo_Clave_Grupo]")
'    ' ... construir JSON ...
'    If InStr("," & pedidos & ",", "," & clave & ",") = 0 Then
'        pedidos = pedidos & sepP & """" & clave & """"
'        sepP = ","
'    End If
'    ...
'    If InStr(respuesta, "total_saved") = 0 Then
'        Var_Caption_Error = "Error servidor: " & Left(respuesta, 200)
'        conn.Close: Exit Sub
'    End If
'    If pedidos <> "" Then
'        conn.Execute "UPDATE [tabla] SET Enviada_MySql = 1 " & _
'                     "WHERE [Campo_Clave_Grupo] IN (" & pedidos & ")"
'    End If


' ── VARIANTE B — EXCEPCION (re-envia todos, sin flag) ─────────────────────────
' SOLO si la tabla VB6 NO tiene Enviada_MySql. Ver nota arriba.
'
' Public Sub [NombreFuncion](Var_Id_Company_Envio As Integer)
'     ...
'     rs.Open "SELECT * FROM [tabla_vb6] WHERE [campo_activo] = 1", conn
'     ...
'     rs.Close
'     conn.Close         <- cerrar ANTES de enviar (sin paso UPDATE)
'     respuesta = ApiPost(...)
'     If respuesta = "" Then Exit Sub
'     ' -- Mostrar estado (sin paso 4) --
'     If InStr(respuesta, "total_saved") = 0 Then
'         Var_Caption_Error = "Error servidor: " & Left(respuesta, 200)
'         Exit Sub
'     End If
'     ...
' End Sub
