' ============================================================
' SincronizarClientes
' Endpoint: POST /api/pos/sync/push/clientes
' Tabla local VB6: clientes
' Tabla servidor: clientes   (llave: company_id + id_cliente)
' Grupo sync:     B — antes de SincronizarListaPreciosCliente (usa Id_Cliente)
' Variante A: solo Enviada_MySql = 0; marca por Id_Cliente confirmado.
' ============================================================
Public Sub SincronizarClientes(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM clientes WHERE Enviada_MySql = 0 LIMIT " & Var_Limit_Registros, conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    Dim json As String, sep As String
    json = "[": sep = ""
    Do While Not rs.EOF
        json = json & sep & "{"
        json = json & """company_id"":"        & Var_Id_Company_Envio                        & ","
        json = json & """id_cliente"":"        & Nz(rs("Id_Cliente"), 0)                     & ","
        json = json & """cedula"":"            & JStr(rs("cedula"))                          & ","
        json = json & """nombres"":"           & JStr(rs("nombres"))                         & ","
        json = json & """apellidos"":"         & JStr(rs("Apellidos"))                       & ","
        json = json & """direccion"":"         & JStr(rs("direccion"))                       & ","
        json = json & """telefono"":"          & JStr(rs("telefono"))                        & ","
        json = json & """barrio"":"            & JStr(rs("Barrio"))                          & ","
        json = json & """mail"":"              & JStr(rs("Mail"))                            & ","
        json = json & """dia_cumple"":"        & JStr(rs("Dia_Cumple"))                      & ","
        json = json & """mes_cumple"":"        & JStr(rs("Mes_Cumple"))                      & ","
        json = json & """edad"":"              & JStr(rs("Edad"))                            & ","
        json = json & """ocupacion"":"         & JStr(rs("Ocupacion"))                       & ","
        json = json & """porc_descuento"":"    & JStr(rs("Porc_Descuento"))                  & ","
        json = json & """observaciones"":"     & JStr(rs("Observaciones"))                   & ","
        json = json & """fecha_aniversario"":" & JFecha(rs("Fecha_Aniversario"))            & ","
        json = json & """fecha_grado"":"       & JFecha(rs("Fecha_Grado"))                   & ","
        json = json & """empresa"":"           & JStr(rs("Empresa"))                         & ","
        json = json & """id_klob"":"           & JStr(rs("Id_Klob"))                         & ","
        json = json & """tarjeta_fiel"":"      & JStr(rs("Tarjeta_Fiel"))                    & ","
        json = json & """cod_barrio"":"        & Nz(rs("Cod_Barrio"), 0)                     & ","
        json = json & """id_sede"":"           & Nz(rs("Id_Sede"), 0)                        & ","
        json = json & """referencia"":"        & JStr(rs("Referencia"))
        json = json & "}"
        sep = ","
        rs.MoveNext
    Loop
    json = json & "]"
    rs.Close

    Dim respuesta As String
    respuesta = ApiPost("/sync/push/clientes", json)
    If respuesta = "" Then
        conn.Close: Exit Sub
    End If

    Dim savedList As String
    savedList = ParseSaved(respuesta)
    If savedList <> "" Then
        conn.Execute "UPDATE clientes SET Enviada_MySql = 1 " & _
                     "WHERE Enviada_MySql = 0 AND Id_Cliente IN (" & savedList & ")"
    End If

    Var_Caption_Error = "Clientes Env.: " & TotalSaved(respuesta)
    conn.Close
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub


' Texto → "valor" JSON escapado (null si vacío)
Private Function JStr(ByVal v As Variant) As String
    If IsNull(v) Or IsEmpty(v) Then
        JStr = "null"
    Else
        JStr = """" & EscapeJson(CStr(v)) & """"
    End If
End Function

' Fecha → "YYYY-MM-DD" o null
Private Function JFecha(ByVal v As Variant) As String
    If IsNull(v) Or IsEmpty(v) Then
        JFecha = "null"
    ElseIf IsDate(v) Then
        JFecha = """" & Format(v, "YYYY-MM-DD") & """"
    Else
        JFecha = "null"
    End If
End Function
