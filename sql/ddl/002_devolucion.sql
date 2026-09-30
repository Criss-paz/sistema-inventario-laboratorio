-- =============================================================================
-- Archivo:      002_devolucion.sql
-- Propósito:    Habilitar la devolución de una salida registrada por error.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  Migración aditiva sobre el esquema de 001_schema.sql. No altera
--               ninguna columna existente ni borra datos: agrega el tipo de
--               movimiento DEVOLUCION y las dos columnas que lo sostienen.
--
--               Por qué un movimiento y no un UPDATE: el trigger
--               trg_historial_inmutable prohíbe modificar o borrar un
--               movimiento ya registrado (RN-09) y su propio mensaje indica
--               "Registre un movimiento inverso para corregir". La devolución
--               ES ese movimiento inverso, con dos datos que una ENTRADA
--               común no tiene: a qué salida corrige y por qué.
--
-- Reglas de negocio que materializa:
--   RN-19  Toda devolución corrige exactamente una salida previa y conserva
--          el vínculo con ella (trazabilidad, RF-35).
--   RN-20  Toda devolución declara el motivo por el que se hace. No se admite
--          una devolución sin justificación escrita.
--
-- Dependencias: 001_schema.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 002_devolucion.sql
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. Ampliar el dominio de tipo_movimiento.
-- ENTRADA y SALIDA siguen significando lo mismo; DEVOLUCION se suma como un
-- tercer tipo que, en existencia, se comporta como una entrada (devuelve el
-- producto al lote del que salió), pero que en los informes se distingue de
-- una compra real.
-- -----------------------------------------------------------------------------
ALTER TABLE movimiento DROP CONSTRAINT ck_movimiento_tipo;

ALTER TABLE movimiento
    ADD CONSTRAINT ck_movimiento_tipo
    CHECK (tipo_movimiento IN ('ENTRADA', 'SALIDA', 'DEVOLUCION'));

-- -----------------------------------------------------------------------------
-- 2. Vínculo con la salida que se corrige (RN-19).
-- Autorreferencia a movimiento. ON DELETE RESTRICT porque el historial no se
-- borra: si la salida original no puede desaparecer, su devolución tampoco
-- debe quedar huérfana.
-- -----------------------------------------------------------------------------
ALTER TABLE movimiento
    ADD COLUMN id_movimiento_origen INTEGER;

ALTER TABLE movimiento
    ADD CONSTRAINT fk_movimiento_origen FOREIGN KEY (id_movimiento_origen)
        REFERENCES movimiento (id_movimiento) ON DELETE RESTRICT ON UPDATE CASCADE;

-- -----------------------------------------------------------------------------
-- 3. Motivo de la devolución (RN-20).
-- Es NULL para entradas y salidas, y obligatorio para devoluciones: por eso la
-- columna es nullable y la exigencia vive en el CHECK de abajo, no en un
-- NOT NULL que rompería las 5,839 filas ya cargadas.
-- -----------------------------------------------------------------------------
ALTER TABLE movimiento
    ADD COLUMN motivo VARCHAR(255);

-- -----------------------------------------------------------------------------
-- 4. Las dos columnas anteriores solo tienen sentido en una devolución, y en
-- una devolución son obligatorias. Un solo CHECK expresa la equivalencia en
-- ambas direcciones, así que es imposible:
--   - una DEVOLUCION sin salida de origen o sin motivo;
--   - una ENTRADA o SALIDA que finja corregir algo.
-- length(trim(...)) evita que un motivo de espacios en blanco pase por bueno.
-- -----------------------------------------------------------------------------
ALTER TABLE movimiento
    ADD CONSTRAINT ck_movimiento_devolucion
    CHECK (
        (tipo_movimiento = 'DEVOLUCION')
        = (id_movimiento_origen IS NOT NULL AND length(trim(coalesce(motivo, ''))) > 0)
    );

-- Índice de apoyo: los informes y la pantalla de detalle preguntan
-- "¿qué devoluciones tiene esta salida?" (RNF-14, rendimiento).
CREATE INDEX ix_movimiento_origen ON movimiento (id_movimiento_origen);

COMMIT;

-- Fin de 002_devolucion.sql
