Attribute VB_Name = "modCatalogoWeb"
Option Explicit

Private Declare Function ShellExecute Lib "shell32.dll" Alias "ShellExecuteA" _
    (ByVal hwnd As Long, ByVal lpOperation As String, ByVal lpFile As String, _
     ByVal lpParameters As String, ByVal lpDirectory As String, ByVal nShowCmd As Long) As Long
' ============================================================
' modCatalogoWeb - Catalogo de EasyPosWeb al escritorio y acceso al panel del Agente Local
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
'
' AVISO Y BLOQUEO ANTES DE SINCRONIZAR (la web manda: lo cambiado alla reemplaza lo del escritorio al
' sincronizar, asi que no conviene editar aqui un registro que tiene cambios de la web sin bajar):
'   El Agente Local copia cada minuto lo pendiente a datatemppos.ag_maestros_pendientes
'     entidad   'plato' (Id_Plato), 'insumo' (Id_Item), 'cliente' (Id_Cliente), 'categoria_platos' y
'               'categoria_productos' (Cod_Categoria), 'forma_medida' (Id_Forma_Medida),
'               'proveedor' (Id_Proveedor), 'lista_precios' (Id_Producto), 'sede' (0)
'     provisional = 1: es nuevo de la web (aun no existe en el escritorio)
'   Al abrir el escritorio o el dashboard:   Call Avisar_Cambios_Web_Pendientes
'   Antes de entrar a modificar el catalogo: If Avisar_Cambios_Web_Pendientes(10) Then Exit Sub
'   Antes de dejar modificar un plato:       If Tiene_Cambios_Web("plato", Id_Plato) Then ... (no dejar editar)
'   Cuando se reviso por ultima vez:         Revision_Cambios_Web()  (si es vieja, el agente no esta conectado)
' ABRIR EL PANEL DEL AGENTE SIN DIGITAR LA CLAVE (boton del escritorio):
'   Call Abrir_Panel_Agente
'   El agente entrega un codigo de un solo uso (vence en 30 s) SOLO a este mismo PC; el panel entra con el.
'   La clave nunca va en el enlace. Mostrar el boton solo a los usuarios administradores.
'
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
If MsgBox("Se bajaran al escritorio los cambios del catalogo hechos en la web (platos, precios, insumos," & vbCrLf & _
          "clientes, listas de precios y datos de la sede)." & vbCrLf & _
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
Call Esperar_Resultado_Catalogo_Web
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


Public Function Cambios_Web_Pendientes() As Long
On Error GoTo Linea
Dim Rs As ADODB.Recordset
Set Rs = New ADODB.Recordset
Rs.Open "SELECT COUNT(*) AS n FROM ag_maestros_pendientes", Base_Reportes_MySql, adOpenStatic, adLockReadOnly
If Not Rs.EOF Then Cambios_Web_Pendientes = Val(Rs!n & "")
Rs.Close
Set Rs = Nothing
Exit Function
Linea:
Cambios_Web_Pendientes = 0
End Function

Public Function Tiene_Cambios_Web(ByVal Entidad As String, ByVal Id As Long) As Boolean
On Error GoTo Linea
Dim Cmd As ADODB.Command, Rs As ADODB.Recordset
Set Cmd = New ADODB.Command
Set Cmd.ActiveConnection = Base_Reportes_MySql
Cmd.CommandType = adCmdText
Cmd.CommandText = "SELECT COUNT(*) AS n FROM ag_maestros_pendientes WHERE entidad = ? AND id = ?"
Cmd.Parameters.Append Cmd.CreateParameter("entidad", adVarChar, adParamInput, 30, Entidad)
Cmd.Parameters.Append Cmd.CreateParameter("id", adInteger, adParamInput, , Id)
Set Rs = Cmd.Execute
If Not Rs.EOF Then Tiene_Cambios_Web = (Val(Rs!n & "") > 0)
Rs.Close
Set Rs = Nothing
Set Cmd = Nothing
Exit Function
Linea:
Tiene_Cambios_Web = False
End Function

Public Function Revision_Cambios_Web() As String
On Error GoTo Linea
Dim Rs As ADODB.Recordset
Set Rs = New ADODB.Recordset
Rs.Open "SELECT valor FROM ag_config WHERE clave = 'maestros_revisado'", Base_Reportes_MySql, adOpenStatic, adLockReadOnly
If Not Rs.EOF Then Revision_Cambios_Web = Trim(Rs!valor & "")
Rs.Close
Set Rs = Nothing
Exit Function
Linea:
Revision_Cambios_Web = ""
End Function

Public Function Avisar_Cambios_Web_Pendientes(Optional ByVal Minutos_Revision As Long = 0) As Boolean
' Devuelve True si hay cambios del catalogo hechos en la web que aun no se han bajado al escritorio
' (y muestra el mensaje). False = todo al dia: se puede entrar a modificar.
' Minutos_Revision (opcional): si el Agente Local no ha revisado en ese tiempo (cerrado o sin internet),
' no se puede saber si hay cambios: tambien devuelve True. 0 = no se revisa. Si la sede no tiene Agente Local
' (nunca ha revisado) no se bloquea: no hay catalogo de la web que bajar.
' Uso:  If Avisar_Cambios_Web_Pendientes(10) Then Exit Sub    ' no deja entrar hasta sincronizar
Dim N As Long, Revisado As String
N = Cambios_Web_Pendientes()
If N > 0 Then
   MsgBox "Hay " & N & " cambio(s) del catalogo hechos en EasyPosWeb que aun no se han bajado al escritorio" & vbCrLf & _
          "(platos, insumos, clientes, categorias, listas de precios...)." & vbCrLf & vbCrLf & _
          "Pulse ""Sincronizar Web"" antes de modificar el catalogo aqui:" & vbCrLf & _
          "lo cambiado en la web reemplaza lo del escritorio al sincronizar.", vbExclamation, "Catalogo de la web"
   Avisar_Cambios_Web_Pendientes = True
   Exit Function
End If
If Minutos_Revision > 0 Then
   Revisado = Revision_Cambios_Web()
   If Revisado = "" Then
      Exit Function                     ' sin Agente Local en esta sede
   ElseIf Not IsDate(Revisado) Then
      Avisar_Cambios_Web_Pendientes = True
   ElseIf DateDiff("n", CDate(Revisado), Now) > Minutos_Revision Then
      Avisar_Cambios_Web_Pendientes = True
   End If
   If Avisar_Cambios_Web_Pendientes Then
      MsgBox "No se pudo confirmar si hay cambios del catalogo pendientes en EasyPosWeb:" & vbCrLf & _
             "el Agente Local no ha revisado" & IIf(IsDate(Revisado), " desde " & Revisado, "") & "." & vbCrLf & vbCrLf & _
             "Verifique que el Agente Local este abierto y con internet, y pulse ""Sincronizar Web"".", _
             vbExclamation, "Catalogo de la web"
   End If
End If
End Function

Public Function Puede_Editar_Plato(ByVal Id_Plato As Long) As Boolean
' Ejemplo de bloqueo: llamar antes de abrir la edicion de un plato
If Tiene_Cambios_Web("plato", Id_Plato) Then
   MsgBox "Este plato tiene cambios hechos en EasyPosWeb que aun no se han bajado." & vbCrLf & _
          "Sincronice el catalogo de la web antes de modificarlo.", vbExclamation, "Catalogo de la web"
   Puede_Editar_Plato = False
Else
   Puede_Editar_Plato = True
End If
End Function


Public Sub Abrir_Panel_Agente(Optional ByVal Puerto As Long = 8090)
' Abre el panel de administracion del Agente Local sin digitar la clave. Si el agente no responde o no
' entrega el codigo, abre la pantalla normal de ingreso (pide la clave).
On Error GoTo Linea
Dim Http As Object, Respuesta As String, Codigo As String, P1 As Long, P2 As Long, Base As String
Base = "http://127.0.0.1:" & Puerto
Set Http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
Http.setTimeouts 3000, 3000, 5000, 5000
Http.Open "POST", Base & "/api/ag/admin/codigo-local", False
Http.setRequestHeader "Content-Type", "application/json"
Http.send "{}"
If Http.Status = 200 Then
   Respuesta = Http.responseText
   P1 = InStr(Respuesta, """codigo"":""")
   If P1 > 0 Then
      P1 = P1 + Len("""codigo"":""")
      P2 = InStr(P1, Respuesta, """")
      If P2 > P1 Then Codigo = Mid(Respuesta, P1, P2 - P1)
   End If
End If
Set Http = Nothing
If Codigo <> "" Then
   ShellExecute 0, "open", Base & "/#/admin/ingresar?codigo=" & Codigo, vbNullString, vbNullString, 1
Else
   ShellExecute 0, "open", Base & "/#/admin/ingresar", vbNullString, vbNullString, 1
End If
Exit Sub
Linea:
' El agente no esta abierto o no responde: se abre la pantalla de ingreso normal
ShellExecute 0, "open", "http://127.0.0.1:" & Puerto & "/#/admin/ingresar", vbNullString, vbNullString, 1
End Sub


Public Sub Esperar_Resultado_Catalogo_Web(Optional ByVal Segundos_Maximo As Long = 120)
' Espera a que el Agente Local termine (revisa cada segundo, sin congelar el programa) y muestra el resultado.
' El agente revisa la solicitud cada 10 segundos; una sincronizacion normal tarda pocos segundos mas.
Dim Inicio As Single, Estado As String, Ultimo As Single
Inicio = Timer
Do
   Ultimo = Timer
   Do While Timer - Ultimo < 1 And Timer >= Ultimo          ' pausa de 1 s sin congelar
      DoEvents
   Loop
   Estado = Estado_Sincronizacion_Catalogo_Web()
   If Estado = "LISTO" Then
      MsgBox "Catalogo de la web sincronizado." & vbCrLf & vbCrLf & Resultado_Sincronizacion_Catalogo_Web(), _
             vbInformation, "Catalogo de la web"
      Exit Sub
   ElseIf Left(Estado, 5) = "ERROR" Then
      MsgBox "No se pudo sincronizar el catalogo de la web:" & vbCrLf & Mid(Estado, 7), vbCritical, "Catalogo de la web"
      Exit Sub
   End If
   If Timer < Inicio Then Inicio = Timer                      ' paso de medianoche
Loop While Timer - Inicio < Segundos_Maximo
If Estado = "SOLICITADO" Then
   MsgBox "El Agente Local no ha tomado la solicitud. Verifique que este abierto y conectado a internet;" & vbCrLf & _
          "la sincronizacion se hara sola apenas lo este.", vbExclamation, "Catalogo de la web"
Else
   MsgBox "La sincronizacion sigue en curso. Revise el resultado en unos minutos" & vbCrLf & _
          "(panel del agente: Catalogo de la web).", vbInformation, "Catalogo de la web"
End If
End Sub
