' ============================================================
' SincronizarDomiciliosRecibo
' Endpoint: POST /api/pos/sync/push/receipt-delivery-fees
' Tabla local VB6: recibos_domicilio
' Tabla servidor: receipt_delivery_fees
' Grupo sync:     J — después de SincronizarRecibos (Grupo F2)
' Depende de:     pos_receipts
' Columnas locales (misma estructura que factura_domicilio):
'   Id_Registro, Nro_Factura, Valor, Fecha, Nro_Pedido, Vendedor, Id_Cliente, Enviada_MySql
' Nota: VB6 llama Nro_Factura al numero de recibo (mismo campo, distinta tabla)
' ============================================================
Public Sub SincronizarDomiciliosRecibo(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM recibos_domicilio WHERE Enviada_MySql = 0 AND year(Fecha) >= 2025 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON + acumular Id_Registro enviados --
    Dim json As String, sep As String, idList As String, idSep As String
    json = "[": sep = "": idList = "": idSep = ""

    Do While Not rs.EOF
        Dim idReg As Long
        idReg = Nz(rs("Id_Registro"), 0)

        json = json & sep & "{"
        json = json & """id_registro"":"     & idReg                     & ","
        json = json & """invoice_number"":""" & rs("Nro_Factura")        & ""","
        json = json & """company_id"":"      & Var_Id_Company_Envio      & ","
        json = json & """amount"":"          & Nz(rs("Valor"), 0)        & ","
        json = json & """date"":"            & """" & Format(rs("Fecha"), "YYYY-MM-DD") & ""","
        json = json & """order_number"":"    & """" & Nz(rs("Nro_Pedido"), "") & ""","
        json = json & """employee_id"":"     & Nz(rs("Vendedor"), 0)     & ","
        json = json & """customer_id"":"     & Nz(rs("Id_Cliente"), 0)
        json = json & "}"

        idList = idList & idSep & idReg
        sep = ",": idSep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/receipt-delivery-fees", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar como enviados por Id_Registro -----------
    If idList <> "" Then
        conn.Execute "UPDATE recibos_domicilio SET Enviada_MySql = 1 " & _
                     "WHERE Id_Registro IN (" & idList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Dom.Recibo Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
