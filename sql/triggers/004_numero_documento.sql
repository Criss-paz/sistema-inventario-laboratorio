-- =============================================================================
-- Archivo:      004_numero_documento.sql
-- Propósito:    Asignar el número de documento (E/S/D + 6 dígitos) a cada
--               movimiento nuevo.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  BEFORE INSERT en movimiento. Si el movimiento no trae número,
--               toma el último de su tipo y le suma 1 (RN-27). Un candado de
--               transacción por tipo (pg_advisory_xact_lock) evita que dos
--               registros simultáneos tomen el mismo número; como el número
--               se calcula dentro de la misma transacción, un registro que
--               falla no deja huecos en la numeración.
--               En las devoluciones escribe además la referencia a la salida
--               corregida por su número ("Devolución de la salida S004750").
-- Reglas de negocio que materializa: RN-27.
-- Dependencias: sql/ddl/005_numero_documento.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 004_numero_documento.sql
-- =============================================================================

CREATE OR REPLACE FUNCTION fn_asignar_numero_documento()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_prefijo   CHAR(1) := left(NEW.tipo_movimiento, 1);
    v_ultimo    VARCHAR(7);
    v_siguiente INTEGER;
BEGIN
    IF NEW.numero_documento IS NULL THEN
        PERFORM pg_advisory_xact_lock(hashtext('movimiento.numero_documento.' || v_prefijo));
        SELECT max(numero_documento) INTO v_ultimo
          FROM movimiento
         WHERE numero_documento BETWEEN v_prefijo || '000000' AND v_prefijo || '999999';
        v_siguiente := coalesce(substring(v_ultimo FROM 2)::INTEGER, 0) + 1;
        IF v_siguiente > 999999 THEN
            RAISE EXCEPTION 'Se agotó la numeración de documentos % (máximo %999999).', v_prefijo, v_prefijo;
        END IF;
        NEW.numero_documento := v_prefijo || lpad(v_siguiente::TEXT, 6, '0');
    END IF;

    IF NEW.tipo_movimiento = 'DEVOLUCION' AND NEW.id_movimiento_origen IS NOT NULL THEN
        SELECT 'Devolución de la salida ' || numero_documento INTO NEW.observacion
          FROM movimiento
         WHERE id_movimiento = NEW.id_movimiento_origen;
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION fn_asignar_numero_documento() IS
    'RN-27: número de documento correlativo por tipo (E/S/D), sin huecos.';

CREATE OR REPLACE TRIGGER trg_movimiento_numero
    BEFORE INSERT ON movimiento
    FOR EACH ROW
    EXECUTE FUNCTION fn_asignar_numero_documento();

-- Fin de 004_numero_documento.sql
