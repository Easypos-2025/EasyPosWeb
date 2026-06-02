' ============================================================
' [NombreFuncion]
' Endpoint: POST /api/pos/sync/push/[endpoint-slug]
' Tabla local VB6: [tabla_vb6]
' Tabla servidor:  [tabla_servidor]
' Grupo sync:      [GRUPO X] — [descripcion posicion]
' Depende de:      [tabla_web_dep1], [tabla_web_dep2]  |  ninguna si es Grupo A
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
'
'   ATENCION — campo numerico guardado como VARCHAR en VB6 (ej: Puerto):
'   Nz() solo reemplaza NULL, NO strings vacios. Si el campo puede ser "",
'   usar este patron para evitar "port":, (JSON invalido):
'     Dim strVal As String
'     strVal = CStr(Nz(rs("[Col]"), ""))
'     If strVal = "" Then strVal = "[default]"
'     json = json & """[campo]"":"  & strVal  & ","
' ============================================================

' ── VARIANTE A — PATRON ESTANDAR (usar siempre) ──────────────────────────────

Public Sub [NombreFuncion](Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)
    Var_Tabla_Error = [NombreFuncion]

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


' ── VARIANTE C — REPLACE POR PEDIDO (tablas temp con items por comanda) ───────
' USAR cuando los registros de detalle pueden ser BORRADOS FISICAMENTE en local.
' Ejemplo: temp_detalle_comanda_parcial, temp_plato_producto_parcial,
'          temp_novedades_plato_pedido.
'
' Razon: si el cajero elimina un item de la comanda, EasyPOS borra el row.
' Un INSERT/UPDATE simple no detectaria la eliminacion — el servidor
' conservaria el item "fantasma". Con REPLACE:
'   1. El servidor borra TODOS los items del pedido
'   2. Reinserta solo los que existen actualmente en local
'   => eliminados desaparecen, nuevos aparecen, modificados se actualizan.
'
' Endpoint servidor: POST /api/pos/sync/push/[modulo]-replace
' Recibe: [ { order_number, company_id, date, items:[...] }, ... ]
' Retorna: { total_orders, total_saved }
'
' FILTRO obligatorio en servidor: skip si order_number LIKE "WEB-%" (evita
' borrar items de pedidos web que bajaron al local como descarga).
'
' Public Sub [NombreFuncion](Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
'     On Error GoTo ErrHandler
'     Dim conn As Object
'     Set conn = GetConnDatatemppos()
'
'     ' 1. Pedidos activos del dia (solo origen desktop)
'     Dim rsOrd As Object
'     Set rsOrd = CreateObject("ADODB.Recordset")
'     rsOrd.Open "SELECT Nro_Pedido, Fecha FROM temp_comanda " & _
'                "WHERE Movil=0 AND Fecha=DATE(NOW())", conn
'
'     If rsOrd.EOF Then rsOrd.Close: conn.Close: Exit Sub
'
'     Dim json As String, sepOrd As String
'     json = "[": sepOrd = ""
'     Dim totalOrders As Integer: totalOrders = 0
'
'     Do While Not rsOrd.EOF
'         Dim nroPedido As String: nroPedido = CStr(rsOrd("Nro_Pedido"))
'         Dim fecha As String:     fecha     = CStr(rsOrd("Fecha"))
'
'         ' 2. Items actuales de este pedido
'         Dim rsItems As Object
'         Set rsItems = CreateObject("ADODB.Recordset")
'         rsItems.Open "SELECT * FROM [tabla_detalle] " & _
'                      "WHERE Nro_Pedido='" & Replace(nroPedido,"'","''") & "' " & _
'                      "  AND Fecha='" & fecha & "' [AND Mostrar=1]", conn
'
'         ' 3. Construir entrada de este pedido
'         Dim ordJson As String
'         ordJson = "{""order_number"":""" & EscapeJson(nroPedido) & ""","
'         ordJson = ordJson & """company_id"":" & Var_Id_Company_Envio & ","
'         ordJson = ordJson & """date"":""" & fecha & ""","
'         ordJson = ordJson & """items"":["
'
'         Dim sepItem As String: sepItem = ""
'         Do While Not rsItems.EOF
'             ordJson = ordJson & sepItem & "{"
'             ' ENTERO:   ordJson = ordJson & """[campo]"":" & CLng(Nz(rsItems("[Col]"), 0))        & ","
'             ' DECIMAL:  ordJson = ordJson & """[campo]"":" & CDbl(Nz(rsItems("[Col]"), 0))        & ","
'             ' TEXTO:    ordJson = ordJson & """[campo]"":""" & EscapeJson(CStr(Nz(rsItems("[Col]"),""))) & ""","
'             ' ULTIMO sin coma:
'             ordJson = ordJson & """[ultimo]"":" & CLng(Nz(rsItems("[Col_Final]"), 0))
'             ordJson = ordJson & "}"
'             sepItem = ","
'             rsItems.MoveNext
'         Loop
'         rsItems.Close: Set rsItems = Nothing
'
'         ordJson = ordJson & "]}"
'         json = json & sepOrd & ordJson
'         sepOrd = ","
'         totalOrders = totalOrders + 1
'         rsOrd.MoveNext
'     Loop
'
'     rsOrd.Close: json = json & "]": conn.Close
'     If totalOrders = 0 Then Exit Sub
'
'     ' 4. Enviar (una sola llamada con todos los pedidos)
'     Dim respuesta As String
'     respuesta = ApiPost("/sync/push/[modulo]-replace", json)
'     If respuesta = "" Then Exit Sub
'
'     Dim sc As Object
'     Set sc = CreateObject("ScriptControl")
'     sc.language = "JScript"
'     sc.ExecuteStatement "var r = " & respuesta & ";"
'     Var_Caption_Error = "[Etiqueta]: " & sc.Eval("r.total_saved") & _
'                         " items | " & sc.Eval("r.total_orders") & " pedidos"
'     Exit Sub
' ErrHandler:
'     Var_Caption_Error = "[NombreFuncion]: " & Err.Description
'     On Error Resume Next
'     If Not rsItems Is Nothing Then rsItems.Close
'     If Not rsOrd   Is Nothing Then rsOrd.Close
'     If Not conn    Is Nothing Then conn.Close
' End Sub
