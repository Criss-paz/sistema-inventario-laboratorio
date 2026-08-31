-- =============================================================================
-- Archivo:      001_schema.sql
-- Propósito:    DDL completo del esquema de la base de datos (Entrega 2)
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/entrega-2/Bitacora-IA.md para el registro de uso.
-- Descripción:  Crea las 11 tablas del modelo relacional documentado en
--               docs/entrega-2/modelo-relacional.md y docs/entrega-2/normalizacion-3fn.md,
--               en orden de dependencia de FK, con PK, FK, UNIQUE, CHECK y DEFAULT.
-- Dependencias: ninguna — primer script a ejecutar sobre una base de datos
--               PostgreSQL vacía (crear la BD `inventario_laboratorio` antes).
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 001_schema.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: rol
-- Catálogo de roles de acceso. RN-14, RF-03, RF-04.
-- -----------------------------------------------------------------------------
CREATE TABLE rol (
    id_rol      INTEGER GENERATED ALWAYS AS IDENTITY,
    nombre      VARCHAR(50)  NOT NULL,
    descripcion VARCHAR(255),
    CONSTRAINT pk_rol PRIMARY KEY (id_rol),
    CONSTRAINT uq_rol_nombre UNIQUE (nombre)
);

-- -----------------------------------------------------------------------------
-- Tabla: usuario
-- Cuentas de acceso al sistema. RF-01 a RF-05, RNF-04/05, RN-14, RN-15.
-- -----------------------------------------------------------------------------
CREATE TABLE usuario (
    id_usuario     INTEGER GENERATED ALWAYS AS IDENTITY,
    id_rol         INTEGER      NOT NULL,
    nombre         VARCHAR(100) NOT NULL,
    usuario        VARCHAR(50)  NOT NULL,
    password_hash  VARCHAR(255) NOT NULL, -- nunca texto plano (RN-15): hash generado por werkzeug.security
    estado         BOOLEAN      NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP    NOT NULL DEFAULT now(),
    CONSTRAINT pk_usuario PRIMARY KEY (id_usuario),
    CONSTRAINT uq_usuario_usuario UNIQUE (usuario),
    CONSTRAINT fk_usuario_rol FOREIGN KEY (id_rol)
        REFERENCES rol (id_rol) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------
-- Tabla: categoria
-- Clasificación de productos. RF-09, RF-10, RN-13.
-- -----------------------------------------------------------------------------
CREATE TABLE categoria (
    id_categoria INTEGER GENERATED ALWAYS AS IDENTITY,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  VARCHAR(255),
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_categoria PRIMARY KEY (id_categoria),
    CONSTRAINT uq_categoria_nombre UNIQUE (nombre)
);

-- -----------------------------------------------------------------------------
-- Tabla: producto
-- Catálogo de productos/insumos. RF-06 a RF-10, RN-10, RN-13.
-- requiere_vencimiento materializa RN-07 (decisión de Fase 2, autorizada por el equipo).
-- -----------------------------------------------------------------------------
CREATE TABLE producto (
    id_producto           INTEGER GENERATED ALWAYS AS IDENTITY,
    id_categoria          INTEGER       NOT NULL,
    codigo                VARCHAR(30)   NOT NULL,
    nombre                VARCHAR(150)  NOT NULL,
    descripcion           VARCHAR(255),
    unidad_medida         VARCHAR(20)   NOT NULL,
    stock_minimo          NUMERIC(10,2) NOT NULL DEFAULT 0,
    requiere_vencimiento  BOOLEAN       NOT NULL DEFAULT TRUE,
    estado                BOOLEAN       NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_producto PRIMARY KEY (id_producto),
    CONSTRAINT uq_producto_codigo UNIQUE (codigo),
    CONSTRAINT ck_producto_unidad_medida CHECK (length(trim(unidad_medida)) > 0),
    CONSTRAINT ck_producto_stock_minimo CHECK (stock_minimo >= 0),
    CONSTRAINT fk_producto_categoria FOREIGN KEY (id_categoria)
        REFERENCES categoria (id_categoria) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------
-- Tabla: proveedor
-- RF-11 a RF-13.
-- -----------------------------------------------------------------------------
CREATE TABLE proveedor (
    id_proveedor INTEGER GENERATED ALWAYS AS IDENTITY,
    nombre       VARCHAR(150) NOT NULL,
    nit          VARCHAR(20)  NOT NULL,
    telefono     VARCHAR(20),
    correo       VARCHAR(150),
    direccion    VARCHAR(255),
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_proveedor PRIMARY KEY (id_proveedor),
    CONSTRAINT uq_proveedor_nit UNIQUE (nit)
);

-- -----------------------------------------------------------------------------
-- Tabla: lote
-- Control de lotes/vencimientos/existencia. RF-14 a RF-19, RN-01, RN-05 a RN-07, RN-12.
-- numero_lote es único POR PRODUCTO (RN-06), no global.
-- -----------------------------------------------------------------------------
CREATE TABLE lote (
    id_lote              INTEGER GENERATED ALWAYS AS IDENTITY,
    id_producto          INTEGER       NOT NULL,
    id_proveedor         INTEGER       NOT NULL,
    numero_lote          VARCHAR(50)   NOT NULL,
    fecha_ingreso        DATE          NOT NULL DEFAULT CURRENT_DATE,
    fecha_vencimiento    DATE,
    cantidad_disponible  NUMERIC(10,2) NOT NULL DEFAULT 0,
    estado               BOOLEAN       NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_lote PRIMARY KEY (id_lote),
    CONSTRAINT uq_lote_producto_numero UNIQUE (id_producto, numero_lote),
    CONSTRAINT ck_lote_cantidad_disponible CHECK (cantidad_disponible >= 0), -- RN-01
    CONSTRAINT ck_lote_fecha_vencimiento CHECK (fecha_vencimiento IS NULL OR fecha_vencimiento >= fecha_ingreso),
    CONSTRAINT fk_lote_producto FOREIGN KEY (id_producto)
        REFERENCES producto (id_producto) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_lote_proveedor FOREIGN KEY (id_proveedor)
        REFERENCES proveedor (id_proveedor) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------
-- Tabla: movimiento
-- Encabezado de entrada/salida. RF-20, RF-21, RF-26 a RF-28, RN-08, RN-09.
-- -----------------------------------------------------------------------------
CREATE TABLE movimiento (
    id_movimiento   INTEGER GENERATED ALWAYS AS IDENTITY,
    id_usuario      INTEGER      NOT NULL,
    tipo_movimiento VARCHAR(10)  NOT NULL,
    fecha_hora      TIMESTAMP    NOT NULL DEFAULT now(),
    observacion     VARCHAR(255),
    CONSTRAINT pk_movimiento PRIMARY KEY (id_movimiento),
    CONSTRAINT ck_movimiento_tipo CHECK (tipo_movimiento IN ('ENTRADA', 'SALIDA')),
    CONSTRAINT fk_movimiento_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE -- RF-27/RN-08
);

-- -----------------------------------------------------------------------------
-- Tabla: detalle_movimiento
-- Resuelve la relación conceptual N:M MOVIMIENTO-LOTE (RN-18). RF-22, RF-23.
-- -----------------------------------------------------------------------------
CREATE TABLE detalle_movimiento (
    id_detalle      INTEGER GENERATED ALWAYS AS IDENTITY,
    id_movimiento   INTEGER       NOT NULL,
    id_lote         INTEGER       NOT NULL,
    cantidad        NUMERIC(10,2) NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT pk_detalle_movimiento PRIMARY KEY (id_detalle),
    CONSTRAINT ck_detalle_cantidad CHECK (cantidad > 0),
    CONSTRAINT ck_detalle_precio_unitario CHECK (precio_unitario >= 0),
    CONSTRAINT fk_detalle_movimiento FOREIGN KEY (id_movimiento)
        REFERENCES movimiento (id_movimiento) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_detalle_lote FOREIGN KEY (id_lote)
        REFERENCES lote (id_lote) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------
-- Tabla: examen_laboratorio
-- Catálogo de exámenes clínicos. RF-36, RF-37.
-- -----------------------------------------------------------------------------
CREATE TABLE examen_laboratorio (
    id_examen      INTEGER GENERATED ALWAYS AS IDENTITY,
    nombre_examen  VARCHAR(150) NOT NULL,
    descripcion    VARCHAR(255),
    codigo_interno VARCHAR(30)  NOT NULL,
    CONSTRAINT pk_examen_laboratorio PRIMARY KEY (id_examen),
    CONSTRAINT uq_examen_codigo_interno UNIQUE (codigo_interno)
);

-- -----------------------------------------------------------------------------
-- Tabla puente: proveedor_producto (relación "Suministra", N:M). RN-16, RF-39.
-- -----------------------------------------------------------------------------
CREATE TABLE proveedor_producto (
    id_proveedor  INTEGER       NOT NULL,
    id_producto   INTEGER       NOT NULL,
    precio_compra NUMERIC(10,2) NOT NULL,
    CONSTRAINT pk_proveedor_producto PRIMARY KEY (id_proveedor, id_producto),
    CONSTRAINT ck_proveedor_producto_precio CHECK (precio_compra >= 0),
    CONSTRAINT fk_proveedor_producto_proveedor FOREIGN KEY (id_proveedor)
        REFERENCES proveedor (id_proveedor) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_proveedor_producto_producto FOREIGN KEY (id_producto)
        REFERENCES producto (id_producto) ON DELETE CASCADE ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------
-- Tabla puente: examen_producto (relación "Requiere", N:M). RN-17, RF-38.
-- -----------------------------------------------------------------------------
CREATE TABLE examen_producto (
    id_examen           INTEGER       NOT NULL,
    id_producto         INTEGER       NOT NULL,
    cantidad_requerida  NUMERIC(10,2) NOT NULL,
    CONSTRAINT pk_examen_producto PRIMARY KEY (id_examen, id_producto),
    CONSTRAINT ck_examen_producto_cantidad CHECK (cantidad_requerida > 0),
    CONSTRAINT fk_examen_producto_examen FOREIGN KEY (id_examen)
        REFERENCES examen_laboratorio (id_examen) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_examen_producto_producto FOREIGN KEY (id_producto)
        REFERENCES producto (id_producto) ON DELETE CASCADE ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------
-- Índices de apoyo para las FK más consultadas por la app web (listados/filtros).
-- No son restricciones de integridad, son de rendimiento (RNF-14).
-- -----------------------------------------------------------------------------
CREATE INDEX ix_producto_categoria ON producto (id_categoria);
CREATE INDEX ix_lote_producto ON lote (id_producto);
CREATE INDEX ix_lote_proveedor ON lote (id_proveedor);
CREATE INDEX ix_movimiento_usuario ON movimiento (id_usuario);
CREATE INDEX ix_detalle_movimiento_movimiento ON detalle_movimiento (id_movimiento);
CREATE INDEX ix_detalle_movimiento_lote ON detalle_movimiento (id_lote);

-- Fin de 001_schema.sql
