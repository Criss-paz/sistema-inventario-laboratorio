-- =============================================================================
-- Archivo:      006_permisos.sql
-- Propósito:    Permisos configurables por rol: el administrador decide qué
--               puede hacer cada rol y puede crear roles nuevos.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  Migración aditiva. Hasta la Entrega 4 el reparto de
--               permisos estaba fijo en el código para 3 roles. Aquí pasa a
--               ser datos:
--                 permiso      catálogo de acciones que se pueden conceder.
--                              Consultar (inventario, lotes, historial,
--                              reportes) no es un permiso: lo tienen todos.
--                 rol_permiso  qué permisos tiene cada rol (N:M).
--               El rol "Administrador" tiene siempre todos los permisos,
--               esté o no en rol_permiso (así nadie puede dejar el sistema
--               sin quien lo administre).
--
--               Cada permiso declara el nivel de base de datos que necesita
--               (ENCARGADO o ADMINISTRADOR). Con eso, fn_rol_bd()
--               (sql/procedures/004_permisos.sql) elige para cada rol el rol
--               de PostgreSQL más bajo que cubre sus permisos, y la app lo
--               adopta con SET ROLE. La app aplica el permiso exacto; la base,
--               el nivel (defensa en profundidad, igual que antes).
--
-- Reglas de negocio que materializa:
--   RN-28  Los permisos de cada rol los define el Administrador; consultar
--          es común a todos los roles.
--   RN-29  El rol Administrador conserva siempre todos los permisos y no se
--          puede renombrar ni eliminar. Un rol con usuarios no se elimina.
--
-- Dependencias: 001_schema.sql, dml/001_seed.sql (roles iniciales)
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 006_permisos.sql
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS permiso (
    codigo      VARCHAR(30)  NOT NULL,
    nombre      VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    nivel_bd    VARCHAR(15)  NOT NULL,
    orden       SMALLINT     NOT NULL,
    CONSTRAINT pk_permiso PRIMARY KEY (codigo),
    CONSTRAINT uq_permiso_nombre UNIQUE (nombre),
    CONSTRAINT ck_permiso_codigo CHECK (codigo ~ '^[A-Z_]+$'),
    CONSTRAINT ck_permiso_nivel CHECK (nivel_bd IN ('ENCARGADO', 'ADMINISTRADOR'))
);

COMMENT ON TABLE permiso IS
    'Acciones que se conceden a un rol (RN-28). nivel_bd: rol de PostgreSQL mínimo que la acción necesita.';

CREATE TABLE IF NOT EXISTS rol_permiso (
    id_rol  INTEGER     NOT NULL,
    codigo  VARCHAR(30) NOT NULL,
    CONSTRAINT pk_rol_permiso PRIMARY KEY (id_rol, codigo),
    -- CASCADE: al eliminar un rol (sin usuarios) se van sus permisos.
    CONSTRAINT fk_rol_permiso_rol FOREIGN KEY (id_rol)
        REFERENCES rol (id_rol) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rol_permiso_permiso FOREIGN KEY (codigo)
        REFERENCES permiso (codigo) ON DELETE RESTRICT ON UPDATE CASCADE
);

COMMENT ON TABLE rol_permiso IS 'Permisos concedidos a cada rol (RN-28).';

INSERT INTO permiso (codigo, nombre, descripcion, nivel_bd, orden) VALUES
    ('REGISTRAR_ENTRADAS', 'Registrar entradas',               'Compras y recepciones: crea o alimenta un lote',                   'ENCARGADO',     10),
    ('REGISTRAR_SALIDAS',  'Registrar salidas',                'Consumo de insumos, repartido por FEFO',                           'ENCARGADO',     20),
    ('DEVOLVER_SALIDAS',   'Devolver salidas',                 'Corregir una salida equivocada reponiendo la existencia',          'ENCARGADO',     30),
    ('CORREGIR_ENTRADAS',  'Corregir entradas',                'Cantidad, precio, proveedor, lote o vencimiento, con motivo',      'ADMINISTRADOR', 40),
    ('EDITAR_LOTES',       'Corregir datos de un lote',        'Número, proveedor, fechas y estado; nunca su existencia',          'ADMINISTRADOR', 50),
    ('PRODUCTOS',          'Productos y categorías',           'Crear, editar y dar de baja productos y categorías',               'ADMINISTRADOR', 60),
    ('PROVEEDORES',        'Proveedores y precios',            'Crear y editar proveedores y los productos que suministran',       'ADMINISTRADOR', 70),
    ('EXAMENES',           'Exámenes',                         'Crear y editar exámenes y los insumos que consumen',               'ADMINISTRADOR', 80),
    ('USUARIOS',           'Usuarios y roles',                 'Crear usuarios, asignar roles y definir sus permisos',             'ADMINISTRADOR', 90),
    ('RESPALDO',           'Descargar respaldo',               'Copia completa de la base de datos',                               'ADMINISTRADOR', 100),
    ('BITACORA',           'Ver la bitácora',                  'Quién hizo qué y cuándo en el sistema',                            'ADMINISTRADOR', 110)
ON CONFLICT (codigo) DO NOTHING;

-- El mismo reparto que había fijo en el código (Entrega 4).
INSERT INTO rol_permiso (id_rol, codigo)
SELECT r.id_rol, p.codigo
  FROM rol r
  JOIN permiso p ON (r.nombre = 'Administrador')
                 OR (r.nombre = 'Encargado de inventario'
                     AND p.codigo IN ('REGISTRAR_ENTRADAS', 'REGISTRAR_SALIDAS', 'DEVOLVER_SALIDAS'))
ON CONFLICT DO NOTHING;

COMMIT;

-- Fin de 006_permisos.sql
