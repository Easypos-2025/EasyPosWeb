' ============================================================
' DescargarCatalogosPlatoPrecios
' Descarga WEB → ESCRITORIO (BD principal de la sede) de:
'   1. Insumos fijos del plato      GET /sync/pull/dish-portions
'        → inventario_porciones_plato
'   2. Cabecera listas de precios   GET /sync/pull/customer-price-list-header
'        → lista_precios_cliente_cabecera
'   3. Detalle listas de precios    GET /sync/pull/customer-price-list
'        → lista_precios_cliente
'
' Las listas de precios por cliente se CREAN en la web (Id_Lista lo genera
' la web); el escritorio solo las recibe.
' Requiere: script vb6_sync/015_escritorio_insumos_fijos_listas_precios.sql
' Llamar desde DescargarTodo (modSyncDownload) con el mismo "desde".
'
' Respuesta de los pull: {"total": n, "since": "...", "<clave>": [ ... ]}
' Seguridad: textos por EscSql(), números por CLng()/CDbl(), fechas por IsDate().
' ============================================================

Public Sub DescargarCatalogosPlatoPrecios(lblEstado As Label, ByVal desde As String)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Descargando insumos fijos y listas de precios..."

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"

    Dim respuesta As String, total As Long, i As Long
    Dim qs As String
    qs = "?company_id=" & COMPANY_ID & "&since=" & URLEncode(desde)

    ' ── 1. Insumos fijos ─────────────────────────────────────
    respuesta = ApiGet("/sync/pull/dish-portions" & qs)
    If respuesta <> "" Then
        sc.ExecuteStatement "var r = " & respuesta & ";"
        total = CLng(sc.Eval("r.dish_portions.length"))
        For i = 0 To total - 1
            conn.Execute "REPLACE INTO inventario_porciones_plato " & _
                "(Id_Plato, Id_Grupo, Id_Item, Cantidad, Unidad_Minima, " & _
                " Porciones_A_Desccontar, Posicion, Opcion_Cambiar, Enviada_MySql) VALUES (" & _
                CLng(sc.Eval("r.dish_portions[" & i & "].id_plato")) & ", " & _
                CLng(sc.Eval("r.dish_portions[" & i & "].id_grupo")) & ", " & _
                CLng(sc.Eval("r.dish_portions[" & i & "].id_item")) & ", " & _
                Str(CDbl(sc.Eval("r.dish_portions[" & i & "].cantidad || 0"))) & ", " & _
                Str(CDbl(sc.Eval("r.dish_portions[" & i & "].unidad_minima || 0"))) & ", " & _
                Str(CDbl(sc.Eval("r.dish_portions[" & i & "].porciones_a_desccontar || 0"))) & ", " & _
                CLng(sc.Eval("r.dish_portions[" & i & "].posicion || 0")) & ", " & _
                CLng(sc.Eval("r.dish_portions[" & i & "].opcion_cambiar || 0")) & ", 1)"
        Next i
    End If

    ' ── 2. Cabecera listas de precios ────────────────────────
    respuesta = ApiGet("/sync/pull/customer-price-list-header" & qs)
    If respuesta <> "" Then
        sc.ExecuteStatement "var r = " & respuesta & ";"
        total = CLng(sc.Eval("r.customer_price_list_header.length"))
        For i = 0 To total - 1
            Dim fecha As String
            fecha = CStr(sc.Eval("r.customer_price_list_header[" & i & "].fecha || ''"))
            If IsDate(fecha) Then fecha = "'" & fecha & "'" Else fecha = "NULL"
            conn.Execute "REPLACE INTO lista_precios_cliente_cabecera " & _
                "(Id_Lista, Id_Cliente, Nombre, Fecha, Activa, Usuario, Observacion, Enviada_MySql) VALUES (" & _
                CLng(sc.Eval("r.customer_price_list_header[" & i & "].id_lista")) & ", " & _
                CLng(sc.Eval("r.customer_price_list_header[" & i & "].id_cliente")) & ", " & _
                "'" & EscSql(CStr(sc.Eval("r.customer_price_list_header[" & i & "].nombre || ''"))) & "', " & _
                fecha & ", " & _
                CLng(sc.Eval("r.customer_price_list_header[" & i & "].activa || 0")) & ", " & _
                "'" & EscSql(CStr(sc.Eval("r.customer_price_list_header[" & i & "].usuario || ''"))) & "', " & _
                "'" & EscSql(CStr(sc.Eval("r.customer_price_list_header[" & i & "].observacion || ''"))) & "', 1)"
        Next i
    End If

    ' ── 3. Detalle listas de precios ─────────────────────────
    respuesta = ApiGet("/sync/pull/customer-price-list" & qs)
    If respuesta <> "" Then
        sc.ExecuteStatement "var r = " & respuesta & ";"
        total = CLng(sc.Eval("r.customer_price_list.length"))
        For i = 0 To total - 1
            conn.Execute "REPLACE INTO lista_precios_cliente " & _
                "(id_lista, Id_Cliente, Id_Producto, Id_Presentacion, Precio_Producto, Fecha, Activa, Enviada_MySql) VALUES (" & _
                CLng(sc.Eval("r.customer_price_list[" & i & "].id_lista")) & ", " & _
                CLng(sc.Eval("r.customer_price_list[" & i & "].id_cliente")) & ", " & _
                CLng(sc.Eval("r.customer_price_list[" & i & "].id_producto")) & ", " & _
                CLng(sc.Eval("r.customer_price_list[" & i & "].id_presentacion || 0")) & ", " & _
                CLng(sc.Eval("Math.round(r.customer_price_list[" & i & "].precio_producto || 0)")) & ", " & _
                "'" & EscSql(CStr(sc.Eval("r.customer_price_list[" & i & "].fecha || '0'"))) & "', " & _
                CLng(sc.Eval("r.customer_price_list[" & i & "].activa || 0")) & ", 1)"
        Next i
    End If

    ' ── 4. Clientes creados en la web ─────────────────────────
    '    INSERT IGNORE: nunca sobrescribe un cliente que ya exista en el escritorio.
    respuesta = ApiGet("/sync/pull/clientes" & qs)
    If respuesta <> "" Then
        sc.ExecuteStatement "var r = " & respuesta & ";"
        total = CLng(sc.Eval("r.clientes.length"))
        For i = 0 To total - 1
            conn.Execute "INSERT IGNORE INTO clientes " & _
                "(Id_Cliente, cedula, nombres, Apellidos, direccion, telefono, Mail, Observaciones, Enviada_MySql) VALUES (" & _
                CLng(sc.Eval("r.clientes[" & i & "].id_cliente")) & ", " & _
                "'" & EscSql(CStr(sc.Eval("r.clientes[" & i & "].cedula || ''"))) & "', " & _
                "'" & EscSql(Left(CStr(sc.Eval("r.clientes[" & i & "].nombres || ''")), 50)) & "', " & _
                "'" & EscSql(Left(CStr(sc.Eval("r.clientes[" & i & "].apellidos || ''")), 50)) & "', " & _
                "'" & EscSql(Left(CStr(sc.Eval("r.clientes[" & i & "].direccion || ''")), 50)) & "', " & _
                "'" & EscSql(CStr(sc.Eval("r.clientes[" & i & "].telefono || ''"))) & "', " & _
                "'" & EscSql(Left(CStr(sc.Eval("r.clientes[" & i & "].mail || ''")), 50)) & "', " & _
                "'" & EscSql(Left(CStr(sc.Eval("r.clientes[" & i & "].observaciones || ''")), 255)) & "', 1)"
        Next i
    End If

    conn.Close
    lblEstado.Caption = "Insumos fijos / listas de precios / clientes al dia: " & Now()
    Exit Sub

ErrHandler:
    Var_Caption_Error = "DescargarCatalogosPlatoPrecios: " & Err.Description
    On Error Resume Next
    If Not conn Is Nothing Then conn.Close
End Sub
