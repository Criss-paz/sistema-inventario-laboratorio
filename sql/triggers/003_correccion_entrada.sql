-- =============================================================================
-- Archivo:      003_correccion_entrada.sql
-- Propósito:    Permitir la corrección controlada de una entrada sin abrir el
--               historial a cambios libres.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code).
-- Descripción:  Tres piezas:
--
--   1. fn_historial_inmutable (reemplazo): sigue prohibiendo modificar y
--      borrar movimientos. Única excepción: un UPDATE de cantidad o
--      precio_unitario en detalle_movimiento mientras corre
--      sp_corregir_entrada, que lo señala con la variable de sesión local
--      inventario.correccion_entrada = 'on' y deja la corrección registrada
--      en correccion_entrada. DELETE nunca se permite. Ningún rol de la app
--      tiene UPDATE sobre detalle_movimiento, así que la variable sola no
--      abre nada: la única vía es el procedimiento.
--
--   2. trg_z_correccion_existencia: si cambia la cantidad de una entrada, la
--      existencia del lote se ajusta por la diferencia, y no se permite que
--      quede negativa (lo que ya salió del lote no puede "desaparecer").
--      Empieza con "z" para dispararse después del trigger de inmutabilidad
--      (PostgreSQL dispara los BEFORE en orden alfabético).
--
--   3. trg_correccion_inmutable: las correcciones tampoco se modifican ni se
--      borran; la tabla solo crece.
--
-- Reglas de negocio:
--   RN-09  El historial se conserva (se precisa: una entrada se corrige, nunca
--          se elimina, y la corrección queda registrada).
--   RN-01  La existencia nunca es negativa, tampoco después de corregir.
--   RN-25  Una entrada se corrige, no se elimina.
--
-- Dependencias: 001_triggers.sql, ddl/004_correccion_entrada.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 003_correccion_entrada.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Inmutabilidad con una sola excepción controlada.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_historial_inmutable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- IF anidados a propósito: NEW.id_lote solo existe en detalle_movimiento,
    -- y PL/pgSQL no garantiza cortocircuito en una sola condición.
    IF TG_OP = 'UPDATE' AND TG_TABLE_NAME = 'detalle_movimiento'
       AND current_setting('inventario.correccion_entrada', true) = 'on' THEN
        -- Solo cantidad y precio: nunca se cambia a qué movimiento o lote pertenece.
        IF NEW.id_movimiento = OLD.id_movimiento AND NEW.id_lote = OLD.id_lote
           AND NEW.id_detalle = OLD.id_detalle THEN
            RETURN NEW;
        END IF;
    END IF;

    RAISE EXCEPTION 'Los movimientos de inventario no se pueden modificar ni eliminar (tabla %). Registre un movimiento inverso o use Corregir entrada.',
                    TG_TABLE_NAME;
END;
$$;

-- -----------------------------------------------------------------------------
-- 2. La existencia del lote sigue a la cantidad corregida (RN-01).
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_correccion_existencia()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_disponible  lote.cantidad_disponible%TYPE;
    v_numero_lote lote.numero_lote%TYPE;
    v_diferencia  NUMERIC;
BEGIN
    v_diferencia := NEW.cantidad - OLD.cantidad;
    IF v_diferencia = 0 THEN
        RETURN NEW;
    END IF;

    SELECT l.cantidad_disponible, l.numero_lote
      INTO v_disponible, v_numero_lote
      FROM lote l
     WHERE l.id_lote = NEW.id_lote
       FOR UPDATE;

    IF v_disponible + v_diferencia < 0 THEN
        RAISE EXCEPTION 'No se puede bajar la entrada a %: del lote % ya salió parte y solo quedan %. Como mínimo la entrada puede quedar en %.',
                        NEW.cantidad, v_numero_lote, v_disponible, OLD.cantidad - v_disponible;
    END IF;

    UPDATE lote
       SET cantidad_disponible = cantidad_disponible + v_diferencia
     WHERE id_lote = NEW.id_lote;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_z_correccion_existencia
    BEFORE UPDATE OF cantidad ON detalle_movimiento
    FOR EACH ROW
    EXECUTE FUNCTION fn_correccion_existencia();

-- -----------------------------------------------------------------------------
-- 3. Las correcciones son definitivas.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TRIGGER trg_correccion_inmutable
    BEFORE UPDATE OR DELETE ON correccion_entrada
    FOR EACH ROW
    EXECUTE FUNCTION fn_historial_inmutable();

-- Fin de 003_correccion_entrada.sql
