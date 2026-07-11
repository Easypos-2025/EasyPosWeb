' ============================================================
' SincronizarInventarioActualPorciones
' Endpoint: POST /api/pos/sync/push/inventory-stock
' Tabla local VB6: inventario_actual_porciones
' Tabla servidor:  inventario_actual_porciones
' Grupo sync:      C — despues de SincronizarInventarioPorciones (Grupo B)
' Variante A: solo envia registros con Enviada_MySql = 0.
'   Enviada_MySql se pone en 0 cuando Cantidad_Actual cambia
'   (venta, entrada, salida, anulacion, recalculo) o cuando
'   cambia cualquier campo maestro (nombre, categoria, costo, etc.)
' UPSERT completo: envia todos los campos para que el servidor
'   cree el registro si no existe o actualice todos sus datos.
' ============================================================
Public Sub SincronizarInventarioActualPorciones(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)
    Var_Tabla_Error = "SincronizarInventarioActualPorciones"

    ' -- 1. Solo los que cambiaron (Enviada_MySql = 0) --------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT Id_Item, Id_Grupo, Codigo_Insumo, Descripcion, Costo, " & _
            "       Und_Compra, Valor_Und_Compra, Und_Min_Utilizadas, Agrupar, " & _
            "       Compras, Controlar, Opcion_Cambios, Und_Uso, Centro_Produccion, " & _
            "       Cantidad_Actual, Bodega, Insumo_Cp, Fecha_Vence, Stock_MInimo " & _
            "FROM inventario_actual_porciones " & _
            "WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ------------------------------------
    Dim json As String, sep As String
    Dim ids As String, sepI As String
    json = "[": sep = ""
    ids = "": sepI = ""

    Do While Not rs.EOF
        Dim lId As Long
        lId = Nz(rs("Id_Item"), 0)

        Dim sFechaVence As String
        If IsNull(rs("Fecha_Vence")) Or rs("Fecha_Vence") = "" Then
            sFechaVence = "null"
        Else
            sFechaVence = """" & Format(rs("Fecha_Vence"), "yyyy-mm-dd") & """"
        End If

        json = json & sep & "{"
        json = json & """company_id"":"         & Var_Id_Company_Envio                                                & ","
        json = json & """id_item"":"            & lId                                                                  & ","
        json = json & """id_grupo"":"           & Nz(rs("Id_Grupo"), 0)                                               & ","
        json = json & """codigo_insumo"":"      & """" & EscapeJson(Nz(rs("Codigo_Insumo"), ""))  & """" & ","
        json = json & """descripcion"":"        & """" & EscapeJson(Nz(rs("Descripcion"), ""))    & """" & ","
        json = json & """costo"":"              & Replace(CStr(Nz(rs("Costo"), 0)), ",", ".")                          & ","
        json = json & """und_compra"":"         & Nz(rs("Und_Compra"), 0)                                             & ","
        json = json & """valor_und_compra"":"   & Replace(CStr(Nz(rs("Valor_Und_Compra"), 0)), ",", ".")              & ","
        json = json & """und_min_utilizadas"":"  & Replace(CStr(Nz(rs("Und_Min_Utilizadas"), 0)), ",", ".")            & ","
        json = json & """agrupar"":"            & Nz(rs("Agrupar"), 0)                                                & ","
        json = json & """compras"":"            & Nz(rs("Compras"), 0)                                                & ","
        json = json & """controlar"":"          & Nz(rs("Controlar"), 0)                                              & ","
        json = json & """opcion_cambios"":"     & Nz(rs("Opcion_Cambios"), 0)                                         & ","
        json = json & """und_uso"":"            & Nz(rs("Und_Uso"), 0)                                                & ","
        json = json & """centro_produccion"":"  & Nz(rs("Centro_Produccion"), 0)                                      & ","
        json = json & """cantidad_actual"":"    & Replace(CStr(Nz(rs("Cantidad_Actual"), 0)), ",", ".")               & ","
        json = json & """bodega"":"             & Nz(rs("Bodega"), 0)                                                 & ","
        json = json & """insumo_cp"":"          & Nz(rs("Insumo_Cp"), 0)                                              & ","
        json = json & """fecha_vence"":"        & sFechaVence                                                          & ","
        json = json & """stock_minimo"":"       & Replace(CStr(Nz(rs("Stock_MInimo"), 0)), ",", ".")
        json = json & "}"
        sep = ","

        ids = ids & sepI & lId
        sepI = ","

        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor --------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/inventory-stock", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar como enviadas las confirmadas --------------
    If InStr(respuesta, "total_saved") = 0 Then
        Var_Caption_Error = "Error servidor: " & Left(respuesta, 200)
        conn.Close: Exit Sub
    End If

    If ids <> "" Then
        conn.Execute "UPDATE inventario_actual_porciones " & _
                     "SET Enviada_MySql = 1 " & _
                     "WHERE Id_Item IN (" & ids & ")"
    End If

    ' -- 5. Mostrar estado ------------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Stock Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
