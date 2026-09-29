' ============================================================
' SincronizarInsumosProveedor / SincronizarInsumosFormaMedida
' Endpoints: POST /api/pos/sync/push/supply-suppliers
'            POST /api/pos/sync/push/supply-measures
' Tablas locales VB6: insumos_proveedor, insumos_forma_medida
' Tablas servidor:    insumos_proveedor, insumos_forma_medida (+ company_id)
' Grupo sync:         C — después de SincronizarProveedores y SincronizarInventarioPorciones
' Id_Insumo = Id_Item del insumo.
' Requiere: columna Enviada_MySql (script 015_escritorio_...sql)
' Variante A: solo Enviada_MySql = 0; marca por fila confirmada (llave compuesta).
' ============================================================

Public Sub SincronizarInsumosProveedor(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM insumos_proveedor WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """company_id"":"                & Var_Id_Company_Envio                                   & ","
        json = json & """id_proveedor"":"              & Nz(rs("Id_Proveedor"), 0)                              & ","
        json = json & """id_insumo"":"                 & Nz(rs("Id_Insumo"), 0)                                 & ","
        json = json & """fecha_inicial_negociacion"":" & """" & FechaIso(rs("Fecha_Inicial_Negociacion"))      & ""","
        json = json & """fecha_final_negociacion"":"   & """" & FechaIso(rs("Fecha_Final_Negociacion"))        & ""","
        json = json & """precio_pactado"":"            & Nz(rs("Precio_Pactado"), 0)                            & ","
        json = json & """id_forma_medida"":"           & Nz(rs("Id_Forma_Medida"), 0)                           & ","
        json = json & """nombre_forma_medida"":"       & """" & EscapeJson(Nz(rs("Nombre_Forma_Medida"), ""))   & ""","
        json = json & """observacion"":"               & """" & EscapeJson(Nz(rs("Observacion"), ""))           & """"
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/supply-suppliers", json)
    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' saved = "Id_Proveedor|Id_Insumo"
    Dim savedList As String
    savedList = ParseSaved(respuesta)
    If savedList <> "" Then
        conn.Execute "UPDATE insumos_proveedor SET Enviada_MySql = 1 " & _
                     "WHERE Enviada_MySql = 0 AND CONCAT(Id_Proveedor,'|',Id_Insumo) IN (" & savedList & ")"
    End If

    Var_Caption_Error = "Insumos-Proveedor Env.: " & TotalSaved(respuesta)
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub


Public Sub SincronizarInsumosFormaMedida(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM insumos_forma_medida WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """company_id"":"            & Var_Id_Company_Envio                       & ","
        json = json & """id_insumo"":"             & Nz(rs("Id_Insumo"), 0)                     & ","
        json = json & """id_forma_medida"":"       & Nz(rs("Id_Forma_Medida"), 0)               & ","
        json = json & """cant_unidades_minimas"":" & Str(Nz(rs("Cant_Unidades_Minimas"), 0))
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/supply-measures", json)
    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' saved = "Id_Forma_Medida|Id_Insumo"
    Dim savedList As String
    savedList = ParseSaved(respuesta)
    If savedList <> "" Then
        conn.Execute "UPDATE insumos_forma_medida SET Enviada_MySql = 1 " & _
                     "WHERE Enviada_MySql = 0 AND CONCAT(Id_Forma_Medida,'|',Id_Insumo) IN (" & savedList & ")"
    End If

    Var_Caption_Error = "Insumos-FormaMedida Env.: " & TotalSaved(respuesta)
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub


' Fecha → "YYYY-MM-DD" (vacío si es nula o inválida)
Private Function FechaIso(ByVal v As Variant) As String
    If IsNull(v) Or IsEmpty(v) Then
        FechaIso = ""
    ElseIf IsDate(v) Then
        FechaIso = Format(v, "YYYY-MM-DD")
    Else
        FechaIso = ""
    End If
End Function
