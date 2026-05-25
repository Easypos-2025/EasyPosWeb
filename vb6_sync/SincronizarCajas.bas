' ============================================================
' SincronizarCajas
' Endpoint: POST /api/pos/sync/push/cash-registers
' Tabla local VB6: cajas
' Tabla servidor: pos_cash_registers
' Columnas locales:
'   Nro_Caja     -> id
'   Nombre_Caja  -> name
'   Base_Inicial -> initial_amount
'   Base_Final   -> final_amount
'   Activa       -> is_active
'   Principal    -> is_principal
'   Abierta      -> is_open
'   Cod_Empleado -> employee_id
'   Id_Impresora -> printer_id
' PK servidor: id (= Nro_Caja en VB6)
' ============================================================
Public Sub SincronizarCajas(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM cajas WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """id"":"             & Nz(rs("Nro_Caja"), 0)                               & ","
        json = json & """company_id"":"     & Var_Id_Company_Envio                                 & ","
        json = json & """name"":"           & """" & EscapeJson(Nz(rs("Nombre_Caja"), ""))        & ""","
        json = json & """initial_amount"":"  & Nz(rs("Base_Inicial"), 0)                           & ","
        json = json & """final_amount"":"   & Nz(rs("Base_Final"), 0)                             & ","
        json = json & """is_active"":"      & Nz(rs("Activa"), 1)                                 & ","
        json = json & """is_principal"":"   & Nz(rs("Principal"), 0)                              & ","
        json = json & """is_open"":"        & Nz(rs("Abierta"), 0)                                & ","
        json = json & """employee_id"":"    & Nz(rs("Cod_Empleado"), 0)                           & ","
        json = json & """printer_id"":"     & Nz(rs("Id_Impresora"), 0)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/cash-registers", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo las confirmadas --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE cajas SET Enviada_MySql = 1 " & _
                     "WHERE Nro_Caja IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Cajas Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
