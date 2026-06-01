Attribute VB_Name = "modSyncDownload"
Option Explicit

' ============================================================
' modSyncDownload.bas
' Módulo maestro de descarga web → desktop
' Llamar DescargarTodo() desde el timer del exe SyncDownloader
' Orden: Comandas → Detalle → Armado → Mesas → Tirillas
' ============================================================

' ── Configuración — misma que modSyncAll ─────────────────────
' API_BASE, API_KEY, COMPANY_ID se toman de modSyncAll.bas
' Si este módulo corre en un exe separado, redeclarar aquí:
'
' Public Const API_BASE   As String = "https://easyposweb.com/api/pos"
' Public Const API_KEY    As String = "easypos-sync-key-2024"
' Public Const COMPANY_ID As Long   = 3
' Public Const BATCH_SIZE As Integer = 50

' ── Intervalo en segundos entre cada ciclo completo ──────────
Public Const DOWNLOAD_INTERVAL As Integer = 10


' ════════════════════════════════════════════════════════════
' FUNCIÓN PRINCIPAL — llamar desde el timer (cada 10s)
' ════════════════════════════════════════════════════════════
Public Sub DescargarTodo(lblEstado As Label)
    ' Verificar conectividad antes de intentar (timeout 5s)
    If Not ServidorDisponible() Then
        lblEstado.Caption = "Sin conexion al servidor - " & Now()
        Exit Sub
    End If

    ' Evitar ejecución paralela si el ciclo anterior aún no terminó
    If SyncEnProceso() Then Exit Sub
    MarcarSyncInicio()

    On Error GoTo ErrCiclo

    ' 1. Comandas (encabezados de pedidos web)
    DescargarComandas lblEstado

    ' 2. Detalle + copia en parcial
    DescargarDetalleComanda lblEstado

    ' 3. Selecciones de armado (modificadores)
    DescargarPlatosProductoParcial lblEstado

    ' 4. Estado de mesas (abierta/libre)
    DescargarMesaAbierta lblEstado

    ' 5. Generar tirillas para impresión (derivado del detalle local)
    DescargarTirilla lblEstado

    ' 6. Actualizar timestamp del pull exitoso
    ActualizarUltimoPull()

    MarcarSyncFin()
    Exit Sub

ErrCiclo:
    Var_Caption_Error = "DescargarTodo: " & Err.Description
    MarcarSyncFin()
End Sub


' ════════════════════════════════════════════════════════════
' HELPERS DE CONTROL
' ════════════════════════════════════════════════════════════

' Lee el ultimo_pull de datatemppos_sync.sync_control
Public Function ObtenerUltimoPull() As String
    On Error GoTo ErrFn
    Dim conn As Object
    Set conn = GetConnSync()
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT ultimo_pull FROM sync_control WHERE id=1", conn
    Dim resultado As String
    resultado = "2024-01-01 00:00:00"
    If Not rs.EOF Then
        If Not IsNull(rs("ultimo_pull")) Then
            resultado = Format(rs("ultimo_pull"), "YYYY-MM-DD HH:MM:SS")
        End If
    End If
    rs.Close: conn.Close
    ObtenerUltimoPull = resultado
    Exit Function
ErrFn:
    ObtenerUltimoPull = "2024-01-01 00:00:00"
End Function

' Actualiza ultimo_pull con la hora actual
Public Sub ActualizarUltimoPull()
    On Error Resume Next
    Dim conn As Object
    Set conn = GetConnSync()
    conn.Execute "UPDATE sync_control SET ultimo_pull=NOW() WHERE id=1"
    conn.Close
End Sub

' Devuelve True si hay un ciclo de sync en proceso (evita solapamiento)
Public Function SyncEnProceso() As Boolean
    On Error GoTo ErrFn
    Dim conn As Object
    Set conn = GetConnSync()
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT en_proceso FROM sync_control WHERE id=1", conn
    Dim resultado As Boolean
    resultado = False
    If Not rs.EOF Then resultado = CBool(Nz(rs("en_proceso"), 0))
    rs.Close: conn.Close
    SyncEnProceso = resultado
    Exit Function
ErrFn:
    SyncEnProceso = False
End Function

Public Sub MarcarSyncInicio()
    On Error Resume Next
    Dim conn As Object
    Set conn = GetConnSync()
    conn.Execute "UPDATE sync_control SET en_proceso=1 WHERE id=1"
    conn.Close
End Sub

Public Sub MarcarSyncFin()
    On Error Resume Next
    Dim conn As Object
    Set conn = GetConnSync()
    conn.Execute "UPDATE sync_control SET en_proceso=0 WHERE id=1"
    conn.Close
End Sub

' Ping al servidor con timeout de 5s
Public Function ServidorDisponible() As Boolean
    On Error GoTo SinConexion
    Dim http As Object
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.Open "GET", API_BASE & "/sync/health", False
    http.SetRequestHeader "X-Api-Key", API_KEY
    http.setTimeouts 3000, 3000, 5000, 5000
    http.Send
    ServidorDisponible = (http.Status = 200)
    Exit Function
SinConexion:
    ServidorDisponible = False
End Function

' Codifica timestamp para query string
Public Function URLEncode(ByVal s As String) As String
    URLEncode = Replace(s, " ", "+")
    URLEncode = Replace(URLEncode, ":", "%3A")
End Function

' Escapa comillas simples para SQL
Public Function EscSql(ByVal s As String) As String
    EscSql = Replace(s, "'", "''")
End Function

' Conexión a datatemppos local
Public Function GetConnDatatemppos() As Object
    Dim conn As Object
    Set conn = CreateObject("ADODB.Connection")
    conn.Open "Driver={MySQL ODBC 8.0 Driver};" & _
              "Server=127.0.0.1;Port=3308;" & _
              "Database=datatemppos;" & _
              "User=root;Password=123456;Option=3;"
    Set GetConnDatatemppos = conn
End Function

' Conexión a datatemppos_sync local
Public Function GetConnSync() As Object
    Dim conn As Object
    Set conn = CreateObject("ADODB.Connection")
    conn.Open "Driver={MySQL ODBC 8.0 Driver};" & _
              "Server=127.0.0.1;Port=3308;" & _
              "Database=datatemppos_sync;" & _
              "User=root;Password=123456;Option=3;"
    Set GetConnSync = conn
End Function
