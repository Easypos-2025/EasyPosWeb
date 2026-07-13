'Attribute VB_Name = "SincronizarHistoricoInventarioActual"
' ============================================================
' SincronizarHistoricoInventarioActual
' Endpoint: POST /api/pos/sync/push/historico-inventario-actual
' Tabla local VB6: historico_inventario_actual_porciones
' Tabla servidor:  historico_inventario_actual_porciones
' Grupo sync:      D — despues de SincronizarInventarioActualPorciones (Grupo C)
' Variante A: solo envia registros con Enviada_MySql = 0.
' Cada corte (Id_Historico) agrupa todos los items del snapshot.
' ============================================================
Public Sub SincronizarHistoricoInventarioActual(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = Base_Principal_Local_MySql
    Var_Tabla_Error = "SincronizarHistoricoInventarioActual"

    ' -- 1. Solo los que no se han enviado ----------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT Id_Historico, Fecha, Id_Grupo, Id_Item, Codigo_Insumo, Descripcion, " & _
            "       Costo, Und_Compra, Valor_Und_Compra, Und_Min_Utilizadas, Posicion, " & _
            "       Agrupar, Compras, Controlar, Opcion_Cambios, Und_Uso, Centro_Produccion, " & _
            "       Cantidad_Actual, Cod_empleado, Insumo_Cp, Fecha_Vence, Stock_MInimo " & _
            "FROM historico_inventario_actual_porciones " & _
            "WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: Exit Sub
    End If

    ' -- 2. Construir JSON + acumular Id_Historico enviados -----
    Dim json As String, sep As String
    Dim historicos As String, sepH As String
    json = "[": sep = ""
    historicos = "": sepH = ""

    Do While Not rs.EOF
        Dim lIdH As Long
        lIdH = Nz(rs("Id_Historico"), 0)

        Dim sFechaVence As String
        If IsNull(rs("Fecha_Vence")) Or rs("Fecha_Vence") = "" Then
            sFechaVence = "null"
        Else
            sFechaVence = """" & Format(rs("Fecha_Vence"), "yyyy-mm-dd") & """"
        End If

        json = json & sep & "{"
        json = json & """company_id"":"         & Var_Id_Company_Envio                                               & ","
        json = json & """id_historico"":"       & lIdH                                                               & ","
        json = json & """fecha"":"              & """" & Format(rs("Fecha"), "yyyy-mm-dd")                & """" & ","
        json = json & """id_grupo"":"           & Nz(rs("Id_Grupo"), 0)                                             & ","
        json = json & """id_item"":"            & Nz(rs("Id_Item"), 0)                                              & ","
        json = json & """codigo_insumo"":"      & """" & EscapeJson(Nz(rs("Codigo_Insumo"), ""))  & """" & ","
        json = json & """descripcion"":"        & """" & EscapeJson(Nz(rs("Descripcion"), ""))    & """" & ","
        json = json & """costo"":"              & Replace(CStr(Nz(rs("Costo"), 0)), ",", ".")                        & ","
        json = json & """und_compra"":"         & Nz(rs("Und_Compra"), 0)                                           & ","
        json = json & """valor_und_compra"":"   & Replace(CStr(Nz(rs("Valor_Und_Compra"), 0)), ",", ".")            & ","
        json = json & """und_min_utilizadas"":"  & Replace(CStr(Nz(rs("Und_Min_Utilizadas"), 0)), ",", ".")          & ","
        json = json & """posicion"":"           & Nz(rs("Posicion"), 0)                                             & ","
        json = json & """agrupar"":"            & Nz(rs("Agrupar"), 0)                                              & ","
        json = json & """compras"":"            & Nz(rs("Compras"), 0)                                              & ","
        json = json & """controlar"":"          & Nz(rs("Controlar"), 0)                                            & ","
        json = json & """opcion_cambios"":"     & Nz(rs("Opcion_Cambios"), 0)                                       & ","
        json = json & """und_uso"":"            & Nz(rs("Und_Uso"), 0)                                              & ","
        json = json & """centro_produccion"":"  & Nz(rs("Centro_Produccion"), 0)                                    & ","
        json = json & """cantidad_actual"":"    & Replace(CStr(Nz(rs("Cantidad_Actual"), 0)), ",", ".")             & ","
        json = json & """cod_empleado"":"       & """" & EscapeJson(Nz(rs("Cod_empleado"), ""))   & """" & ","
        json = json & """insumo_cp"":"          & Nz(rs("Insumo_Cp"), 0)                                            & ","
        json = json & """fecha_vence"":"        & sFechaVence                                                        & ","
        json = json & """stock_minimo"":"       & Replace(CStr(Nz(rs("Stock_MInimo"), 0)), ",", ".")
        json = json & "}"
        sep = ","

        ' Acumular Id_Historico unicos para el UPDATE final
        If InStr("," & historicos & ",", "," & lIdH & ",") = 0 Then
            historicos = historicos & sepH & lIdH
            sepH = ","
        End If

        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor -----------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/historico-inventario-actual", json)

    If respuesta = "" Then Exit Sub

    ' -- 4. Marcar como enviados todos los items de los cortes --
    If InStr(respuesta, "total_saved") = 0 Then
        Var_Caption_Error = "Error servidor: " & Left(respuesta, 200)
        Exit Sub
    End If

    If historicos <> "" Then
        conn.Execute "UPDATE historico_inventario_actual_porciones " & _
                     "SET Enviada_MySql = 1 " & _
                     "WHERE Id_Historico IN (" & historicos & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Hist.Inv Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    Exit Sub

ErrHandler:
    Var_Caption_Error = "SincronizarHistoricoInventarioActual: " & Err.Description
    On Error Resume Next
    If Not rs Is Nothing Then If rs.State = 1 Then rs.Close
End Sub
