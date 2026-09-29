' ============================================================
' SincronizarProveedores
' Endpoint: POST /api/pos/sync/push/suppliers
' Tabla local VB6: proveedores
' Tabla servidor: suppliers   (llave: company_id + id_proveedor)
' Grupo sync:     B — antes de SincronizarPlatosProductos (plato_producto.id_proveedor)
' Requiere:       columna Enviada_MySql (script 015_escritorio_...sql)
' Variante A: solo envía Enviada_MySql = 0; marca por Id_Proveedor confirmado.
' ============================================================
Public Sub SincronizarProveedores(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    ' -- 1. Leer pendientes (lotes) -------------------------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM proveedores WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- 2. Construir JSON ----------------------------------
    Dim json As String, sep As String
    json = "[": sep = ""

    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """company_id"":"        & Var_Id_Company_Envio                                    & ","
        json = json & """id_proveedor"":"      & Nz(rs("Id_Proveedor"), 0)                               & ","
        json = json & """nit"":"               & """" & EscapeJson(Nz(rs("Nit"), ""))                    & ""","
        json = json & """empresa"":"           & """" & EscapeJson(Nz(rs("Empresa"), ""))                & ""","
        json = json & """mail_empresa"":"      & """" & EscapeJson(Nz(rs("Mail_Empresa"), ""))           & ""","
        json = json & """direccion"":"         & """" & EscapeJson(Nz(rs("Direccion"), ""))              & ""","
        json = json & """telefono_fijo"":"     & """" & EscapeJson(Nz(rs("Telefono_Fijo"), ""))          & ""","
        json = json & """telefono_celular"":"  & """" & EscapeJson(Nz(rs("Telefono_Celular"), ""))       & ""","
        json = json & """observaciones"":"     & """" & EscapeJson(Nz(rs("Observaciones"), ""))          & ""","
        json = json & """activo"":"            & Nz(rs("Activo"), 1)
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    ' -- 3. Enviar al servidor ------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/suppliers", json)

    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    ' -- 4. Marcar solo los confirmados --------------------
    Dim savedList As String
    savedList = ParseSaved(respuesta)

    If savedList <> "" Then
        conn.Execute "UPDATE proveedores SET Enviada_MySql = 1 " & _
                     "WHERE Enviada_MySql = 0 AND Id_Proveedor IN (" & savedList & ")"
    End If

    ' -- 5. Mostrar estado ---------------------------------
    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Proveedores Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
