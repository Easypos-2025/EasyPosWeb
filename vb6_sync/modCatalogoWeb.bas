Attribute VB_Name = "modCatalogoWeb"
Option Explicit
' ============================================================
' modCatalogoWeb - Bajar el catalogo de EasyPosWeb al escritorio (S3)
' ------------------------------------------------------------
' No es automatico: el admin lo pide (desde aqui o desde el panel de la mini-app del agente).
' Este modulo solo deja la solicitud en datatemppos.ag_config; el Agente Local la atiende en
' unos segundos: baja los platos creados o modificados en la web (con sus impresoras), los datos
' de la sede y las fotos. La web manda: lo que cambio alla reemplaza lo del escritorio.
'
' Uso desde el dashboard:
'   Call Solicitar_Sincronizar_Catalogo_Web          (boton "Bajar catalogo de la web")
'   lblEstado.Caption = Estado_Sincronizacion_Catalogo_Web()   (en un Timer, ej. cada 5 s)
'
' Estados: SOLICITADO -> EN CURSO -> LISTO (o ERROR: ...). Resultado: Resultado_Sincronizacion_Catalogo_Web()
' Requiere: Base_Reportes_MySql (conexion ADO a datatemppos), Var_Nombre_Usuario, referencia a ADO.
' ============================================================

Public Sub Solicitar_Sincronizar_Catalogo_Web()
On Error GoTo Linea
Dim Cmd As ADODB.Command, Estado As String, Usuario As String
Estado = Estado_Sincronizacion_Catalogo_Web()
If Estado = "SOLICITADO" Or Estado = "EN CURSO" Then
   MsgBox "Ya hay una sincronizacion del catalogo en curso. Espere unos segundos.", vbInformation
   Exit Sub
End If
If MsgBox("Se bajaran al escritorio los platos y datos de la sede modificados en la web." & vbCrLf & _
          "Lo que cambio en la web reemplaza lo del escritorio. ¿Continuar?", vbQuestion + vbYesNo) = vbNo Then Exit Sub
Usuario = Trim(Var_Nombre_Usuario & "")
If Usuario = "" Then Usuario = "escritorio"
Set Cmd = New ADODB.Command
Set Cmd.ActiveConnection = Base_Reportes_MySql
Cmd.CommandType = adCmdText
Cmd.CommandText = "INSERT INTO ag_config (clave, valor) VALUES ('maestros_solicitud', ?) ON DUPLICATE KEY UPDATE valor = VALUES(valor)"
Cmd.Parameters.Append Cmd.CreateParameter("valor", adVarChar, adParamInput, 255, Left("SOLICITADO|" & Usuario, 255))
Cmd.Execute , , adExecuteNoRecords
Set Cmd = Nothing
MsgBox "Solicitud enviada. El Agente Local la atiende en unos segundos.", vbInformation
Exit Sub
Linea:
MsgBox "No se pudo solicitar la sincronizacion del catalogo: " & Err.Description, vbCritical
End Sub

Public Function Estado_Sincronizacion_Catalogo_Web() As String
On Error GoTo Linea
Dim Rs As ADODB.Recordset, Valor As String
Set Rs = New ADODB.Recordset
Rs.Open "SELECT valor FROM ag_config WHERE clave = 'maestros_solicitud'", Base_Reportes_MySql, adOpenStatic, adLockReadOnly
If Not Rs.EOF Then Valor = Trim(Rs!valor & "")
Rs.Close
Set Rs = Nothing
If InStr(Valor, "|") > 0 Then Valor = Left(Valor, InStr(Valor, "|") - 1)
Estado_Sincronizacion_Catalogo_Web = Valor
Exit Function
Linea:
Estado_Sincronizacion_Catalogo_Web = ""
End Function

Public Function Resultado_Sincronizacion_Catalogo_Web() As String
On Error GoTo Linea
Dim Rs As ADODB.Recordset
Set Rs = New ADODB.Recordset
Rs.Open "SELECT valor FROM ag_config WHERE clave = 'maestros_resultado'", Base_Reportes_MySql, adOpenStatic, adLockReadOnly
If Not Rs.EOF Then Resultado_Sincronizacion_Catalogo_Web = Trim(Rs!valor & "")
Rs.Close
Set Rs = Nothing
Exit Function
Linea:
Resultado_Sincronizacion_Catalogo_Web = ""
End Function
