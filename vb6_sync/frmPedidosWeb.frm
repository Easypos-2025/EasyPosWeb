VERSION 5.00
Object = "{86CF1D34-0C5F-11D2-A9FC-0000F8754DA1}#2.0#0"; "mscomct2.ocx"
Object = "{5E9E78A0-531B-11CF-91F6-C2863C385E30}#1.0#0"; "MSFLXGRD.OCX"
Begin VB.Form frmPedidosWeb
   BackColor       =   &H00C0C0C0&
   BorderStyle     =   1  'Fixed Single
   Caption         =   "Pedidos Web - Aceptar / Rechazar"
   ClientHeight    =   9300
   ClientLeft      =   45
   ClientTop       =   390
   ClientWidth     =   15000
   BeginProperty Font
      Name            =   "Arial"
      Size            =   9.75
      Charset         =   0
      Weight          =   400
      Underline       =   0   'False
      Italic          =   0   'False
      Strikethrough   =   0   'False
   EndProperty
   KeyPreview      =   -1  'True
   LinkTopic       =   "Form1"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   9300
   ScaleWidth      =   15000
   StartUpPosition =   2  'CenterScreen
   Begin VB.Timer Timer1
      Interval        =   10000
      Left            =   14400
      Top             =   1080
   End
   Begin VB.CommandButton cmdPendientes
      BackColor       =   &H00C0FFC0&
      Caption         =   "&Pendientes"
      BeginProperty Font
         Name            =   "Arial"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   600
      Left            =   120
      Style           =   1  'Graphical
      TabIndex        =   0
      Top             =   120
      Width           =   2400
   End
   Begin VB.CommandButton cmdProcesados
      BackColor       =   &H00E0E0E0&
      Caption         =   "P&rocesados"
      BeginProperty Font
         Name            =   "Arial"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   600
      Left            =   2640
      Style           =   1  'Graphical
      TabIndex        =   1
      Top             =   120
      Width           =   2400
   End
   Begin VB.CommandButton cmdActualizar
      BackColor       =   &H00FFFFC0&
      Caption         =   "&Actualizar"
      BeginProperty Font
         Name            =   "Arial"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   600
      Left            =   10200
      Style           =   1  'Graphical
      TabIndex        =   4
      Top             =   120
      Width           =   2220
   End
   Begin VB.CommandButton cmdCerrar
      BackColor       =   &H00E0E0E0&
      Caption         =   "&Cerrar"
      BeginProperty Font
         Name            =   "Arial"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   600
      Left            =   12600
      Style           =   1  'Graphical
      TabIndex        =   5
      Top             =   120
      Width           =   2280
   End
   Begin MSComCtl2.DTPicker DTPicker1
      Height          =   405
      Left            =   6000
      TabIndex        =   3
      Top             =   210
      Visible         =   0   'False
      Width           =   1935
      _ExtentX        =   3413
      _ExtentY        =   714
      _Version        =   393216
   End
   Begin VB.CheckBox chkTodos
      BackColor       =   &H00C0C0C0&
      Caption         =   "Marcar todos"
      Height          =   300
      Left            =   120
      TabIndex        =   6
      Top             =   1200
      Width           =   2400
   End
   Begin MSFlexGridLib.MSFlexGrid grdLotes
      Height          =   4200
      Left            =   120
      TabIndex        =   7
      Top             =   1560
      Width           =   14760
      _ExtentX        =   26035
      _ExtentY        =   7408
      _Version        =   393216
      BackColorSel    =   65535
      BackColorBkg    =   14737632
   End
   Begin MSFlexGridLib.MSFlexGrid grdDetalle
      Height          =   2900
      Left            =   120
      TabIndex        =   8
      Top             =   6240
      Width           =   10200
      _ExtentX        =   17992
      _ExtentY        =   5115
      _Version        =   393216
      BackColorBkg    =   14737632
   End
   Begin VB.CommandButton cmdAceptar
      BackColor       =   &H0080FF80&
      Caption         =   "ACEPTAR MARCADOS"
      BeginProperty Font
         Name            =   "Arial"
         Size            =   14.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   1300
      Left            =   10560
      Style           =   1  'Graphical
      TabIndex        =   9
      Top             =   6240
      Width           =   4320
   End
   Begin VB.CommandButton cmdRechazar
      BackColor       =   &H008080FF&
      Caption         =   "RECHAZAR MARCADOS"
      BeginProperty Font
         Name            =   "Arial"
         Size            =   14.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   1300
      Left            =   10560
      Style           =   1  'Graphical
      TabIndex        =   10
      Top             =   7840
      Width           =   4320
   End
   Begin VB.Label lblFecha
      BackStyle       =   0  'Transparent
      Caption         =   "Fecha:"
      BeginProperty Font
         Name            =   "Arial"
         Size            =   11.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   300
      Left            =   5200
      TabIndex        =   2
      Top             =   270
      Visible         =   0   'False
      Width           =   780
   End
   Begin VB.Label lblInfo
      BackStyle       =   0  'Transparent
      Caption         =   "lblInfo"
      Height          =   300
      Left            =   120
      TabIndex        =   11
      Top             =   840
      Width           =   14160
   End
   Begin VB.Label lblDetalle
      BackStyle       =   0  'Transparent
      Caption         =   "Detalle: haga clic en un pedido para ver sus productos"
      BeginProperty Font
         Name            =   "Arial"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   300
      Left            =   120
      TabIndex        =   12
      Top             =   5880
      Width           =   10200
   End
End
Attribute VB_Name = "frmPedidosWeb"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit
' ============================================================
' frmPedidosWeb - Pedidos web pendientes de aceptar en caja
' ------------------------------------------------------------
' Los pedidos (y productos agregados) que se envian desde EasyPosWeb llegan por el Agente Local
' a datatemppos.ag_pw_lote2 / ag_pw_item. Nada pasa al escritorio ni se imprime hasta aceptarlo
' aqui (o en el panel de la mini-app del agente).
'   * Tipos: pedido nuevo, productos agregados, ELIMINAR productos y CANCELAR cuenta (estos dos
'     traen el motivo del mesero; al aceptarlos el agente imprime la anulacion y pasa al historico).
'   * Este form SOLO marca el estado: PENDIENTE o ERROR -> ACEPTADO o RECHAZADO (con motivo).
'     El Agente Local pasa lo aceptado a Temp_comanda / Temp_detalle_comanda (y _parcial) y lo
'     envia a impresion (Temp_Impresion_Tirilla_comanda) en unos segundos, igual que
'     "Enviar pedido".
'   * Si no se pudo pasar (caja cerrada, mesa ocupada, pedido ya cerrado...) queda en ERROR con
'     el mensaje: se puede volver a aceptar o rechazar.
'   * Nada se borra: la pestana Procesados muestra lo aceptado / rechazado de una fecha.
'   * Si dos personas procesan el mismo pedido a la vez, cuenta solo el primero
'     (UPDATE ... WHERE estado IN ('PENDIENTE','ERROR')).
' Requiere: Base_Reportes_MySql (conexion ADO a datatemppos), Var_Nombre_Usuario,
'           MSFLXGRD.OCX, mscomct2.ocx (DTPicker) y la referencia a ADO.
' Consulta para la alerta del dashboard (pedidos web por atender):
'   SELECT COUNT(*) FROM ag_pw_lote2 WHERE estado IN ('PENDIENTE','ERROR')
' ============================================================

Private Const COL_MARCA As Integer = 0
Private Const COL_HORA As Integer = 1
Private Const COL_TIPO As Integer = 2
Private Const COL_MESA As Integer = 3
Private Const COL_MESERO As Integer = 4
Private Const COL_ITEMS As Integer = 5
Private Const COL_TOTAL As Integer = 6
Private Const COL_ESTADO As Integer = 7
Private Const COL_OBS As Integer = 8
Private Const COL_ID As Integer = 9
Private Const COL_ESTADO_BD As Integer = 10
Private Const TOTAL_COLS As Integer = 11

Private Const COLOR_ACTIVO As Long = &HC0FFC0
Private Const COLOR_INACTIVO As Long = &HE0E0E0
Private Const COLOR_PENDIENTE As Long = &HC0FFFF
Private Const COLOR_ACEPTADO As Long = &HC0FFC0
Private Const COLOR_ERROR As Long = &HC0C0FF
Private Const COLOR_BLANCO As Long = &HFFFFFF

Private Var_Vista As String           ' "P" = pendientes, "R" = procesados
Private Var_Marcados As String        ' ids marcados, ej: ",12,15,"
Private Var_Id_Detalle As Long
Private Var_Cargando As Boolean

Private Sub Form_Load()
On Error GoTo Linea
Var_Vista = "P"
Var_Marcados = ","
DTPicker1.Format = dtpShortDate
DTPicker1.Value = Date
Call Configurar_Grillas
Call Mostrar_Vista
Exit Sub
Linea:
MsgBox "frmPedidosWeb Form_Load " & Err.Description
End Sub

Private Sub Form_KeyDown(KeyCode As Integer, Shift As Integer)
If KeyCode = vbKeyEscape Then Unload Me
If KeyCode = vbKeyF5 Then Call Cargar_Lotes
End Sub

Private Sub Form_Unload(Cancel As Integer)
Timer1.Enabled = False
End Sub

Private Function Texto(ByVal Valor As Variant) As String
If IsNull(Valor) Then
   Texto = ""
Else
   Texto = Trim(CStr(Valor))
End If
End Function

Private Function Pesos(ByVal Valor As Variant) As String
If IsNull(Valor) Then Valor = 0
Pesos = Format(CDbl(Valor), "$ #,##0")
End Function

Private Function Nombre_Usuario() As String
Nombre_Usuario = Trim(Var_Nombre_Usuario & "")
If Nombre_Usuario = "" Then Nombre_Usuario = "Usuario escritorio"
Nombre_Usuario = Left(Nombre_Usuario, 150)
End Function

Private Sub Configurar_Grillas()
With grdLotes
    .Redraw = False
    .Cols = TOTAL_COLS
    .Rows = 2
    .FixedRows = 1
    .FixedCols = 0
    .SelectionMode = flexSelectionByRow
    .FocusRect = flexFocusNone
    .AllowUserResizing = flexResizeColumns
    .TextMatrix(0, COL_MARCA) = "X"
    .TextMatrix(0, COL_HORA) = "Recibido"
    .TextMatrix(0, COL_TIPO) = "Tipo"
    .TextMatrix(0, COL_MESA) = "Mesa"
    .TextMatrix(0, COL_MESERO) = "Mesero"
    .TextMatrix(0, COL_ITEMS) = "Prod."
    .TextMatrix(0, COL_TOTAL) = "Total"
    .TextMatrix(0, COL_ESTADO) = "Estado"
    .TextMatrix(0, COL_OBS) = "Observacion"
    .ColWidth(COL_MARCA) = 450
    .ColWidth(COL_HORA) = 1650
    .ColWidth(COL_TIPO) = 1900
    .ColWidth(COL_MESA) = 1700
    .ColWidth(COL_MESERO) = 2000
    .ColWidth(COL_ITEMS) = 700
    .ColWidth(COL_TOTAL) = 1400
    .ColWidth(COL_ESTADO) = 1700
    .ColWidth(COL_OBS) = 3900
    .ColWidth(COL_ID) = 0
    .ColWidth(COL_ESTADO_BD) = 0
    .ColAlignment(COL_MARCA) = flexAlignCenterCenter
    .ColAlignment(COL_ITEMS) = flexAlignCenterCenter
    .ColAlignment(COL_TOTAL) = flexAlignRightCenter
    .RowHeight(0) = 380
    .Redraw = True
End With
With grdDetalle
    .Redraw = False
    .Cols = 4
    .Rows = 2
    .FixedRows = 1
    .FixedCols = 0
    .SelectionMode = flexSelectionByRow
    .FocusRect = flexFocusNone
    .TextMatrix(0, 0) = "Cant."
    .TextMatrix(0, 1) = "Producto"
    .TextMatrix(0, 2) = "Novedad"
    .TextMatrix(0, 3) = "Valor"
    .ColWidth(0) = 800
    .ColWidth(1) = 4200
    .ColWidth(2) = 3500
    .ColWidth(3) = 1400
    .ColAlignment(0) = flexAlignCenterCenter
    .ColAlignment(3) = flexAlignRightCenter
    .RowHeight(0) = 380
    .Redraw = True
End With
End Sub

Private Sub Mostrar_Vista()
cmdPendientes.BackColor = IIf(Var_Vista = "P", COLOR_ACTIVO, COLOR_INACTIVO)
cmdProcesados.BackColor = IIf(Var_Vista = "R", COLOR_ACTIVO, COLOR_INACTIVO)
lblFecha.Visible = (Var_Vista = "R")
DTPicker1.Visible = (Var_Vista = "R")
chkTodos.Visible = (Var_Vista = "P")
cmdAceptar.Enabled = (Var_Vista = "P")
cmdRechazar.Enabled = (Var_Vista = "P")
Var_Marcados = ","
chkTodos.Value = vbUnchecked
Var_Id_Detalle = 0
Call Limpiar_Detalle
Call Cargar_Lotes
End Sub

' MSFlexGrid exige al menos una fila de datos bajo la fija: se deja una en blanco
Private Sub Vaciar_Grilla(Grilla As MSFlexGridLib.MSFlexGrid)
Dim C As Integer
Grilla.Rows = 2
For C = 0 To Grilla.Cols - 1
    Grilla.TextMatrix(1, C) = ""
Next C
End Sub

Private Sub Limpiar_Detalle()
Call Vaciar_Grilla(grdDetalle)
lblDetalle.Caption = "Detalle: haga clic en un pedido para ver sus productos"
End Sub

Private Sub Pintar_Fila(ByVal Fila As Long, ByVal Color As Long)
Dim C As Integer
With grdLotes
    .Row = Fila
    For C = 0 To .Cols - 1
        .Col = C
        .CellBackColor = Color
    Next C
End With
End Sub

Private Function Nombre_Tipo(ByVal Tipo As String) As String
Select Case Tipo
   Case "NUEVO": Nombre_Tipo = "Pedido nuevo"
   Case "AGREGAR": Nombre_Tipo = "Prod. agregados"
   Case "ELIMINAR": Nombre_Tipo = "ELIMINAR prod."
   Case "CANCELAR": Nombre_Tipo = "CANCELAR cuenta"
   Case Else: Nombre_Tipo = Tipo
End Select
End Function

Private Function Es_Marcable(ByVal Estado As String) As Boolean
Es_Marcable = (Estado = "PENDIENTE" Or Estado = "ERROR")
End Function

Private Sub Cargar_Lotes()
On Error GoTo Linea
Dim Rs As ADODB.Recordset
Dim Sql As String, Fila As Long, Estado As String, Obs As String, Desde As String
Dim Nuevos_Marcados As String, Cantidad As Long, Fila_Detalle As Long
If Var_Cargando Then Exit Sub
Var_Cargando = True
Sql = "SELECT id, nro_pedido, DATE_FORMAT(recibido_en,'%d/%m %h:%i %p') AS hora, tipo, mesa, motivo_solicitud," & _
      " COALESCE(NULLIF(mesero_nombre,''), mesero) AS mesero, items, total, estado, mensaje, motivo," & _
      " procesado_por, procesado_desde, pc, DATE_FORMAT(procesado_en,'%h:%i %p') AS hora_proc," & _
      " TIMESTAMPDIFF(SECOND, procesado_en, NOW()) AS espera FROM ag_pw_lote2"
If Var_Vista = "P" Then
   Sql = Sql & " WHERE estado IN ('PENDIENTE','ACEPTADO','ERROR') ORDER BY id"
Else
   Desde = Format(DTPicker1.Value, "yyyy-mm-dd")
   Sql = Sql & " WHERE estado IN ('APLICADO','RECHAZADO') AND procesado_en >= '" & Desde & "'" & _
         " AND procesado_en < DATE_ADD('" & Desde & "', INTERVAL 1 DAY) ORDER BY procesado_en DESC"
End If
Set Rs = New ADODB.Recordset
Rs.Open Sql, Base_Reportes_MySql, adOpenStatic, adLockReadOnly
Nuevos_Marcados = ","
With grdLotes
    .Redraw = False
    Call Vaciar_Grilla(grdLotes)
    Call Pintar_Fila(1, COLOR_BLANCO)
    Fila = 0
    Do While Not Rs.EOF
       Fila = Fila + 1
       If Fila > 1 Then .Rows = Fila + 1
       .RowHeight(Fila) = 360
       Estado = Texto(Rs!Estado)
       .TextMatrix(Fila, COL_ID) = Texto(Rs!id)
       .TextMatrix(Fila, COL_ESTADO_BD) = Estado
       .TextMatrix(Fila, COL_HORA) = Texto(Rs!hora)
       .TextMatrix(Fila, COL_TIPO) = Nombre_Tipo(Texto(Rs!tipo))
       .TextMatrix(Fila, COL_MESA) = Texto(Rs!mesa)
       .TextMatrix(Fila, COL_MESERO) = Texto(Rs!mesero)
       .TextMatrix(Fila, COL_ITEMS) = Texto(Rs!items)
       .TextMatrix(Fila, COL_TOTAL) = Pesos(Rs!total)
       Select Case Estado
          Case "PENDIENTE"
             .TextMatrix(Fila, COL_ESTADO) = "Pendiente"
             Obs = ""
             If Texto(Rs!motivo_solicitud) <> "" Then Obs = "Motivo del mesero: " & Texto(Rs!motivo_solicitud)
             Call Pintar_Fila(Fila, COLOR_PENDIENTE)
          Case "ACEPTADO"
             .TextMatrix(Fila, COL_ESTADO) = "Aceptado"
             If Val(Texto(Rs!espera)) > 60 Then
                Obs = "Esperando al Agente Local: verifique que este en ejecucion"
             Else
                Obs = "Pasando al escritorio..."
             End If
             Call Pintar_Fila(Fila, COLOR_ACEPTADO)
          Case "ERROR"
             .TextMatrix(Fila, COL_ESTADO) = "No se pudo pasar"
             Obs = Texto(Rs!mensaje)
             Call Pintar_Fila(Fila, COLOR_ERROR)
          Case "APLICADO"
             .TextMatrix(Fila, COL_ESTADO) = "Aceptado"
             Obs = "Por " & Texto(Rs!procesado_por) & " (" & IIf(Texto(Rs!procesado_desde) = "VB", "escritorio", "panel") & ") " & Texto(Rs!hora_proc)
             Call Pintar_Fila(Fila, COLOR_BLANCO)
          Case "RECHAZADO"
             .TextMatrix(Fila, COL_ESTADO) = "Rechazado"
             Obs = "Motivo: " & Texto(Rs!motivo) & " - Por " & Texto(Rs!procesado_por) & " " & Texto(Rs!hora_proc)
             Call Pintar_Fila(Fila, COLOR_ERROR)
          Case Else
             .TextMatrix(Fila, COL_ESTADO) = Estado
             Obs = ""
       End Select
       .TextMatrix(Fila, COL_OBS) = Obs
       If Var_Vista = "P" And Es_Marcable(Estado) And InStr(Var_Marcados, "," & Texto(Rs!id) & ",") > 0 Then
          .TextMatrix(Fila, COL_MARCA) = "X"
          Nuevos_Marcados = Nuevos_Marcados & Texto(Rs!id) & ","
       End If
       If Val(Texto(Rs!id)) = Var_Id_Detalle Then Fila_Detalle = Fila
       Cantidad = Cantidad + 1
       Rs.MoveNext
    Loop
    If Fila_Detalle > 0 Then
       .Row = Fila_Detalle
       .Col = 0
       .ColSel = .Cols - 1
    End If
    .Redraw = True
End With
Rs.Close
Set Rs = Nothing
Var_Marcados = Nuevos_Marcados
If Var_Vista = "P" Then
   lblInfo.Caption = Cantidad & " pedido(s) por atender. Marque con clic en la columna X y pulse Aceptar o Rechazar." & _
                     " Lo aceptado pasa al escritorio y se imprime en unos segundos."
Else
   lblInfo.Caption = Cantidad & " pedido(s) procesado(s) el " & Format(DTPicker1.Value, "dd/mm/yyyy") & "."
End If
If Var_Id_Detalle > 0 And Fila_Detalle = 0 Then
   Var_Id_Detalle = 0
   Call Limpiar_Detalle
End If
Var_Cargando = False
Exit Sub
Linea:
Var_Cargando = False
grdLotes.Redraw = True
lblInfo.Caption = "No se pudieron cargar los pedidos web: " & Err.Description
End Sub

Private Sub Cargar_Detalle(ByVal Id_Lote As Long)
On Error GoTo Linea
Dim Rs As ADODB.Recordset, Fila As Long
Var_Id_Detalle = Id_Lote
Set Rs = New ADODB.Recordset
Rs.Open "SELECT nro_pedido, enviado_por FROM ag_pw_lote2 WHERE id = " & Id_Lote, Base_Reportes_MySql, adOpenStatic, adLockReadOnly
If Rs.EOF Then
   Rs.Close
   Call Limpiar_Detalle
   Exit Sub
End If
lblDetalle.Caption = "Pedido " & Texto(Rs!nro_pedido) & "  -  enviado por " & IIf(Texto(Rs!enviado_por) = "", "-", Texto(Rs!enviado_por))
Rs.Close
Rs.Open "SELECT cantidad, COALESCE(NULLIF(producto_personalizado,''), descripcion, CONCAT('Producto ', id_plato)) AS nombre," & _
        " novedad, valor FROM ag_pw_item WHERE lote_id = " & Id_Lote & " ORDER BY item", Base_Reportes_MySql, adOpenStatic, adLockReadOnly
With grdDetalle
    .Redraw = False
    Call Vaciar_Grilla(grdDetalle)
    Fila = 0
    Do While Not Rs.EOF
       Fila = Fila + 1
       If Fila > 1 Then .Rows = Fila + 1
       .RowHeight(Fila) = 340
       .TextMatrix(Fila, 0) = Format(CDbl(Rs!Cantidad), "0.###")
       .TextMatrix(Fila, 1) = Texto(Rs!nombre)
       .TextMatrix(Fila, 2) = Texto(Rs!novedad)
       .TextMatrix(Fila, 3) = Pesos(Rs!valor)
       Rs.MoveNext
    Loop
    .Redraw = True
End With
Rs.Close
Set Rs = Nothing
Exit Sub
Linea:
grdDetalle.Redraw = True
MsgBox "Cargar_Detalle " & Err.Description
End Sub

Private Sub Alternar_Marca(ByVal Fila As Long)
Dim Id As String
Id = grdLotes.TextMatrix(Fila, COL_ID)
If Not Es_Marcable(grdLotes.TextMatrix(Fila, COL_ESTADO_BD)) Then Exit Sub
If InStr(Var_Marcados, "," & Id & ",") > 0 Then
   Var_Marcados = Replace(Var_Marcados, "," & Id & ",", ",")
   grdLotes.TextMatrix(Fila, COL_MARCA) = ""
Else
   Var_Marcados = Var_Marcados & Id & ","
   grdLotes.TextMatrix(Fila, COL_MARCA) = "X"
End If
End Sub

Private Function Contar_Marcados() As Long
Dim Partes() As String, i As Long
If Len(Var_Marcados) <= 1 Then Exit Function
Partes = Split(Mid(Var_Marcados, 2, Len(Var_Marcados) - 2), ",")
For i = 0 To UBound(Partes)
    If Val(Partes(i)) > 0 Then Contar_Marcados = Contar_Marcados + 1
Next i
End Function

Private Function Procesar_Marcados(ByVal Estado As String, ByVal Motivo As String) As Long
On Error GoTo Linea
Dim Partes() As String, i As Long, Afectadas As Long
Dim Cmd As ADODB.Command
If Len(Var_Marcados) <= 1 Then Exit Function
Partes = Split(Mid(Var_Marcados, 2, Len(Var_Marcados) - 2), ",")
For i = 0 To UBound(Partes)
    If Val(Partes(i)) > 0 Then
       Set Cmd = New ADODB.Command
       Set Cmd.ActiveConnection = Base_Reportes_MySql
       Cmd.CommandType = adCmdText
       Cmd.CommandText = "UPDATE ag_pw_lote2 SET estado = ?, procesado_por = ?, procesado_desde = 'VB', pc = ?," & _
                         " procesado_en = NOW(), motivo = ?, mensaje = NULL" & _
                         " WHERE id = ? AND estado IN ('PENDIENTE','ERROR')"
       Cmd.Parameters.Append Cmd.CreateParameter("estado", adVarChar, adParamInput, 12, Estado)
       Cmd.Parameters.Append Cmd.CreateParameter("por", adVarChar, adParamInput, 150, Nombre_Usuario())
       Cmd.Parameters.Append Cmd.CreateParameter("pc", adVarChar, adParamInput, 100, Left(Environ("COMPUTERNAME") & "", 100))
       If Motivo = "" Then
          Cmd.Parameters.Append Cmd.CreateParameter("motivo", adVarChar, adParamInput, 255, Null)
       Else
          Cmd.Parameters.Append Cmd.CreateParameter("motivo", adVarChar, adParamInput, 255, Left(Motivo, 255))
       End If
       Cmd.Parameters.Append Cmd.CreateParameter("id", adInteger, adParamInput, , CLng(Partes(i)))
       Afectadas = 0
       Cmd.Execute Afectadas, , adExecuteNoRecords
       Procesar_Marcados = Procesar_Marcados + Afectadas
       Set Cmd = Nothing
    End If
Next i
Exit Function
Linea:
MsgBox "No se pudo procesar el pedido web: " & Err.Description, vbCritical
End Function

Private Sub cmdPendientes_Click()
Var_Vista = "P"
Call Mostrar_Vista
End Sub

Private Sub cmdProcesados_Click()
Var_Vista = "R"
Call Mostrar_Vista
End Sub

Private Sub cmdActualizar_Click()
Call Cargar_Lotes
If Var_Id_Detalle > 0 Then Call Cargar_Detalle(Var_Id_Detalle)
End Sub

Private Sub cmdCerrar_Click()
Unload Me
End Sub

Private Sub DTPicker1_Change()
Var_Id_Detalle = 0
Call Limpiar_Detalle
Call Cargar_Lotes
End Sub

Private Sub chkTodos_Click()
Dim Fila As Long
If Var_Cargando Then Exit Sub
Var_Marcados = ","
For Fila = 1 To grdLotes.Rows - 1
    If chkTodos.Value = vbChecked And Es_Marcable(grdLotes.TextMatrix(Fila, COL_ESTADO_BD)) Then
       Var_Marcados = Var_Marcados & grdLotes.TextMatrix(Fila, COL_ID) & ","
       grdLotes.TextMatrix(Fila, COL_MARCA) = "X"
    Else
       grdLotes.TextMatrix(Fila, COL_MARCA) = ""
    End If
Next Fila
End Sub

Private Sub grdLotes_Click()
Dim Fila As Long
Fila = grdLotes.MouseRow
If Fila < 1 Or Fila >= grdLotes.Rows Then Exit Sub
If grdLotes.TextMatrix(Fila, COL_ID) = "" Then Exit Sub
If Var_Vista = "P" And grdLotes.MouseCol = COL_MARCA Then Call Alternar_Marca(Fila)
Call Cargar_Detalle(CLng(Val(grdLotes.TextMatrix(Fila, COL_ID))))
End Sub

Private Sub grdLotes_DblClick()
Dim Fila As Long
Fila = grdLotes.MouseRow
If Fila < 1 Or Fila >= grdLotes.Rows Then Exit Sub
If grdLotes.TextMatrix(Fila, COL_ID) = "" Then Exit Sub
If Var_Vista = "P" And grdLotes.MouseCol <> COL_MARCA Then Call Alternar_Marca(Fila)
End Sub

Private Sub cmdAceptar_Click()
Dim N As Long, Hechos As Long
N = Contar_Marcados()
If N = 0 Then
   MsgBox "Marque los pedidos a aceptar (clic en la columna X).", vbInformation
   Exit Sub
End If
If MsgBox("¿Aceptar " & N & " pedido(s) web?" & vbCrLf & "Pasan al escritorio y se envian a impresion.", vbQuestion + vbYesNo) = vbNo Then Exit Sub
Hechos = Procesar_Marcados("ACEPTADO", "")
If Hechos < N Then MsgBox (N - Hechos) & " pedido(s) ya habian sido procesados por otra persona.", vbInformation
Var_Marcados = ","
chkTodos.Value = vbUnchecked
Call Cargar_Lotes
End Sub

Private Sub cmdRechazar_Click()
Dim N As Long, Hechos As Long, Motivo As String
N = Contar_Marcados()
If N = 0 Then
   MsgBox "Marque los pedidos a rechazar (clic en la columna X).", vbInformation
   Exit Sub
End If
Motivo = InputBox("Motivo del rechazo (obligatorio)." & vbCrLf & "Los productos salen del pedido en la web y solo quedan en el historico.", "Rechazar " & N & " pedido(s) web")
Motivo = Trim(Replace(Replace(Motivo, vbCr, " "), vbLf, " "))
If Len(Motivo) < 3 Then
   MsgBox "Debe digitar el motivo del rechazo.", vbExclamation
   Exit Sub
End If
Hechos = Procesar_Marcados("RECHAZADO", Motivo)
If Hechos < N Then MsgBox (N - Hechos) & " pedido(s) ya habian sido procesados por otra persona.", vbInformation
Var_Marcados = ","
chkTodos.Value = vbUnchecked
Call Cargar_Lotes
End Sub

Private Sub Timer1_Timer()
If Var_Vista = "P" Then Call Cargar_Lotes
End Sub
