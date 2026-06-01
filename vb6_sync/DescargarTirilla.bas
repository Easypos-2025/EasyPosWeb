' ============================================================
' DescargarTirilla.bas
' No llama un endpoint propio — se ejecuta DESPUÉS de DescargarDetalleComanda.
' Lee temp_detalle_comanda local (pedidos web aún no impresos)
' e inserta en temp_impresion_tirilla_comanda para que el módulo
' de impresión del escritorio los envíe a las impresoras físicas.
' Condición: Nro_pedido LIKE 'WEB-%' AND Impreso=0
' ============================================================
Public Sub DescargarTirilla(lblEstado As Label)
    On Error GoTo ErrHandler
    lblEstado.Caption = "Preparando tirillas web para imprimir..."

    Dim conn As Object
    Set conn = GetConnDatatemppos()

    ' Leer ítems de pedidos web que aún no tienen tirilla generada
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT d.Nro_pedido, d.Fecha, d.Id_Plato, d.Item, d.Depende, " & _
            "       d.Cantidad, d.Novedad, d.Cambios, d.Hora_Plato, " & _
            "       d.Nro_Puesto, d.Impresora, " & _
            "       c.Mesa AS Nro_Mesa, c.Hora, " & _
            "       COALESCE(e.nombres,'Web') AS Mesero " & _
            "FROM temp_detalle_comanda d " & _
            "JOIN temp_comanda c ON c.Nro_Pedido=d.Nro_pedido AND c.Fecha=d.Fecha " & _
            "LEFT JOIN meseros e ON e.cod_empleado=c.Mesero " & _
            "WHERE d.Nro_pedido LIKE 'WEB-%' " & _
            "  AND d.Fecha=DATE(NOW()) " & _
            "  AND d.Impreso=0 " & _
            "  AND c.Cancelado=0 " & _
            "  AND NOT EXISTS (" & _
            "      SELECT 1 FROM temp_impresion_tirilla_comanda t " & _
            "      WHERE t.Nro_pedido=d.Nro_pedido " & _
            "        AND t.Id_Plato=d.Id_Plato " & _
            "        AND t.Item=d.Item " & _
            "        AND t.Depende=d.Depende)", conn

    If rs.EOF Then
        rs.Close: conn.Close
        lblEstado.Caption = "Tirillas web: todo impreso " & Now()
        Exit Sub
    End If

    Dim ins As Integer
    ins = 0

    Do While Not rs.EOF
        Dim nroPed  As String: nroPed  = EscSql(CStr(Nz(rs("Nro_pedido"), "")))
        Dim fecha   As String: fecha   = Format(rs("Fecha"), "YYYY-MM-DD")
        Dim dishId  As Long:   dishId  = CLng(Nz(rs("Id_Plato"), 0))
        Dim item    As Long:   item    = CLng(Nz(rs("Item"), 0))
        Dim depende As Long:   depende = CLng(Nz(rs("Depende"), 0))
        Dim cant    As Double: cant    = CDbl(Nz(rs("Cantidad"), 0))
        Dim novedad As String: novedad = EscSql(CStr(Nz(rs("Novedad"), "")))
        Dim cambios As String: cambios = EscSql(CStr(Nz(rs("Cambios"), "")))
        Dim horaP   As String: horaP   = EscSql(CStr(Nz(rs("Hora_Plato"), "")))
        Dim puesto  As Long:   puesto  = CLng(Nz(rs("Nro_Puesto"), 0))
        Dim imprsr  As String: imprsr  = EscSql(CStr(Nz(rs("Impresora"), "")))
        Dim mesa    As String: mesa    = EscSql(CStr(Nz(rs("Nro_Mesa"), "")))
        Dim hora    As String: hora    = EscSql(CStr(Nz(rs("Hora"), "")))
        Dim mesero  As String: mesero  = EscSql(CStr(Nz(rs("Mesero"), "Web")))

        conn.Execute "INSERT IGNORE INTO temp_impresion_tirilla_comanda " & _
            "(Nro_pedido,Mesero,Fecha,Nro_Mesa,Id_Plato,Item," & _
            " Cantidad,Hora,Novedad,Impreso,Cambios,Mostrar," & _
            " Impresora,Nro_Puesto,Nuevo,Cancelado,Enviado_Desde,Hora_Plato,Depende) " & _
            "VALUES (" & _
            "'" & nroPed & "','" & mesero & "','" & fecha & "','" & mesa & "'," & _
            dishId & "," & item & "," & _
            Replace(CStr(cant), ",", ".") & ",'" & hora & "','" & novedad & "'," & _
            "0,'" & cambios & "',1,'" & imprsr & "'," & puesto & ",1,0,'WEB','" & horaP & "'," & depende & ")"
        ins = ins + 1
        rs.MoveNext
    Loop

    rs.Close
    conn.Close
    lblEstado.Caption = "Tirillas web generadas: " & ins & " | " & Now()
    Exit Sub
ErrHandler:
    Var_Caption_Error = "DescargarTirilla: " & Err.Description
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    If Not conn Is Nothing Then conn.Close
End Sub
