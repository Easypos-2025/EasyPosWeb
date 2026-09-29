' ============================================================
' SincronizarInventarioPorcionesPlato
' Endpoint: POST /api/pos/sync/push/dish-portions
' Tabla local VB6: inventario_porciones_plato   (insumos FIJOS del plato)
' Tabla servidor: inventario_porciones_plato
' Grupo sync:     D — después de SincronizarPlatos + SincronizarInventarioPorciones
' Depende de:     pos_dishes, supply_items
' Requiere:       script vb6_sync/015_escritorio_insumos_fijos_listas_precios.sql
'                 (columna Enviada_MySql + PK Id_Plato, Id_Grupo, Id_Item)
' Nota: saved retorna Id_Plato solo si TODAS sus filas se guardaron
' ============================================================
Public Sub SincronizarInventarioPorcionesPlato(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM inventario_porciones_plato WHERE Enviada_MySql = 0 " & _
            "ORDER BY Id_Plato LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """company_id"":"             & Var_Id_Company_Envio                        & ","
        json = json & """id_plato"":"               & Nz(rs("Id_Plato"), 0)                       & ","
        json = json & """id_grupo"":"               & Nz(rs("Id_Grupo"), 0)                       & ","
        json = json & """id_item"":"                & Nz(rs("Id_Item"), 0)                        & ","
        json = json & """cantidad"":"               & Str(Nz(rs("Cantidad"), 0))                  & ","
        json = json & """unidad_minima"":"          & Str(Nz(rs("Unidad_Minima"), 0))             & ","
        json = json & """porciones_a_desccontar"":" & Str(Nz(rs("Porciones_A_Desccontar"), 0))    & ","
        json = json & """posicion"":"               & Nz(rs("Posicion"), 0)                       & ","
        json = json & """opcion_cambiar"":"         & Nz(rs("Opcion_Cambiar"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/dish-portions", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE inventario_porciones_plato SET Enviada_MySql = 1 " & _
                     "WHERE Enviada_MySql = 0 AND Id_Plato IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Insumos Fijos Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
