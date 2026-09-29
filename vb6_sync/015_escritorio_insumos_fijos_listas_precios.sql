-- ============================================================
-- Script ESCRITORIO (BD principal de cada sede) — acompaña a la migración web 015
--
-- 1. inventario_porciones_plato: agregar Enviada_MySql para poder
--    sincronizar solo lo pendiente (la tabla no lo tenía).
--    Llave: (Id_Plato, Id_Grupo, Id_Item) — requerida por el UPDATE de marcado
--    y por la descarga web → escritorio.
--
-- 2. lista_precios_cliente_cabecera: cabecera de las listas de precios por
--    cliente. El detalle sigue en lista_precios_cliente (relación Id_Lista).
--    Id_Lista NO es autoincremental: lo genera la WEB y aquí solo se descarga.
--
-- Ejecutar UNA vez por BD de escritorio. Si una columna/índice ya existe,
-- MySQL devolverá error en esa línea: ignorarlo y continuar.
-- ============================================================

ALTER TABLE inventario_porciones_plato
    ADD COLUMN Enviada_MySql TINYINT(4) NOT NULL DEFAULT 0;

-- Verificar duplicados ANTES de crear la llave (debe devolver 0 filas):
-- SELECT Id_Plato, Id_Grupo, Id_Item, COUNT(*) FROM inventario_porciones_plato
--  GROUP BY Id_Plato, Id_Grupo, Id_Item HAVING COUNT(*) > 1;
ALTER TABLE inventario_porciones_plato
    ADD PRIMARY KEY (Id_Plato, Id_Grupo, Id_Item);


-- 3. lista_precios_cliente: la subida pasa a enviar solo Enviada_MySql = 0.
--    Varias BD ya tienen la columna (ej. maduritos); si existe, esta línea
--    dará error "Duplicate column" y se ignora.
ALTER TABLE lista_precios_cliente
    ADD COLUMN Enviada_MySql TINYINT(4) DEFAULT 0;


-- 4. proveedores: sincronización a la web (suppliers) solo de lo pendiente.
ALTER TABLE proveedores
    ADD COLUMN Enviada_MySql TINYINT(4) NOT NULL DEFAULT 0;


-- 5. insumos_proveedor / insumos_forma_medida: sincronización a la web.
ALTER TABLE insumos_proveedor
    ADD COLUMN Enviada_MySql TINYINT(4) NOT NULL DEFAULT 0;
ALTER TABLE insumos_forma_medida
    ADD COLUMN Enviada_MySql TINYINT(4) NOT NULL DEFAULT 0;


-- 6. clientes: sincronización a la web. Varias BD ya tienen la columna (ej. maduritos):
--    si existe, esta línea dará "Duplicate column" y se ignora.
ALTER TABLE clientes
    ADD COLUMN Enviada_MySql TINYINT(4) DEFAULT 0;


CREATE TABLE IF NOT EXISTS lista_precios_cliente_cabecera (
    Id_Lista      INT(11)      NOT NULL DEFAULT 0,
    Id_Cliente    INT(11)      NOT NULL DEFAULT 0,
    Nombre        VARCHAR(100) NOT NULL DEFAULT '',
    Fecha         DATE         DEFAULT NULL,
    Activa        TINYINT(4)   NOT NULL DEFAULT 1,
    Usuario       VARCHAR(50)  DEFAULT NULL,
    Observacion   VARCHAR(255) DEFAULT NULL,
    Enviada_MySql TINYINT(4)   NOT NULL DEFAULT 1,
    PRIMARY KEY (Id_Lista),
    KEY idx_lpcc_cliente (Id_Cliente, Activa)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
