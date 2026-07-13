' ============================================================
' ModRecalcularStock
' Gestiona el stock de inventario_actual_porciones en tres modos:
'
'   1. RecalcularStock(conn, lCategoria)
'      Reconciliacion completa desde cero usando toda la historia.
'      Usar periodicamente o al detectar desajustes.
'      lCategoria = 0 -> todos | lCategoria <> 0 -> esa categoria (Agrupar)
'
'   2. DescontarStockFactura(conn, sNroFactura, sFecha)
'      Delta inmediato al cerrar una factura. Resta solo los items
'      de esa factura. Mas liviano que recalcular todo.
'
'   3. DescontarStockRecibo(conn, sNroRecibo, sFecha)
'      Delta inmediato al cerrar un recibo. Misma logica que facturas
'      pero sobre las tablas de recibos.
'
' Formula completa (usada en RecalcularStock):
'   Cantidad_Actual = ultimo_inventario_fisico
'                   + entradas desde esa fecha
'                   - salidas desde esa fecha
'                   - ventas en recibos no anulados
'                   - ventas en facturas no anuladas
'
' Nota: en recibos el numero de documento se guarda en Nro_Factura
'       (misma estructura de columnas que facturas, solo cambia la tabla).
'
' Requiere: MySQL 8+ / MariaDB 10.2+ (usa WITH ... CTE)
' ============================================================

' ── CTE completo para reconciliacion total ───────────────────────────────────
Private Function BuildCTE_VB6() As String
    Dim s As String
    s = "WITH ranked_phys AS ( "
    s = s & "SELECT Id_Item, Cantidad, Fecha, "
    s = s & "ROW_NUMBER() OVER (PARTITION BY Id_Item ORDER BY Fecha DESC) AS rn "
    s = s & "FROM inventarios_fisicos_manuales "
    s = s & "), "
    s = s & "last_phys AS ( "
    s = s & "SELECT Id_Item, Cantidad, Fecha FROM ranked_phys WHERE rn = 1 "
    s = s & "), "
    s = s & "entries_adj AS ( "
    s = s & "SELECT ie.Id_Item, SUM(ie.Cantidad) AS total "
    s = s & "FROM inventarios_entradas_manuales ie "
    s = s & "LEFT JOIN last_phys lp ON lp.Id_Item = ie.Id_Item "
    s = s & "WHERE (lp.Fecha IS NULL OR ie.Fecha >= lp.Fecha) "
    s = s & "GROUP BY ie.Id_Item "
    s = s & "), "
    s = s & "exits_adj AS ( "
    s = s & "SELECT ix.Id_Item, SUM(ix.Cantidad) AS total "
    s = s & "FROM inventarios_salidas_manuales ix "
    s = s & "LEFT JOIN last_phys lp ON lp.Id_Item = ix.Id_Item "
    s = s & "WHERE (lp.Fecha IS NULL OR ix.Fecha >= lp.Fecha) "
    s = s & "GROUP BY ix.Id_Item "
    s = s & "), "
    s = s & "receipt_sales AS ( "
    s = s & "SELECT prd.Id_Item, SUM(rod.Cantidad * prd.Cantidad) AS total "
    s = s & "FROM recibos_detalle_comanda_producto prd "
    s = s & "INNER JOIN recibos_detalle_comanda rod "
    s = s & "ON rod.Nro_Pedido   = prd.Nro_Pedido "
    s = s & "AND rod.Nro_Factura = prd.Nro_Factura "
    s = s & "AND rod.Fecha       = prd.Fecha "
    s = s & "AND rod.Id_Plato    = prd.Id_Plato "
    s = s & "AND rod.Item        = prd.Item "
    s = s & "INNER JOIN recibos pr "
    s = s & "ON pr.Nro_Factura = rod.Nro_Factura "
    s = s & "AND pr.Fecha      = rod.Fecha "
    s = s & "AND (pr.Anulada IS NULL OR pr.Anulada = 0) "
    s = s & "LEFT JOIN last_phys lp ON lp.Id_Item = prd.Id_Item "
    s = s & "WHERE (lp.Fecha IS NULL OR prd.Fecha >= lp.Fecha) "
    s = s & "GROUP BY prd.Id_Item "
    s = s & "), "
    s = s & "invoice_sales AS ( "
    s = s & "SELECT pod.Id_Item, SUM(od.Cantidad * pod.Cantidad) AS total "
    s = s & "FROM detalle_comanda_producto pod "
    s = s & "INNER JOIN detalle_comanda od "
    s = s & "ON od.Nro_Pedido   = pod.Nro_Pedido "
    s = s & "AND od.Nro_Factura = pod.Nro_Factura "
    s = s & "AND od.Fecha       = pod.Fecha "
    s = s & "AND od.Id_Plato    = pod.Id_Plato "
    s = s & "AND od.Item        = pod.Item "
    s = s & "INNER JOIN facturas pi "
    s = s & "ON pi.Nro_Factura = od.Nro_Factura "
    s = s & "AND pi.Fecha      = od.Fecha "
    s = s & "AND (pi.Anulada IS NULL OR pi.Anulada = 0) "
    s = s & "LEFT JOIN last_phys lp ON lp.Id_Item = pod.Id_Item "
    s = s & "WHERE (lp.Fecha IS NULL OR pod.Fecha >= lp.Fecha) "
    s = s & "GROUP BY pod.Id_Item "
    s = s & ") "
    BuildCTE_VB6 = s
End Function

' ── Insertar en inventario_actual_porciones los items que falten ──────────────
Private Sub InsertarFaltantes(ByVal conn As Object, ByVal sWhere As String)
    Dim s As String
    s = "INSERT INTO inventario_actual_porciones "
    s = s & "(Id_Grupo, Id_Item, Codigo_Insumo, Descripcion, Costo, "
    s = s & "Und_Compra, Valor_Und_Compra, Und_Min_Utilizadas, Posicion, Agrupar, "
    s = s & "Compras, Controlar, Opcion_Cambios, Und_Uso, Centro_Produccion, "
    s = s & "Cantidad_Actual, Bodega, Insumo_Cp, Fecha_Vence, Stock_MInimo) "
    s = s & "SELECT ip.Id_Grupo, ip.Id_Item, ip.Codigo_Insumo, ip.Descripcion, ip.Costo, "
    s = s & "ip.Und_Compra, ip.Valor_Und_Compra, ip.Und_Min_Utilizadas, ip.Posicion, ip.Agrupar, "
    s = s & "ip.Compras, ip.Controlar, ip.Opcion_Cambios, ip.Und_Uso, ip.Centro_Produccion, "
    s = s & "0, ip.Bodega, ip.Insumo_Cp, ip.Fecha_Vence, ip.Stock_MInimo "
    s = s & "FROM inventario_porciones ip "
    s = s & "LEFT JOIN inventario_actual_porciones iap ON iap.Id_Item = ip.Id_Item "
    s = s & "WHERE iap.Id_Item IS NULL"
    If sWhere <> "" Then s = s & " AND " & sWhere
    conn.Execute s
End Sub

' ── Calcular y actualizar Cantidad_Actual (reconciliacion completa) ───────────
Private Sub EjecutarRecalculo_VB6(ByVal conn As Object, ByVal sWhere As String)
    On Error GoTo ErrHandler

    Dim sSQL As String
    sSQL = BuildCTE_VB6()
    sSQL = sSQL & "SELECT ip.Id_Item, "
    sSQL = sSQL & "COALESCE(lp.Cantidad,0) + COALESCE(ea.total,0) - COALESCE(xa.total,0) "
    sSQL = sSQL & "- COALESCE(rs.total,0) - COALESCE(inv.total,0) AS nueva_cantidad "
    sSQL = sSQL & "FROM inventario_porciones ip "
    sSQL = sSQL & "LEFT JOIN last_phys lp      ON lp.Id_Item  = ip.Id_Item "
    sSQL = sSQL & "LEFT JOIN entries_adj ea    ON ea.Id_Item   = ip.Id_Item "
    sSQL = sSQL & "LEFT JOIN exits_adj xa      ON xa.Id_Item   = ip.Id_Item "
    sSQL = sSQL & "LEFT JOIN receipt_sales rs  ON rs.Id_Item   = ip.Id_Item "
    sSQL = sSQL & "LEFT JOIN invoice_sales inv ON inv.Id_Item  = ip.Id_Item "
    sSQL = sSQL & "WHERE 1=1"
    If sWhere <> "" Then sSQL = sSQL & " AND " & sWhere

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open sSQL, conn, 0, 1

    If rs.EOF Then
        rs.Close: Set rs = Nothing
        MsgBox "No se encontraron insumos para recalcular.", vbInformation
        Exit Sub
    End If

    Dim lCount As Long
    lCount = 0
    conn.BeginTrans
    Do While Not rs.EOF
        Dim sUpd As String
        sUpd = "UPDATE inventario_actual_porciones "
        sUpd = sUpd & "SET Cantidad_Actual = " & CDbl(rs("nueva_cantidad")) & ", "
        sUpd = sUpd & "Enviada_MySql = 0 "
        sUpd = sUpd & "WHERE Id_Item = " & CLng(rs("Id_Item"))
        conn.Execute sUpd
        lCount = lCount + 1
        rs.MoveNext
    Loop
    conn.CommitTrans
    rs.Close: Set rs = Nothing

    MsgBox lCount & " insumo(s) recalculados.", vbInformation, "Recalcular Stock"
    Exit Sub

ErrHandler:
    On Error Resume Next
    conn.RollbackTrans
    MsgBox "EjecutarRecalculo: " & Err.Description, vbCritical
End Sub


' ════════════════════════════════════════════════════════════════
'  RecalcularStock  —  Reconciliacion completa desde cero
'  lCategoria = 0  -> recalcula TODOS los productos
'  lCategoria <> 0 -> recalcula solo esa categoria (campo Agrupar)
'
'  Uso:
'    Call RecalcularStock(cnDB, 0)     ' todos
'    Call RecalcularStock(cnDB, 5)     ' solo categoria 5
' ════════════════════════════════════════════════════════════════
Public Sub RecalcularStock(ByVal conn As Object, ByVal lCategoria As Long)
    On Error GoTo ErrHandler

    Dim sWhere As String
    sWhere = IIf(lCategoria <> 0, "ip.Agrupar = " & CStr(lCategoria), "")

    Call InsertarFaltantes(conn, sWhere)
    Call EjecutarRecalculo_VB6(conn, sWhere)
    Exit Sub

ErrHandler:
    MsgBox "RecalcularStock: " & Err.Description, vbCritical
End Sub


' ════════════════════════════════════════════════════════════════
'  DescontarStockFactura  —  Delta al cerrar una factura
'  Resta del stock los items vendidos en ESA factura especifica.
'  Llamar inmediatamente despues de guardar/cerrar la factura.
'
'  Uso:
'    Call DescontarStockFactura(cnDB, Nro_Factura, Format(Date,"yyyy-mm-dd"))
' ════════════════════════════════════════════════════════════════
Public Sub DescontarStockFactura(ByVal conn As Object, ByVal sNroFactura As String, ByVal dFecha As Date)
    On Error GoTo ErrHandler

    Dim sFecha As String
    sFecha = Format(dFecha, "yyyy-mm-dd")

    Dim s As String
    s = "UPDATE inventario_actual_porciones iap "
    s = s & "INNER JOIN ( "
    s = s & "SELECT pod.Id_Item, SUM(od.Cantidad * pod.Cantidad) AS total "
    s = s & "FROM detalle_comanda_producto pod "
    s = s & "INNER JOIN detalle_comanda od "
    s = s & "ON od.Nro_Pedido   = pod.Nro_Pedido "
    s = s & "AND od.Nro_Factura = pod.Nro_Factura "
    s = s & "AND od.Fecha       = pod.Fecha "
    s = s & "AND od.Id_Plato    = pod.Id_Plato "
    s = s & "AND od.Item        = pod.Item "
    s = s & "WHERE od.Nro_Factura = '" & sNroFactura & "' "
    s = s & "AND od.Fecha = '" & sFecha & "' "
    s = s & "GROUP BY pod.Id_Item "
    s = s & ") ventas ON ventas.Id_Item = iap.Id_Item "
    s = s & "SET iap.Cantidad_Actual = iap.Cantidad_Actual - ventas.total, "
    s = s & "iap.Enviada_MySql = 0"
    conn.Execute s
    Exit Sub

ErrHandler:
    MsgBox "DescontarStockFactura: " & Err.Description, vbCritical
End Sub


' ════════════════════════════════════════════════════════════════
'  DescontarStockRecibo  —  Delta al cerrar un recibo
'  Resta del stock los items vendidos en ESE recibo especifico.
'  Llamar inmediatamente despues de guardar/cerrar el recibo.
'
'  Nota: en recibos_detalle_comanda el numero de recibo se guarda
'        en Nro_Factura (misma estructura que facturas).
'
'  Uso:
'    Call DescontarStockRecibo(cnDB, Nro_Recibo, Format(Date,"yyyy-mm-dd"))
' ════════════════════════════════════════════════════════════════
Public Sub DescontarStockRecibo(ByVal conn As Object, ByVal sNroRecibo As String, ByVal dFecha As Date)
    On Error GoTo ErrHandler

    Dim sFecha As String
    sFecha = Format(dFecha, "yyyy-mm-dd")

    Dim s As String
    s = "UPDATE inventario_actual_porciones iap "
    s = s & "INNER JOIN ( "
    s = s & "SELECT prd.Id_Item, SUM(rod.Cantidad * prd.Cantidad) AS total "
    s = s & "FROM recibos_detalle_comanda_producto prd "
    s = s & "INNER JOIN recibos_detalle_comanda rod "
    s = s & "ON rod.Nro_Pedido   = prd.Nro_Pedido "
    s = s & "AND rod.Nro_Factura = prd.Nro_Factura "
    s = s & "AND rod.Fecha       = prd.Fecha "
    s = s & "AND rod.Id_Plato    = prd.Id_Plato "
    s = s & "AND rod.Item        = prd.Item "
    s = s & "WHERE rod.Nro_Factura = '" & sNroRecibo & "' "
    s = s & "AND rod.Fecha = '" & sFecha & "' "
    s = s & "GROUP BY prd.Id_Item "
    s = s & ") ventas ON ventas.Id_Item = iap.Id_Item "
    s = s & "SET iap.Cantidad_Actual = iap.Cantidad_Actual - ventas.total, "
    s = s & "iap.Enviada_MySql = 0"
    conn.Execute s
    Exit Sub

ErrHandler:
    MsgBox "DescontarStockRecibo: " & Err.Description, vbCritical
End Sub


' ════════════════════════════════════════════════════════════════
'  DevolverStockFactura  —  Delta al ANULAR una factura
'  Devuelve al stock los items que se habian descontado.
'  Llamar inmediatamente despues de marcar la factura como anulada.
'
'  Uso:
'    Call DevolverStockFactura(cnDB, Nro_Factura, Format(Date,"yyyy-mm-dd"))
' ════════════════════════════════════════════════════════════════
Public Sub DevolverStockFactura(ByVal conn As Object, ByVal sNroFactura As String, ByVal dFecha As Date)
    On Error GoTo ErrHandler

    Dim sFecha As String
    sFecha = Format(dFecha, "yyyy-mm-dd")

    Dim s As String
    s = "UPDATE inventario_actual_porciones iap "
    s = s & "INNER JOIN ( "
    s = s & "SELECT pod.Id_Item, SUM(od.Cantidad * pod.Cantidad) AS total "
    s = s & "FROM detalle_comanda_producto pod "
    s = s & "INNER JOIN detalle_comanda od "
    s = s & "ON od.Nro_Pedido   = pod.Nro_Pedido "
    s = s & "AND od.Nro_Factura = pod.Nro_Factura "
    s = s & "AND od.Fecha       = pod.Fecha "
    s = s & "AND od.Id_Plato    = pod.Id_Plato "
    s = s & "AND od.Item        = pod.Item "
    s = s & "WHERE od.Nro_Factura = '" & sNroFactura & "' "
    s = s & "AND od.Fecha = '" & sFecha & "' "
    s = s & "GROUP BY pod.Id_Item "
    s = s & ") ventas ON ventas.Id_Item = iap.Id_Item "
    s = s & "SET iap.Cantidad_Actual = iap.Cantidad_Actual + ventas.total, "
    s = s & "iap.Enviada_MySql = 0"
    conn.Execute s
    Exit Sub

ErrHandler:
    MsgBox "DevolverStockFactura: " & Err.Description, vbCritical
End Sub


' ════════════════════════════════════════════════════════════════
'  DevolverStockRecibo  —  Delta al ANULAR un recibo
'  Devuelve al stock los items que se habian descontado.
'  Llamar inmediatamente despues de marcar el recibo como anulado.
'
'  Uso:
'    Call DevolverStockRecibo(cnDB, Nro_Recibo, Format(Date,"yyyy-mm-dd"))
' ════════════════════════════════════════════════════════════════
Public Sub DevolverStockRecibo(ByVal conn As Object, ByVal sNroRecibo As String, ByVal dFecha As Date)
    On Error GoTo ErrHandler

    Dim sFecha As String
    sFecha = Format(dFecha, "yyyy-mm-dd")

    Dim s As String
    s = "UPDATE inventario_actual_porciones iap "
    s = s & "INNER JOIN ( "
    s = s & "SELECT prd.Id_Item, SUM(rod.Cantidad * prd.Cantidad) AS total "
    s = s & "FROM recibos_detalle_comanda_producto prd "
    s = s & "INNER JOIN recibos_detalle_comanda rod "
    s = s & "ON rod.Nro_Pedido   = prd.Nro_Pedido "
    s = s & "AND rod.Nro_Factura = prd.Nro_Factura "
    s = s & "AND rod.Fecha       = prd.Fecha "
    s = s & "AND rod.Id_Plato    = prd.Id_Plato "
    s = s & "AND rod.Item        = prd.Item "
    s = s & "WHERE rod.Nro_Factura = '" & sNroRecibo & "' "
    s = s & "AND rod.Fecha = '" & sFecha & "' "
    s = s & "GROUP BY prd.Id_Item "
    s = s & ") ventas ON ventas.Id_Item = iap.Id_Item "
    s = s & "SET iap.Cantidad_Actual = iap.Cantidad_Actual + ventas.total, "
    s = s & "iap.Enviada_MySql = 0"
    conn.Execute s
    Exit Sub

ErrHandler:
    MsgBox "DevolverStockRecibo: " & Err.Description, vbCritical
End Sub


' ════════════════════════════════════════════════════════════════
'  AgregarEntrada  —  Delta al REGISTRAR una entrada de inventario
'  Suma la cantidad al stock del insumo.
'  Llamar al guardar el registro en inventarios_entradas_manuales.
'
'  Uso:
'    Call AgregarEntrada(cnDB, lIdItem, dblCantidad)
' ════════════════════════════════════════════════════════════════
Public Sub AgregarEntrada(ByVal conn As Object, ByVal lIdItem As Long, ByVal dblCantidad As Double)
    On Error GoTo ErrHandler

    conn.Execute "UPDATE inventario_actual_porciones " & _
                 "SET Cantidad_Actual = Cantidad_Actual + " & Replace(CStr(dblCantidad), ",", ".") & ", " & _
                 "Enviada_MySql = 0 " & _
                 "WHERE Id_Item = " & lIdItem
    Exit Sub

ErrHandler:
    MsgBox "AgregarEntrada: " & Err.Description, vbCritical
End Sub


' ════════════════════════════════════════════════════════════════
'  RevertirEntrada  —  Delta al ELIMINAR una entrada de inventario
'  Resta la cantidad al stock (deshace lo que AgregarEntrada sumo).
'  Llamar antes o despues de eliminar el registro.
'
'  Uso:
'    Call RevertirEntrada(cnDB, lIdItem, dblCantidad)
' ════════════════════════════════════════════════════════════════
Public Sub RevertirEntrada(ByVal conn As Object, ByVal lIdItem As Long, ByVal dblCantidad As Double)
    On Error GoTo ErrHandler

    conn.Execute "UPDATE inventario_actual_porciones " & _
                 "SET Cantidad_Actual = Cantidad_Actual - " & Replace(CStr(dblCantidad), ",", ".") & ", " & _
                 "Enviada_MySql = 0 " & _
                 "WHERE Id_Item = " & lIdItem
    Exit Sub

ErrHandler:
    MsgBox "RevertirEntrada: " & Err.Description, vbCritical
End Sub


' ════════════════════════════════════════════════════════════════
'  AgregarSalida  —  Delta al REGISTRAR una salida de inventario
'  Resta la cantidad al stock del insumo.
'  Llamar al guardar el registro en inventarios_salidas_manuales.
'
'  Uso:
'    Call AgregarSalida(cnDB, lIdItem, dblCantidad)
' ════════════════════════════════════════════════════════════════
Public Sub AgregarSalida(ByVal conn As Object, ByVal lIdItem As Long, ByVal dblCantidad As Double)
    On Error GoTo ErrHandler

    conn.Execute "UPDATE inventario_actual_porciones " & _
                 "SET Cantidad_Actual = Cantidad_Actual - " & Replace(CStr(dblCantidad), ",", ".") & ", " & _
                 "Enviada_MySql = 0 " & _
                 "WHERE Id_Item = " & lIdItem
    Exit Sub

ErrHandler:
    MsgBox "AgregarSalida: " & Err.Description, vbCritical
End Sub


' ════════════════════════════════════════════════════════════════
'  RevertirSalida  —  Delta al ELIMINAR una salida de inventario
'  Suma la cantidad al stock (deshace lo que AgregarSalida resto).
'  Llamar antes o despues de eliminar el registro.
'
'  Uso:
'    Call RevertirSalida(cnDB, lIdItem, dblCantidad)
' ════════════════════════════════════════════════════════════════
Public Sub RevertirSalida(ByVal conn As Object, ByVal lIdItem As Long, ByVal dblCantidad As Double)
    On Error GoTo ErrHandler

    conn.Execute "UPDATE inventario_actual_porciones " & _
                 "SET Cantidad_Actual = Cantidad_Actual + " & Replace(CStr(dblCantidad), ",", ".") & ", " & _
                 "Enviada_MySql = 0 " & _
                 "WHERE Id_Item = " & lIdItem
    Exit Sub

ErrHandler:
    MsgBox "RevertirSalida: " & Err.Description, vbCritical
End Sub
