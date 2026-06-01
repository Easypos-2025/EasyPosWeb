' ============================================================
' PLANTILLA_Descargar.bas
' Descarga registros creados en WEB → inserta/actualiza en datatemppos local
' Endpoint: GET /api/pos/sync/pull/[endpoint-slug]
'
' Tabla destino local: datatemppos.[tabla_local]
' Tabla origen web:    [tabla_web_servidor]
' Filtro:             order_number LIKE 'WEB-%' (pedidos creados en web)
'                     updated_at > ultimo_pull (solo cambios nuevos)
'
' REGLA GENERAL: SIEMPRE usar este patrón.
'   - Consultar /sync/pull/[slug]?company_id=X&desde=YYYY-MM-DD+HH:MM:SS
'   - Por cada registro recibido:
'       · Si NO existe en local  → INSERT
'       · Si SÍ existe en local  → UPDATE solo si lock no activo
'   - Actualizar datatemppos_sync.sync_control.ultimo_pull al final
'   - NUNCA insertar si el Nro_Pedido ya existe con estado facturado (Nro_Factura <> '0')
'
' TIPOS DE CAMPO AL LEER JSON con ScriptControl:
'   ENTERO:   CInt(sc.Eval("r[" & i & "].[campo]"))
'   LONG:     CLng(sc.Eval("r[" & i & "].[campo]"))
'   TEXTO:    CStr(sc.Eval("r[" & i & "].[campo]"))
'   FLOAT:    CDbl(sc.Eval("r[" & i & "].[campo]"))
'   FECHA:    CStr(sc.Eval("r[" & i & "].[campo]"))   ' viene como "YYYY-MM-DD"
'   NULO:     sc.Eval("r[" & i & "].[campo] || ''")   ' coalesce a string vacío
'             sc.Eval("r[" & i & "].[campo] || 0")    ' coalesce a 0
'
' NOTA SEGURIDAD — Evitar SQL injection al construir INSERTs desde JSON:
'   - Campos texto: siempre pasar por EscSql() antes de concatenar
'   - Campos numéricos: siempre CLng() o CInt() para validar tipo
'   - Campos fecha: validar formato con IsDate() antes de usar
' ============================================================


' ── VARIANTE A — INSERTAR/ACTUALIZAR comanda y detalle ───────────────────────
' Usar para: temp_comanda, temp_detalle_comanda, temp_mesas (estado)
'
' Public Sub [NombreFuncion](lblEstado As Label)

Public Sub DescargarComandasWeb(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Descargando pedidos web..."

    ' -- 1. Obtener timestamp del último pull -----------------
    Dim connSync As Object
    Set connSync = GetConnSync()            ' conexión a datatemppos_sync local
    Dim rsCtrl As Object
    Set rsCtrl = CreateObject("ADODB.Recordset")
    rsCtrl.Open "SELECT ultimo_pull FROM sync_control WHERE id = 1", connSync
    Dim desde As String
    desde = ""
    If Not rsCtrl.EOF Then
        If Not IsNull(rsCtrl("ultimo_pull")) Then
            desde = Format(rsCtrl("ultimo_pull"), "YYYY-MM-DD HH:MM:SS")
        End If
    End If
    rsCtrl.Close
    If desde = "" Then desde = "2024-01-01 00:00:00"

    ' -- 2. Llamar al endpoint de pull -----------------------
    Dim endpoint As String
    endpoint = "/sync/pull/web-orders?company_id=" & COMPANY_ID & _
               "&desde=" & URLEncode(desde)

    Dim respuesta As String
    respuesta = ApiGet(endpoint)

    If respuesta = "" Or respuesta = "[]" Then
        connSync.Close
        lblEstado.Caption = "Sin pedidos web nuevos: " & Now()
        Exit Sub
    End If

    ' -- 3. Parsear JSON con ScriptControl -------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"

    On Error Resume Next
    sc.ExecuteStatement "var r = " & respuesta & ";"
    If Err.Number <> 0 Then
        Var_Caption_Error = "JSON inválido en descarga comandas"
        connSync.Close: Exit Sub
    End If
    On Error GoTo ErrHandler

    Dim total As Integer
    total = CInt(sc.Eval("r.length"))
    If total = 0 Then
        connSync.Close
        lblEstado.Caption = "Sin pedidos web nuevos: " & Now()
        Exit Sub
    End If

    ' -- 4. Insertar/Actualizar en datatemppos local ---------
    Dim connDT As Object
    Set connDT = GetConnDatatemppos()      ' conexión a datatemppos local

    Dim insertados As Integer, actualizados As Integer, omitidos As Integer
    insertados = 0: actualizados = 0: omitidos = 0

    Dim i As Integer
    For i = 0 To total - 1
        ' Leer campos del objeto JSON
        Dim nroPedido As String
        nroPedido = EscSql(CStr(sc.Eval("r[" & i & "].order_number")))

        Dim fecha As String
        fecha = CStr(sc.Eval("r[" & i & "].date"))
        If Not IsDate(fecha) Then GoTo SiguienteComanda

        Dim nroFac As String
        nroFac = EscSql(CStr(sc.Eval("r[" & i & "].invoice_number || '0'")))

        Dim mesa As String
        mesa = EscSql(CStr(sc.Eval("r[" & i & "].table_name || ''")))

        Dim hora As String
        hora = EscSql(CStr(sc.Eval("r[" & i & "].time || ''")))

        Dim mesero As Long
        mesero = CLng(sc.Eval("r[" & i & "].waiter_id || 0"))

        Dim cancelado As Integer
        cancelado = CInt(sc.Eval("r[" & i & "].cancelled || 0"))

        Dim valor As Long
        valor = CLng(sc.Eval("r[" & i & "].amount || 0"))

        Dim novedad As String
        novedad = EscSql(CStr(sc.Eval("r[" & i & "].notes || ''")))

        Dim cortesia As Integer
        cortesia = CInt(sc.Eval("r[" & i & "].complimentary || 0"))

        Dim comensales As Integer
        comensales = CInt(sc.Eval("r[" & i & "].guests_count || 0"))

        Dim domicilio As Integer
        domicilio = CInt(sc.Eval("r[" & i & "].delivery || 0"))

        Dim idCliente As Long
        idCliente = CLng(sc.Eval("r[" & i & "].customer_id || 0"))

        Dim idMesa As Long
        idMesa = CLng(sc.Eval("r[" & i & "].table_id || 0"))

        ' Verificar si ya existe en local
        Dim rsCheck As Object
        Set rsCheck = CreateObject("ADODB.Recordset")
        rsCheck.Open "SELECT Nro_Factura FROM temp_comanda " & _
                     "WHERE Nro_Pedido = '" & nroPedido & "' " & _
                     "AND Fecha = '" & fecha & "'", connDT

        If rsCheck.EOF Then
            ' No existe → INSERT
            connDT.Execute "INSERT INTO temp_comanda " & _
                "(Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora, Mesero, " & _
                " Cancelado, Valor, Novedad, Cortesia, Nro_Comenzales, " & _
                " Domicilio, Id_Cliente, Id_Mesa, Movil) VALUES (" & _
                "'" & nroPedido & "', '" & fecha & "', '" & nroFac & "', " & _
                "'" & mesa & "', '" & hora & "', " & mesero & ", " & _
                cancelado & ", " & valor & ", '" & novedad & "', " & cortesia & ", " & _
                comensales & ", " & domicilio & ", " & idCliente & ", " & idMesa & ", 1)"
                ' Movil=1 identifica pedidos creados en web/móvil
            insertados = insertados + 1
        Else
            ' Ya existe — solo actualizar si NO está facturado
            Dim facExistente As String
            facExistente = Nz(rsCheck("Nro_Factura"), "0")
            If facExistente = "0" Then
                ' No facturado → actualizar estado
                connDT.Execute "UPDATE temp_comanda SET " & _
                    "Cancelado = " & cancelado & ", " & _
                    "Valor = " & valor & ", " & _
                    "Novedad = '" & novedad & "' " & _
                    "WHERE Nro_Pedido = '" & nroPedido & "' " & _
                    "AND Fecha = '" & fecha & "'"
                actualizados = actualizados + 1
            Else
                omitidos = omitidos + 1    ' ya facturado, no tocar
            End If
        End If
        rsCheck.Close

SiguienteComanda:
        Set rsCheck = Nothing
    Next i

    ' -- 5. Actualizar timestamp del pull --------------------
    connSync.Execute "UPDATE sync_control SET ultimo_pull = NOW() WHERE id = 1"

    ' -- 6. Mostrar estado -----------------------------------
    lblEstado.Caption = "Web→Local: +" & insertados & " nuevos | " & _
                        actualizados & " actulz | " & omitidos & " omitidos"

    connDT.Close
    connSync.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = "DescargarComandasWeb: " & Err.Description
    On Error Resume Next
    If Not connDT Is Nothing Then connDT.Close
    If Not connSync Is Nothing Then connSync.Close
End Sub


' ── VARIANTE B — ACTUALIZAR ESTADO DE MESAS ──────────────────────────────────
' Usar para: temp_mesas (solo actualiza Activa, no inserta mesas nuevas)
'
Public Sub DescargarEstadoMesas(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando estado de mesas..."

    Dim respuesta As String
    respuesta = ApiGet("/sync/pull/table-status?company_id=" & COMPANY_ID)

    If respuesta = "" Or respuesta = "[]" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"

    Dim total As Integer
    total = CInt(sc.Eval("r.length"))

    Dim connDT As Object
    Set connDT = GetConnDatatemppos()

    Dim i As Integer
    For i = 0 To total - 1
        Dim idMesa As Long
        idMesa = CLng(sc.Eval("r[" & i & "].table_id"))
        Dim activa As Integer
        activa = CInt(sc.Eval("r[" & i & "].is_active || 0"))

        connDT.Execute "UPDATE temp_mesas SET Activa = " & activa & _
                       " WHERE Id_Mesa = " & idMesa
    Next i

    connDT.Close
    lblEstado.Caption = "Mesas actualizadas: " & Now()
    Exit Sub

ErrHandler:
    Var_Caption_Error = "DescargarEstadoMesas: " & Err.Description
    On Error Resume Next
    If Not connDT Is Nothing Then connDT.Close
End Sub


' ════════════════════════════════════════════════════════════
' HELPERS — Agregar a modSyncAll.bas o modSyncDownload.bas
' ════════════════════════════════════════════════════════════

' Conexión a datatemppos local (BD de pedidos temporales)
Public Function GetConnDatatemppos() As Object
    Dim conn As Object
    Set conn = CreateObject("ADODB.Connection")
    conn.Open "Driver={MySQL ODBC 8.0 Driver};" & _
              "Server=127.0.0.1;Port=3308;" & _
              "Database=datatemppos;" & _
              "User=root;Password=123456;Option=3;"
    Set GetConnDatatemppos = conn
End Function

' Conexión a datatemppos_sync local (BD de control de sync)
Public Function GetConnSync() As Object
    Dim conn As Object
    Set conn = CreateObject("ADODB.Connection")
    conn.Open "Driver={MySQL ODBC 8.0 Driver};" & _
              "Server=127.0.0.1;Port=3308;" & _
              "Database=datatemppos_sync;" & _
              "User=root;Password=123456;Option=3;"
    Set GetConnSync = conn
End Function

' Escapa comillas simples para SQL (previene injection)
Public Function EscSql(ByVal s As String) As String
    EscSql = Replace(s, "'", "''")
End Function

' Codifica espacios y caracteres especiales para URL query string
Public Function URLEncode(ByVal s As String) As String
    URLEncode = Replace(s, " ", "+")
    URLEncode = Replace(URLEncode, ":", "%3A")
End Function

' Verificar conectividad antes de intentar pull
Public Function ServidorDisponible() As Boolean
    On Error GoTo Sin_Conexion
    Dim http As Object
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.Open "GET", API_BASE & "/sync/health", False
    http.SetRequestHeader "X-Api-Key", API_KEY
    http.setTimeouts 3000, 3000, 5000, 5000   ' 5s timeout máximo
    http.Send
    ServidorDisponible = (http.Status = 200)
    Exit Function
Sin_Conexion:
    ServidorDisponible = False
End Function
