/*M!999999\- enable the sandbox mode */ 

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `a_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `a_comanda` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` datetime DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Mesa` int(11) DEFAULT 0,
  `Hora` datetime DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `a_detalle_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `a_detalle_comanda` (
  `Nro_pedido` varchar(255) DEFAULT NULL,
  `Fecha` datetime DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Cantidad` int(11) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento` float DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Cambios` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `a_detalle_comanda_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `a_detalle_comanda_producto` (
  `Nro_pedido` varchar(255) DEFAULT NULL,
  `Fecha` datetime DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `a_detalle_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `a_detalle_factura` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` datetime DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Cantidad` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Valor_Plato` int(11) DEFAULT 0,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `a_facturas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `a_facturas` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` datetime DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `a_temp_inventarios_porciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `a_temp_inventarios_porciones` (
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Und_Compra` int(11) DEFAULT 0,
  `Valor_Und_Compra` float DEFAULT 0,
  `Und_Min_Utilizadas` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Compras` tinyint(4) DEFAULT 0,
  `Controlar` tinyint(4) DEFAULT 0,
  `Imprimir` tinyint(4) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Inv_Inicial` float DEFAULT 0,
  `Inv_Fisico` float DEFAULT 0,
  `Ventas` float DEFAULT 0,
  `Salidas` float DEFAULT 0,
  `Entradas` float DEFAULT 0,
  `Diferencia` float DEFAULT 0,
  `Observacion_Uno` varchar(255) DEFAULT NULL,
  `Observacion_Dos` varchar(255) DEFAULT NULL,
  `Cantidad_Minima` float DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Insumo_Cp` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `a_temp_inventarios_porciones_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `a_temp_inventarios_porciones_categoria` (
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Und_Compra` int(11) DEFAULT 0,
  `Valor_Und_Compra` float DEFAULT 0,
  `Und_Min_Utilizadas` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Compras` tinyint(4) DEFAULT 0,
  `Controlar` tinyint(4) DEFAULT 0,
  `Imprimir` tinyint(4) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Inv_Inicial` float DEFAULT 0,
  `Inv_Fisico` float DEFAULT 0,
  `Ventas` float DEFAULT 0,
  `Salidas` float DEFAULT 0,
  `Entradas` float DEFAULT 0,
  `Diferencia` float DEFAULT 0,
  `Observacion_Uno` varchar(255) DEFAULT NULL,
  `Observacion_Dos` varchar(255) DEFAULT NULL,
  `Cantidad_Minima` float DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Insumo_Cp` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=COMPACT;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `a_temp_inventarios_porciones_excel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `a_temp_inventarios_porciones_excel` (
  `Sede` varchar(255) DEFAULT NULL,
  `Categoria` varchar(255) DEFAULT NULL,
  `Codigo_Producto` varchar(255) DEFAULT NULL,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float DEFAULT 0,
  `Presentacion` varchar(255) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Total` float DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Precio_Venta` double DEFAULT 0,
  `Fecha` date DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `a_temp_inventarios_porciones_todos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `a_temp_inventarios_porciones_todos` (
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Und_Compra` int(11) DEFAULT 0,
  `Valor_Und_Compra` float DEFAULT 0,
  `Und_Min_Utilizadas` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Compras` tinyint(4) DEFAULT 0,
  `Controlar` tinyint(4) DEFAULT 0,
  `Imprimir` tinyint(4) DEFAULT 0,
  `Fecha` date DEFAULT NULL,
  `Inv_Inicial` float DEFAULT 0,
  `Inv_Fisico` float DEFAULT 0,
  `Ventas` float DEFAULT 0,
  `Salidas` float DEFAULT 0,
  `Entradas` float DEFAULT 0,
  `Diferencia` float DEFAULT 0,
  `Observacion_Uno` varchar(255) DEFAULT NULL,
  `Observacion_Dos` varchar(255) DEFAULT NULL,
  `Cantidad_Minima` float DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Insumo_Cp` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `asociados_web`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `asociados_web` (
  `Id_Sede` double DEFAULT 0,
  `Activa` tinyint(4) DEFAULT 0,
  `Remoto` tinyint(4) DEFAULT 0,
  `IpBd` varchar(200) DEFAULT NULL,
  `Bd` varchar(200) DEFAULT NULL,
  `Almacen` varchar(200) DEFAULT NULL,
  `Caja` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `asociadoseasypos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `asociadoseasypos` (
  `Id_Ingreso` bigint(20) DEFAULT 0,
  `Id_Sede` double DEFAULT 0,
  `Nombre_Empresa` varchar(250) DEFAULT NULL,
  `Nombre_Contacto` varchar(250) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `Telefono_Contacto` varchar(250) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `e_mail` varchar(50) DEFAULT NULL,
  `Password` varchar(50) DEFAULT NULL,
  `Id_Pais` int(11) DEFAULT 0,
  `Id_Departametno` int(11) DEFAULT 0,
  `Id_Ciudad` int(11) DEFAULT 0,
  `Id_Plan` int(11) DEFAULT 0,
  `Id_Tipo_Negocio` int(11) DEFAULT 0,
  `Fecha_Registro` date DEFAULT NULL,
  `Activa` tinyint(4) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `historico_liquidacion_propinas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `historico_liquidacion_propinas` (
  `Id_Liquidacion` bigint(20) NOT NULL DEFAULT 0,
  `Fecha` date NOT NULL,
  `Turno` int(11) NOT NULL DEFAULT 0,
  `cod_empleado` int(11) NOT NULL DEFAULT 0,
  `Valor` double NOT NULL DEFAULT 0,
  `Normal` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Liquidacion`,`Fecha`,`Turno`,`cod_empleado`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `lista_precios_cliente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lista_precios_cliente` (
  `id_lista` int(11) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `paso_temp_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `paso_temp_comanda` (
  `Nro_Pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(50) NOT NULL,
  `Mesa` varchar(100) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(1) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(1) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Id_Mesa` int(11) DEFAULT 0,
  PRIMARY KEY (`Nro_Pedido`,`Fecha`,`Nro_Factura`),
  KEY `Nro_Pedido` (`Nro_Pedido`),
  KEY `Fecha` (`Fecha`),
  KEY `Nro_Factura` (`Nro_Factura`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `paso_temp_detalle_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `paso_temp_detalle_comanda` (
  `Nro_pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(50) NOT NULL,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(1) DEFAULT 0,
  `Porc_Descuento_Plato` float DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Nro_Puesto` tinyint(4) DEFAULT 0,
  `Cambios` varchar(250) DEFAULT NULL,
  `Hora_Plato` varchar(250) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL,
  `Depende` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Nro_pedido`,`Fecha`,`Nro_Factura`,`Id_Plato`,`Item`),
  KEY `Id_Plato` (`Id_Plato`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `paso_temp_detalle_comanda_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `paso_temp_detalle_comanda_producto` (
  `Nro_pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(50) NOT NULL,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `paso_temp_detalle_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `paso_temp_detalle_factura` (
  `Nro_Factura` varchar(50) NOT NULL,
  `Nro_Pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Cantidad` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Valor_Plato` int(11) DEFAULT 0,
  `Cortesia` tinyint(1) DEFAULT 0,
  `Porc_Descuento` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Depende` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Nro_Factura`,`Nro_Pedido`,`Fecha`,`Id_Plato`,`Item`),
  KEY `Nro_Factura` (`Nro_Factura`),
  KEY `Nro_Pedido` (`Nro_Pedido`),
  KEY `Fecha` (`Fecha`),
  KEY `Id_Plato` (`Id_Plato`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `paso_temp_facturas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `paso_temp_facturas` (
  `Nro_Factura` varchar(50) NOT NULL,
  `Fecha` date DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(1) DEFAULT 0,
  `Pago_Iva` tinyint(1) DEFAULT 0,
  `Arreglo` tinyint(1) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(1) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(1) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` tinyint(4) DEFAULT 0,
  `Factura_Domicilio` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Nro_Factura`),
  KEY `Fecha` (`Fecha`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tarjetas_baucher`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tarjetas_baucher` (
  `Id_Tarjeta` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Largo` varchar(50) DEFAULT NULL,
  `Nombre_Corto` varchar(50) DEFAULT NULL,
  `Banco` varchar(50) DEFAULT NULL,
  `Porcentaje` float DEFAULT 0,
  `Activa` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_a_tabla_temporal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_a_tabla_temporal` (
  `Nro_Pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(50) NOT NULL,
  `Mesa` varchar(100) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(1) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(1) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Id_Mesa` int(11) DEFAULT 0,
  PRIMARY KEY (`Nro_Pedido`,`Fecha`,`Nro_Factura`) USING BTREE,
  KEY `Nro_Pedido` (`Nro_Pedido`) USING BTREE,
  KEY `Fecha` (`Fecha`) USING BTREE,
  KEY `Nro_Factura` (`Nro_Factura`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_analisis_venta_almuerzos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_analisis_venta_almuerzos` (
  `Id_Sede` varchar(100) NOT NULL DEFAULT '0',
  `Mes` int(11) DEFAULT 0,
  `Año` int(11) DEFAULT 0,
  `Venta_T1` double DEFAULT 0,
  `Venta_Almuerzos` double DEFAULT 0,
  `Cantidad_Almuerzos` double DEFAULT 0,
  `Venta_Pf_T1` double DEFAULT 0,
  `Cantidad_Pf` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_apidian_clientes_adquiriente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_apidian_clientes_adquiriente` (
  `Id_Cliente` bigint(20) NOT NULL AUTO_INCREMENT,
  `cedula` varchar(50) DEFAULT NULL,
  `PersonaJuridica` tinyint(4) DEFAULT 0,
  `Tipo_Documento` varchar(50) DEFAULT NULL,
  `DV` varchar(2) DEFAULT NULL,
  `RegContributivo` varchar(50) DEFAULT NULL,
  `nombres` varchar(255) DEFAULT NULL,
  `Apellidos` varchar(255) DEFAULT NULL,
  `direccion` varchar(255) DEFAULT NULL,
  `telefono` varchar(255) DEFAULT NULL,
  `Barrio` varchar(50) DEFAULT NULL,
  `Mail` varchar(50) DEFAULT NULL,
  `Dia_Cumple` varchar(50) DEFAULT NULL,
  `Mes_Cumple` varchar(50) DEFAULT NULL,
  `Edad` varchar(50) DEFAULT NULL,
  `Ocupacion` varchar(50) DEFAULT NULL,
  `Porc_Descuento` varchar(50) DEFAULT NULL,
  `Observaciones` varchar(255) DEFAULT NULL,
  `Fecha_Aniversario` date DEFAULT NULL,
  `Fecha_Grado` date DEFAULT NULL,
  `Empresa` varchar(150) DEFAULT NULL,
  `Id_Klob` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Tarjeta_Fiel` varchar(50) DEFAULT NULL,
  `Cod_Barrio` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Referencia` varchar(255) DEFAULT NULL,
  `Cod_Municipio` int(11) DEFAULT 0,
  `Ciudad` int(11) DEFAULT 0,
  `Departamento` int(11) DEFAULT 0,
  `CodPais` int(11) DEFAULT 0,
  PRIMARY KEY (`Id_Cliente`) USING BTREE,
  UNIQUE KEY `cedula` (`cedula`) USING BTREE
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_apidian_clientes_facturar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_apidian_clientes_facturar` (
  `Id_Cliente` bigint(20) NOT NULL AUTO_INCREMENT,
  `cedula` varchar(50) DEFAULT NULL,
  `PersonaJuridica` tinyint(4) DEFAULT 0,
  `Tipo_Documento` varchar(50) DEFAULT NULL,
  `DV` varchar(2) DEFAULT NULL,
  `RegContributivo` varchar(50) DEFAULT NULL,
  `nombres` varchar(255) DEFAULT NULL,
  `Apellidos` varchar(255) DEFAULT NULL,
  `direccion` varchar(255) DEFAULT NULL,
  `telefono` varchar(250) DEFAULT NULL,
  `Barrio` varchar(50) DEFAULT NULL,
  `Mail` varchar(50) DEFAULT NULL,
  `Dia_Cumple` varchar(50) DEFAULT NULL,
  `Mes_Cumple` varchar(50) DEFAULT NULL,
  `Edad` varchar(50) DEFAULT NULL,
  `Ocupacion` varchar(50) DEFAULT NULL,
  `Porc_Descuento` varchar(50) DEFAULT NULL,
  `Observaciones` varchar(255) DEFAULT NULL,
  `Fecha_Aniversario` date DEFAULT NULL,
  `Fecha_Grado` date DEFAULT NULL,
  `Empresa` varchar(150) DEFAULT NULL,
  `Id_Klob` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Tarjeta_Fiel` varchar(50) DEFAULT NULL,
  `Cod_Barrio` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Referencia` varchar(255) DEFAULT NULL,
  `Cod_Municipio` int(11) DEFAULT 0,
  `Ciudad` int(11) DEFAULT 0,
  `Departamento` int(11) DEFAULT 0,
  `CodPais` int(11) DEFAULT 0,
  PRIMARY KEY (`Id_Cliente`) USING BTREE,
  UNIQUE KEY `cedula` (`cedula`) USING BTREE
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_apidian_comanda_previo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_apidian_comanda_previo` (
  `Nro_Pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(50) NOT NULL DEFAULT '0',
  `Mesa` varchar(200) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Movil` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Nro_Pedido`,`Fecha`,`Nro_Factura`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_apidian_detalle_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_apidian_detalle_comanda` (
  `Nro_pedido` varchar(255) NOT NULL DEFAULT '0',
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(100) DEFAULT '0',
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float NOT NULL DEFAULT 0,
  `Valor` double DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` text DEFAULT NULL,
  `Salio` tinyint(1) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` double DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` varchar(50) NOT NULL DEFAULT '0',
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT NULL,
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL,
  PRIMARY KEY (`Nro_pedido`,`Fecha`,`Id_Plato`,`Item`,`Depende`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_apidian_factura_forma_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_apidian_factura_forma_pago` (
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Forma_Pago` int(11) NOT NULL DEFAULT 0,
  `Id_Tarjeta` int(11) NOT NULL DEFAULT 0,
  `Nro_Factura` varchar(100) NOT NULL DEFAULT '0',
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Valor` double DEFAULT 0,
  `Porcentaje` float DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Fecha` varchar(255) DEFAULT NULL,
  `Valor_Domicilio` double DEFAULT 0,
  `Id_Bono` int(11) NOT NULL DEFAULT 0,
  `Prefix` varchar(50) DEFAULT NULL,
  `Fac_PE` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_apidian_factura_previo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_apidian_factura_previo` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` date DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` varchar(255) DEFAULT '0',
  `Factura_Domicilio` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_archivo_contable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_archivo_contable` (
  `EMPRESA` varchar(250) DEFAULT NULL,
  `CU` varchar(50) DEFAULT NULL,
  `DOCUMENTO` varchar(50) DEFAULT NULL,
  `NRO` varchar(50) DEFAULT NULL,
  `BENEFICIARIO` varchar(50) DEFAULT NULL,
  `SUCURSAL` varchar(50) DEFAULT NULL,
  `FECHA` varchar(50) DEFAULT NULL,
  `DIASVCTO` varchar(50) DEFAULT NULL,
  `FECHA_VCTO` varchar(50) DEFAULT NULL,
  `COD_VENDOR` varchar(50) DEFAULT NULL,
  `OBSERVACIONES_CAB` varchar(50) DEFAULT NULL,
  `BODEGA` varchar(50) DEFAULT NULL,
  `COD_ITM_REF` varchar(50) DEFAULT NULL,
  `CPTO_MOV` varchar(50) DEFAULT NULL,
  `TIPO_MOV` varchar(50) DEFAULT NULL,
  `CC` varchar(50) DEFAULT NULL,
  `UNIMED` varchar(50) DEFAULT NULL,
  `CANTIDAD` varchar(50) DEFAULT NULL,
  `VALOR_UNITARIO` varchar(50) DEFAULT NULL,
  `VALOR_TOTAL_SIN_IVA_NI_DCTOS` varchar(50) DEFAULT NULL,
  `CLASE_MVTO` varchar(50) DEFAULT NULL,
  `OBSERVA_DETALLE` varchar(50) DEFAULT NULL,
  `DCTO_GLOBAL` varchar(50) DEFAULT NULL,
  `DCTO_UNI` varchar(50) DEFAULT NULL,
  `VLR_DCTO` varchar(50) DEFAULT NULL,
  `COD_IMPTO` varchar(50) DEFAULT NULL,
  `TASA_IMPTO` varchar(50) DEFAULT NULL,
  `EXCLUIDO` varchar(50) DEFAULT NULL,
  `VLR_IMPTO` varchar(50) DEFAULT NULL,
  `IMPOCONSUMO` varchar(50) DEFAULT NULL,
  `COSTO_UNI` varchar(50) DEFAULT NULL,
  `COSTO_TOTAL` varchar(50) DEFAULT NULL,
  `V_Columna_AG` varchar(50) DEFAULT NULL,
  `V_Columna_AH` varchar(50) DEFAULT NULL,
  `V_Columna_AI` varchar(50) DEFAULT NULL,
  `V_Columna_AJ` varchar(50) DEFAULT NULL,
  `V_Columna_AK` varchar(50) DEFAULT NULL,
  `V_Columna_AL` varchar(50) DEFAULT NULL,
  `V_Columna_AM` varchar(50) DEFAULT NULL,
  `V_Columna_AN` varchar(50) DEFAULT NULL,
  `V_Columna_AO` varchar(50) DEFAULT NULL,
  `V_Columna_AP` varchar(50) DEFAULT NULL,
  `V_Columna_AQ` varchar(50) DEFAULT NULL,
  `V_Columna_AR` varchar(50) DEFAULT NULL,
  `V_Columna_AS` varchar(50) DEFAULT NULL,
  `V_Columna_AT` varchar(50) DEFAULT NULL,
  `V_Columna_AU` varchar(50) DEFAULT NULL,
  `V_Columna_AV` varchar(50) DEFAULT NULL,
  `V_Columna_AW` varchar(50) DEFAULT NULL,
  `V_Columna_AX` varchar(50) DEFAULT NULL,
  `V_Columna_AY` varchar(50) DEFAULT NULL,
  `V_Columna_AZ` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_auxiliar_pedido_productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_auxiliar_pedido_productos` (
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Semana` varchar(50) DEFAULT NULL,
  `Nro_Semana` int(11) DEFAULT 0,
  `Año` int(11) DEFAULT 0,
  `Nombre_Plato` varchar(50) DEFAULT NULL,
  `Fecha_Uno` varchar(50) DEFAULT NULL,
  `Cantidad_Uno` int(11) DEFAULT 0,
  `Fecha_Dos` varchar(50) DEFAULT NULL,
  `Cantidad_dos` int(11) DEFAULT 0,
  `Dia_Uno_Lunes` float DEFAULT 0,
  `Dia_Dos_Martes` float DEFAULT 0,
  `Dia_Tres_Miercoles` float DEFAULT 0,
  `Dia_Cuatro_Jueves` float DEFAULT 0,
  `Dia_Cinco_Viernes` float DEFAULT 0,
  `Dia_Seis_Sabado` float DEFAULT 0,
  `Dia_Siete_Domingo` float DEFAULT 0,
  `Inv_Actual_Sede` int(11) DEFAULT 0,
  `Inv_Actual_Cp` int(11) DEFAULT 0,
  `Pedido_Uno` int(11) DEFAULT 0,
  `Pedido_Dos` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Fecha_Pedido_Uno` date DEFAULT NULL,
  `Fecha_Pedido_Dos` date DEFAULT NULL,
  `Fecha_Llegada_Uno` date DEFAULT NULL,
  `Fecha_Llegada_Dos` date DEFAULT NULL,
  `Usuario` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_c_detalle_comanda_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_c_detalle_comanda_producto` (
  `Nro_pedido` varchar(255) DEFAULT NULL,
  `Fecha` date DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_c_detalle_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_c_detalle_factura` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` date DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Cantidad` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Valor_Plato` int(11) DEFAULT 0,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_c_facturas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_c_facturas` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` date DEFAULT NULL,
  `Valor_Efectivo` float DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` float DEFAULT 0,
  `Valor_T_Debito` float DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` float DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Mesa` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_caja_facturas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_caja_facturas` (
  `Nro_Caja` int(11) NOT NULL DEFAULT 0,
  `Nro_Factura` varchar(50) NOT NULL,
  `Fecha` date DEFAULT NULL,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Valor` double DEFAULT 0,
  `Empleado` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Pc_Desde` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_caja_facturas_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_caja_facturas_cierres` (
  `Nro_Caja` int(11) NOT NULL DEFAULT 0,
  `Nro_Factura` varchar(50) NOT NULL,
  `Fecha` date DEFAULT NULL,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Valor` double DEFAULT 0,
  `Empleado` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Pc_Desde` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_cambios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_cambios` (
  `Id_Cambio` bigint(20) NOT NULL DEFAULT 0,
  `Id_Cliente` double DEFAULT 0,
  `Valor_Entra` double DEFAULT 0,
  `Valor_Sale` double DEFAULT 0,
  `Fecha_Cambio` date DEFAULT NULL,
  `Fecha_Vence` date DEFAULT NULL,
  `Redimido` tinyint(4) DEFAULT 0,
  `Fecha_Redimido` date DEFAULT NULL,
  `Anulado` tinyint(4) DEFAULT 0,
  `Nro_Bono` varchar(50) DEFAULT NULL,
  `Observaciones` mediumtext DEFAULT NULL,
  `Cod_Empleado` int(11) DEFAULT 0,
  `Nro_Gasto` int(11) DEFAULT 0,
  `Nro_Factura_Recompra` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_cambios_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_cambios_detalle` (
  `Id_Cambio` bigint(20) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Posicion` int(11) NOT NULL DEFAULT 0,
  `Precio_Actual` int(11) DEFAULT 0,
  `Cantidad` double DEFAULT 0,
  `Posicion_Entra` tinyint(4) DEFAULT 0,
  `Codigo_Producto` varchar(255) DEFAULT NULL,
  `Producto` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id_Cambio`,`Item`,`Posicion`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_categoria_platos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_categoria_platos` (
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Categoria` int(11) NOT NULL DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Nombre_foto` varchar(50) DEFAULT NULL,
  `Porcentaje` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Lunes` tinyint(4) DEFAULT 0,
  `Martes` tinyint(4) DEFAULT 0,
  `Miercoles` tinyint(4) DEFAULT 0,
  `Jueves` tinyint(4) DEFAULT 0,
  `Viernes` tinyint(4) DEFAULT 0,
  `Sabado` tinyint(4) DEFAULT 0,
  `Domingo` tinyint(4) DEFAULT 0,
  `Activa` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Cod_Categoria`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_categoria_productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_categoria_productos` (
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Porcentaje` int(11) DEFAULT 0,
  `Activa` tinyint(4) DEFAULT 0,
  `Exgir_Seleccion` tinyint(4) NOT NULL DEFAULT 0,
  `Imprimir_Armar_Solo_Cambio` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Cod_Categoria`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_categorias` (
  `cod_categoria` int(11) NOT NULL DEFAULT 0,
  `descripcion` varchar(50) NOT NULL,
  `Nombre_foto` varchar(50) NOT NULL,
  `Activa` varchar(50) NOT NULL,
  PRIMARY KEY (`cod_categoria`),
  UNIQUE KEY `descripcion` (`descripcion`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_clientes` (
  `Id_Cliente` int(11) NOT NULL DEFAULT 0,
  `cedula` varchar(50) DEFAULT NULL,
  `nombres` varchar(255) DEFAULT NULL,
  `Apellidos` varchar(255) DEFAULT NULL,
  `direccion` varchar(255) DEFAULT NULL,
  `telefono` varchar(250) DEFAULT NULL,
  `Barrio` varchar(50) DEFAULT NULL,
  `Mail` varchar(50) DEFAULT NULL,
  `Dia_Cumple` varchar(50) DEFAULT NULL,
  `Mes_Cumple` varchar(50) DEFAULT NULL,
  `Edad` varchar(50) DEFAULT NULL,
  `Ocupacion` varchar(50) DEFAULT NULL,
  `Porc_Descuento` varchar(50) DEFAULT NULL,
  `Observaciones` varchar(255) DEFAULT NULL,
  `Fecha_Aniversario` varchar(50) DEFAULT NULL,
  `Fecha_Grado` varchar(50) DEFAULT NULL,
  `Empresa` varchar(150) DEFAULT NULL,
  `Id_Klob` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Tarjeta_Fiel` varchar(50) DEFAULT NULL,
  `Cod_Barrio` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Referencia` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id_Cliente`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_clientes_facturar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_clientes_facturar` (
  `Id_Cliente` int(11) NOT NULL DEFAULT 0,
  `cedula` varchar(50) DEFAULT NULL,
  `nombres` varchar(255) NOT NULL,
  `Apellidos` varchar(255) DEFAULT NULL,
  `direccion` varchar(255) DEFAULT NULL,
  `telefono` varchar(250) DEFAULT NULL,
  `Barrio` varchar(50) DEFAULT NULL,
  `Mail` varchar(50) DEFAULT NULL,
  `Dia_Cumple` int(11) DEFAULT 0,
  `Mes_Cumple` int(11) DEFAULT 0,
  `Edad` int(11) DEFAULT 0,
  `Ocupacion` varchar(50) DEFAULT NULL,
  `Porc_Descuento` int(11) DEFAULT 0,
  `Observaciones` mediumtext DEFAULT NULL,
  `Fecha_Aniversario` date DEFAULT NULL,
  `Fecha_Grado` date DEFAULT NULL,
  `Empresa` varchar(150) DEFAULT NULL,
  `Id_Klob` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Tarjeta_Fiel` varchar(50) DEFAULT '0',
  `Cod_Barrio` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Referencia` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id_Cliente`),
  KEY `cedula` (`cedula`),
  KEY `Apellidos` (`Apellidos`),
  KEY `nombres` (`nombres`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_codificar_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_codificar_comanda` (
  `Nro_Pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(50) NOT NULL,
  `Mesa` varchar(100) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(1) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(1) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Id_Mesa` int(11) DEFAULT 0,
  PRIMARY KEY (`Nro_Pedido`,`Fecha`,`Nro_Factura`),
  KEY `Nro_Pedido` (`Nro_Pedido`),
  KEY `Fecha` (`Fecha`),
  KEY `Nro_Factura` (`Nro_Factura`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_codificar_detalle_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_codificar_detalle_comanda` (
  `Nro_pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(50) NOT NULL,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Cantidad` int(11) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(1) DEFAULT 0,
  `Porc_Descuento_Plato` float DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Hora_Plato` varchar(255) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL,
  PRIMARY KEY (`Nro_pedido`,`Fecha`,`Nro_Factura`,`Id_Plato`,`Item`),
  KEY `Nro_pedido` (`Nro_pedido`),
  KEY `Fecha` (`Fecha`),
  KEY `Nro_Factura` (`Nro_Factura`),
  KEY `Id_Plato` (`Id_Plato`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_codificar_detalle_comanda_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_codificar_detalle_comanda_producto` (
  `Nro_pedido` varchar(255) DEFAULT NULL,
  `Fecha` date DEFAULT NULL,
  `Nro_Factura` varchar(50) NOT NULL,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_codificar_detalle_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_codificar_detalle_factura` (
  `Nro_Factura` varchar(50) NOT NULL,
  `Nro_Pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Cantidad` int(11) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Valor_Plato` int(11) DEFAULT 0,
  `Cortesia` tinyint(1) DEFAULT 0,
  `Porc_Descuento` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Nro_Factura`,`Nro_Pedido`,`Fecha`,`Id_Plato`,`Item`),
  KEY `Nro_Factura` (`Nro_Factura`),
  KEY `Nro_Pedido` (`Nro_Pedido`),
  KEY `Fecha` (`Fecha`),
  KEY `Id_Plato` (`Id_Plato`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_codificar_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_codificar_factura` (
  `Nro_Factura` varchar(50) NOT NULL,
  `Fecha` date DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(1) DEFAULT 0,
  `Pago_Iva` tinyint(1) DEFAULT 0,
  `Arreglo` tinyint(1) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(1) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(1) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` tinyint(4) DEFAULT 0,
  `Factura_Domicilio` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Nro_Factura`),
  KEY `Fecha` (`Fecha`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_comanda` (
  `Nro_Pedido` varchar(255) NOT NULL,
  `Fecha` varchar(10) NOT NULL DEFAULT '0',
  `Nro_Factura` varchar(50) NOT NULL DEFAULT '0',
  `Mesa` varchar(200) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Movil` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Nro_Pedido`,`Fecha`,`Nro_Factura`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_comanda_domicilios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_comanda_domicilios` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Mesa` varchar(200) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Nro_Mesas` int(11) DEFAULT 0,
  `Nro_Domicilios` int(11) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_comanda_domicilios_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_comanda_domicilios_cierres` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Mesa` varchar(200) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Nro_Mesas` int(11) DEFAULT 0,
  `Nro_Domicilios` int(11) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_comanda_historico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_comanda_historico` (
  `Nro_Pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(50) NOT NULL DEFAULT '0',
  `Mesa` varchar(200) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Mesa` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_comanda_historico_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_comanda_historico_cierres` (
  `Nro_Pedido` varchar(255) NOT NULL,
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(50) NOT NULL DEFAULT '0',
  `Mesa` varchar(200) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Mesa` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_comanda_parcial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_comanda_parcial` (
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Fecha` date DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Mesa` varchar(200) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Movil` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Nro_Pedido`),
  KEY `Nro_Pedido` (`Nro_Pedido`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_comanda_previo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_comanda_previo` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` date DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Mesa` varchar(200) DEFAULT NULL,
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` double DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Movil` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_comanda_restaurar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_comanda_restaurar` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` date DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Mesa` varchar(200) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Movil` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_comanda_test`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_comanda_test` (
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Fecha` date DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Mesa` varchar(200) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Movil` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Nro_Pedido`),
  KEY `Nro_Pedido` (`Nro_Pedido`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_combo_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_combo_producto` (
  `Id_Combo` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Valor_Plato_Combo` int(11) DEFAULT 0,
  `Cantidad` int(11) DEFAULT 0,
  PRIMARY KEY (`Id_Combo`,`Id_Plato`,`Item`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_combos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_combos` (
  `Id_Combo` int(11) NOT NULL AUTO_INCREMENT,
  `Id_Plato_Combo` int(11) DEFAULT 0,
  `Nombre` varchar(250) DEFAULT NULL,
  `Impresora_Combo` varchar(250) DEFAULT NULL,
  `Valor_Combo` double DEFAULT 0,
  `Activo` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Id_Combo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_configuracion_conexion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_configuracion_conexion` (
  `Id_Sede` int(11) DEFAULT 0,
  `Usar_MySql` tinyint(4) DEFAULT 0,
  `Ip_Publica` varchar(50) DEFAULT NULL,
  `Ip_Local` varchar(50) DEFAULT NULL,
  `Base_Datos_Principal` varchar(50) DEFAULT NULL,
  `Base_Datos_Reportes` varchar(50) DEFAULT NULL,
  `Base_Serv_Base` varchar(50) DEFAULT NULL,
  `Ip_Servidor` varchar(50) DEFAULT NULL,
  `Copia_Seguridad` tinyint(4) DEFAULT 0,
  `Ruta_Bases_Datos` varchar(200) DEFAULT NULL,
  `Ruta_Copia_Seguridad` varchar(200) DEFAULT NULL,
  `Base_Datos_Fiscal` varchar(200) DEFAULT NULL,
  `Hacer_Cierre_Fiscal` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_configuracion_facturacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_configuracion_facturacion` (
  `Id_Sede` int(11) DEFAULT 0,
  `Impuesto_Iva` double DEFAULT 0,
  `Impuesto_Impoconsumo` double DEFAULT 0,
  `Impuesto_Rete_Fuente` double DEFAULT 0,
  `Liquidar_Propina` tinyint(4) DEFAULT 0,
  `Resolucion_Propina` longtext DEFAULT NULL,
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Precios_Incluyen_Impuesto` tinyint(4) DEFAULT 0,
  `Imprimir_Logo_Factura` tinyint(4) DEFAULT 0,
  `Nombre_Logo_Factura` varchar(200) DEFAULT '0',
  `Tipo_Moneda` tinyint(1) DEFAULT 0,
  `Texto_Numeracion` varchar(100) DEFAULT '0',
  `Nombre_Cliente_Facturacion_Varia` varchar(100) DEFAULT '0',
  `Codigo_Cliente_Facturacion_Varia` varchar(100) DEFAULT '0',
  `Id_Cliente_Facturacion_Varia` double DEFAULT 0,
  `Usa_Lector_Barras` tinyint(4) DEFAULT 0,
  `Imprimir_Encabezado_Factura` tinyint(4) DEFAULT 0,
  `Impresora_Facturas` int(11) DEFAULT 0,
  `Mensaje_Factura` varchar(255) DEFAULT '0',
  `Longitud_Factura_Sistema` int(11) DEFAULT 0,
  `Longitud_Factura_Manual` int(11) DEFAULT 0,
  `Cantidad_Impresiones_Factura` int(11) DEFAULT 1,
  `Porcentaje_Propina` float DEFAULT 0,
  `Activar_Precio_x_Mayor` tinyint(4) DEFAULT 0,
  `Usar_Precuenta` tinyint(4) DEFAULT 0,
  `Imprimir_Resolucion_Propina` tinyint(4) DEFAULT 0,
  `Imprimir_Datos_Legales` tinyint(4) DEFAULT 0,
  `Imprimir_Datos_Cliente` tinyint(4) DEFAULT 0,
  `Imprimir_Recibo_Domiciliario` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_configuracion_sede`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_configuracion_sede` (
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Almacen` varchar(250) DEFAULT NULL,
  `Nombre_Autorizado` varchar(250) DEFAULT NULL,
  `Nit_Autorizado` varchar(250) DEFAULT NULL,
  `Razon_Social` varchar(255) DEFAULT NULL,
  `Direccion_Sede` varchar(255) DEFAULT NULL,
  `Mail_Uno` varchar(100) DEFAULT NULL,
  `Mail_Dos` varchar(100) DEFAULT NULL,
  `Nombre_Logo_Empresa` varchar(200) DEFAULT '0'
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_conteo_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_conteo_factura` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` date DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_cuadre_caja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_cuadre_caja` (
  `Id_Caja` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Fecha` date DEFAULT NULL,
  `Base` int(11) DEFAULT 0,
  `Venta_Total` int(11) DEFAULT 0,
  `Venta_Efectivo` int(11) DEFAULT 0,
  `Venta_Baucher` int(11) DEFAULT 0,
  `Propinas` int(11) DEFAULT 0,
  `Propinas_Extra` int(11) DEFAULT 0,
  `Gastos` int(11) DEFAULT 0,
  `Vales` int(11) DEFAULT 0,
  `Consumo_Jefes` int(11) DEFAULT 0,
  `Base_Final` int(11) DEFAULT 0,
  `F_Totales` int(11) DEFAULT 0,
  `F_Baucher` int(11) DEFAULT 0,
  `F_Copias` int(11) DEFAULT 0,
  `F_Anuladas` int(11) DEFAULT 0,
  `Factura_Inicio` varchar(50) DEFAULT '0',
  `Factura_Fin` varchar(50) DEFAULT '0',
  `Billetes` int(11) DEFAULT 0,
  `Monedas` int(11) DEFAULT 0,
  `Compras` int(11) DEFAULT 0,
  `Venta_Clientes` int(11) DEFAULT 0,
  `Cierre` tinyint(4) DEFAULT 0,
  `Pesos_Venta` int(11) DEFAULT 0,
  `Pesos_Tasa` int(11) DEFAULT 0,
  `pesos_Cambio` int(11) DEFAULT 0,
  `Tarjeta_Venta` int(11) DEFAULT 0,
  `Tarjeta_Tasa` int(11) DEFAULT 0,
  `Tarjeta_Cambio` int(11) DEFAULT 0,
  `Dolar_Venta` int(11) DEFAULT 0,
  `Dolar_Tasa` int(11) DEFAULT 0,
  `Dolar_Cambio` int(11) DEFAULT 0,
  `Euro_Venta` int(11) DEFAULT 0,
  `Euro_Tasa` int(11) DEFAULT 0,
  `Euro_Cambio` int(11) DEFAULT 0,
  `Venta_Coctel` int(11) DEFAULT 0,
  `Nro_Coctel` int(11) DEFAULT 0,
  `Porcentaje_Uno` int(11) DEFAULT 0,
  `Porcentaje_Dos` int(11) DEFAULT 0,
  `Factura_Inicio_Manual` varchar(50) DEFAULT NULL,
  `Factura_Fin_Manual` varchar(50) DEFAULT NULL,
  `Ingreso_Domicilio` double DEFAULT 0,
  `Egreso_Domicilio` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_cuadre_caja_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_cuadre_caja_cierres` (
  `Id_Caja` int(11) DEFAULT 0,
  `Nro_Caja` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Fecha` date DEFAULT NULL,
  `Base` int(11) DEFAULT 0,
  `Venta_Total` int(11) DEFAULT 0,
  `Venta_Efectivo` int(11) DEFAULT 0,
  `Venta_Baucher` int(11) DEFAULT 0,
  `Propinas` int(11) DEFAULT 0,
  `Propinas_Extra` int(11) DEFAULT 0,
  `Gastos` int(11) DEFAULT 0,
  `Vales` int(11) DEFAULT 0,
  `Consumo_Jefes` int(11) DEFAULT 0,
  `Base_Final` int(11) DEFAULT 0,
  `F_Totales` int(11) DEFAULT 0,
  `F_Baucher` int(11) DEFAULT 0,
  `F_Copias` int(11) DEFAULT 0,
  `F_Anuladas` int(11) DEFAULT 0,
  `Factura_Inicio` varchar(50) DEFAULT '0',
  `Factura_Fin` varchar(50) DEFAULT '0',
  `Billetes` int(11) DEFAULT 0,
  `Monedas` int(11) DEFAULT 0,
  `Compras` int(11) DEFAULT 0,
  `Venta_Clientes` int(11) DEFAULT 0,
  `Cierre` tinyint(4) DEFAULT 0,
  `Pesos_Venta` int(11) DEFAULT 0,
  `Pesos_Tasa` int(11) DEFAULT 0,
  `pesos_Cambio` int(11) DEFAULT 0,
  `Tarjeta_Venta` int(11) DEFAULT 0,
  `Tarjeta_Tasa` int(11) DEFAULT 0,
  `Tarjeta_Cambio` int(11) DEFAULT 0,
  `Dolar_Venta` int(11) DEFAULT 0,
  `Dolar_Tasa` int(11) DEFAULT 0,
  `Dolar_Cambio` int(11) DEFAULT 0,
  `Euro_Venta` int(11) DEFAULT 0,
  `Euro_Tasa` int(11) DEFAULT 0,
  `Euro_Cambio` int(11) DEFAULT 0,
  `Venta_Coctel` int(11) DEFAULT 0,
  `Nro_Coctel` int(11) DEFAULT 0,
  `Porcentaje_Uno` int(11) DEFAULT 0,
  `Porcentaje_Dos` int(11) DEFAULT 0,
  `Factura_Inicio_Manual` varchar(50) DEFAULT NULL,
  `Factura_Fin_Manual` varchar(50) DEFAULT NULL,
  `Ingreso_Domicilio` double DEFAULT 0,
  `Egreso_Domicilio` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_cumplimiento_mesero`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_cumplimiento_mesero` (
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Sede` varchar(100) DEFAULT NULL,
  `Nombre_Jefatura` varchar(100) DEFAULT NULL,
  `Nombre_Mesero` varchar(100) DEFAULT NULL,
  `Tipo_Empleado` int(11) DEFAULT 0,
  `Cod_Empleado` int(11) DEFAULT 0,
  `Fecha` date DEFAULT NULL,
  `Turno` int(11) DEFAULT 0,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Mesa` varchar(50) DEFAULT NULL,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Cod_Categoria` int(11) DEFAULT 0,
  `Categoria` varchar(50) DEFAULT NULL,
  `Cantidad_Vendida` double DEFAULT 0,
  `Cumplio` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_cumplimiento_mesero_resumen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_cumplimiento_mesero_resumen` (
  `Id_Consecutivo` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Sede` varchar(100) DEFAULT NULL,
  `Fecha` date DEFAULT NULL,
  `Cargo` varchar(100) DEFAULT NULL,
  `Nombre_Empleado` varchar(100) DEFAULT NULL,
  `Turno` int(11) DEFAULT 0,
  `Nro_Registros` int(11) DEFAULT 0,
  `Nro_Platos` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Cod_Categoria` int(11) DEFAULT 0,
  `Categoria` varchar(50) DEFAULT NULL,
  `Cantidad_Bebidas` double DEFAULT 0,
  `Cumplio_Bebidas` tinyint(4) DEFAULT 0,
  `Cantidad_Entradas` double DEFAULT 0,
  `Cumplio_Entradas` tinyint(4) DEFAULT 0,
  `Cantidad_Postres` double DEFAULT 0,
  `Cumplio_Postres` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_datos_grafica_presupuesto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_datos_grafica_presupuesto` (
  `Id_Sede` varchar(100) NOT NULL DEFAULT '0',
  `Mes` varchar(50) DEFAULT NULL,
  `Año` int(11) DEFAULT 0,
  `Venta_Referencia` double DEFAULT 0,
  `Venta_Presupuesto` double DEFAULT 0,
  `Venta_Actual` double DEFAULT 0,
  `Venta_Esperada_Mes` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_datos_grafica_presupuesto_mes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_datos_grafica_presupuesto_mes` (
  `Id_Sede` varchar(100) NOT NULL DEFAULT '0',
  `Mes` varchar(50) DEFAULT NULL,
  `Año` int(11) DEFAULT 0,
  `Dia` varchar(50) DEFAULT '0',
  `Venta_Referencia` double DEFAULT 0,
  `Venta_Presupuesto` double DEFAULT 0,
  `Venta_Actual` double DEFAULT 0,
  `Venta_Esperada_Mes` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_descuentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_descuentos` (
  `Id_Descuento` bigint(20) NOT NULL DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Prefix` varchar(50) DEFAULT NULL,
  `Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Id_Tipificacion` int(11) DEFAULT 0,
  `Valor_Original_Producto` double DEFAULT 0,
  `Valor_Venta_Producto` double DEFAULT 0,
  `Valor_Base` double DEFAULT 0,
  `Valor_Impuesto` double DEFAULT 0,
  `Valor_Descuento_Pesos` double DEFAULT 0,
  `Porcentaje` float DEFAULT 0,
  `Motivo` varchar(255) DEFAULT NULL,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_descuentos_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_descuentos_cierres` (
  `Id_Descuento` bigint(20) NOT NULL DEFAULT 0,
  `Factura` varchar(50) DEFAULT NULL,
  `Nro_Pedido` varchar(200) DEFAULT NULL,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Valor_Descuento` double DEFAULT 0,
  `Id_Tipificacion` int(11) DEFAULT 0,
  `Id_Clasificacion` int(11) DEFAULT 0,
  `Motivo` varchar(255) DEFAULT NULL,
  `Id_Cliente` bigint(20) DEFAULT 0,
  `Telefono` varchar(50) DEFAULT NULL,
  `Email` varchar(50) DEFAULT NULL,
  `Descuento_Factura` tinyint(4) DEFAULT 0,
  `Descuento_Plato` tinyint(4) DEFAULT 0,
  `Porcentaje` decimal(10,0) DEFAULT 0,
  `Fecha` date DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_descuentos_pagos_creditos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_descuentos_pagos_creditos` (
  `Nro_Pago` bigint(20) NOT NULL DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Nro_Credito` varchar(50) DEFAULT NULL,
  `Id_Tipificacion_Descuento` int(11) DEFAULT 1,
  `Valor_Descuento` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_descuentos_reporte`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_descuentos_reporte` (
  `Id_Descuento` bigint(20) NOT NULL DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Prefix` varchar(50) DEFAULT NULL,
  `Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Id_Tipificacion` int(11) DEFAULT 0,
  `Valor_Original_Producto` double DEFAULT 0,
  `Valor_Venta_Producto` double DEFAULT 0,
  `Valor_Base` double DEFAULT 0,
  `Valor_Impuesto` double DEFAULT 0,
  `Valor_Descuento_Pesos` double DEFAULT 0,
  `Porcentaje` float DEFAULT 0,
  `Motivo` varchar(255) DEFAULT NULL,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_comanda` (
  `Nro_pedido` varchar(255) NOT NULL DEFAULT '0',
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(100) DEFAULT '0',
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float NOT NULL DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` text DEFAULT NULL,
  `Salio` tinyint(1) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` decimal(10,0) DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` varchar(50) NOT NULL DEFAULT '0',
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT NULL,
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL,
  PRIMARY KEY (`Nro_pedido`,`Fecha`,`Id_Plato`,`Item`,`Depende`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_comanda_historico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_comanda_historico` (
  `Nro_pedido` varchar(255) NOT NULL DEFAULT '0',
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(100) DEFAULT '0',
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float NOT NULL DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` text DEFAULT NULL,
  `Salio` tinyint(1) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` float DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` varchar(50) NOT NULL DEFAULT '0',
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT '0',
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_comanda_parcial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_comanda_parcial` (
  `Nro_pedido` varchar(255) NOT NULL DEFAULT '0',
  `Fecha` date NOT NULL,
  `Nro_Factura` varchar(100) DEFAULT '0',
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float NOT NULL DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` text DEFAULT NULL,
  `Salio` tinyint(1) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` float DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` varchar(50) NOT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 1,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT '0',
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL,
  PRIMARY KEY (`Nro_pedido`,`Fecha`,`Id_Plato`,`Item`,`Depende`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_comanda_previo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_comanda_previo` (
  `Nro_pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` float DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` varchar(50) DEFAULT NULL,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT NULL,
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_comanda_reserva`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_comanda_reserva` (
  `Nro_pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float NOT NULL DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` text DEFAULT NULL,
  `Salio` tinyint(1) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` float DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(1) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT NULL,
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL,
  KEY `Fecha` (`Fecha`),
  KEY `Id_Plato` (`Id_Plato`),
  KEY `Item` (`Item`),
  KEY `Nro_pedido` (`Nro_pedido`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_comanda_restaurar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_comanda_restaurar` (
  `Nro_pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float NOT NULL DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` text DEFAULT NULL,
  `Salio` tinyint(1) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` float DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(1) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT NULL,
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL,
  KEY `Fecha` (`Fecha`),
  KEY `Id_Plato` (`Id_Plato`),
  KEY `Item` (`Item`),
  KEY `Nro_pedido` (`Nro_pedido`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_comanda_test`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_comanda_test` (
  `Nro_pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float NOT NULL DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` text DEFAULT NULL,
  `Salio` tinyint(1) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` float DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT '0',
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL,
  KEY `Fecha` (`Fecha`),
  KEY `Id_Plato` (`Id_Plato`),
  KEY `Item` (`Item`),
  KEY `Nro_pedido` (`Nro_pedido`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_factura` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Valor_Plato` int(11) DEFAULT 0,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_factura_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_factura_cierres` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Valor_Plato` int(11) DEFAULT 0,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_factura_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_factura_compra` (
  `Id_Registro` varchar(50) NOT NULL DEFAULT '0',
  `Item` int(11) NOT NULL DEFAULT 0,
  `Tipo_Documento` int(11) NOT NULL DEFAULT 0,
  `Nombre_Producto` varchar(100) DEFAULT NULL,
  `Id_Und_Compra` int(11) NOT NULL DEFAULT 0,
  `Valor_Unitario` double DEFAULT 0,
  `Cantidad` double DEFAULT 0,
  `Valor_Total` double DEFAULT 0,
  `Impuesto` double DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Id_Registro`,`Item`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_plato_costeo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_plato_costeo` (
  `Id_Plato` int(11) DEFAULT 0,
  `Nombre` varchar(255) DEFAULT NULL,
  `Precio_Carta` float DEFAULT 0,
  `ImpoConsumo` float DEFAULT 0,
  `Precio_Base` float DEFAULT 0,
  `Costo_Insumos` float DEFAULT 0,
  `Variacion` float DEFAULT 0,
  `Tarjeta_Credito` float DEFAULT 0,
  `Precio_Venta` float DEFAULT 0,
  `Margen_Pesos` float DEFAULT 0,
  `Margen_Porcen` float DEFAULT 0,
  `Ventas` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_preparacion_porciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_preparacion_porciones` (
  `Id_Preparacion` int(11) NOT NULL DEFAULT 0,
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Costo_Preparacion` float DEFAULT 0,
  `Unidad_Minima` float DEFAULT 0,
  `Descripcion` varchar(150) DEFAULT NULL,
  `Agrupar` int(11) DEFAULT 0,
  PRIMARY KEY (`Id_Preparacion`,`Id_Grupo`,`Id_Item`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_detalle_seleccion_productos_almuerzos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_detalle_seleccion_productos_almuerzos` (
  `Id_Seleccion` int(11) NOT NULL DEFAULT 0,
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad_Armar` float DEFAULT 0,
  `Id_Grupo_Quitar` int(11) NOT NULL DEFAULT 0,
  `Id_Item_Quitar` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Seleccion`,`Id_Grupo`,`Id_Item`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_domi_almuerzos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_domi_almuerzos` (
  `Cantidad` int(11) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Fecha` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_domi_diurno`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_domi_diurno` (
  `Cantidad` int(11) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Fecha` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_domi_mensajero`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_domi_mensajero` (
  `Cantidad` int(11) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Fecha` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_empleados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_empleados` (
  `cod_empleado` int(11) NOT NULL DEFAULT 0,
  `nombres` varchar(50) DEFAULT NULL,
  `telefonos` varchar(50) DEFAULT NULL,
  `direccion` varchar(50) DEFAULT NULL,
  `login` varchar(50) DEFAULT NULL,
  `clave` varchar(50) DEFAULT NULL,
  `estado` tinyint(4) DEFAULT 0,
  `tipo_empleado` int(11) DEFAULT 0,
  `Skin_Personal` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`cod_empleado`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_empresas_domiciliarias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_empresas_domiciliarias` (
  `Id_Empresa` int(11) DEFAULT 0,
  `Nombre_Empresa` varchar(50) DEFAULT NULL,
  `Id_Forma_Pago` int(11) DEFAULT 0,
  `Activa` tinyint(4) DEFAULT 0,
  `Cobrar_Domicilio` tinyint(4) DEFAULT 0,
  `Liquidar_Propina` tinyint(4) DEFAULT 0,
  `Valor_Domicilio` int(11) DEFAULT 0,
  `Porcentaje_Comision` decimal(10,0) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_factura` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` varchar(50) DEFAULT NULL,
  `Factura_Domicilio` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_factura_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_factura_cierres` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` varchar(50) DEFAULT NULL,
  `Factura_Domicilio` tinyint(4) DEFAULT 0,
  `Nro_Caja` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_factura_domicilio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_factura_domicilio` (
  `Nro_Factura` varchar(100) NOT NULL DEFAULT '0',
  `Valor` double NOT NULL DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Vendedor` int(11) NOT NULL DEFAULT 0,
  `Id_Cliente` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_factura_domicilio_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_factura_domicilio_cierres` (
  `Nro_Factura` varchar(100) NOT NULL DEFAULT '0',
  `Valor` double NOT NULL DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Vendedor` int(11) NOT NULL DEFAULT 0,
  `Id_Cliente` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_factura_forma_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_factura_forma_pago` (
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Forma_Pago` int(11) NOT NULL DEFAULT 0,
  `Id_Tarjeta` int(11) NOT NULL DEFAULT 0,
  `Nro_Factura` varchar(100) NOT NULL DEFAULT '0',
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Valor` double DEFAULT 0,
  `Porcentaje` float DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Fecha` varchar(255) DEFAULT NULL,
  `Valor_Domicilio` double DEFAULT 0,
  `Id_Bono` int(11) NOT NULL DEFAULT 0,
  `Prefix` varchar(50) DEFAULT NULL,
  `Fac_PE` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_factura_forma_pago_cambio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_factura_forma_pago_cambio` (
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Forma_Pago` int(11) NOT NULL DEFAULT 0,
  `Id_Tarjeta` int(11) NOT NULL DEFAULT 0,
  `Nro_Factura` varchar(100) NOT NULL DEFAULT '0',
  `Nro_Pedido` varchar(100) NOT NULL DEFAULT '0',
  `Valor` double DEFAULT 0,
  `Porcentaje` float DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Fecha` varchar(255) DEFAULT NULL,
  `Valor_Domicilio` double DEFAULT 0,
  `Id_Bono` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Item`,`Id_Forma_Pago`,`Id_Tarjeta`,`Nro_Factura`,`Nro_Pedido`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_factura_previo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_factura_previo` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` date DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` varchar(255) DEFAULT '0',
  `Factura_Domicilio` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_factura_previo_domicilios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_factura_previo_domicilios` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` varchar(255) DEFAULT '0',
  `Factura_Domicilio` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_facturas_caja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_facturas_caja` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` varchar(50) DEFAULT '0',
  `Factura_Domicilio` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_facturas_caja_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_facturas_caja_cierres` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` varchar(50) DEFAULT '0',
  `Factura_Domicilio` tinyint(4) DEFAULT 0,
  `Nro_Caja` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_facturas_categorias_platos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_facturas_categorias_platos` (
  `cod_categoria` int(11) DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Valor_Total` double DEFAULT 0,
  `Cuenta` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_facturas_categorias_platos_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_facturas_categorias_platos_cierres` (
  `cod_categoria` int(11) DEFAULT 0,
  `Nro_Caja` int(11) DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Valor_Total` double DEFAULT 0,
  `Cuenta` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_facturas_grupo_platos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_facturas_grupo_platos` (
  `cod_categoria` int(11) DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Valor_Total` double DEFAULT 0,
  `Cuenta` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_facturas_grupo_platos_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_facturas_grupo_platos_cierres` (
  `cod_categoria` int(11) DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Valor_Total` double DEFAULT 0,
  `Cuenta` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_facturas_impresion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_facturas_impresion` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(255) DEFAULT NULL,
  `Hora_Texto` varchar(255) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` varchar(50) DEFAULT '0',
  `Factura_Domicilio` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=COMPACT;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_facturas_ventana`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_facturas_ventana` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Almacen` varchar(255) DEFAULT NULL,
  `Origen` varchar(150) DEFAULT NULL,
  `Factura_Domicilio` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_facturas_ventana_cierres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_facturas_ventana_cierres` (
  `Nro_Caja` int(11) NOT NULL DEFAULT 0,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Almacen` varchar(255) DEFAULT NULL,
  `Origen` varchar(150) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_forma_medida`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_forma_medida` (
  `Id_Forma_Medida` int(11) DEFAULT 0,
  `Descripcion` varchar(50) DEFAULT NULL,
  `Activa` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_forma_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_forma_pago` (
  `Id_Forma_Pago` int(11) NOT NULL DEFAULT 0,
  `Descripcion_Forma_Pago` varchar(50) NOT NULL,
  `Validar` tinyint(4) DEFAULT 0,
  `Activo` tinyint(4) DEFAULT 0,
  `Seleccionar_Tarjeta` tinyint(4) DEFAULT 0,
  `Valor` double DEFAULT 0,
  `Pedir_Observacion` tinyint(4) DEFAULT 0,
  `Pedir_Cliente` tinyint(4) DEFAULT 0,
  `Suma_Efectivo` tinyint(4) DEFAULT 0,
  `Validar_Numero` tinyint(4) DEFAULT 0,
  `Forma_Pago_Default` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_formato_impresion_clientes_factura_manual`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_formato_impresion_clientes_factura_manual` (
  `Id_Cliente` int(11) NOT NULL DEFAULT 0,
  `cedula` varchar(50) DEFAULT NULL,
  `nombres` varchar(50) DEFAULT NULL,
  `Apellidos` varchar(50) DEFAULT NULL,
  `direccion` varchar(50) DEFAULT NULL,
  `telefono` varchar(250) DEFAULT NULL,
  `Barrio` varchar(50) DEFAULT NULL,
  `Mail` varchar(50) DEFAULT NULL,
  `Dia_Cumple` int(11) DEFAULT 0,
  `Mes_Cumple` int(11) DEFAULT 0,
  `Edad` int(11) DEFAULT 0,
  `Ocupacion` varchar(50) DEFAULT NULL,
  `Porc_Descuento` int(11) DEFAULT 0,
  `Observaciones` varchar(255) DEFAULT NULL,
  `Fecha_Aniversario` varchar(50) DEFAULT NULL,
  `Fecha_Grado` varchar(50) DEFAULT NULL,
  `Empresa` varchar(150) DEFAULT NULL,
  `Id_Klob` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Tarjeta_Fiel` tinyint(4) DEFAULT 0,
  `Cod_Barrio` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Referencia` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id_Cliente`),
  KEY `cedula` (`cedula`),
  KEY `Apellidos` (`Apellidos`),
  KEY `nombres` (`nombres`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_formato_impresion_detalle_factura_manual`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_formato_impresion_detalle_factura_manual` (
  `Nro_pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Descripcion` varchar(50) DEFAULT NULL,
  `Cantidad` int(11) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` varchar(50) DEFAULT NULL,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_formato_impresion_factura_manual`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_formato_impresion_factura_manual` (
  `Nro_Factura` varchar(50) NOT NULL DEFAULT '0',
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(1) DEFAULT 0,
  `Arreglo` tinyint(1) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(1) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(1) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` tinyint(4) DEFAULT 0,
  `Factura_Domicilio` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Nro_Factura`),
  KEY `Id_Resolucion` (`Id_Resolucion`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_historico_inventario_actual_porciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_historico_inventario_actual_porciones` (
  `Id_Historico` int(11) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Codigo_Insumo` varchar(100) DEFAULT NULL,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Und_Compra` int(11) DEFAULT 0,
  `Valor_Und_Compra` float DEFAULT 0,
  `Und_Min_Utilizadas` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Compras` tinyint(4) DEFAULT 0,
  `Controlar` tinyint(4) DEFAULT 0,
  `Opcion_Cambios` tinyint(4) DEFAULT 0,
  `Und_Uso` int(11) DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Cantidad_Actual` float DEFAULT 0,
  `Cod_empleado` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Insumo_Cp` tinyint(4) DEFAULT 0,
  `Fecha_Vence` varchar(50) DEFAULT NULL,
  `Stock_MInimo` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_historico_movimientos_pedidos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_historico_movimientos_pedidos` (
  `Id_Movto` int(11) NOT NULL DEFAULT 0,
  `Fecha_Facturacion` varchar(50) DEFAULT NULL,
  `Fecha_Pc` varchar(50) DEFAULT NULL,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Cantidad` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Hora_Texto` varchar(255) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Pc_Programa_Form` varchar(255) DEFAULT NULL,
  `Tipo` int(11) DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Operacion_Realizada` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_imagenes_intro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_imagenes_intro` (
  `Cod_Imagen` int(11) NOT NULL DEFAULT 0,
  `Nombre_Imagen` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_impresion_recetas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_impresion_recetas` (
  `Nombre_Razon_Social` varchar(255) NOT NULL DEFAULT '0',
  `Id_Preparacion` int(10) unsigned NOT NULL DEFAULT 0,
  `Nombre_Categoria` varchar(255) DEFAULT NULL,
  `Nombre_Preparacion` varchar(255) DEFAULT NULL,
  `Valor` float NOT NULL DEFAULT 0,
  `Nombre_Insumo` varchar(255) DEFAULT NULL,
  `Nombre_Presentacion` varchar(255) DEFAULT NULL,
  `Cantidad` double NOT NULL DEFAULT 0,
  `Costo` double NOT NULL DEFAULT 0,
  `Total_Costo` double NOT NULL DEFAULT 0,
  `Codigo_Producto` varchar(100) DEFAULT NULL,
  `Stock_Minimo` double NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_impresion_tirilla_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_impresion_tirilla_comanda` (
  `Nro_pedido` varchar(255) DEFAULT '0',
  `Mesero` varchar(255) DEFAULT '0',
  `Fecha` date DEFAULT NULL,
  `Nro_Mesa` varchar(255) DEFAULT '0',
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Novedad` varchar(255) DEFAULT NULL,
  `Impreso` tinyint(1) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT '0',
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Nuevo` tinyint(4) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Enviado_Desde` varchar(255) DEFAULT NULL,
  `Hora_Impresion` varchar(255) DEFAULT NULL,
  `Hora_Plato` varchar(255) DEFAULT NULL,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Depende` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_impresoras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_impresoras` (
  `Id_Impresora` int(11) NOT NULL DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_impuestos_pedido`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_impuestos_pedido` (
  `Id_Registro` int(11) NOT NULL DEFAULT 0,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Detalle_Impuesto` varchar(50) DEFAULT NULL,
  `Impuesto` decimal(10,1) DEFAULT 0.0,
  `Valor_Base` decimal(10,1) DEFAULT 0.0,
  `Valor_Impuesto` decimal(10,1) DEFAULT 0.0,
  `Total_Plato` decimal(10,1) DEFAULT 0.0,
  `Pagar` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_indicador_presupuesto_jefaturas_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_indicador_presupuesto_jefaturas_detalle` (
  `cod_empleado` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Sede` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Turno` int(11) DEFAULT 0,
  `Venta_Esperada_T1` double DEFAULT 0,
  `Venta_Actual_T1` double DEFAULT 0,
  `Cumplio_T1` int(11) DEFAULT 0,
  `Venta_Esperada_T2` double DEFAULT 0,
  `Venta_Actual_T2` double DEFAULT 0,
  `Cumplio_T2` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_indicador_presupuesto_jefaturas_encabezado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_indicador_presupuesto_jefaturas_encabezado` (
  `cod_empleado` int(11) DEFAULT 0,
  `nombres` varchar(50) DEFAULT NULL,
  `Nro_Turnos` int(11) DEFAULT 0,
  `Nro_Verde` int(11) DEFAULT 0,
  `Nro_Rojo` int(11) DEFAULT 0,
  `Nro_Amarillo` int(11) DEFAULT 0,
  `Venta_Esperada` double DEFAULT 0,
  `Venta_Actual` double DEFAULT 0,
  `Porcentaje_Cumplio` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_indicador_visitas_admon_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_indicador_visitas_admon_detalle` (
  `Id_Registro` int(11) NOT NULL DEFAULT 0,
  `Id_Sede` int(11) NOT NULL DEFAULT 0,
  `Informe_Admon` tinyint(4) DEFAULT 0,
  `Fecha_Registro` varchar(50) DEFAULT NULL,
  `Fecha_Visita` varchar(50) DEFAULT NULL,
  `Reporte_Admon` longtext DEFAULT NULL,
  `Administrativo` varchar(50) DEFAULT '0',
  `Reporte_Jefatura` varchar(100) DEFAULT NULL,
  `Usuario` varchar(100) DEFAULT NULL,
  `Hora_Registro` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_indicador_visitas_admon_encabezado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_indicador_visitas_admon_encabezado` (
  `Administrativo` varchar(50) DEFAULT NULL,
  `Nombre_Sede` varchar(100) DEFAULT '0',
  `Id_Sede` int(11) DEFAULT 0,
  `Nro_Visitas` int(11) DEFAULT 0,
  `Porcentaje_Cumplio` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_informacion_exogena`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_informacion_exogena` (
  `Nro_Registro` int(11) DEFAULT 0,
  `Nombre_Reporte` varchar(255) DEFAULT NULL,
  `fecha_Impresion` varchar(50) DEFAULT NULL,
  `Mes` int(11) DEFAULT 0,
  `Ano` int(11) DEFAULT 0,
  `Dia` int(11) DEFAULT 0,
  `nro_contrato` varchar(15) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nombres` varchar(255) DEFAULT '0',
  `Cedula` varchar(200) DEFAULT NULL,
  `Telefono` varchar(200) DEFAULT NULL,
  `Direccion` varchar(200) DEFAULT NULL,
  `Categoria` varchar(200) DEFAULT NULL,
  `Detalle` mediumtext DEFAULT NULL,
  `Forma_Pago` varchar(200) DEFAULT NULL,
  `Cantidad` double DEFAULT 0,
  `Impuesto_Porcentaje` double DEFAULT 0,
  `Base` double DEFAULT 0,
  `Impuesto_Pesos` double DEFAULT 0,
  `Valor_Total` double DEFAULT 0,
  `Costo` double DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Propina` double DEFAULT 0,
  `Vendedor` varchar(255) DEFAULT NULL,
  `Domiciliario` varchar(255) DEFAULT NULL,
  `Valor_domicilio` double DEFAULT 0,
  `Observacion_Factura` mediumtext DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_insumo_forma_medida`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_insumo_forma_medida` (
  `Descripcion` varchar(255) NOT NULL DEFAULT '0',
  `Id_Insumo` int(11) NOT NULL DEFAULT 0,
  `Id_Forma_Medida` int(11) NOT NULL DEFAULT 0,
  `Cant_Unidades_Minimas` float NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Insumo`,`Id_Forma_Medida`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_insumo_proveedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_insumo_proveedor` (
  `Id_Proveedor` int(11) NOT NULL DEFAULT 0,
  `Id_Insumo` int(11) NOT NULL DEFAULT 0,
  `Fecha_Inicial_Negociacion` varchar(50) NOT NULL DEFAULT '0',
  `Fecha_Final_Negociacion` varchar(50) DEFAULT NULL,
  `Precio_Pactado` int(11) NOT NULL DEFAULT 0,
  `Id_Forma_Medida` int(11) DEFAULT 0,
  `Nombre_Forma_Medida` varchar(50) DEFAULT NULL,
  `Observacion` longtext DEFAULT NULL,
  PRIMARY KEY (`Id_Proveedor`,`Id_Insumo`,`Fecha_Inicial_Negociacion`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_insumos_forma_medida`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_insumos_forma_medida` (
  `Id_Insumo` int(11) NOT NULL DEFAULT 0,
  `Id_Forma_Medida` int(11) NOT NULL DEFAULT 0,
  `Cant_Unidades_Minimas` float NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Forma_Medida`,`Id_Insumo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_actual_porciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_actual_porciones` (
  `Id_Grupo` int(11) DEFAULT 0,
  `Codigo_Insumo` varchar(100) DEFAULT NULL,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Und_Compra` int(11) DEFAULT 0,
  `Valor_Und_Compra` float DEFAULT 0,
  `Und_Min_Utilizadas` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Compras` tinyint(4) DEFAULT 0,
  `Controlar` tinyint(4) DEFAULT 0,
  `Opcion_Cambios` tinyint(4) DEFAULT 0,
  `Und_Uso` int(11) DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Cantidad_Actual` float DEFAULT 0,
  `Bodega` tinyint(4) DEFAULT 0,
  `Insumo_Cp` tinyint(4) DEFAULT 0,
  `Fecha_Vence` varchar(50) DEFAULT NULL,
  `Stock_MInimo` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_actual_porciones_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_actual_porciones_categoria` (
  `Id_Grupo` int(11) DEFAULT 0,
  `Codigo_Insumo` varchar(100) DEFAULT NULL,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Und_Compra` int(11) DEFAULT 0,
  `Valor_Und_Compra` float DEFAULT 0,
  `Und_Min_Utilizadas` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Compras` tinyint(4) DEFAULT 0,
  `Controlar` tinyint(4) DEFAULT 0,
  `Opcion_Cambios` tinyint(4) DEFAULT 0,
  `Und_Uso` int(11) DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Cantidad_Actual` float DEFAULT 0,
  `Bodega` tinyint(4) DEFAULT 0,
  `Insumo_Cp` tinyint(4) DEFAULT 0,
  `Fecha_Vence` varchar(50) DEFAULT NULL,
  `Stock_MInimo` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_porcion_costo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_porcion_costo` (
  `Cod_Categoria` int(11) DEFAULT 0,
  `Categoria_Plato` int(11) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad_Comanda` float DEFAULT 0,
  `Cantidad_Insumo` float DEFAULT 0,
  `Costo` float DEFAULT 0,
  `Valor_Venta` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_porcion_plato`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_porcion_plato` (
  `Id_Plato` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Unidad_Minima` float DEFAULT 0,
  `Porciones_A_Desccontar` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Opcion_Cambiar` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_porcion_plato_impresion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_porcion_plato_impresion` (
  `Id_Plato` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Unidad_Minima` float DEFAULT 0,
  `Porciones_A_Desccontar` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Opcion_Cambiar` tinyint(4) DEFAULT 0,
  `Des_Unidad` varchar(255) DEFAULT '0',
  `Total_Costo` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_porciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_porciones` (
  `Codigo_Insumo` varchar(100) DEFAULT NULL,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Und_Compra` int(11) DEFAULT 0,
  `Valor_Und_Compra` float DEFAULT 0,
  `Und_Min_Utilizadas` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Compras` tinyint(4) DEFAULT 0,
  `Controlar` tinyint(4) DEFAULT 0,
  `Opcion_Cambios` tinyint(4) DEFAULT 0,
  `Und_Uso` int(11) DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Tipo_Und_Minima` varchar(100) DEFAULT NULL,
  `Cant_Und_Minimas` int(11) DEFAULT 0,
  `Bodega` int(11) DEFAULT 0,
  `Producto_Preparado` tinyint(4) DEFAULT 0,
  `Id_preparacion` int(11) DEFAULT 0,
  `Preparado_En_Sede` tinyint(4) DEFAULT 0,
  `Descargar_En_Venta` tinyint(4) DEFAULT 0,
  `Armar_Plato` tinyint(4) DEFAULT 0,
  `Cantidad_Armar` float DEFAULT 0,
  `Id_Insumo` int(11) DEFAULT 0,
  `Insumo_Cp` tinyint(4) DEFAULT 0,
  `Porcentaje_Merma` double DEFAULT 0,
  `Marca_Referencia` varchar(255) DEFAULT '0',
  `Fecha_Vence` varchar(50) DEFAULT NULL,
  `Stock_MInimo` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_porciones_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_porciones_categoria` (
  `Cod_Categoria` int(11) DEFAULT 0,
  `Id_Plato` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_porciones_categoria_plato`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_porciones_categoria_plato` (
  `Cod_Categoria` int(11) DEFAULT 0,
  `Id_Plato` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_porciones_listados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_porciones_listados` (
  `Codigo_Insumo` varchar(100) DEFAULT NULL,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(50) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Und_Compra` int(11) DEFAULT 0,
  `Valor_Und_Compra` float DEFAULT 0,
  `Und_Min_Utilizadas` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Compras` tinyint(4) DEFAULT 0,
  `Controlar` tinyint(4) DEFAULT 0,
  `Opcion_Cambios` tinyint(4) DEFAULT 0,
  `Und_Uso` int(11) DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Tipo_Und_Minima` varchar(100) DEFAULT NULL,
  `Cant_Und_Minimas` int(11) DEFAULT 0,
  `Bodega` int(11) DEFAULT 0,
  `Producto_Preparado` tinyint(4) DEFAULT 0,
  `Id_preparacion` int(11) DEFAULT 0,
  `Preparado_En_Sede` tinyint(4) DEFAULT 0,
  `Descargar_En_Venta` tinyint(4) DEFAULT 0,
  `Armar_Plato` tinyint(4) DEFAULT 0,
  `Cantidad_Armar` float DEFAULT 0,
  `Id_Insumo` int(11) DEFAULT 0,
  `Insumo_Cp` tinyint(4) DEFAULT 0,
  `Porcentaje_Merma` double DEFAULT 0,
  `Marca_Referencia` varchar(255) DEFAULT '0',
  `Fecha_Vence` varchar(50) DEFAULT NULL,
  `Stock_MInimo` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_porciones_listas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_porciones_listas` (
  `Codigo_Insumo` varchar(100) DEFAULT NULL,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(50) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Und_Compra` int(11) DEFAULT 0,
  `Valor_Und_Compra` float DEFAULT 0,
  `Und_Min_Utilizadas` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Compras` tinyint(4) DEFAULT 0,
  `Controlar` tinyint(4) DEFAULT 0,
  `Opcion_Cambios` tinyint(4) DEFAULT 0,
  `Und_Uso` int(11) DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Tipo_Und_Minima` varchar(100) DEFAULT NULL,
  `Cant_Und_Minimas` int(11) DEFAULT 0,
  `Bodega` int(11) DEFAULT 0,
  `Producto_Preparado` tinyint(4) DEFAULT 0,
  `Id_preparacion` int(11) DEFAULT 0,
  `Preparado_En_Sede` tinyint(4) DEFAULT 0,
  `Descargar_En_Venta` tinyint(4) DEFAULT 0,
  `Armar_Plato` tinyint(4) DEFAULT 0,
  `Cantidad_Armar` float DEFAULT 0,
  `Id_Insumo` int(11) DEFAULT 0,
  `Insumo_Cp` tinyint(4) DEFAULT 0,
  `Porcentaje_Merma` double DEFAULT 0,
  `Marca_Referencia` varchar(255) DEFAULT NULL,
  `Fecha_Vence` varchar(50) DEFAULT NULL,
  `Stock_MInimo` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_porciones_plato`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_porciones_plato` (
  `Id_Plato` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Unidad_Minima` float DEFAULT 0,
  `Porciones_A_Desccontar` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Opcion_Cambiar` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventario_porciones_precios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventario_porciones_precios` (
  `Id_Registro` int(11) NOT NULL DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Fecha_Registro` varchar(50) DEFAULT NULL,
  `Precio_Anterior` int(11) DEFAULT 0,
  `Precio_Actual` int(11) DEFAULT 0,
  `Id_Presentacion` int(11) DEFAULT 0,
  `Id_Proveedor` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id_Registro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventarios_entradas_manuales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventarios_entradas_manuales` (
  `Id_Entrada` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Producto` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Turno` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Nombre_Usuario` varchar(100) DEFAULT NULL,
  `Usuario` varchar(50) DEFAULT NULL,
  `Hora` varchar(50) DEFAULT NULL,
  `Observacion` varchar(255) DEFAULT NULL,
  `Autorizada` bigint(20) DEFAULT NULL,
  `Revisada` tinyint(4) DEFAULT 0,
  `Cobrar` tinyint(4) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Codigo_Motivo` int(11) DEFAULT 0,
  `Id_Preparacion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Codigo_Insumo` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventarios_fisicos_manuales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventarios_fisicos_manuales` (
  `Id_Fisico` int(11) NOT NULL DEFAULT 0,
  `Posicion` int(11) NOT NULL DEFAULT 0,
  `Id_Novedad` int(11) DEFAULT 0,
  `Nombre_Novedad` varchar(100) DEFAULT NULL,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Producto` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Turno` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Nombre_Usuario` varchar(100) DEFAULT NULL,
  `Usuario` varchar(50) DEFAULT NULL,
  `Hora` varchar(50) DEFAULT NULL,
  `Observacion` varchar(255) DEFAULT NULL,
  `Autorizada` bigint(20) DEFAULT NULL,
  `Revisada` tinyint(4) DEFAULT 0,
  `Cobrar` int(11) NOT NULL DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Codigo_Motivo` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Codigo_Insumo` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`Id_Fisico`,`Posicion`,`Cobrar`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventarios_porciones_mes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventarios_porciones_mes` (
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Costo` float DEFAULT 0,
  `Und_Compra` int(11) DEFAULT 0,
  `Valor_Und_Compra` float DEFAULT 0,
  `Und_Min_Utilizadas` float DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Compras` tinyint(4) DEFAULT 0,
  `Controlar` tinyint(4) DEFAULT 0,
  `Opcion_Cambios` tinyint(4) DEFAULT 0,
  `Dia_1` float DEFAULT 0,
  `Dia_2` float DEFAULT 0,
  `Dia_3` float DEFAULT 0,
  `Dia_4` float DEFAULT 0,
  `Dia_5` float DEFAULT 0,
  `Dia_6` float DEFAULT 0,
  `Dia_7` float DEFAULT 0,
  `Dia_8` float DEFAULT 0,
  `Dia_9` float DEFAULT 0,
  `Dia_10` float DEFAULT 0,
  `Dia_11` float DEFAULT 0,
  `Dia_12` float DEFAULT 0,
  `Dia_13` float DEFAULT 0,
  `Dia_14` float DEFAULT 0,
  `Dia_15` float DEFAULT 0,
  `Dia_16` float DEFAULT 0,
  `Dia_17` float DEFAULT 0,
  `Dia_18` float DEFAULT 0,
  `Dia_19` float DEFAULT 0,
  `Dia_20` float DEFAULT 0,
  `Dia_21` float DEFAULT 0,
  `Dia_22` float DEFAULT 0,
  `Dia_23` float DEFAULT 0,
  `Dia_24` float DEFAULT 0,
  `Dia_25` float DEFAULT 0,
  `Dia_26` float DEFAULT 0,
  `Dia_27` float DEFAULT 0,
  `Dia_28` float DEFAULT 0,
  `Dia_29` float DEFAULT 0,
  `Dia_30` float DEFAULT 0,
  `Dia_31` float DEFAULT 0,
  `Total` float DEFAULT 0,
  `Observacion_Uno` varchar(255) DEFAULT NULL,
  `Observacion_Dos` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=COMPACT;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_inventarios_salidas_manuales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_inventarios_salidas_manuales` (
  `Id_Salida` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Producto` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Turno` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Nombre_Usuario` varchar(100) DEFAULT NULL,
  `Usuario` varchar(50) DEFAULT NULL,
  `Hora` varchar(50) DEFAULT NULL,
  `Observacion` varchar(255) DEFAULT NULL,
  `Autorizada` bigint(20) DEFAULT NULL,
  `Revisada` tinyint(4) DEFAULT 0,
  `Cobrar` tinyint(4) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Codigo_Motivo` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_liquidacion_propinas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_liquidacion_propinas` (
  `Fecha` varchar(50) DEFAULT NULL,
  `cod_empleado` bigint(20) DEFAULT 0,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Nro_Mesa` varchar(50) DEFAULT NULL,
  `Propina_Pagada` int(11) DEFAULT 0,
  `Propina_Liquidada` int(11) DEFAULT 0,
  `Mesa` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_lista_precios_cliente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_lista_precios_cliente` (
  `id_lista` int(11) NOT NULL DEFAULT 0,
  `Id_Cliente` int(11) NOT NULL DEFAULT 0,
  `Id_Producto` int(11) NOT NULL DEFAULT 0,
  `Id_Presentacion` int(11) NOT NULL DEFAULT 0,
  `Precio_Producto` int(11) NOT NULL DEFAULT 0,
  `Fecha` varchar(50) NOT NULL DEFAULT '0',
  `Activa` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id_lista`,`Id_Cliente`,`Id_Producto`,`Id_Presentacion`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=COMPACT;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_listado_clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_listado_clientes` (
  `Id_Cliente` double NOT NULL DEFAULT 0,
  `nombres` varchar(50) DEFAULT NULL,
  `Nro_Factura_Reserva` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor` double DEFAULT 0,
  `Tel_Fijo` varchar(250) DEFAULT NULL,
  `Tel_Celular` varchar(50) DEFAULT NULL,
  `Mail` varchar(50) DEFAULT NULL,
  `direccion` varchar(255) DEFAULT NULL,
  `Tarjeta_Fiel` tinyint(4) DEFAULT 0,
  `Observacion_Referencia` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_mensajes_diarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_mensajes_diarios` (
  `Id_Mensaje` int(11) NOT NULL DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Sede` int(11) DEFAULT 0,
  `Enviado_por` varchar(50) DEFAULT NULL,
  `Mensaje_Caja` text DEFAULT NULL,
  `Mensaje_Mesas` text DEFAULT NULL,
  `Mensaje_General` text DEFAULT NULL,
  `Anulado` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Id_Mensaje`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_menu_diario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_menu_diario` (
  `Id_Menu` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Categoria` varchar(50) NOT NULL DEFAULT '0',
  `Descripcion` varchar(50) NOT NULL DEFAULT '0',
  `Agrupar` int(11) NOT NULL DEFAULT 0,
  `Seleccionado` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Menu`,`Id_Item`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_mesa_abierta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_mesa_abierta` (
  `Id_Mesa` int(11) DEFAULT 0,
  `Mesa` varchar(255) DEFAULT NULL,
  `Abierta` tinyint(4) DEFAULT 0,
  `Abierta_Desde` varchar(100) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_mesas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_mesas` (
  `Id_Mesa` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Mesa` varchar(50) DEFAULT NULL,
  `Ubicacion` varchar(50) DEFAULT NULL,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Id_Cliente` bigint(20) NOT NULL DEFAULT 0,
  `Zona_Dinamica` tinyint(4) DEFAULT 0,
  `Activa` tinyint(4) DEFAULT 0,
  `Id_Zona` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_meseros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_meseros` (
  `cod_empleado` int(11) NOT NULL DEFAULT 0,
  `nombres` varchar(50) DEFAULT NULL,
  `telefonos` varchar(50) DEFAULT NULL,
  `direccion` varchar(50) DEFAULT NULL,
  `estado` tinyint(1) NOT NULL DEFAULT 0,
  `Tipo_Empleado` int(11) DEFAULT 0,
  `Clave` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`cod_empleado`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_meseros_dia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_meseros_dia` (
  `cod_empleado` int(11) NOT NULL DEFAULT 0,
  `nombres` varchar(50) DEFAULT NULL,
  `telefonos` varchar(50) DEFAULT NULL,
  `direccion` varchar(50) DEFAULT NULL,
  `estado` tinyint(1) NOT NULL DEFAULT 0,
  `Tipo_Empleado` int(11) DEFAULT 0,
  `Clave` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`cod_empleado`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_meseros_propinas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_meseros_propinas` (
  `cod_empleado` int(11) NOT NULL DEFAULT 0,
  `nombres` varchar(50) DEFAULT NULL,
  `telefonos` varchar(50) DEFAULT NULL,
  `direccion` varchar(50) DEFAULT NULL,
  `estado` tinyint(1) NOT NULL DEFAULT 0,
  `Tipo_Empleado` int(11) DEFAULT 0,
  `Clave` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_novedades_categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_novedades_categorias` (
  `Id_Consecutivo` int(11) DEFAULT 0,
  `Cod_Categoria` int(11) DEFAULT 0,
  `Id_Novedad` int(11) DEFAULT 0,
  `Novedad` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_novedades_inventarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_novedades_inventarios` (
  `Id_Movimiento` int(11) DEFAULT 0,
  `Id_Novedad` int(11) DEFAULT 0,
  `Nombre_Novedad` varchar(100) DEFAULT NULL,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Producto` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Turno` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Nombre_Usuario` varchar(100) DEFAULT NULL,
  `Usuario` varchar(50) DEFAULT NULL,
  `Hora` varchar(50) DEFAULT NULL,
  `Observacion` varchar(255) DEFAULT NULL,
  `Autorizada` int(11) DEFAULT NULL,
  `Revisada` bigint(20) DEFAULT NULL,
  `Cobrar` tinyint(4) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Codigo_Motivo` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Tipo` int(11) DEFAULT 0,
  `Id_Preparacion` int(11) DEFAULT 0,
  `Enviada_Correo` tinyint(4) DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Codigo_Insumo` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_novedades_plato_pedido`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_novedades_plato_pedido` (
  `Id_Consecutivo` int(11) NOT NULL DEFAULT 0,
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Item` int(11) NOT NULL DEFAULT 0,
  `Depende` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Id_Novedad` int(11) NOT NULL DEFAULT 0,
  `Novedad` mediumtext DEFAULT NULL,
  PRIMARY KEY (`Id_Consecutivo`,`Nro_Pedido`,`Item`,`Depende`,`Cod_Categoria`,`Id_Novedad`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_novedades_plato_pedido_restaurar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_novedades_plato_pedido_restaurar` (
  `Id_Consecutivo` int(11) NOT NULL DEFAULT 0,
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Item` int(11) NOT NULL DEFAULT 0,
  `Depende` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Id_Novedad` int(11) NOT NULL DEFAULT 0,
  `Novedad` mediumtext DEFAULT NULL,
  PRIMARY KEY (`Id_Consecutivo`,`Nro_Pedido`,`Item`,`Depende`,`Cod_Categoria`,`Id_Novedad`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_novedades_productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_novedades_productos` (
  `Id_Novedad` int(11) NOT NULL DEFAULT 0,
  `Novedad` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`Id_Novedad`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_nro_pedido_nro_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_nro_pedido_nro_comanda` (
  `Nro_Comanda` int(11) NOT NULL DEFAULT 0,
  `Nro_Pedido` varchar(255) DEFAULT '0',
  `Fecha` varchar(50) DEFAULT NULL,
  `Mesa` varchar(200) DEFAULT '0',
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`Nro_Comanda`),
  UNIQUE KEY `Nro_Comanda` (`Nro_Comanda`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_opciones_empleado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_opciones_empleado` (
  `cod_empleado` int(11) NOT NULL DEFAULT 0,
  `Acti_Administrativo` tinyint(4) DEFAULT 0,
  `Acti_Inicio_Sesion` tinyint(4) DEFAULT 0,
  `Acti_Anular_Facturas` tinyint(4) DEFAULT 0,
  `Acti_Imprimir_Cuadres` tinyint(4) DEFAULT 0,
  `Acti_Cambiar_Propina` tinyint(4) DEFAULT 0,
  `Acti_Dar_Descuentos` tinyint(4) DEFAULT 0,
  `Acti_Reimprimir_Factura` tinyint(4) DEFAULT 0,
  `Acti_Panel_Configuracion` tinyint(4) DEFAULT 0,
  `Acti_Registro_Empleados` tinyint(4) DEFAULT 0,
  `Acti_Eliminar_Pedidos` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`cod_empleado`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_orden_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_orden_compra` (
  `Id_Orden_Compra` int(11) NOT NULL DEFAULT 0,
  `Fecha_Orden` varchar(50) DEFAULT NULL,
  `Fecha_Entrega` varchar(50) DEFAULT NULL,
  `Fecha_Vencimiento` varchar(50) DEFAULT NULL,
  `Total_Orden_Compra` float DEFAULT 0,
  `Id_Proveedor` int(11) DEFAULT 0,
  `Nombre_Proveedor` varchar(255) DEFAULT NULL,
  `Generada` tinyint(4) DEFAULT 0,
  `Revisada` tinyint(4) DEFAULT 0,
  `Orden_Pago` tinyint(4) DEFAULT 0,
  `Contabilizada` tinyint(4) DEFAULT 0,
  `Observacion` varchar(255) DEFAULT '0',
  `Usuario` varchar(50) DEFAULT '0',
  `Abierta` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_orden_compra_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_orden_compra_detalle` (
  `Id_Orden_Compra` int(11) NOT NULL DEFAULT 0,
  `Id_Proveedor` int(11) DEFAULT 0,
  `item` int(11) DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Nombre_Producto` varchar(255) DEFAULT NULL,
  `Marca_Referencia` varchar(50) DEFAULT NULL,
  `Id_Presentacion_compra` int(11) DEFAULT 0,
  `Nombre_presentacion` varchar(255) DEFAULT NULL,
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Sede` varchar(255) DEFAULT NULL,
  `Cantidad_Pedido` float DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Valor_Referencia` float DEFAULT 0,
  `Valor_Ultima_Compra` float DEFAULT 0,
  `Valor_Pedido` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_orden_impresion_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_orden_impresion_factura` (
  `Id_Registro` int(11) NOT NULL DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Orden` int(11) DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Imprimir` tinyint(4) DEFAULT 0,
  `Nombre_Personalizado` mediumtext DEFAULT NULL,
  `Centrar` tinyint(4) DEFAULT 0,
  `Valor` mediumtext DEFAULT NULL,
  PRIMARY KEY (`Id_Registro`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_orden_pedido_nuevo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_orden_pedido_nuevo` (
  `Id_Orden` int(11) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Agrupar` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Stock_Final_Sede` float DEFAULT 0,
  `Stock_Critico` float DEFAULT 0,
  `Stock_Minimo` float DEFAULT 0,
  `Total_Pedido_Sede` float DEFAULT 0,
  `Stock_Centro_P` float DEFAULT 0,
  `Cantidad_Pedido` int(11) DEFAULT 0,
  `Cantidad_Remisionada` int(11) DEFAULT 0,
  `Id_Presentacion` int(11) DEFAULT 0,
  `Remisionada` tinyint(4) DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Bodega` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_orden_pedido_nuevo_requisicion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_orden_pedido_nuevo_requisicion` (
  `Id_Orden` int(11) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Agrupar` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Stock_Final_Sede` float DEFAULT 0,
  `Stock_Critico` float DEFAULT 0,
  `Stock_Minimo` float DEFAULT 0,
  `Total_Pedido_Sede` float DEFAULT 0,
  `Stock_Centro_P` float DEFAULT 0,
  `Cantidad_Pedido` float DEFAULT 0,
  `Cantidad_Remisionada` float DEFAULT 0,
  `Id_Presentacion` int(11) DEFAULT 0,
  `Remisionada` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=COMPACT;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_orden_trabajo_conceptos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_orden_trabajo_conceptos` (
  `Cod_Concepto` int(11) NOT NULL DEFAULT 0,
  `descripcion` varchar(50) DEFAULT NULL,
  `Activa` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_pedido_sede`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_pedido_sede` (
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Inv_Final` float DEFAULT 0,
  `Stock_Minimo` float DEFAULT 0,
  `Pedido` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato` (
  `Id_Plato` int(11) DEFAULT 0,
  `Nombre` varchar(250) DEFAULT NULL,
  `Codigo_Producto` varchar(250) DEFAULT NULL,
  `Valor` int(11) DEFAULT 0,
  `Tiempo` int(11) DEFAULT 0,
  `Activo` tinyint(4) DEFAULT 0,
  `Cod_Categoria` int(11) DEFAULT 0,
  `Ruta_Foto` varchar(255) DEFAULT NULL,
  `Procedimiento` longtext DEFAULT NULL,
  `Descripcion_Plato` longtext DEFAULT NULL,
  `Impresora` varchar(250) DEFAULT NULL,
  `Comentario` varchar(255) DEFAULT NULL,
  `Impresion_Extra` varchar(255) DEFAULT NULL,
  `Impresora_2` varchar(255) DEFAULT NULL,
  `Preparacion_Previa` tinyint(4) DEFAULT 0,
  `Ofrecer` tinyint(4) DEFAULT 0,
  `Prioridad_Ofrecer` int(11) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Precio_x_Mayor` double DEFAULT 0,
  `Costo_Producto` double DEFAULT 0,
  `Stock_Minimo` double DEFAULT 0,
  `Pedir_Valor_Venta_Producto` tinyint(4) DEFAULT 0,
  `Pedir_Descripcion_Producto` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_armar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_armar` (
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Item_Comanda` int(11) NOT NULL DEFAULT 0,
  `Cantidad_Elegir` int(11) NOT NULL DEFAULT 0,
  `Activa` tinyint(4) NOT NULL DEFAULT 0,
  `Exgir_Seleccion` tinyint(4) NOT NULL DEFAULT 0,
  `Imprimir_Armar_Solo_Cambio` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Plato`,`Cod_Categoria`,`Nro_Pedido`,`Item_Comanda`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_armar_crear`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_armar_crear` (
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Item_Comanda` int(11) NOT NULL DEFAULT 0,
  `Cantidad_Elegir` int(11) NOT NULL DEFAULT 0,
  `Activa` tinyint(4) NOT NULL DEFAULT 0,
  `Exgir_Seleccion` tinyint(4) NOT NULL DEFAULT 0,
  `Imprimir_Armar_Solo_Cambio` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Plato`,`Cod_Categoria`,`Nro_Pedido`,`Item_Comanda`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_armar_crear_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_armar_crear_detalle` (
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Posicion` int(11) NOT NULL DEFAULT 0,
  `Item_Comanda` int(11) NOT NULL DEFAULT 0,
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Precio_Insumo` float DEFAULT 0,
  `Cantidad_Descontar` float DEFAULT 0,
  `Por_Default` tinyint(4) DEFAULT 0,
  `Insumo` varchar(255) NOT NULL DEFAULT '0',
  `Cantidad_Elegir` int(11) NOT NULL DEFAULT 0,
  `Activa` tinyint(4) NOT NULL DEFAULT 0,
  `Exgir_Seleccion` tinyint(4) NOT NULL DEFAULT 0,
  `Imprimir_Armar_Solo_Cambio` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Plato`,`Cod_Categoria`,`Item`,`Posicion`,`Item_Comanda`,`Nro_Pedido`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_armar_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_armar_detalle` (
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Posicion` int(11) NOT NULL DEFAULT 0,
  `Item_Comanda` int(11) NOT NULL DEFAULT 0,
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Precio_Insumo` float DEFAULT 0,
  `Cantidad_Descontar` float DEFAULT 0,
  `Por_Default` tinyint(4) DEFAULT 0,
  `Insumo` varchar(255) NOT NULL DEFAULT '0',
  PRIMARY KEY (`Id_Plato`,`Cod_Categoria`,`Item`,`Posicion`,`Item_Comanda`,`Nro_Pedido`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_armar_detalle_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_armar_detalle_menu` (
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Posicion` int(11) NOT NULL DEFAULT 0,
  `Item_Comanda` int(11) NOT NULL DEFAULT 0,
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Precio_Insumo` float DEFAULT 0,
  `Cantidad_Descontar` float DEFAULT 0,
  `Por_Default` tinyint(4) DEFAULT 0,
  `Insumo` varchar(255) NOT NULL DEFAULT '0',
  PRIMARY KEY (`Id_Plato`,`Cod_Categoria`,`Item`,`Posicion`,`Item_Comanda`,`Nro_Pedido`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_armar_detalle_origen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_armar_detalle_origen` (
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Posicion` int(11) NOT NULL DEFAULT 0,
  `Precio_Insumo` float DEFAULT 0,
  `Cantidad_Descontar` float DEFAULT 0,
  `Por_Default` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Id_Plato`,`Cod_Categoria`,`Item`,`Posicion`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_armar_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_armar_menu` (
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Cantidad_Elegir` int(11) DEFAULT 0,
  `Activa` tinyint(4) NOT NULL DEFAULT 0,
  `Exgir_Seleccion` tinyint(4) NOT NULL DEFAULT 0,
  `Imprimir_Armar_Solo_Cambio` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Plato`,`Cod_Categoria`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_armar_origen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_armar_origen` (
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Cantidad_Elegir` int(11) DEFAULT 0,
  `Activa` tinyint(4) NOT NULL DEFAULT 0,
  `Exgir_Seleccion` tinyint(4) NOT NULL DEFAULT 0,
  `Imprimir_Armar_Solo_Cambio` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Plato`,`Cod_Categoria`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_impresoras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_impresoras` (
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Id_Impresora` int(11) NOT NULL DEFAULT 0,
  `Cant_Impresiones` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Plato`,`Id_Impresora`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_presentacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_presentacion` (
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Id_Forma_Medida` int(11) NOT NULL DEFAULT 0,
  `Unidades_Minimas` double DEFAULT 0,
  `Valor_Presentacion` double DEFAULT 0,
  `Descripcion` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`Id_Plato`,`Id_Forma_Medida`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_producto` (
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Fecha` varchar(50) NOT NULL DEFAULT '0',
  `Nro_Factura` varchar(50) NOT NULL DEFAULT '0',
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Opcion_Cambiar` tinyint(4) DEFAULT 0,
  `Valor_Adicional_Armar` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_producto_historico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_producto_historico` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Opcion_Cambiar` tinyint(4) DEFAULT 0,
  `Valor_Adicional_Armar` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_producto_parcial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_producto_parcial` (
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Fecha` varchar(50) NOT NULL DEFAULT '0',
  `Nro_Factura` varchar(50) NOT NULL DEFAULT '0',
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Opcion_Cambiar` tinyint(4) DEFAULT 0,
  `Valor_Adicional_Armar` double DEFAULT 0,
  PRIMARY KEY (`Nro_Pedido`,`Fecha`,`Nro_Factura`,`Id_Plato`,`Item`,`Id_Grupo`,`Id_Item`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_producto_restaurar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_producto_restaurar` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Opcion_Cambiar` tinyint(4) DEFAULT 0,
  `Valor_Adicional_Armar` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_venta` (
  `Id_Sede` varchar(50) DEFAULT NULL,
  `Nombre_Sede` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Cod_Categoria` int(11) DEFAULT 0,
  `Nombre_Categoria` varchar(255) DEFAULT NULL,
  `Nombre_Plato` varchar(255) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Cantidad` double DEFAULT 0,
  `Cantidad_T1` double DEFAULT 0,
  `Cantidad_T2` double DEFAULT 0,
  `Valor_Plato` double DEFAULT 0,
  `Valor_Costo` double DEFAULT 0,
  `Fecha1` varchar(50) DEFAULT NULL,
  `Fecha2` varchar(50) DEFAULT NULL,
  `Valor1` float DEFAULT 0,
  `Valor2` float DEFAULT 0,
  `Margen` float DEFAULT 0,
  `Margen_Pesos` float DEFAULT 0,
  `Margen_Total_Pesos` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_plato_venta_semana`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_plato_venta_semana` (
  `Fecha` varchar(50) DEFAULT NULL,
  `Cod_Categoria` int(11) DEFAULT 0,
  `Nombre_Categoria` varchar(50) DEFAULT NULL,
  `Nombre_Plato` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Lunes` int(11) DEFAULT 0,
  `Martes` int(11) DEFAULT 0,
  `Miercoles` int(11) DEFAULT 0,
  `Jueves` int(11) DEFAULT 0,
  `Viernes` int(11) DEFAULT 0,
  `Sabado` int(11) DEFAULT 0,
  `Domingo` int(11) DEFAULT 0,
  `Total` int(11) DEFAULT 0,
  `Valor_Plato` int(11) DEFAULT 0,
  `Valor_Costo` int(11) DEFAULT 0,
  `Fecha1` varchar(50) DEFAULT NULL,
  `Fecha2` varchar(50) DEFAULT NULL,
  `Valor1` float DEFAULT 0,
  `Valor2` float DEFAULT 0,
  `Margen` float DEFAULT 0,
  `Margen_Pesos` float DEFAULT 0,
  `Margen_Total_Pesos` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_platos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_platos` (
  `Id_Plato` int(11) DEFAULT 0,
  `Nombre` varchar(250) DEFAULT NULL,
  `Codigo_Producto` varchar(250) DEFAULT NULL,
  `Valor` int(11) DEFAULT 0,
  `Tiempo` int(11) DEFAULT 0,
  `Activo` tinyint(4) DEFAULT 0,
  `Cod_Categoria` int(11) DEFAULT 0,
  `Ruta_Foto` varchar(255) DEFAULT NULL,
  `Procedimiento` longtext DEFAULT NULL,
  `Descripcion_Plato` longtext DEFAULT NULL,
  `Impresora` varchar(250) DEFAULT NULL,
  `Comentario` varchar(255) DEFAULT NULL,
  `Impresion_Extra` varchar(255) DEFAULT NULL,
  `Impresora_2` varchar(255) DEFAULT NULL,
  `Preparacion_Previa` tinyint(4) DEFAULT 0,
  `Ofrecer` tinyint(4) DEFAULT 0,
  `Prioridad_Ofrecer` int(11) DEFAULT 0,
  `Impuesto` int(11) DEFAULT 0,
  `Precio_x_Mayor` double DEFAULT 0,
  `Costo_Producto` double DEFAULT 0,
  `Stock_Minimo` double DEFAULT 0,
  `Pedir_Valor_Venta_Producto` tinyint(4) DEFAULT 0,
  `Pedir_Descripcion_Producto` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_platos_ofrecer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_platos_ofrecer` (
  `Id_Plato` int(11) DEFAULT 0,
  `Nombre` varchar(255) DEFAULT NULL,
  `Valor` int(11) DEFAULT 0,
  `Margen_Pesos` varchar(255) DEFAULT NULL,
  `Margen_Porcentaje` varchar(255) DEFAULT NULL,
  `Cod_Categoria` varchar(255) DEFAULT NULL,
  `Prioridad` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_platos_ofrecer_copy`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_platos_ofrecer_copy` (
  `Id_Plato` int(11) DEFAULT 0,
  `Nombre` varchar(255) DEFAULT NULL,
  `Valor` int(11) DEFAULT 0,
  `Margen_Pesos` varchar(255) DEFAULT NULL,
  `Margen_Porcentaje` varchar(255) DEFAULT NULL,
  `Cod_Categoria` varchar(255) DEFAULT NULL,
  `Prioridad` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_porciones_cambio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_porciones_cambio` (
  `Cod_Categoria` int(11) DEFAULT 0,
  `Id_Plato` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_porciones_plato_nuevo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_porciones_plato_nuevo` (
  `Id_Plato` int(11) DEFAULT 0,
  `Nombre_Porcion` varchar(200) DEFAULT NULL,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Unidad_Minima` float DEFAULT 0,
  `Porciones_A_Desccontar` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_clientes_facturar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_clientes_facturar` (
  `Id_Cliente` int(11) NOT NULL DEFAULT 0,
  `cedula` varchar(50) DEFAULT '0',
  `nombres` varchar(50) NOT NULL DEFAULT '0',
  `Apellidos` varchar(50) DEFAULT NULL,
  `direccion` varchar(50) DEFAULT NULL,
  `telefono` varchar(250) DEFAULT NULL,
  `Barrio` varchar(50) DEFAULT NULL,
  `Mail` varchar(50) DEFAULT NULL,
  `Dia_Cumple` int(11) DEFAULT 0,
  `Mes_Cumple` int(11) DEFAULT 0,
  `Edad` int(11) DEFAULT 0,
  `Ocupacion` varchar(50) DEFAULT NULL,
  `Porc_Descuento` int(11) DEFAULT 0,
  `Observaciones` varchar(255) DEFAULT NULL,
  `Fecha_Aniversario` varchar(50) DEFAULT NULL,
  `Fecha_Grado` varchar(50) DEFAULT NULL,
  `Empresa` varchar(150) DEFAULT NULL,
  `Id_Klob` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Tarjeta_Fiel` varchar(50) DEFAULT NULL,
  `Cod_Barrio` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Referencia` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id_Cliente`) USING BTREE,
  KEY `cedula` (`cedula`) USING BTREE,
  KEY `Apellidos` (`Apellidos`) USING BTREE,
  KEY `nombres` (`nombres`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_comanda` (
  `Nro_Pedido` varchar(50) NOT NULL DEFAULT '0',
  `Fecha` varchar(50) NOT NULL DEFAULT '0',
  `Nro_Factura` varchar(50) NOT NULL DEFAULT '0',
  `Mesa` varchar(50) DEFAULT NULL,
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Movil` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Nro_Pedido`,`Fecha`,`Nro_Factura`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_comanda_previo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_comanda_previo` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Mesa` varchar(200) DEFAULT NULL,
  `Hora` varchar(50) DEFAULT NULL,
  `Mesero` int(11) DEFAULT 0,
  `Cancelado` tinyint(4) DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Imprimio_Precuenta` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puestos` int(11) DEFAULT 0,
  `Domicilio` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Movil` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_descuentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_descuentos` (
  `Id_Descuento` bigint(20) NOT NULL DEFAULT 0,
  `Factura` varchar(50) DEFAULT NULL,
  `Nro_Pedido` varchar(200) DEFAULT NULL,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Valor_Descuento` double DEFAULT 0,
  `Id_Tipificacion` int(11) DEFAULT 0,
  `Id_Clasificacion` int(11) DEFAULT 0,
  `Motivo` varchar(255) DEFAULT NULL,
  `Id_Cliente` bigint(20) DEFAULT 0,
  `Telefono` varchar(50) DEFAULT NULL,
  `Email` varchar(50) DEFAULT NULL,
  `Descuento_Factura` tinyint(4) DEFAULT 0,
  `Descuento_Plato` tinyint(4) DEFAULT 0,
  `Porcentaje` decimal(10,0) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_detalle_comanda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_detalle_comanda` (
  `Nro_pedido` varchar(255) NOT NULL DEFAULT '0',
  `Fecha` varchar(50) NOT NULL DEFAULT '0',
  `Nro_Factura` varchar(100) DEFAULT '0',
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float NOT NULL DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` text DEFAULT NULL,
  `Salio` tinyint(1) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` decimal(10,0) DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` int(11) NOT NULL DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT NULL,
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL,
  PRIMARY KEY (`Nro_pedido`,`Fecha`,`Id_Plato`,`Item`,`Depende`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_detalle_comanda_parcial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_detalle_comanda_parcial` (
  `Nro_pedido` varchar(255) NOT NULL DEFAULT '0',
  `Fecha` varchar(50) NOT NULL DEFAULT '0',
  `Nro_Factura` varchar(100) DEFAULT '0',
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float NOT NULL DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` text DEFAULT NULL,
  `Salio` tinyint(1) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` float DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` tinyint(4) DEFAULT 0,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` int(11) NOT NULL DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT '0',
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext DEFAULT NULL,
  PRIMARY KEY (`Nro_pedido`,`Fecha`,`Id_Plato`,`Item`,`Depende`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_detalle_comanda_previo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_detalle_comanda_previo` (
  `Nro_pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad` float DEFAULT 0,
  `Valor` int(11) DEFAULT 0,
  `Min` int(11) DEFAULT 0,
  `Min_S` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Salio` tinyint(4) DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento_Plato` float DEFAULT 0,
  `Porc_Descuento_General` float DEFAULT 0,
  `Impreso` tinyint(4) DEFAULT 0,
  `Cambios` varchar(255) DEFAULT NULL,
  `Mostrar` varchar(50) DEFAULT NULL,
  `Impresora` varchar(255) DEFAULT NULL,
  `Depende` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Puesto` int(11) DEFAULT 0,
  `Cod_Categoria_Plato` int(11) DEFAULT 0,
  `Hora_Plato` varchar(50) DEFAULT NULL,
  `Paga_Impuesto` tinyint(4) DEFAULT 0,
  `Impuesto` decimal(10,0) DEFAULT 0,
  `Impuesto_Original` decimal(10,0) DEFAULT 0,
  `Paga_Plato` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Producto_Personalizado` mediumtext CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_detalle_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_detalle_factura` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Novedad` varchar(250) DEFAULT NULL,
  `Valor_Plato` int(11) DEFAULT 0,
  `Cortesia` tinyint(4) DEFAULT 0,
  `Porc_Descuento` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_factura` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` varchar(50) DEFAULT NULL,
  `Factura_Domicilio` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_factura_forma_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_factura_forma_pago` (
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Forma_Pago` int(11) NOT NULL DEFAULT 0,
  `Id_Tarjeta` int(11) NOT NULL DEFAULT 0,
  `Nro_Factura` varchar(100) NOT NULL DEFAULT '0',
  `Nro_Pedido` varchar(100) DEFAULT NULL,
  `Valor` double DEFAULT 0,
  `Porcentaje` float DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Fecha` varchar(255) DEFAULT NULL,
  `Valor_Domicilio` double DEFAULT 0,
  `Id_Bono` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Item`,`Id_Forma_Pago`,`Id_Tarjeta`,`Nro_Factura`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_factura_previo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_factura_previo` (
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Valor_Efectivo` int(11) DEFAULT 0,
  `Descuento` int(11) DEFAULT 0,
  `Cedula` varchar(50) DEFAULT NULL,
  `Empleado` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Pago_Iva` tinyint(4) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Hora_Texto` varchar(50) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Valor_Sin_Propina` int(11) DEFAULT 0,
  `Analizada` tinyint(4) DEFAULT 0,
  `Tipo_Moneda` int(11) DEFAULT 0,
  `Valor_Extrangero` float DEFAULT 0,
  `Factura_Manual` tinyint(4) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Id_Cliente` int(11) DEFAULT 0,
  `Factura_Reserva` varchar(50) DEFAULT '0',
  `Factura_Domicilio` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_novedades_plato_pedido`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_novedades_plato_pedido` (
  `Id_Consecutivo` int(11) NOT NULL DEFAULT 0,
  `Nro_Pedido` varchar(255) NOT NULL DEFAULT '0',
  `Item` int(11) NOT NULL DEFAULT 0,
  `Depende` int(11) NOT NULL DEFAULT 0,
  `Cod_Categoria` int(11) NOT NULL DEFAULT 0,
  `Id_Novedad` int(11) NOT NULL DEFAULT 0,
  `Novedad` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`Id_Consecutivo`,`Nro_Pedido`,`Item`,`Depende`,`Cod_Categoria`,`Id_Novedad`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_plato_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_plato_producto` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Opcion_Cambiar` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_precuenta_plato_producto_parcial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_precuenta_plato_producto_parcial` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Id_Plato` int(11) DEFAULT 0,
  `Item` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` float DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Item_Original` int(11) DEFAULT 0,
  `Posicion` int(11) DEFAULT 0,
  `Opcion_Cambiar` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_preparacion_porciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_preparacion_porciones` (
  `Id_Preparacion` int(11) NOT NULL DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Preparacion` longtext DEFAULT NULL,
  `Cantidad_Porciones` int(11) DEFAULT 0,
  PRIMARY KEY (`Id_Preparacion`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_producto_forma_medida`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_producto_forma_medida` (
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Id_Forma_Medida` int(11) NOT NULL DEFAULT 0,
  `Unidad_Minima` float DEFAULT 0,
  PRIMARY KEY (`Id_Grupo`,`Id_Item`,`Id_Forma_Medida`),
  KEY `Id_Forma_Medida` (`Id_Forma_Medida`),
  KEY `Id_Grupo` (`Id_Grupo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_producto_proveedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_producto_proveedores` (
  `Posicion` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Id_Proveedor` int(11) NOT NULL DEFAULT 0,
  `Empresa` varchar(50) DEFAULT NULL,
  `Cantidad_Pedido` float DEFAULT 0,
  `Valor_Referencia` float DEFAULT 0,
  `Ultima_Compra` float DEFAULT 0,
  `Valor_Pactado` float DEFAULT 0,
  `Valor_Pedido` float DEFAULT 0,
  `Diferencia_Check` float DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Und_Medida_Comrpa` varchar(255) DEFAULT NULL,
  `Ultima_Orden` float DEFAULT 0,
  `Und_Medida_Orden` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_producto_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_producto_venta` (
  `Fecha` varchar(50) DEFAULT NULL,
  `Cod_Categoria` int(11) DEFAULT 0,
  `Nombre_Categoria` varchar(50) DEFAULT NULL,
  `Nombre_Producto` varchar(50) DEFAULT NULL,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad` int(11) DEFAULT 0,
  `Valor_Producto` int(11) DEFAULT 0,
  `Valor_Costo` int(11) DEFAULT 0,
  `Fecha1` varchar(50) DEFAULT NULL,
  `Fecha2` varchar(50) DEFAULT NULL,
  `Valor1` float DEFAULT 0,
  `Valor2` float DEFAULT 0,
  `Margen` float DEFAULT 0,
  `Margen_Pesos` float DEFAULT 0,
  `Margen_Total_Pesos` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=COMPACT;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_productos_descontar_inventarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_productos_descontar_inventarios` (
  `Nro_Pedido` varchar(255) DEFAULT NULL,
  `Item` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Cantidad_Producto` float DEFAULT 0,
  `Cantidad_Comanda` float DEFAULT 0,
  `Suma` tinyint(4) DEFAULT 0,
  `Descontado` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_promedio_venta_persona`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_promedio_venta_persona` (
  `Sede` varchar(250) DEFAULT NULL,
  `Periodo` varchar(50) DEFAULT NULL,
  `Fecha_Generacion` varchar(50) DEFAULT NULL,
  `Concepto` varchar(50) DEFAULT NULL,
  `Valor` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_promedio_venta_persona_sedes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_promedio_venta_persona_sedes` (
  `Id_Registro` int(11) DEFAULT 0,
  `Periodo` varchar(50) DEFAULT NULL,
  `Fecha_Generacion` varchar(50) DEFAULT NULL,
  `Concepto` varchar(50) DEFAULT NULL,
  `Valor_Sede1` int(11) DEFAULT 0,
  `Valor_Sede2` int(11) DEFAULT 0,
  `Valor_Sede3` int(11) DEFAULT 0,
  `Valor_Sede4` int(11) DEFAULT 0,
  `Valor_Sede5` int(11) DEFAULT 0,
  `Valor_Sede6` int(11) DEFAULT 0,
  `Valor_Sede7` int(11) DEFAULT 0,
  `Valor_Sede8` int(11) DEFAULT 0,
  `Valor_Sede9` int(11) DEFAULT 0,
  `Valor_Sede10` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_propinas_modificadas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_propinas_modificadas` (
  `Id_Modificacion` int(11) NOT NULL DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Propina_Liquidada` int(11) DEFAULT 0,
  `Propina_Pagada` int(11) DEFAULT 0,
  `Usuario` varchar(50) DEFAULT NULL,
  `Valor_efectivo` int(11) DEFAULT 0,
  `Valor_T_Credito` int(11) DEFAULT 0,
  `Valor_T_Debito` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Mesero` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Mesa` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id_Modificacion`),
  KEY `Id_Modificacion` (`Id_Modificacion`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_proveedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_proveedores` (
  `Id_Proveedor` int(11) NOT NULL DEFAULT 0,
  `Nit` varchar(50) DEFAULT NULL,
  `Empresa` varchar(255) DEFAULT NULL,
  `Mail_Empresa` varchar(255) DEFAULT NULL,
  `Direccion` varchar(50) DEFAULT NULL,
  `Telefono_Fijo` varchar(50) DEFAULT NULL,
  `Telefono_Celular` varchar(50) DEFAULT NULL,
  `Observaciones` varchar(50) DEFAULT NULL,
  `Activo` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_Proveedor`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_proyeccion_remision`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_proyeccion_remision` (
  `Id_Orden` int(11) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Agrupar` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Stock_Final_Sede` float DEFAULT 0,
  `Stock_Critico` float DEFAULT 0,
  `Stock_Minimo` float DEFAULT 0,
  `Total_Pedido_Sede` float DEFAULT 0,
  `Stock_Centro_P` float DEFAULT 0,
  `Cantidad_Pedido` int(11) DEFAULT 0,
  `Cantidad_Remisionada` int(11) DEFAULT 0,
  `Id_Presentacion` int(11) DEFAULT 0,
  `Remisionada` tinyint(4) DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Bodega` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_proyecion_venta_esperada_grafica`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_proyecion_venta_esperada_grafica` (
  `Id_Registro` double NOT NULL DEFAULT 0,
  `Id_Sede` int(11) NOT NULL DEFAULT 0,
  `Año` int(11) DEFAULT 0,
  `Mes` int(11) DEFAULT 0,
  `Fecha_Anterior` varchar(50) DEFAULT NULL,
  `Fecha_Actual` varchar(50) DEFAULT NULL,
  `Venta_Mes_Año_Anterior` double DEFAULT 0,
  `Turno_Uno_Anterior` double DEFAULT 0,
  `Turno_Dos_Anterior` double DEFAULT 0,
  `Venta_Mes_Esperada` double DEFAULT 0,
  `Turno_Uno_Esperada` double DEFAULT 0,
  `Turno_Dos_Esperada` double DEFAULT 0,
  `Total_Turno_Esperada` double DEFAULT 0,
  `Turno_Uno_Actual` double DEFAULT 0,
  `Turno_Dos_Actual` double DEFAULT 0,
  `Total_Turno_Actual` double DEFAULT 0,
  `Cumplimiento_Turno_Uno` double DEFAULT 0,
  `Cumplimiento_Turno_Dos` double DEFAULT 0,
  `Porcentaje_Aplicado_T1` double DEFAULT 0,
  `Porcentaje_Aplicado_T2` double DEFAULT 0,
  `Total_Venta_Esperada_Año` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_proyecion_venta_esperada_sede_ano`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_proyecion_venta_esperada_sede_ano` (
  `Id_Registro` double NOT NULL DEFAULT 0,
  `Id_Sede` int(11) NOT NULL DEFAULT 0,
  `Concepto` varchar(50) DEFAULT NULL,
  `Año` varchar(50) DEFAULT NULL,
  `Venta_Esperada` double DEFAULT 0,
  `Enero_Promedio` double DEFAULT 0,
  `Enero` double DEFAULT 0,
  `Febrero_Promedio` double DEFAULT 0,
  `Febrero` double DEFAULT 0,
  `Marzo_Promedio` double DEFAULT 0,
  `Marzo` double DEFAULT 0,
  `Abril_Promedio` double DEFAULT 0,
  `Abril` double DEFAULT 0,
  `Mayo_Promedio` double DEFAULT 0,
  `Mayo` double DEFAULT 0,
  `Junio_Promedio` double DEFAULT 0,
  `Junio` double DEFAULT 0,
  `Julio_Promedio` double DEFAULT 0,
  `Julio` double DEFAULT 0,
  `Agosto_Promedio` double DEFAULT 0,
  `Agosto` double DEFAULT 0,
  `Septiembre_Promedio` double DEFAULT 0,
  `Septiembre` double DEFAULT 0,
  `Octubre_Promedio` double DEFAULT 0,
  `Octubre` double DEFAULT 0,
  `Noviembre_Promedio` double DEFAULT 0,
  `Noviembre` double DEFAULT 0,
  `Diciembre_Promedio` double DEFAULT 0,
  `Diciembre` double DEFAULT 0,
  `Total_Promedio` double DEFAULT 0,
  `Total_Venta_Esperada_Año` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_proyecion_venta_esperada_sede_ano_promedio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_proyecion_venta_esperada_sede_ano_promedio` (
  `Id_Registro` double NOT NULL DEFAULT 0,
  `Id_Sede` int(11) NOT NULL DEFAULT 0,
  `Concepto` varchar(50) DEFAULT NULL,
  `Venta_Esperada` double DEFAULT 0,
  `Año` varchar(50) DEFAULT NULL,
  `Enero_Promedio` double DEFAULT 0,
  `Enero` double DEFAULT 0,
  `Febrero_Promedio` double DEFAULT 0,
  `Febrero` double DEFAULT 0,
  `Marzo_Promedio` double DEFAULT 0,
  `Marzo` double DEFAULT 0,
  `Abril_Promedio` double DEFAULT 0,
  `Abril` double DEFAULT 0,
  `Mayo_Promedio` double DEFAULT 0,
  `Mayo` double DEFAULT 0,
  `Junio_Promedio` double DEFAULT 0,
  `Junio` double DEFAULT 0,
  `Julio_Promedio` double DEFAULT 0,
  `Julio` double DEFAULT 0,
  `Agosto_Promedio` double DEFAULT 0,
  `Agosto` double DEFAULT 0,
  `Septiembre_Promedio` double DEFAULT 0,
  `Septiembre` double DEFAULT 0,
  `Octubre_Promedio` double DEFAULT 0,
  `Octubre` double DEFAULT 0,
  `Noviembre_Promedio` double DEFAULT 0,
  `Noviembre` double DEFAULT 0,
  `Diciembre_Promedio` double DEFAULT 0,
  `Diciembre` double DEFAULT 0,
  `Total_Promedio` double DEFAULT 0,
  `Total_Venta_Esperada_Año` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_proyecion_venta_esperada_sede_dia_turno`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_proyecion_venta_esperada_sede_dia_turno` (
  `Id_Registro` double NOT NULL DEFAULT 0,
  `Id_Sede` int(11) NOT NULL DEFAULT 0,
  `Año` int(11) DEFAULT 0,
  `Mes` int(11) DEFAULT 0,
  `Fecha_Anterior` varchar(50) DEFAULT NULL,
  `Fecha_Actual` varchar(50) DEFAULT NULL,
  `Venta_Mes_Año_Anterior` double DEFAULT 0,
  `Turno_Uno_Anterior` double DEFAULT 0,
  `Turno_Dos_Anterior` double DEFAULT 0,
  `Venta_Mes_Esperada` double DEFAULT 0,
  `Turno_Uno_Esperada` double DEFAULT 0,
  `Turno_Dos_Esperada` double DEFAULT 0,
  `Total_Turno_Esperada` double DEFAULT 0,
  `Turno_Uno_Actual` double DEFAULT 0,
  `Turno_Dos_Actual` double DEFAULT 0,
  `Total_Turno_Actual` double DEFAULT 0,
  `Cumplimiento_Turno_Uno` double DEFAULT 0,
  `Cumplimiento_Turno_Dos` double DEFAULT 0,
  `Porcentaje_Aplicado_T1` double DEFAULT 0,
  `Porcentaje_Aplicado_T2` double DEFAULT 0,
  `Total_Venta_Esperada_Año` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=FIXED;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_recibo_forma_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_recibo_forma_pago` (
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Forma_Pago` int(11) NOT NULL DEFAULT 0,
  `Id_Tarjeta` int(11) NOT NULL DEFAULT 0,
  `Nro_Factura` varchar(100) DEFAULT NULL,
  `Nro_Pedido` varchar(100) DEFAULT NULL,
  `Valor` double DEFAULT 0,
  `Porcentaje` float DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Fecha` varchar(255) DEFAULT NULL,
  `Valor_Domicilio` double DEFAULT 0,
  `Id_Bono` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_registro_baucher_sedes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_registro_baucher_sedes` (
  `Id_Registro` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Fecha_Factura` varchar(50) DEFAULT NULL,
  `Fecha_Guardado` varchar(50) DEFAULT NULL,
  `Id_Tarjeta` int(11) DEFAULT 0,
  `Nro_Baucher` float DEFAULT 0,
  `Porcentaje` double DEFAULT 0,
  `Total_Baucher` float DEFAULT 0,
  `Compra_Mas_Iva` float DEFAULT 0,
  `Base_Compra` float DEFAULT 0,
  `Iac` float DEFAULT 0,
  `Propina` float DEFAULT 0,
  `Total_Factura` float DEFAULT 0,
  `Valor_Pago_Efectivo` float DEFAULT 0,
  `Comision_Tarjeta` float DEFAULT 0,
  `Retefuente` float DEFAULT 0,
  `Dinero_Abonado` float DEFAULT 0,
  `Propina_Mas` float DEFAULT 0,
  `Propina_Efectivo` float DEFAULT 0,
  `Total_Baucher_Iva` float DEFAULT 0,
  `Porcentaje_Tarjeta` float DEFAULT 0,
  `Nro_Factura` varchar(200) DEFAULT NULL,
  `Marca` tinyint(4) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Observacion` varchar(200) DEFAULT NULL,
  `Usuario` varchar(200) DEFAULT NULL,
  `Desglose` tinyint(4) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_registro_baucher_sedes_desglose`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_registro_baucher_sedes_desglose` (
  `Id_Registro` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Fecha_Factura` varchar(50) DEFAULT NULL,
  `Fecha_Guardado` varchar(50) DEFAULT NULL,
  `Id_Tarjeta` int(11) DEFAULT 0,
  `Nro_Baucher` float DEFAULT 0,
  `Porcentaje` double DEFAULT 0,
  `Total_Baucher` float DEFAULT 0,
  `Compra_Mas_Iva` float DEFAULT 0,
  `Base_Compra` float DEFAULT 0,
  `Iac` float DEFAULT 0,
  `Propina` float DEFAULT 0,
  `Total_Factura` float DEFAULT 0,
  `Valor_Pago_Efectivo` float DEFAULT 0,
  `Comision_Tarjeta` float DEFAULT 0,
  `Retefuente` float DEFAULT 0,
  `Dinero_Abonado` float DEFAULT 0,
  `Propina_Mas` float DEFAULT 0,
  `Propina_Efectivo` float DEFAULT 0,
  `Total_Baucher_Iva` float DEFAULT 0,
  `Porcentaje_Tarjeta` float DEFAULT 0,
  `Nro_Factura` varchar(200) DEFAULT NULL,
  `Marca` tinyint(4) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Observacion` varchar(200) DEFAULT NULL,
  `Usuario` varchar(200) DEFAULT NULL,
  `Desglose` tinyint(4) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_registro_dispositivos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_registro_dispositivos` (
  `Id_Dispositivo` int(11) NOT NULL DEFAULT 0,
  `Nombre_Dispositivo` varchar(150) DEFAULT NULL,
  `Usuario` varchar(25) DEFAULT NULL,
  `Contrasena` varchar(25) DEFAULT NULL,
  `Activo` tinyint(4) NOT NULL DEFAULT 0,
  `Fecha_Activacion` varchar(50) DEFAULT NULL,
  `Cod_Empleado` bigint(20) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_registro_facturas_anuladas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_registro_facturas_anuladas` (
  `Id_Anulacion` int(11) NOT NULL DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Nro_Factura` varchar(50) DEFAULT NULL,
  `Motivo_Anulacion` longtext DEFAULT NULL,
  `Usuario` varchar(50) DEFAULT NULL,
  `Factura_Reemplaza` varchar(255) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  KEY `Fecha_Nro_Factura` (`Fecha`,`Nro_Factura`),
  KEY `Usuario` (`Usuario`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_registro_novedad_categorias_sede`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_registro_novedad_categorias_sede` (
  `Categoria_Tipificacion` int(11) NOT NULL DEFAULT 0,
  `Descripcion` varchar(100) DEFAULT NULL,
  `Responsable_Categoria` int(11) NOT NULL DEFAULT 0,
  `Id_Area` int(11) NOT NULL DEFAULT 0,
  `Enviar_Correo` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Categoria_Tipificacion`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_remision_columna`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_remision_columna` (
  `Nombre_Reporte` varchar(150) DEFAULT NULL,
  `Restaurante` varchar(100) DEFAULT NULL,
  `Fecha_Nro_Pedido` varchar(100) DEFAULT NULL,
  `Fecha_Nro_Remision` varchar(100) DEFAULT NULL,
  `Id_Orden` int(11) DEFAULT 0,
  `Cp_1` varchar(1) DEFAULT '0',
  `Id_Grupo_C1` int(11) DEFAULT 0,
  `Id_Item_C1` int(11) DEFAULT 0,
  `Nombre_Producto_C1` varchar(100) DEFAULT NULL,
  `Cantidad_Pedido_C1` float DEFAULT 0,
  `Cantidad_Remision_C1` float DEFAULT 0,
  `Precio_Costo_C1` float DEFAULT 0,
  `Precio_Venta_C1` float DEFAULT 0,
  `Valor_Aux_C1` int(11) DEFAULT 0,
  `Texto_Aux_C1` varchar(150) DEFAULT NULL,
  `Cp_2` varchar(1) DEFAULT '0',
  `Id_Grupo_C2` int(11) DEFAULT 0,
  `Id_Item_C2` int(11) DEFAULT 0,
  `Nombre_Producto_C2` varchar(100) DEFAULT NULL,
  `Cantidad_Pedido_C2` float DEFAULT 0,
  `Cantidad_Remision_C2` float DEFAULT 0,
  `Precio_Costo_C2` float DEFAULT 0,
  `Precio_Venta_C2` float DEFAULT 0,
  `Valor_Aux_C2` int(11) DEFAULT 0,
  `Texto_Aux_C2` varchar(150) DEFAULT NULL,
  `Cp_3` varchar(1) DEFAULT '0',
  `Id_Grupo_C3` int(11) DEFAULT 0,
  `Id_Item_C3` int(11) DEFAULT 0,
  `Nombre_Producto_C3` varchar(100) DEFAULT NULL,
  `Cantidad_Pedido_C3` float DEFAULT 0,
  `Cantidad_Remision_C3` float DEFAULT 0,
  `Precio_Costo_C3` float DEFAULT 0,
  `Precio_Venta_C3` float DEFAULT 0,
  `Valor_Aux_C3` int(11) DEFAULT 0,
  `Texto_Aux_C3` varchar(150) DEFAULT NULL,
  `Cp_4` varchar(1) DEFAULT '0',
  `Id_Grupo_C4` int(11) DEFAULT 0,
  `Id_Item_C4` int(11) DEFAULT 0,
  `Nombre_Producto_C4` varchar(100) DEFAULT NULL,
  `Cantidad_Pedido_C4` float DEFAULT 0,
  `Cantidad_Remision_C4` float DEFAULT 0,
  `Precio_Costo_C4` float DEFAULT 0,
  `Precio_Venta_C4` float DEFAULT 0,
  `Valor_Aux_C4` int(11) DEFAULT 0,
  `Texto_Aux_C4` varchar(150) DEFAULT NULL,
  `Cp_5` varchar(1) DEFAULT '0',
  `Id_Grupo_C5` int(11) DEFAULT 0,
  `Id_Item_C5` int(11) DEFAULT 0,
  `Nombre_Producto_C5` varchar(100) DEFAULT NULL,
  `Cantidad_Pedido_C5` float DEFAULT 0,
  `Cantidad_Remision_C5` float DEFAULT 0,
  `Precio_Costo_C5` float DEFAULT 0,
  `Precio_Venta_C5` float DEFAULT 0,
  `Valor_Aux_C5` int(11) DEFAULT 0,
  `Texto_Aux_C5` varchar(150) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_remision_consulta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_remision_consulta` (
  `Id_Remision` varchar(50) DEFAULT NULL,
  `Id_Orden_Pedido` varchar(50) DEFAULT NULL,
  `Fecha_Pedido` varchar(50) DEFAULT NULL,
  `Fecha_Remision` varchar(50) DEFAULT NULL,
  `Agrupar` int(11) NOT NULL DEFAULT 0,
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Cantidad_Actual` float DEFAULT 0,
  `Stock_Minimo` float DEFAULT 0,
  `Cantidad_Pedido` float DEFAULT 0,
  `Cantidad_Remisionada` float DEFAULT 0,
  `Guardada` tinyint(1) DEFAULT 0,
  `Id_Presentacion` int(11) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0,
  `Hora` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_reporte_sedes_dinamico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_reporte_sedes_dinamico` (
  `Fecha_Generacion` varchar(200) DEFAULT NULL,
  `Periodo_Evaluado` varchar(200) NOT NULL DEFAULT '0',
  `Concepto` varchar(200) NOT NULL DEFAULT '0',
  `Valor` double NOT NULL DEFAULT 0,
  `Normal` tinyint(4) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_requisicion_externa_productos_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_requisicion_externa_productos_detalle` (
  `Id_Requisicion` int(11) NOT NULL DEFAULT 0,
  `Id_Proveedor` int(11) NOT NULL DEFAULT 0,
  `Id_Sede` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Fecha_Registro` date DEFAULT NULL,
  `Hora_Registro` varchar(50) DEFAULT NULL,
  `Usuario` varchar(100) DEFAULT '0',
  `Und_Uso` int(11) DEFAULT 0,
  `Nombre_Und_Compra` varchar(50) DEFAULT '0',
  `Posicion` int(11) DEFAULT 0,
  `Nombre_Producto` varchar(100) DEFAULT NULL,
  `Marca_Referencia` varchar(150) DEFAULT '0',
  `Cantidad_Sugerida` float DEFAULT 0,
  `Cantidad_Pedido` float DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Cod_Empleado` varchar(50) DEFAULT NULL,
  `Agrupar` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Id_Requisicion`,`Id_Proveedor`,`Id_Sede`,`Item`,`Id_Grupo`,`Id_Item`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_requisicion_productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_requisicion_productos` (
  `Id_Requisicion` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 5,
  `Fecha` varchar(50) DEFAULT NULL,
  `Hora` varchar(50) DEFAULT NULL,
  `Turno` int(11) DEFAULT 0,
  `Revisada` tinyint(4) DEFAULT 0,
  `Autorizada` tinyint(4) DEFAULT 0,
  `Usuario` varchar(50) DEFAULT NULL,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Cerrada` tinyint(4) DEFAULT 0,
  `Cargada_A_Remision` tinyint(4) DEFAULT 0,
  `Anulada` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_requisicion_productos_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_requisicion_productos_detalle` (
  `Id_Requisicion` int(11) DEFAULT 0,
  `Id_Sede` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Producto` varchar(50) DEFAULT NULL,
  `Cantidad` float DEFAULT 0,
  `Observacion` varchar(255) DEFAULT NULL,
  `Agrupar` int(11) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Insumo_Cp` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_reservas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_reservas` (
  `Id_Reserva` int(11) NOT NULL AUTO_INCREMENT,
  `Fecha_Registro` varchar(50) DEFAULT NULL,
  `Fecha_Reserva` varchar(50) DEFAULT NULL,
  `Id_Sede` int(11) DEFAULT 0,
  `Empresa` varchar(100) DEFAULT NULL,
  `Nit` varchar(100) DEFAULT NULL,
  `Nombre_Contacto` varchar(100) DEFAULT NULL,
  `Primer_Apellido` varchar(100) DEFAULT NULL,
  `Segundo_Apellido` varchar(100) DEFAULT NULL,
  `Cedula` varchar(50) DEFAULT NULL,
  `Tel_Fijo` varchar(150) DEFAULT NULL,
  `Tel_Celular` varchar(50) DEFAULT NULL,
  `Nro_Personas` int(11) DEFAULT 0,
  `Mail` varchar(50) DEFAULT NULL,
  `Hora_Llegada` varchar(50) DEFAULT NULL,
  `Motivo_Reserva` varchar(255) DEFAULT 'OTRO',
  `Decoracion` varchar(255) DEFAULT NULL,
  `Ubicacion` varchar(255) DEFAULT 'NINGUNA',
  `Ayudas_Electronicas` varchar(255) DEFAULT NULL,
  `Porcentaje_Descuento` int(11) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Observaciones` mediumtext DEFAULT NULL,
  `Copia_Correo_Cliente` mediumtext DEFAULT NULL,
  `Carta_Escogida` tinyint(4) DEFAULT 0,
  `Pendiente` tinyint(4) DEFAULT 0,
  `Cancelada` tinyint(4) DEFAULT 0,
  `Motivo_Cancelacion` varchar(255) DEFAULT NULL,
  `Atendida_Por` varchar(50) DEFAULT NULL,
  `Observacion_Carta_Abierta` varchar(255) DEFAULT NULL,
  `Empleado` varchar(100) DEFAULT NULL,
  `Nro_Interno` varchar(255) DEFAULT NULL,
  `Codigo_Motivo` int(11) DEFAULT 12,
  `Codigo_Ubicacion` int(11) DEFAULT 10,
  `Vista_x_T1` tinyint(4) NOT NULL DEFAULT 0,
  `Vista_x_T2` tinyint(4) NOT NULL DEFAULT 0,
  `Atencion_Post_Reserva` text DEFAULT NULL,
  `Id_Barrio` int(11) DEFAULT 0,
  `Modificada` tinyint(4) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Id_Cliente` double DEFAULT 0,
  PRIMARY KEY (`Id_Reserva`),
  KEY `Fecha_Registro` (`Fecha_Registro`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_resoluciones_facturas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_resoluciones_facturas` (
  `Id_Sede` int(11) DEFAULT 0,
  `Id_Resolucion` int(11) DEFAULT 0,
  `Nro_Resolucion` varchar(50) DEFAULT NULL,
  `Fecha_Resolucion` varchar(50) DEFAULT NULL,
  `Facturas_Autorizadas` varchar(50) DEFAULT NULL,
  `Nombre_Autorizado` varchar(50) DEFAULT NULL,
  `Nit_Autorizado` varchar(50) DEFAULT NULL,
  `Regimen` varchar(50) DEFAULT NULL,
  `Prefijo` varchar(10) DEFAULT NULL,
  `Facturacion_Manual` tinyint(4) DEFAULT 0,
  `Activa` tinyint(4) NOT NULL DEFAULT 0,
  `Fecha_Vence_Resolucion` varchar(50) DEFAULT NULL,
  `Numero_Vence_Resolucion` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_restaurantes_cantidad_pedido`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_restaurantes_cantidad_pedido` (
  `Id_Restaurante` int(11) NOT NULL DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Cantidad_Pedido` double NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_resumen_indicador_presupuesto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_resumen_indicador_presupuesto` (
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Sede` varchar(50) DEFAULT NULL,
  `Fecha_Inicial` varchar(50) DEFAULT NULL,
  `Fecha_Final` varchar(50) DEFAULT NULL,
  `Venta_Esperada_T1` double DEFAULT 0,
  `Venta_Actual_T1` double DEFAULT 0,
  `Diferencia_T1` double DEFAULT 0,
  `Cumplio_T1` float DEFAULT 0,
  `Venta_Esperada_T2` double DEFAULT 0,
  `Venta_Actual_T2` double DEFAULT 0,
  `Diferencia_T2` double DEFAULT 0,
  `Cumplio_T2` float DEFAULT 0,
  `Venta_Esperada_T` double DEFAULT 0,
  `Venta_Actual_T` double DEFAULT 0,
  `Diferencia_T` double DEFAULT 0,
  `Cumplio_T` float DEFAULT 0,
  `Sumar` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_resumen_indicador_presupuesto_acumulado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_resumen_indicador_presupuesto_acumulado` (
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Sede` varchar(50) DEFAULT NULL,
  `Fecha_Inicial` varchar(50) DEFAULT NULL,
  `Fecha_Final` varchar(50) DEFAULT NULL,
  `Venta_Esperada_T1` double DEFAULT 0,
  `Venta_Actual_T1` double DEFAULT 0,
  `Diferencia_T1` double DEFAULT 0,
  `Cumplio_T1` float DEFAULT 0,
  `Venta_Esperada_T2` double DEFAULT 0,
  `Venta_Actual_T2` double DEFAULT 0,
  `Diferencia_T2` double DEFAULT 0,
  `Cumplio_T2` float DEFAULT 0,
  `Venta_Esperada_T` double DEFAULT 0,
  `Venta_Actual_T` double DEFAULT 0,
  `Diferencia_T` double DEFAULT 0,
  `Cumplio_T` float DEFAULT 0,
  `Sumar` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_resumen_indicador_presupuesto_acumulado_1`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_resumen_indicador_presupuesto_acumulado_1` (
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Sede` varchar(50) DEFAULT NULL,
  `Fecha_Inicial` varchar(50) DEFAULT NULL,
  `Fecha_Final` varchar(50) DEFAULT NULL,
  `Venta_Esperada_T1` double DEFAULT 0,
  `Venta_Actual_T1` double DEFAULT 0,
  `Diferencia_T1` double DEFAULT 0,
  `Cumplio_T1` float DEFAULT 0,
  `Venta_Esperada_T2` double DEFAULT 0,
  `Venta_Actual_T2` double DEFAULT 0,
  `Diferencia_T2` double DEFAULT 0,
  `Cumplio_T2` float DEFAULT 0,
  `Venta_Esperada_T` double DEFAULT 0,
  `Venta_Actual_T` double DEFAULT 0,
  `Diferencia_T` double DEFAULT 0,
  `Cumplio_T` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_resumen_indicador_presupuesto_acumulado_2`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_resumen_indicador_presupuesto_acumulado_2` (
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Sede` varchar(50) DEFAULT NULL,
  `Fecha_Inicial` varchar(50) DEFAULT NULL,
  `Fecha_Final` varchar(50) DEFAULT NULL,
  `Venta_Esperada_T1` double DEFAULT 0,
  `Venta_Actual_T1` double DEFAULT 0,
  `Diferencia_T1` double DEFAULT 0,
  `Cumplio_T1` float DEFAULT 0,
  `Venta_Esperada_T2` double DEFAULT 0,
  `Venta_Actual_T2` double DEFAULT 0,
  `Diferencia_T2` double DEFAULT 0,
  `Cumplio_T2` float DEFAULT 0,
  `Venta_Esperada_T` double DEFAULT 0,
  `Venta_Actual_T` double DEFAULT 0,
  `Diferencia_T` double DEFAULT 0,
  `Cumplio_T` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_seguimiento_porciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_seguimiento_porciones` (
  `Id_Orden` int(11) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Concepto` varchar(50) DEFAULT '0',
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Id_Plato` int(11) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Nro_Factura` varchar(50) DEFAULT '0',
  `Cantidad_Actual` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_seguimiento_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_seguimiento_producto` (
  `Id_Seguimiento` int(11) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT '0',
  `Inicial` float DEFAULT 0,
  `Entrada` float DEFAULT 0,
  `Ventas` float DEFAULT 0,
  `Salida` float DEFAULT 0,
  `Total` float DEFAULT 0,
  `Observacion` varchar(50) DEFAULT '0'
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_separados_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_separados_detalle` (
  `Id_Registro` bigint(20) NOT NULL DEFAULT 0,
  `Item` int(11) NOT NULL DEFAULT 0,
  `Posicion` int(11) NOT NULL DEFAULT 0,
  `Precio_Actual` int(11) DEFAULT 0,
  `Cantidad` double DEFAULT 0,
  `Codigo_Producto` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id_Registro`,`Item`,`Posicion`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_soft_10`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_soft_10` (
  `Id_Sede` double DEFAULT 0,
  `Activa` tinyint(4) DEFAULT 0,
  `Remoto` tinyint(4) DEFAULT 0,
  `IpBd` varchar(200) DEFAULT NULL,
  `Bd` varchar(200) DEFAULT NULL,
  `Almacen` varchar(200) DEFAULT NULL,
  `Caja` tinyint(4) DEFAULT 0,
  `company_id` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_stock_porciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_stock_porciones` (
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Nombre_Plato` varchar(50) DEFAULT '0',
  `Cantidad_Actual` float DEFAULT 0,
  `Cantidad_Minima` float DEFAULT 0,
  `Cantidad_Maxima` float DEFAULT 0,
  `Cantidad_Compra` float DEFAULT 0,
  `Controlar` tinyint(1) DEFAULT 0,
  `Imprimir` tinyint(1) DEFAULT 0,
  `Cantidad_Fisico` decimal(19,4) DEFAULT 0.0000,
  `Cantidad_Venta` decimal(19,4) DEFAULT 0.0000,
  `Cantidad_Entrada` decimal(19,4) DEFAULT 0.0000,
  `Cantidad_Salida` decimal(19,4) DEFAULT 0.0000,
  `Und_Uso` int(11) DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_stocks_minimos_semana`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_stocks_minimos_semana` (
  `Semana` varchar(40) NOT NULL DEFAULT '0',
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Nombre_Plato` varchar(50) DEFAULT NULL,
  `Mes` varchar(50) DEFAULT '0',
  `Dia_Uno_Lunes` float DEFAULT 0,
  `Dia_Dos_Martes` float DEFAULT 0,
  `Dia_Tres_Miercoles` float DEFAULT 0,
  `Dia_Cuatro_Jueves` float DEFAULT 0,
  `Dia_Cinco_Viernes` float DEFAULT 0,
  `Dia_Seis_Sabado` float DEFAULT 0,
  `Dia_Siete_Domingo` float DEFAULT 0,
  `Dia_Ocho_Sabado_Mas_Domingo` int(11) DEFAULT 0,
  `Prom_Max_Uno` float DEFAULT 0,
  `Prom_Max_Dos` float DEFAULT 0,
  `Prom_Max_Tres` float DEFAULT 0,
  `Prom_Max_Cuatro` float DEFAULT 0,
  `Prom_Max_Cinco` float DEFAULT 0,
  `Prom_Max_Seis` float DEFAULT 0,
  `Prom_Max_Siete` float DEFAULT 0,
  `Prom_Max_Ocho` float DEFAULT 0,
  `Promedio_Venta_Mes` int(11) DEFAULT 0,
  `Stock_Critico` int(11) DEFAULT 0,
  `Centro_Produccion` tinyint(1) DEFAULT 0,
  `Nro_Semana` int(11) DEFAULT 0,
  `Año` int(11) DEFAULT 0,
  PRIMARY KEY (`Semana`,`Id_Grupo`,`Id_Item`),
  KEY `Nombre_Plato` (`Nombre_Plato`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_stocks_minimos_semana_insumos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_stocks_minimos_semana_insumos` (
  `Semana` varchar(50) DEFAULT NULL,
  `Id_Sede` int(11) DEFAULT 0,
  `Nombre_Sede` varchar(100) DEFAULT NULL,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Id_Insumo` int(11) DEFAULT 0,
  `Nombre_Insumo` varchar(100) DEFAULT NULL,
  `Nombre_Plato` varchar(100) DEFAULT NULL,
  `Tipo_Und_Minima` int(11) DEFAULT 0,
  `Nombre_Tipo_Und_Minima` varchar(100) DEFAULT NULL,
  `Und_Uso` int(11) DEFAULT 0,
  `Nombre_Unidad_Uso` varchar(100) DEFAULT NULL,
  `Dia_Uno_Lunes` float DEFAULT 0,
  `Dia_Dos_Martes` float DEFAULT 0,
  `Dia_Tres_Miercoles` float DEFAULT 0,
  `Dia_Cuatro_Jueves` float DEFAULT 0,
  `Dia_Cinco_Viernes` float DEFAULT 0,
  `Dia_Seis_Sabado` float DEFAULT 0,
  `Dia_Siete_Domingo` float DEFAULT 0,
  `Total_Unidades_Semana` int(11) DEFAULT 0,
  `Und_Minimas_Porcion` double DEFAULT 0,
  `Total_Unidades_Minimas` double DEFAULT 0,
  `Total_Consumo_Semana` double DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_stocks_minimos_semana_requisicion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_stocks_minimos_semana_requisicion` (
  `Posicion` int(11) DEFAULT 0,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Nro_Semana` int(11) DEFAULT 0,
  `Año_Semana` int(11) DEFAULT 0,
  `Producto` varchar(255) DEFAULT NULL,
  `Dia_Uno_Lunes` double DEFAULT 0,
  `Dia_Dos_Martes` double DEFAULT 0,
  `Dia_Tres_Miercoles` double DEFAULT 0,
  `Dia_Cuatro_Jueves` double DEFAULT 0,
  `Dia_Cinco_Viernes` double DEFAULT 0,
  `Dia_Seis_Sabado` double DEFAULT 0,
  `Dia_Siete_Domingo` double DEFAULT 0,
  `Inv_Actual_Sede` double DEFAULT 0,
  `Inv_Actual_Cp` double DEFAULT 0,
  `Total` double DEFAULT 0,
  `Diferencia` double DEFAULT 0,
  `Cantidad_Requisicion` double DEFAULT 0,
  `Bodega` int(11) DEFAULT 0,
  `Agrupar` int(11) DEFAULT 0,
  `Und_Uso` int(11) DEFAULT 0,
  `Nombre_Und_Uso` varchar(255) DEFAULT NULL,
  `Observacion` longtext DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_stocks_minimos_semana_sede`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_stocks_minimos_semana_sede` (
  `Semana` varchar(40) NOT NULL DEFAULT '0',
  `Id_Grupo` int(11) NOT NULL DEFAULT 0,
  `Id_Item` int(11) NOT NULL DEFAULT 0,
  `Nombre_Plato` varchar(50) DEFAULT NULL,
  `Mes` varchar(50) DEFAULT '0',
  `Dia_Uno_Lunes` float DEFAULT 0,
  `Dia_Dos_Martes` float DEFAULT 0,
  `Dia_Tres_Miercoles` float DEFAULT 0,
  `Dia_Cuatro_Jueves` float DEFAULT 0,
  `Dia_Cinco_Viernes` float DEFAULT 0,
  `Dia_Seis_Sabado` float DEFAULT 0,
  `Dia_Siete_Domingo` float DEFAULT 0,
  `Dia_Ocho_Sabado_Mas_Domingo` int(11) DEFAULT 0,
  `Prom_Max_Uno` float DEFAULT 0,
  `Prom_Max_Dos` float DEFAULT 0,
  `Prom_Max_Tres` float DEFAULT 0,
  `Prom_Max_Cuatro` float DEFAULT 0,
  `Prom_Max_Cinco` float DEFAULT 0,
  `Prom_Max_Seis` float DEFAULT 0,
  `Prom_Max_Siete` float DEFAULT 0,
  `Prom_Max_Ocho` float DEFAULT 0,
  `Promedio_Venta_Mes` int(11) DEFAULT 0,
  `Stock_Critico` int(11) DEFAULT 0,
  `Centro_Produccion` tinyint(1) DEFAULT 0,
  `Nro_Semana` int(11) DEFAULT 0,
  `Año` int(11) DEFAULT 0,
  PRIMARY KEY (`Semana`,`Id_Grupo`,`Id_Item`),
  KEY `Nombre_Plato` (`Nombre_Plato`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_stocks_minimos_semana_servidor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_stocks_minimos_semana_servidor` (
  `Semana` varchar(50) DEFAULT NULL,
  `Id_Grupo` int(11) DEFAULT 0,
  `Id_Item` int(11) DEFAULT 0,
  `Nombre_Plato` varchar(50) DEFAULT NULL,
  `Mes` varchar(50) DEFAULT NULL,
  `Dia_Uno_Lunes` float DEFAULT 0,
  `Dia_Dos_Martes` float DEFAULT 0,
  `Dia_Tres_Miercoles` float DEFAULT 0,
  `Dia_Cuatro_Jueves` float DEFAULT 0,
  `Dia_Cinco_Viernes` float DEFAULT 0,
  `Dia_Seis_Sabado` float DEFAULT 0,
  `Dia_Siete_Domingo` float DEFAULT 0,
  `Dia_Ocho_Sabado_Mas_Domingo` int(11) DEFAULT 0,
  `Prom_Max_Uno` float DEFAULT 0,
  `Prom_Max_Dos` float DEFAULT 0,
  `Prom_Max_Tres` float DEFAULT 0,
  `Prom_Max_Cuatro` float DEFAULT 0,
  `Prom_Max_Cinco` float DEFAULT 0,
  `Prom_Max_Seis` float DEFAULT 0,
  `Prom_Max_Siete` float DEFAULT 0,
  `Prom_Max_Ocho` float DEFAULT 0,
  `Promedio_Venta_Mes` int(11) DEFAULT 0,
  `Stock_Critico` int(11) DEFAULT 0,
  `Centro_Produccion` tinyint(4) DEFAULT 0,
  `Inv_Actual_Sede` int(11) DEFAULT 0,
  `Inv_Actual_Cp` int(11) DEFAULT 0,
  `Total` int(11) DEFAULT 0,
  `Diferencia` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_tarjetas_baucher`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_tarjetas_baucher` (
  `Id_Tarjeta` int(11) NOT NULL DEFAULT 0,
  `Id_Sede` varchar(50) DEFAULT NULL,
  `Nombre_Largo` varchar(50) DEFAULT NULL,
  `Nombre_Corto` varchar(50) DEFAULT NULL,
  `Banco` varchar(50) DEFAULT NULL,
  `Porcentaje` float DEFAULT 0,
  `Activa` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`Id_Tarjeta`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_temporal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_temporal` (
  `di` text DEFAULT NULL,
  `mi` varchar(50) DEFAULT NULL,
  `a1i` varchar(50) DEFAULT NULL,
  `a2i` varchar(50) DEFAULT NULL,
  `df` varchar(50) DEFAULT NULL,
  `mf` varchar(50) DEFAULT NULL,
  `a1f` varchar(50) DEFAULT NULL,
  `a2f` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_tipificaciones_descuentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_tipificaciones_descuentos` (
  `Id_Tipificacion` int(11) NOT NULL DEFAULT 0,
  `Nombre` varchar(100) DEFAULT NULL,
  `Info_Adicional` tinyint(4) DEFAULT 0,
  `Enviar_Correo` tinyint(4) DEFAULT 0,
  `Enviada_MySql` tinyint(4) DEFAULT 0,
  `Desactivada` tinyint(4) DEFAULT 0,
  `Texto` tinyint(4) DEFAULT 0,
  `Combo` tinyint(4) DEFAULT 0,
  `Exigir_Info_Cliente` tinyint(4) DEFAULT 0,
  `Valor_Descuento_Pesos` double DEFAULT 0,
  `Valor_Descuento_Porcentaje` int(11) DEFAULT 0,
  PRIMARY KEY (`Id_Tipificacion`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_tipo_empleado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_tipo_empleado` (
  `Cod_Tipo` int(11) NOT NULL DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Porcentaje` double DEFAULT 0,
  PRIMARY KEY (`Cod_Tipo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_tipo_moneda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_tipo_moneda` (
  `Tipo_Moneda` int(11) NOT NULL DEFAULT 0,
  `Nombre` varchar(50) DEFAULT NULL,
  `Taza` float NOT NULL DEFAULT 0,
  PRIMARY KEY (`Tipo_Moneda`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_variables_del_sistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_variables_del_sistema` (
  `Id_Sede` int(11) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Dia` varchar(50) DEFAULT NULL,
  `Turno` int(11) DEFAULT 0,
  `Porcentaje_Ganancia` float DEFAULT 0,
  `Base_Incial` int(11) DEFAULT 0,
  `Base_Final` int(11) DEFAULT 0,
  `Cerrar_Dia` tinyint(4) DEFAULT 0,
  `Imprimir_Tirilla_Comanda` tinyint(4) DEFAULT 0,
  `Actualizar_Informacion` tinyint(4) DEFAULT 0,
  `Actualizar_Tablas_Manualmente` tinyint(4) DEFAULT 0,
  `Modulo_Mesas` tinyint(4) DEFAULT 0,
  `Modulo_To_Go` tinyint(4) DEFAULT 0,
  `Tipo_Negocio` int(11) DEFAULT 0,
  `Obligado_A_Facturar` tinyint(4) DEFAULT 0,
  `Skin_Usado` int(11) DEFAULT 0,
  `Skin_Usado_Comandera` int(11) DEFAULT 0,
  `Pedir_Cantidad_Mod_Mesas` tinyint(4) DEFAULT 0,
  `Pedir_Cantidad_Mod_To_Go` tinyint(4) DEFAULT 0,
  `Pedir_Cantidad_Comenzales` tinyint(4) DEFAULT 0,
  `Nombre_Archivo_Exe` varchar(100) DEFAULT '0',
  `Pedir_Monto` tinyint(4) DEFAULT 0,
  `Mostrar_Generar_Archivo` tinyint(4) DEFAULT 0,
  `Pregunta_Imprimir_Factura` tinyint(4) DEFAULT 0,
  `Imprimir_Monto_Pagado` tinyint(4) DEFAULT 0,
  `Pedir_Valor_Venta` tinyint(4) DEFAULT 0,
  `Comanda_Domicilio_Caja` tinyint(4) DEFAULT 0,
  `Vendedor_Automatico` tinyint(4) DEFAULT 0,
  `Imprimir_Comanda_Plazoleta` tinyint(4) DEFAULT 0,
  `Pedir_Turno` tinyint(4) DEFAULT 0,
  `Texto_Turno` varchar(20) DEFAULT '0',
  `Activar_Inv_Fisico_Automatico` tinyint(4) DEFAULT 0,
  `Pedir_Clave_Mesero` tinyint(4) DEFAULT 0,
  `Usar_Comanda_Corta` tinyint(4) DEFAULT 0,
  `Usar_Referencia_Almacen` tinyint(4) DEFAULT 0,
  `Incluir_Codigo_Barras_Venta` tinyint(4) DEFAULT 0,
  `Sumar_Efectivo_Domicilio_Caja` tinyint(4) DEFAULT 0,
  `Sumar_Efectivo_Propina_Caja` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_venta_dia_semana_periodo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_venta_dia_semana_periodo` (
  `Sede` varchar(250) DEFAULT NULL,
  `Fecha` varchar(50) DEFAULT NULL,
  `Lunes_T1` float NOT NULL DEFAULT 0,
  `Lunes_T2` float NOT NULL DEFAULT 0,
  `Cuenta_Lunes` float DEFAULT 0,
  `Martes_T1` float DEFAULT 0,
  `Martes_T2` float DEFAULT 0,
  `Cuenta_Martes` float DEFAULT 0,
  `Miercoles_T1` float DEFAULT 0,
  `Miercoles_T2` float DEFAULT 0,
  `Cuenta_Miercoles` float DEFAULT 0,
  `Jueves_T1` float DEFAULT 0,
  `Jueves_T2` float DEFAULT 0,
  `Cuenta_Jueves` float DEFAULT 0,
  `Viernes_T1` float DEFAULT 0,
  `Viernes_T2` float DEFAULT 0,
  `Cuenta_Viernes` float DEFAULT 0,
  `Sabado_T1` float DEFAULT 0,
  `Sabado_T2` float DEFAULT 0,
  `Cuenta_Sabado` float DEFAULT 0,
  `Domingo_T1` float DEFAULT 0,
  `Domingo_T2` float DEFAULT 0,
  `Cuenta_Domingo` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_venta_promedio_mes_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_venta_promedio_mes_detalle` (
  `Sede` varchar(50) DEFAULT NULL,
  `Mes_Evaluado` int(11) NOT NULL DEFAULT 0,
  `Año_Evaluado` int(11) DEFAULT 0,
  `Venta_Mes` double DEFAULT 0,
  `Venta_Mes_T1` double DEFAULT 0,
  `Venta_Mes_T2` double DEFAULT 0,
  `Porcentaje_Mes_T1` double DEFAULT 0,
  `Porcentaje_Mes_T2` double DEFAULT 0,
  `Lunes_T1` float NOT NULL DEFAULT 0,
  `Lunes_T2` float NOT NULL DEFAULT 0,
  `Cuenta_Lunes` float DEFAULT 0,
  `Martes_T1` float DEFAULT 0,
  `Martes_T2` float DEFAULT 0,
  `Cuenta_Martes` float DEFAULT 0,
  `Miercoles_T1` float DEFAULT 0,
  `Miercoles_T2` float DEFAULT 0,
  `Cuenta_Miercoles` float DEFAULT 0,
  `Jueves_T1` float DEFAULT 0,
  `Jueves_T2` float DEFAULT 0,
  `Cuenta_Jueves` float DEFAULT 0,
  `Viernes_T1` float DEFAULT 0,
  `Viernes_T2` float DEFAULT 0,
  `Cuenta_Viernes` float DEFAULT 0,
  `Sabado_T1` float DEFAULT 0,
  `Sabado_T2` float DEFAULT 0,
  `Cuenta_Sabado` float DEFAULT 0,
  `Domingo_T1` float DEFAULT 0,
  `Domingo_T2` float DEFAULT 0,
  `Cuenta_Domingo` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_venta_promedio_mes_resumen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_venta_promedio_mes_resumen` (
  `Sede` varchar(50) DEFAULT NULL,
  `Mes_Evaluado` int(11) NOT NULL DEFAULT 0,
  `Año_Evaluado` int(11) DEFAULT 0,
  `Promedio_Venta_Mes` double DEFAULT 0,
  `Promedio_Venta_Mes_T1` double DEFAULT 0,
  `Promedio_Venta_Mes_T2` double DEFAULT 0,
  `Promedio_Porcentaje_Mes_T1` double DEFAULT 0,
  `Promedio_Porcentaje_Mes_T2` double DEFAULT 0,
  `Promedio_Lunes_T1` float NOT NULL DEFAULT 0,
  `Promedio_Lunes_T2` float NOT NULL DEFAULT 0,
  `Promedio_Martes_T1` float DEFAULT 0,
  `Promedio_Martes_T2` float DEFAULT 0,
  `Promedio_Miercoles_T1` float DEFAULT 0,
  `Promedio_Miercoles_T2` float DEFAULT 0,
  `Promedio_Jueves_T1` float DEFAULT 0,
  `Promedio_Jueves_T2` float DEFAULT 0,
  `Promedio_Viernes_T1` float DEFAULT 0,
  `Promedio_Viernes_T2` float DEFAULT 0,
  `Promedio_Sabado_T1` float DEFAULT 0,
  `Promedio_Sabado_T2` float DEFAULT 0,
  `Promedio_Domingo_T1` float DEFAULT 0,
  `Promedio_Domingo_T2` float DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_ventas_ano`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_ventas_ano` (
  `Id_Mes` int(11) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Efectivo` int(11) DEFAULT 0,
  `Credito` int(11) DEFAULT 0,
  `Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Interno` int(11) DEFAULT 0,
  `Total` int(11) DEFAULT 0,
  `Empresa` varchar(250) DEFAULT '0',
  `Propina_Extra` int(11) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=COMPACT;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_ventas_mes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_ventas_mes` (
  `Factura` varchar(50) DEFAULT '0',
  `Fecha` varchar(50) DEFAULT NULL,
  `Efectivo1` int(11) DEFAULT 0,
  `Efectivo2` int(11) DEFAULT 0,
  `Tarjeta1` int(11) DEFAULT 0,
  `Tarjeta2` int(11) DEFAULT 0,
  `Propina1` int(11) DEFAULT 0,
  `Propina2` int(11) DEFAULT 0,
  `Interno` int(11) DEFAULT 0,
  `Total1` int(11) DEFAULT 0,
  `Total2` int(11) DEFAULT 0,
  `Total` int(11) DEFAULT 0,
  `Empresa` varchar(250) DEFAULT NULL,
  `Propina_Extra1` int(11) DEFAULT 0,
  `Propina_Extra2` int(11) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0,
  `Turno` int(11) DEFAULT 0,
  `Nro_Comenzales` int(11) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_ventas_mes_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_ventas_mes_factura` (
  `Id_Mes` int(11) DEFAULT 0,
  `Fecha` varchar(50) DEFAULT NULL,
  `Efectivo` int(11) DEFAULT 0,
  `Credito` int(11) DEFAULT 0,
  `Debito` int(11) DEFAULT 0,
  `Propina` int(11) DEFAULT 0,
  `Interno` int(11) DEFAULT 0,
  `Total` int(11) DEFAULT 0,
  `Empresa` varchar(250) DEFAULT NULL,
  `Propina_Extra` int(11) DEFAULT 0,
  `Arreglo` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `temp_zonas_asientos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_zonas_asientos` (
  `Id_Sede` int(11) DEFAULT 0,
  `Id_Zona` int(11) DEFAULT 0,
  `Ubicacion` varchar(50) DEFAULT NULL,
  `Nro_Asientos` int(11) DEFAULT 0,
  `Activa` tinyint(4) DEFAULT 0,
  `Zona_Dinamica` tinyint(4) DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

