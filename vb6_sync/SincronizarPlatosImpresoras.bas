' ============================================================
' SincronizarPlatosImpresoras
' Endpoint: POST /api/pos/sync/push/dish-printers
' Tabla local VB6: plato_impresoras
' Tabla servidor: pos_item_printers
' Nota: el servidor hace DELETE+INSERT por (company_id, item_id)
'        saved retorna item_id; se marca por Id_Item
' ============================================================
Public Sub SincronizarPlatosImpresoras(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM plato_impresoras WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """item_id"":"        & Nz(rs("Id_Item"), 0)          & ","
        json = json & """company_id"":"     & Var_Id_Company_Envio          & ","
        json = json & """printer_id"":"     & Nz(rs("Id_Impresora"), 0)     & ","
        json = json & """print_copies"":"   & Nz(rs("Copias_Imprimir"), 1)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/dish-printers", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE plato_impresoras SET Enviada_MySql = 1 " & _
                     "WHERE Id_Item IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Plato.Imp Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
