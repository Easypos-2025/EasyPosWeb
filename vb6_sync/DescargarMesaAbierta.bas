' ============================================================
' DescargarMesaAbierta.bas
' Endpoint: GET /api/pos/sync/pull/table-status
' Tabla destino local: datatemppos.temp_Mesa_Abierta
' Solo actualiza el campo Abierta — no inserta mesas nuevas.
' Las mesas ya existen en local porque el desktop las sincroniza.
' ============================================================
Public Sub DescargarMesaAbierta(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Sincronizando estado de mesas..."

    Dim respuesta As String
    respuesta = ApiGet("/sync/pull/table-status?company_id=" & COMPANY_ID)

    If respuesta = "" Or respuesta = "[]" Then
        lblEstado.Caption = "Mesas: sin cambios " & Now()
        Exit Sub
    End If

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"
    On Error Resume Next
    sc.ExecuteStatement "var r = " & respuesta & ";"
    If Err.Number <> 0 Then
        Var_Caption_Error = "DescargarMesaAbierta: JSON invalido"
        Exit Sub
    End If
    On Error GoTo ErrHandler

    Dim total As Integer
    total = CInt(sc.Eval("r.length"))
    If total = 0 Then Exit Sub

    Dim conn As Object
    Set conn = GetConnDatatemppos()
    Dim act As Integer
    act = 0

    Dim i As Integer
    For i = 0 To total - 1
        Dim idMesa  As Long:    idMesa  = CLng(sc.Eval("r[" & i & "].table_id || 0"))
        Dim isOpen  As Integer: isOpen  = CInt(sc.Eval("r[" & i & "].is_open || 0"))
        Dim nombre  As String:  nombre  = EscSql(CStr(sc.Eval("r[" & i & "].table_name || ''")))

        ' Verificar si la mesa existe en local antes de actualizar
        Dim rs As Object
        Set rs = CreateObject("ADODB.Recordset")
        rs.Open "SELECT 1 FROM temp_Mesa_Abierta WHERE Id_Mesa=" & idMesa, conn

        If Not rs.EOF Then
            conn.Execute "UPDATE temp_Mesa_Abierta SET Abierta=" & isOpen & _
                         " WHERE Id_Mesa=" & idMesa
            act = act + 1
        Else
            ' La mesa no existe en local — insertar como referencia
            conn.Execute "INSERT INTO temp_Mesa_Abierta (Id_Mesa,Mesa,Abierta) " & _
                         "VALUES (" & idMesa & ",'" & nombre & "'," & isOpen & ")"
            act = act + 1
        End If
        rs.Close
        Set rs = Nothing
    Next i

    conn.Close
    lblEstado.Caption = "Mesas actualizadas: " & act & " | " & Now()
    Exit Sub
ErrHandler:
    Var_Caption_Error = "DescargarMesaAbierta: " & Err.Description
    On Error Resume Next: If Not conn Is Nothing Then conn.Close
End Sub
