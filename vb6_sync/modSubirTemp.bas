Attribute VB_Name = "modSubirTemp"
Option Explicit

' ============================================================
' modSubirTemp.bas
' Orquestador de subida LOCAL -> WEB — pedidos activos datatemppos
' Integra datatemppos_sync.sync_control:
'   - Mutex (en_proceso): evita ciclos solapados si el timer es rapido
'   - Timestamp (ultimo_push): visibilidad del ultimo ciclo exitoso
'
' USO: En el timer del exe de sincronizacion, reemplazar las llamadas
' individuales a SubirTemp* por una sola llamada a SubirTodo().
'
' FASE 1 (actual) : LOCAL -> WEB  (pedidos desktop suben al servidor)
' FASE 2 (futura) : WEB -> LOCAL  (pedidos web bajan al desktop)
'   La Fase 2 usa modSyncDownload.bas + sync_control.ultimo_pull
' ============================================================


' ── Conexion privada a datatemppos_sync ──────────────────────
' Funcion privada para no colisionar con GetConnSync()
' de modSyncDownload.bas si ambos modulos estan en el mismo proyecto.
Private Function GetConnSubirSync() As Object
    On Error GoTo ErrConn
    Dim conn As Object
    Set conn = CreateObject("ADODB.Connection")
    conn.Open "Driver={MySQL ODBC 8.0 Driver};" & _
              "Server=127.0.0.1;Port=3308;" & _
              "Database=datatemppos_sync;" & _
              "User=root;Password=123456;Option=3;"
    Set GetConnSubirSync = conn
    Exit Function
ErrConn:
    Set GetConnSubirSync = Nothing
End Function


' ── Mutex: evita solapamiento de ciclos de subida ────────────
Private Function SubirEnProceso() As Boolean
    On Error GoTo ErrFn
    Dim conn As Object
    Set conn = GetConnSubirSync()
    If conn Is Nothing Then SubirEnProceso = False: Exit Function
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT en_proceso FROM sync_control WHERE id=1", conn
    SubirEnProceso = False
    If Not rs.EOF Then
        If CInt(Nz(rs("en_proceso"), 0)) = 1 Then SubirEnProceso = True
    End If
    rs.Close: conn.Close
    Exit Function
ErrFn:
    SubirEnProceso = False
End Function

Private Sub SubirMarcarInicio()
    On Error Resume Next
    Dim conn As Object
    Set conn = GetConnSubirSync()
    If conn Is Nothing Then Exit Sub
    conn.Execute "UPDATE sync_control SET en_proceso=1 WHERE id=1"
    conn.Close
End Sub

Private Sub SubirMarcarFin()
    On Error Resume Next
    Dim conn As Object
    Set conn = GetConnSubirSync()
    If conn Is Nothing Then Exit Sub
    conn.Execute "UPDATE sync_control SET en_proceso=0 WHERE id=1"
    conn.Close
End Sub


' ── Timestamp del ultimo ciclo exitoso ───────────────────────
Private Sub ActualizarUltimoPush()
    On Error Resume Next
    Dim conn As Object
    Set conn = GetConnSubirSync()
    If conn Is Nothing Then Exit Sub
    conn.Execute "UPDATE sync_control SET ultimo_push=NOW() WHERE id=1"
    conn.Close
End Sub

Public Function ObtenerUltimoPush() As String
    On Error GoTo ErrFn
    Dim conn As Object
    Set conn = GetConnSubirSync()
    If conn Is Nothing Then ObtenerUltimoPush = "sin datos": Exit Function
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT ultimo_push FROM sync_control WHERE id=1", conn
    ObtenerUltimoPush = "sin datos"
    If Not rs.EOF Then
        If Not IsNull(rs("ultimo_push")) Then
            ObtenerUltimoPush = Format(rs("ultimo_push"), "YYYY-MM-DD HH:MM:SS")
        End If
    End If
    rs.Close: conn.Close
    Exit Function
ErrFn:
    ObtenerUltimoPush = "error sync_control"
End Function


' ════════════════════════════════════════════════════════════
' SubirTodo — llamar desde el timer del exe (cada N segundos)
'
' Parametros:
'   Var_Id_Company_Envio  — ID de la sede/empresa (ej: 1)
'   Var_Limit_Registros   — maximo de filas por lote (ej: 500)
'
' Reemplaza en el timer:
'   SubirTempComandas              Var_Id_Company, Var_Limit
'   SubirTempDetalleComanda        Var_Id_Company, Var_Limit
'   SubirTempPlatosProductoParcial Var_Id_Company, Var_Limit
'   SubirTempNovedadesPlatoPedido  Var_Id_Company, Var_Limit
'   SubirTempMesaAbierta           Var_Id_Company, Var_Limit
'
' Por una sola llamada:
'   SubirTodo Var_Id_Company, Var_Limit
' ════════════════════════════════════════════════════════════
Public Sub SubirTodo(Var_Id_Company_Envio As Integer, Var_Limit_Registros As Variant)
    ' 1. Mutex: si el ciclo anterior aun corre, salir y esperar proximo tick
    If SubirEnProceso() Then
        Var_Caption_Error = "Subida en proceso, esperando..."
        Exit Sub
    End If

    SubirMarcarInicio

    On Error GoTo ErrCiclo

    ' 2. Subir las 5 tablas en orden de dependencia
    SubirTempComandas              Var_Id_Company_Envio, Var_Limit_Registros
    SubirTempDetalleComanda        Var_Id_Company_Envio, Var_Limit_Registros
    SubirTempPlatosProductoParcial Var_Id_Company_Envio, Var_Limit_Registros
    SubirTempNovedadesPlatoPedido  Var_Id_Company_Envio, Var_Limit_Registros
    SubirTempMesaAbierta           Var_Id_Company_Envio, Var_Limit_Registros

    ' 3. Registrar timestamp del push exitoso en sync_control
    ActualizarUltimoPush
    SubirMarcarFin
    Exit Sub

ErrCiclo:
    Var_Caption_Error = "SubirTodo ERROR: " & Err.Description
    SubirMarcarFin
End Sub
