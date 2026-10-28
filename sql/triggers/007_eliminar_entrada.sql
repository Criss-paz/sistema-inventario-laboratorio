-- =============================================================================
-- Archivo:      007_eliminar_entrada.sql
-- Propósito:    Segunda excepción controlada a la inmutabilidad del historial:
--               eliminar una entrada registrada por error.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  Reemplaza fn_historial_inmutable (triggers/003) conservando
--               la excepción de la corrección de entradas y agregando otra:
--               DELETE de una ENTRADA y de su detalle mientras corre
--               sp_eliminar_entrada (procedures/005), que lo indica con la
--               variable de sesión local inventario.eliminar_entrada. La
--               variable sola no sirve de nada: ningún rol tiene DELETE sobre
--               movimiento ni detalle_movimiento, así que el único camino es
--               el procedimiento, que valida todo y deja constancia en la
--               bitácora. Salidas y devoluciones siguen sin poder borrarse.
-- Reglas de negocio que materializa: RN-09, RN-25, RN-31.
-- Dependencias: sql/triggers/001_triggers.sql, 003_correccion_entrada.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 007_eliminar_entrada.sql
-- =============================================================================

CREATE OR REPLACE FUNCTION fn_historial_inmutable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- IF anidados a propósito: cada tabla tiene columnas distintas, y
    -- PL/pgSQL no garantiza cortocircuito en una sola condición.
    IF TG_OP = 'UPDATE' AND TG_TABLE_NAME = 'detalle_movimiento'
       AND current_setting('inventario.correccion_entrada', true) = 'on' THEN
        -- Corrección (RN-25): solo cantidad y precio, nunca a qué movimiento o lote pertenece.
        IF NEW.id_movimiento = OLD.id_movimiento AND NEW.id_lote = OLD.id_lote
           AND NEW.id_detalle = OLD.id_detalle THEN
            RETURN NEW;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' AND current_setting('inventario.eliminar_entrada', true) = 'on' THEN
        -- Eliminación de una entrada (RN-31): el detalle de la entrada y su cabecera.
        IF TG_TABLE_NAME = 'detalle_movimiento' THEN
            RETURN OLD;
        END IF;
        IF TG_TABLE_NAME = 'movimiento' THEN
            IF OLD.tipo_movimiento = 'ENTRADA' THEN
                RETURN OLD;
            END IF;
        END IF;
    END IF;

    RAISE EXCEPTION 'Los movimientos de inventario no se pueden modificar ni eliminar (tabla %). Registre un movimiento inverso o use Corregir entrada.',
                    TG_TABLE_NAME;
END;
$$;

COMMENT ON FUNCTION fn_historial_inmutable() IS
    'RN-09: historial de solo inserción, salvo corregir (RN-25) o eliminar (RN-31) una entrada por su procedimiento.';

-- Fin de 007_eliminar_entrada.sql
