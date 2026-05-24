' ============================================================
' SincronizarDomiciliosFactura
' Endpoint: POST /api/pos/sync/push/invoice-delivery-fees
' Tabla local VB6: factura_domicilio
' Tabla servidor: factura_domicilio
' Columnas locales (tal como las vio el usuario):
'   Id_Registro, Nro_Factura, Valor, Fecha, Nro_Pedido, Vendedor, Id_Cliente, Enviada_MySql
' ============================================================
Public Sub SincronizarDomiciliosFactura(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM factura_domicilio WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """invoice_number"":""" & rs("Nro_Factura")       & ""","
        json = json & """company_id"":"       & Var_Id_Company_Envio     & ","
        json = json & """amount"":"           & Nz(rs("Valor"), 0)       & ","
        json = json & """date"":"             & """" & Format(rs("Fecha"), "YYYY-MM-DD") & ""","
        json = json & """order_number"":"     & """" & Nz(rs("Nro_Pedido"), "") & ""","
        json = json & """employee_id"":"      & Nz(rs("Vendedor"), 0)    & ","
        json = json & """customer_id"":"      & Nz(rs("Id_Cliente"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/invoice-delivery-fees", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE factura_domicilio SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Factura IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Dom.Factura Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
