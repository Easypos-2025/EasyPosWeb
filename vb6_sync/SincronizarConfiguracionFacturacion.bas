' ============================================================
' SincronizarConfiguracionFacturacion
' Endpoint: POST /api/pos/sync/push/billing-config
' Tabla local VB6: configuracion_facturacion
' Tabla servidor: configuracion_facturacion   (llave: company_id — una fila por empresa)
' La tabla no tiene Enviada_MySql: se envía la fila completa cada vez que se llame
' (p. ej. al guardar la configuración o una vez al iniciar). El servidor también
' actualiza company_configs.has_tip / tip_percentage.
' Nota: en empresas mixtas (escritorio + web) lo último enviado desde escritorio
'       reemplaza lo editado en la vista web "Configuración Facturación".
' ============================================================
Public Sub SincronizarConfiguracionFacturacion(Var_Id_Company_Envio As Integer)
    On Error GoTo ErrHandler

    Dim conn As Object
    Set conn = GetConn(Var_Sql_Base_Datos_Principal_Sede)

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM configuracion_facturacion LIMIT 1", conn

    If rs.EOF Then
        rs.Close: conn.Close
        Exit Sub
    End If

    ' -- Construir JSON (Str() usa punto decimal sin importar la configuración regional)
    Dim json As String
    json = "[{"
    json = json & """company_id"":"                       & Var_Id_Company_Envio                                         & ","
    json = json & """id_sede"":"                          & Str(Nz(rs("Id_Sede"), 0))                                    & ","
    json = json & """impuesto_iva"":"                     & Str(Nz(rs("Impuesto_Iva"), 0))                               & ","
    json = json & """impuesto_impoconsumo"":"             & Str(Nz(rs("Impuesto_Impoconsumo"), 0))                       & ","
    json = json & """impuesto_rete_fuente"":"             & Str(Nz(rs("Impuesto_Rete_Fuente"), 0))                       & ","
    json = json & """liquidar_propina"":"                 & IIf(Nz(rs("Liquidar_Propina"), 0) <> 0, 1, 0)                & ","
    json = json & """resolucion_propina"":"               & """" & EscapeJson(Nz(rs("Resolucion_Propina"), ""))          & ""","
    json = json & """paga_impuesto"":"                    & IIf(Nz(rs("Paga_Impuesto"), 0) <> 0, 1, 0)                   & ","
    json = json & """precios_incluyen_impuesto"":"        & IIf(Nz(rs("Precios_Incluyen_Impuesto"), 0) <> 0, 1, 0)       & ","
    json = json & """imprimir_logo_factura"":"            & IIf(Nz(rs("Imprimir_Logo_Factura"), 0) <> 0, 1, 0)           & ","
    json = json & """nombre_logo_factura"":"              & """" & EscapeJson(Nz(rs("Nombre_Logo_Factura"), ""))         & ""","
    json = json & """tipo_moneda"":"                      & Str(Nz(rs("Tipo_Moneda"), 1))                                & ","
    json = json & """texto_numeracion"":"                 & """" & EscapeJson(Nz(rs("Texto_Numeracion"), ""))            & ""","
    json = json & """nombre_cliente_facturacion_varia"":" & """" & EscapeJson(Nz(rs("Nombre_Cliente_Facturacion_Varia"), "")) & ""","
    json = json & """codigo_cliente_facturacion_varia"":" & """" & EscapeJson(Nz(rs("Codigo_Cliente_Facturacion_Varia"), "")) & ""","
    json = json & """id_cliente_facturacion_varia"":"     & Str(Nz(rs("Id_Cliente_Facturacion_Varia"), 1))               & ","
    json = json & """usa_lector_barras"":"                & IIf(Nz(rs("Usa_Lector_Barras"), 0) <> 0, 1, 0)               & ","
    json = json & """imprimir_encabezado_factura"":"      & IIf(Nz(rs("Imprimir_Encabezado_Factura"), 0) <> 0, 1, 0)     & ","
    json = json & """impresora_facturas"":"               & Str(Nz(rs("Impresora_Facturas"), 0))                         & ","
    json = json & """mensaje_factura"":"                  & """" & EscapeJson(Nz(rs("Mensaje_Factura"), ""))             & ""","
    json = json & """longitud_factura_sistema"":"         & Str(Nz(rs("Longitud_Factura_Sistema"), 1))                   & ","
    json = json & """longitud_factura_manual"":"          & Str(Nz(rs("Longitud_Factura_Manual"), 1))                    & ","
    json = json & """cantidad_impresiones_factura"":"     & Str(Nz(rs("Cantidad_Impresiones_Factura"), 1))               & ","
    json = json & """porcentaje_propina"":"               & Str(Nz(rs("Porcentaje_Propina"), 0))                         & ","
    json = json & """activar_precio_x_mayor"":"           & IIf(Nz(rs("Activar_Precio_x_Mayor"), 0) <> 0, 1, 0)          & ","
    json = json & """usar_precuenta"":"                   & IIf(Nz(rs("Usar_Precuenta"), 0) <> 0, 1, 0)                  & ","
    json = json & """imprimir_resolucion_propina"":"      & IIf(Nz(rs("Imprimir_Resolucion_Propina"), 0) <> 0, 1, 0)     & ","
    json = json & """imprimir_datos_legales"":"           & IIf(Nz(rs("Imprimir_Datos_Legales"), 0) <> 0, 1, 0)          & ","
    json = json & """imprimir_datos_cliente"":"           & IIf(Nz(rs("Imprimir_Datos_Cliente"), 0) <> 0, 1, 0)          & ","
    json = json & """imprimir_recibo_domiciliario"":"     & IIf(Nz(rs("Imprimir_Recibo_Domiciliario"), 0) <> 0, 1, 0)    & ","
    json = json & """preguntar_valor_propina"":"          & IIf(Nz(rs("Preguntar_Valor_Propina"), 0) <> 0, 1, 0)         & ","
    json = json & """usar_comanda_corta"":"               & IIf(Nz(rs("Usar_Comanda_Corta"), 0) <> 0, 1, 0)
    json = json & "}]"
    rs.Close

    ' -- Enviar al servidor --------------------------------
    Dim respuesta As String
    respuesta = ApiPost("/sync/push/billing-config", json)
    conn.Close

    If respuesta = "" Then Exit Sub

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.language = "JScript"
    sc.ExecuteStatement "var r = " & respuesta & ";"
    Var_Caption_Error = "Config. Facturacion Env.: " & sc.Eval("r.total_saved") & _
                        " | Fallidas: " & sc.Eval("r.total_failed")
    Exit Sub

ErrHandler:
    Var_Caption_Error = Err.Description
End Sub
