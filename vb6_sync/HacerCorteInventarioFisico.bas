Attribute VB_Name = "HacerCorteInventarioFisico"
' ============================================================
' HacerCorteInventarioFisico
' Verifica si han pasado mas de 90 dias desde el ultimo inventario fisico.
' Si es asi, ofrece hacer un corte automatico:
'   1. Recalcula stock con RecalcularStock (ModRecalcularStock)
'   2. INSERT en inventarios_fisicos_manuales con los valores de inventario_actual_porciones
'   3. Marca Enviada_MySql=0 para que SincronizarInventariosFisicos los suba al servidor
' Llamar desde el modulo de inicio o desde el menu de inventario.
' ============================================================
Public Sub HacerCorteInventarioFisico(Var_Id_Company_Envio As Integer)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = Base_Principal_Local_MySql

    ' -- 1. Verificar fecha del ultimo inventario fisico ------
    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT MAX(Fecha) AS ultima FROM inventarios_fisicos_manuales", conn

    Dim diasDesde As Long
    If rs.EOF Or IsNull(rs("ultima")) Or rs("ultima") = "" Then
        diasDesde = 9999
    Else
        diasDesde = DateDiff("d", CDate(rs("ultima")), Date)
    End If
    rs.Close

    If diasDesde <= 90 Then Exit Sub

    ' -- 2. Confirmar con el usuario --------------------------
    Dim msg As String
    If diasDesde >= 9999 Then
        msg = "No se ha registrado ningun inventario fisico." & vbCrLf & vbCrLf
    Else
        msg = "Han pasado " & diasDesde & " dias desde el ultimo inventario fisico." & vbCrLf & vbCrLf
    End If
    msg = msg & "Se recomienda hacer un CORTE AUTOMATICO de inventario." & vbCrLf & vbCrLf
    msg = msg & "Este proceso:" & vbCrLf
    msg = msg & "  1. Recalcula el stock actual de todos los insumos" & vbCrLf
    msg = msg & "  2. Registra esos valores como inventario fisico de hoy" & vbCrLf
    msg = msg & "  3. Los proximos recalculos partiran desde esta nueva fecha" & vbCrLf & vbCrLf
    msg = msg & "Si no lo hace, el recalculo de stock tardara mas tiempo." & vbCrLf & vbCrLf
    msg = msg & "Desea hacer el corte de inventario ahora?"

    If MsgBox(msg, vbYesNo + vbQuestion, "Corte de inventario fisico automatico") = vbNo Then
        Exit Sub
    End If

    ' -- 3. Recalcular stock (actualiza inventario_actual_porciones) --
    Var_Caption_Error = "Recalculando stock..."
    DoEvents
    Call RecalcularStock(conn, 0)   ' 0 = todos los items

    ' -- 4. Obtener proximo Id_Fisico -------------------------
    rs.Open "SELECT COALESCE(MAX(Id_Fisico), 0) + 1 AS prox FROM inventarios_fisicos_manuales", conn
    Dim lIdFisico As Long
    lIdFisico = CLng(Nz(rs("prox"), 1))
    rs.Close

    ' -- 5. INSERT masivo en inventarios_fisicos_manuales -----
    Var_Caption_Error = "Guardando inventario fisico..."
    DoEvents
    Dim sFecha As String
    sFecha = Format(Date, "yyyy-mm-dd")

    conn.Execute "INSERT INTO inventarios_fisicos_manuales " & _
                 "(Id_Fisico, Id_Item, Fecha, Cantidad, Observacion, Autorizada, " & _
                 " Cod_Usuario, Enviada_MySql) " & _
                 "SELECT " & lIdFisico & ", Id_Item, '" & sFecha & "', " & _
                 "Cantidad_Actual, 'Corte automatico del sistema', 1, " & _
                 "'SISTEMA', 0 " & _
                 "FROM inventario_actual_porciones"

    ' -- 6. INSERT snapshot completo en historico_inventario_actual_porciones --
    Var_Caption_Error = "Guardando historico de inventario..."
    DoEvents

    ' Obtener proximo Id_Historico
    rs.Open "SELECT COALESCE(MAX(Id_Historico), 0) + 1 AS prox FROM historico_inventario_actual_porciones", conn
    Dim lIdHistorico As Long
    lIdHistorico = CLng(Nz(rs("prox"), 1))
    rs.Close

    conn.Execute "INSERT INTO historico_inventario_actual_porciones " & _
                 "(Id_Historico, Fecha, Id_Grupo, Id_Item, Codigo_Insumo, Descripcion, " & _
                 " Costo, Und_Compra, Valor_Und_Compra, Und_Min_Utilizadas, Posicion, " & _
                 " Agrupar, Compras, Controlar, Opcion_Cambios, Und_Uso, Centro_Produccion, " & _
                 " Cantidad_Actual, Cod_empleado, Insumo_Cp, Fecha_Vence, Stock_MInimo, Enviada_MySql) " & _
                 "SELECT " & lIdHistorico & ", '" & sFecha & "', Id_Grupo, Id_Item, " & _
                 "Codigo_Insumo, Descripcion, Costo, Und_Compra, Valor_Und_Compra, " & _
                 "Und_Min_Utilizadas, 0, Agrupar, Compras, Controlar, Opcion_Cambios, " & _
                 "Und_Uso, Centro_Produccion, Cantidad_Actual, 'SISTEMA', " & _
                 "Insumo_Cp, Fecha_Vence, Stock_MInimo, 0 " & _
                 "FROM inventario_actual_porciones"

    ' -- 7. Los registros con Enviada_MySql=0 se sincronizan en el proximo ciclo --
    ' SincronizarInventariosFisicos  → sube inventarios_fisicos_manuales
    ' SincronizarHistoricoInventario → sube historico_inventario_actual_porciones

    Var_Caption_Error = "Corte de inventario completado. Id fisico: " & lIdFisico
    MsgBox "Corte de inventario completado." & vbCrLf & vbCrLf & _
           "Se registraron los stocks actuales como inventario fisico del " & sFecha & "." & vbCrLf & _
           "En la proxima sincronizacion estos datos se enviaran al servidor.", _
           vbInformation, "Corte completado"

    Exit Sub

ErrHandler:
    Var_Caption_Error = "HacerCorteInventarioFisico: " & Err.Description
    On Error Resume Next
    If Not rs Is Nothing Then If rs.State = 1 Then rs.Close
End Sub
