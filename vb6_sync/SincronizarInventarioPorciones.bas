' ============================================================
' SincronizarInventarioPorciones
' Endpoint: POST /api/pos/sync/push/supply-items
' Tabla local VB6: inventario_porciones
' Tabla servidor: supply_items
' Grupo sync:     B — después de SincronizarFormaMedida (Grupo A)
' Depende de:     pos_measure_forms (unit_id, unit_uso_id, tipo_und_minima)
' PK local: Id_Item (Id_Grupo siempre = 1, no se envía)
' Columnas locales:
'   Codigo_Insumo, Id_Item, Descripcion, Costo,
'   Und_Compra, Valor_Und_Compra, Und_Min_Utilizadas, Posicion,
'   Agrupar, Compras, Controlar, Opcion_Cambios, Und_Uso,
'   Centro_Produccion, Tipo_Und_Minima, Cant_Und_Minimas, Bodega,
'   Producto_Preparado, Id_preparacion, Preparado_En_Sede,
'   Descargar_En_Venta, Armar_Plato, Cantidad_Armar, Id_Insumo,
'   Insumo_Cp, Porcentaje_Merma, Marca_Referencia, Fecha_Vence,
'   Stock_MInimo
' ============================================================

Public Sub SincronizarInventarioPorciones(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes --------------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM inventario_porciones WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    Dim sentIds As String, siSep As String
    Dim fv As String
    json = "[": sep = ""
    sentIds = "": siSep = ""

    Do While Not rs.EOF
        ' Fecha_Vence: convertir a ISO o null
        If IsNull(rs("Fecha_Vence")) Or rs("Fecha_Vence") = "" Then
            fv = "null"
        Else
            fv = """" & Format(rs("Fecha_Vence"), "yyyy-mm-dd") & """"
        End If

        json = json & sep & "{"
        json = json & """id_item"":"            & Nz(rs("Id_Item"), 0)                                     & ","
        json = json & """company_id"":"         & Var_Id_Company_Envio                                      & ","
        json = json & """id_insumo"":"          & Nz(rs("Id_Insumo"), 0)                                   & ","
        json = json & """code"":"               & """" & EscapeJson(Nz(rs("Codigo_Insumo"), ""))           & ""","
        json = json & """description"":"         & """" & EscapeJson(Nz(rs("Descripcion"), ""))             & ""","
        json = json & """marca_referencia"":"   & """" & EscapeJson(Nz(rs("Marca_Referencia"), ""))        & ""","
        json = json & """cost_price"":"         & Nz(rs("Costo"), 0)                                       & ","
        json = json & """unit_id"":"            & Nz(rs("Und_Compra"), 0)                                  & ","
        json = json & """unit_uso_id"":"        & Nz(rs("Und_Uso"), 0)                                     & ","
        json = json & """valor_und_compra"":"   & Nz(rs("Valor_Und_Compra"), 0)                            & ","
        json = json & """und_min_utilizadas"":"  & Nz(rs("Und_Min_Utilizadas"), 0)                          & ","
        json = json & """min_stock"":"          & Nz(rs("Stock_MInimo"), 0)                                & ","
        json = json & """waste_pct"":"          & Nz(rs("Porcentaje_Merma"), 0)                            & ","
        json = json & """fecha_vence"":"        & fv                                                        & ","
        json = json & """posicion"":"           & Nz(rs("Posicion"), 0)                                    & ","
        json = json & """agrupar"":"            & Nz(rs("Agrupar"), 0)                                     & ","
        json = json & """control_stock"":"      & Nz(rs("Controlar"), 0)                                   & ","
        json = json & """compras"":"            & Nz(rs("Compras"), 0)                                     & ","
        json = json & """opcion_cambios"":"     & Nz(rs("Opcion_Cambios"), 0)                              & ","
        json = json & """centro_produccion"":"  & Nz(rs("Centro_Produccion"), 0)                           & ","
        json = json & """tipo_und_minima"":"    & Nz(rs("Tipo_Und_Minima"), 0)                             & ","
        json = json & """cant_und_minimas"":"   & Nz(rs("Cant_Und_Minimas"), 0)                            & ","
        json = json & """bodega"":"             & Nz(rs("Bodega"), 0)                                      & ","
        json = json & """producto_preparado"":"  & Nz(rs("Producto_Preparado"), 0)                          & ","
        json = json & """id_preparacion"":"     & Nz(rs("Id_preparacion"), 0)                              & ","
        json = json & """preparado_en_sede"":"  & Nz(rs("Preparado_En_Sede"), 0)                           & ","
        json = json & """descargar_en_venta"":"  & Nz(rs("Descargar_En_Venta"), 1)                          & ","
        json = json & """armar_plato"":"        & Nz(rs("Armar_Plato"), 0)                                 & ","
        json = json & """cantidad_armar"":"     & Nz(rs("Cantidad_Armar"), 0)                              & ","
        json = json & """insumo_cp"":"          & Nz(rs("Insumo_Cp"), 0)
        json = json & "}"

        ' Acumular Id_Item para el UPDATE posterior
        sentIds = sentIds & siSep & Nz(rs("Id_Item"), 0)

        sep = ","
        siSep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/supply-items", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar enviadas por Id_Item --------------------
    If sentIds <> "" Then
        conn.Execute "UPDATE inventario_porciones SET Enviada_MySql = 1 " & _
                     "WHERE Id_Item IN (" & sentIds & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Insumos Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
