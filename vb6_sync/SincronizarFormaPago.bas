' ============================================================
' SincronizarFormaPago
' Endpoint: POST /api/pos/sync/push/payment-types
' Tabla local VB6: forma_pago
' Tabla servidor: pos_payment_types
' Columnas locales:
'   Id_Forma_Pago, Descripcion_Forma_Pago, Validar, Activo,
'   Seleccionar_Tarjeta, Valor, Pedir_Observacion, Pedir_Cliente,
'   Suma_Efectivo, Validar_Numero, Forma_Pago_Default
' Nota: tabla sin Enviada_MySql — se envian todos los registros
' ============================================================
Public Sub SincronizarFormaPago(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer todos los registros -----------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM forma_pago LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"               & Nz(rs("Id_Forma_Pago"), 0)                           & ","
        json = json & """company_id"":"       & Var_Id_Company_Envio                                  & ","
        json = json & """name"":"             & """" & EscapeJson(Nz(rs("Descripcion_Forma_Pago"), "")) & ""","
        json = json & """validate_amount"":"  & Nz(rs("Validar"), 0)                                  & ","
        json = json & """is_active"":"        & Nz(rs("Activo"), 0)                                   & ","
        json = json & """select_card"":"      & Nz(rs("Seleccionar_Tarjeta"), 0)                      & ","
        json = json & """value"":"            & Nz(rs("Valor"), 0)                                    & ","
        json = json & """ask_notes"":"        & Nz(rs("Pedir_Observacion"), 0)                        & ","
        json = json & """ask_customer"":"     & Nz(rs("Pedir_Cliente"), 0)                            & ","
        json = json & """adds_to_cash"":"     & Nz(rs("Suma_Efectivo"), 0)                            & ","
        json = json & """validate_number"":"  & Nz(rs("Validar_Numero"), 0)                           & ","
        json = json & """is_default"":"       & Nz(rs("Forma_Pago_Default"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/payment-types", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Mostrar estado (sin UPDATE — catálogo) ---------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Forma Pago Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
