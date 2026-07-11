' ============================================================
' ModRecalcularStock
' Recalcula inventario_actual_porciones.Cantidad_Actual usando
' la formula completa desde las transacciones reales.
' 
' Formula:
'   Cantidad_Actual = ultimo_inventario_fisico
'                   + entradas desde esa fecha
'                   - salidas desde esa fecha
'                   - ventas en recibos no anulados (recibos_detalle_comanda.Cantidad
'                                                  * recibos_detalle_comanda_producto.Cantidad)
'                   - ventas en facturas no anuladas (detalle_comanda.Cantidad
'                                                   * detalle_comanda_producto.Cantidad)
'
' Mapeo tablas VB6 -> Web:
'   inventario_porciones              -> supply_items
'   inventario_actual_porciones       -> inventario_actual_porciones
'   inventarios_fisicos_manuales      -> inventory_physical
'   inventarios_entradas_manuales     -> inventory_entries
'   inventarios_salidas_manuales      -> inventory_exits
'   facturas                          -> pos_invoices
'   detalle_comanda                   -> pos_order_details
'   detalle_comanda_producto          -> pos_order_detail_products
'   recibos                           -> pos_receipts
'   recibos_detalle_comanda           -> pos_receipt_order_details
'   recibos_detalle_comanda_producto  -> pos_receipt_order_detail_products
'
' Nota: Facturas y Recibos tienen estructura identica, mismos nombres de columna.
'   Solo cambia el nombre de la tabla. Nro_Factura = numero de documento en ambas.
'
' Requiere: MySQL 8+ / MariaDB 10.2+ (usa WITH ... CTE)
' ============================================================

' ── SQL: CTE completo con nombres de tablas VB6 ─────────────────────────────
Private Function BuildCTE_VB6() As String
    BuildCTE_VB6 = _
        "WITH ranked_phys AS ( " & _
        "  SELECT Id_Item, Cantidad, Fecha, " & _
        "         ROW_NUMBER() OVER (PARTITION BY Id_Item ORDER BY Fecha DESC) AS rn " & _
        "  FROM inventarios_fisicos_manuales " & _
        "), " & _
        "last_phys AS ( " & _
        "  SELECT Id_Item, Cantidad, Fecha FROM ranked_phys WHERE rn = 1 " & _
        "), " & _
        "entries_adj AS ( " & _
        "  SELECT ie.Id_Item, SUM(ie.Cantidad) AS total " & _
        "  FROM inventarios_entradas_manuales ie " & _
        "  LEFT JOIN last_phys lp ON lp.Id_Item = ie.Id_Item " & _
        "  WHERE (lp.Fecha IS NULL OR ie.Fecha >= lp.Fecha) " & _
        "  GROUP BY ie.Id_Item " & _
        "), " & _
        "exits_adj AS ( " & _
        "  SELECT ix.Id_Item, SUM(ix.Cantidad) AS total " & _
        "  FROM inventarios_salidas_manuales ix " & _
        "  LEFT JOIN last_phys lp ON lp.Id_Item = ix.Id_Item " & _
        "  WHERE (lp.Fecha IS NULL OR ix.Fecha >= lp.Fecha) " & _
        "  GROUP BY ix.Id_Item " & _
        "), " & _
        "receipt_sales AS ( " & _
        "  SELECT prd.Id_Item, SUM(rod.Cantidad * prd.Cantidad) AS total " & _
        "  FROM recibos_detalle_comanda_producto prd " & _
        "  INNER JOIN recibos_detalle_comanda rod " & _
        "      ON  rod.Nro_Pedido  = prd.Nro_Pedido " & _
        "      AND rod.Nro_Factura = prd.Nro_Factura " & _
        "      AND rod.Fecha       = prd.Fecha " & _
        "      AND rod.Id_Plato    = prd.Id_Plato " & _
        "      AND rod.Item        = prd.Item " & _
        "  INNER JOIN recibos pr " & _
        "      ON  pr.Nro_Factura = rod.Nro_Factura " & _
        "      AND pr.Fecha       = rod.Fecha " & _
        "      AND (pr.Anulada IS NULL OR pr.Anulada = 0) " & _
        "  LEFT JOIN last_phys lp ON lp.Id_Item = prd.Id_Item " & _
        "  WHERE (lp.Fecha IS NULL OR prd.Fecha >= lp.Fecha) " & _
        "  GROUP BY prd.Id_Item " & _
        "), " & _
        "invoice_sales AS ( " & _
        "  SELECT pod.Id_Item, SUM(od.Cantidad * pod.Cantidad) AS total " & _
        "  FROM detalle_comanda_producto pod " & _
        "  INNER JOIN detalle_comanda od " & _
        "      ON  od.Nro_Pedido  = pod.Nro_Pedido " & _
        "      AND od.Nro_Factura = pod.Nro_Factura " & _
        "      AND od.Fecha       = pod.Fecha " & _
        "      AND od.Id_Plato    = pod.Id_Plato " & _
        "      AND od.Item        = pod.Item " & _
        "  INNER JOIN facturas pi " & _
        "      ON  pi.Nro_Factura = od.Nro_Factura " & _
        "      AND pi.Fecha       = od.Fecha " & _
        "      AND (pi.Anulada IS NULL OR pi.Anulada = 0) " & _
        "  LEFT JOIN last_phys lp ON lp.Id_Item = pod.Id_Item " & _
        "  WHERE (lp.Fecha IS NULL OR pod.Fecha >= lp.Fecha) " & _
        "  GROUP BY pod.Id_Item " & _
        ") "
End Function

' ── Paso 1: Insertar en inventario_actual_porciones los items faltantes ──────
Private Sub InsertarFaltantes(ByVal conn As Object, ByVal sWhere As String)
    conn.Execute _
        "INSERT INTO inventario_actual_porciones " & _
        "  (Id_Grupo, Id_Item, Codigo_Insumo, Descripcion, Costo, " & _
        "   Und_Compra, Valor_Und_Compra, Und_Min_Utilizadas, Posicion, Agrupar, " & _
        "   Compras, Controlar, Opcion_Cambios, Und_Uso, Centro_Produccion, " & _
        "   Cantidad_Actual, Bodega, Insumo_Cp, Fecha_Vence, Stock_MInimo) " & _
        "SELECT ip.Id_Grupo, ip.Id_Item, ip.Codigo_Insumo, ip.Descripcion, ip.Costo, " & _
        "       ip.Und_Compra, ip.Valor_Und_Compra, ip.Und_Min_Utilizadas, ip.Posicion, ip.Agrupar, " & _
        "       ip.Compras, ip.Controlar, ip.Opcion_Cambios, ip.Und_Uso, ip.Centro_Produccion, " & _
        "       0, ip.Bodega, ip.Insumo_Cp, ip.Fecha_Vence, ip.Stock_MInimo " & _
        "FROM inventario_porciones ip " & _
        "LEFT JOIN inventario_actual_porciones iap ON iap.Id_Item = ip.Id_Item " & _
        "WHERE iap.Id_Item IS NULL " & IIf(sWhere <> "", " AND " & sWhere, "")
End Sub

' ── Paso 2: Calcular y actualizar Cantidad_Actual ────────────────────────────
Private Sub EjecutarRecalculo_VB6(ByVal conn As Object, ByVal sWhere As String)
    Dim sSQL As String
    sSQL = BuildCTE_VB6() & _
           "SELECT ip.Id_Item, ip.Id_Grupo, " & _
           "       COALESCE(lp.Cantidad,0) + COALESCE(ea.total,0) - COALESCE(xa.total,0) " & _
           "       - COALESCE(rs.total,0) - COALESCE(inv.total,0) AS nueva_cantidad " & _
           "FROM inventario_porciones ip " & _
           "LEFT JOIN last_phys lp      ON lp.Id_Item  = ip.Id_Item " & _
           "LEFT JOIN entries_adj ea    ON ea.Id_Item   = ip.Id_Item " & _
           "LEFT JOIN exits_adj xa      ON xa.Id_Item   = ip.Id_Item " & _
           "LEFT JOIN receipt_sales rs  ON rs.Id_Item   = ip.Id_Item " & _
           "LEFT JOIN invoice_sales inv ON inv.Id_Item  = ip.Id_Item " & _
           "WHERE 1=1" & IIf(sWhere <> "", " AND " & sWhere, "")

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open sSQL, conn, 0, 1  ' adOpenForwardOnly, adLockReadOnly

    If rs.EOF Then
        rs.Close: Set rs = Nothing
        MsgBox "No se encontraron insumos para recalcular.", vbInformation
        Exit Sub
    End If

    Dim lCount As Long: lCount = 0
    conn.BeginTrans
    Do While Not rs.EOF
        conn.Execute _
            "UPDATE inventario_actual_porciones " & _
            "SET Cantidad_Actual = " & CDbl(rs("nueva_cantidad")) & ", " & _
            "    Enviada_MySql   = 0 " & _
            "WHERE Id_Item = " & CLng(rs("Id_Item"))
        lCount = lCount + 1
        rs.MoveNext
    Loop
    conn.CommitTrans
    rs.Close: Set rs = Nothing

    MsgBox lCount & " insumo(s) recalculados correctamente.", vbInformation, "Recalcular Stock"
    Exit Sub

ErrHandler:
    On Error Resume Next
    conn.RollbackTrans
    MsgBox "Error al recalcular: " & Err.Description, vbCritical
End Sub


' ════════════════════════════════════════════════════════════════
'  RecalcularStock
'  lCategoria = 0  → recalcula TODOS los productos
'  lCategoria <> 0 → recalcula solo esa categoria (campo Agrupar)
'
'  Uso:
'    Call RecalcularStock(cnDB, 0)   ' todos
'    Call RecalcularStock(cnDB, 5)   ' solo categoria 5
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
