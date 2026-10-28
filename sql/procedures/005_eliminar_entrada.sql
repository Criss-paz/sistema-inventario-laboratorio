-- =============================================================================
-- Archivo:      005_eliminar_entrada.sql
-- Propósito:    Eliminar una entrada registrada por error y ajustar el
--               inventario en la misma operación.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  sp_eliminar_entrada(usuario, movimiento, motivo):
--                 1. Solo un usuario activo con el rol Administrador.
--                 2. Solo entradas; sin correcciones registradas; motivo de
--                    al menos 10 caracteres.
--                 3. Bloquea cada lote de la entrada y comprueba que conserve
--                    todo lo que la entrada sumó: si ya salió parte, no se
--                    puede quitar sin dejar la existencia negativa, y se
--                    rechaza con el máximo que se puede bajar (Corregir
--                    entrada).
--                 4. Deja constancia en la bitácora ANTES de borrar: el
--                    movimiento, su detalle y el motivo.
--                 5. Resta la cantidad de cada lote, borra el detalle y el
--                    movimiento, y borra el lote si se quedó sin movimientos.
--               Todo en una transacción: o se hace completo o no se hace.
--               El kardex y el valor del inventario se recalculan solos,
--               porque salen del historial.
-- Reglas de negocio que materializa:
--   RN-31  Solo el Administrador elimina una entrada, con motivo, y solo si
--          ninguna de sus unidades salió del lote; el inventario se ajusta y
--          la eliminación queda en la bitácora.
-- Dependencias: sql/triggers/007_eliminar_entrada.sql, sql/ddl/007_bitacora.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 005_eliminar_entrada.sql
-- =============================================================================

CREATE OR REPLACE PROCEDURE sp_eliminar_entrada(
    p_id_usuario     INTEGER,
    p_id_movimiento  INTEGER,
    p_motivo         VARCHAR,
    INOUT p_lotes_eliminados INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_mov   movimiento%ROWTYPE;
    v_lotes INTEGER[];
    r       RECORD;
BEGIN
    PERFORM fn_validar_usuario_activo(p_id_usuario);

    IF NOT EXISTS (SELECT 1 FROM usuario u JOIN rol ro ON ro.id_rol = u.id_rol
                    WHERE u.id_usuario = p_id_usuario AND ro.nombre = 'Administrador') THEN
        RAISE EXCEPTION 'Solo el Administrador puede eliminar una entrada.';
    END IF;

    IF p_motivo IS NULL OR length(trim(p_motivo)) < 10 THEN
        RAISE EXCEPTION 'Explique el motivo de la eliminación (al menos 10 caracteres).';
    END IF;

    SELECT * INTO v_mov FROM movimiento WHERE id_movimiento = p_id_movimiento FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El movimiento #% no existe.', p_id_movimiento;
    END IF;
    IF v_mov.tipo_movimiento <> 'ENTRADA' THEN
        RAISE EXCEPTION 'Solo se eliminan entradas. Una salida equivocada se corrige con una devolución.';
    END IF;
    IF EXISTS (SELECT 1 FROM correccion_entrada WHERE id_movimiento = p_id_movimiento) THEN
        RAISE EXCEPTION 'La entrada % tiene correcciones registradas y no se puede eliminar. Si sobra cantidad, corríjala.',
                        v_mov.numero_documento;
    END IF;

    FOR r IN SELECT d.id_lote, d.cantidad, l.numero_lote, l.cantidad_disponible
               FROM detalle_movimiento d JOIN lote l ON l.id_lote = d.id_lote
              WHERE d.id_movimiento = p_id_movimiento
                FOR UPDATE OF l
    LOOP
        IF r.cantidad_disponible < r.cantidad THEN
            RAISE EXCEPTION 'No se puede eliminar la entrada %: del lote % ya salieron % de las % que sumó. Si la cantidad estaba mal, use Corregir entrada.',
                            v_mov.numero_documento, r.numero_lote,
                            r.cantidad - r.cantidad_disponible, r.cantidad;
        END IF;
        v_lotes := array_append(v_lotes, r.id_lote);
    END LOOP;

    -- Constancia en la bitácora antes de borrar (RN-30).
    INSERT INTO bitacora (id_usuario, accion, entidad, id_registro, referencia, detalle)
    VALUES (p_id_usuario, 'ELIMINAR', 'movimiento', v_mov.id_movimiento::TEXT, v_mov.numero_documento,
            jsonb_build_object(
                'motivo', trim(p_motivo),
                'movimiento', to_jsonb(v_mov),
                'detalle', (SELECT jsonb_agg(to_jsonb(d)) FROM detalle_movimiento d
                             WHERE d.id_movimiento = p_id_movimiento)));

    -- El inventario baja lo que la entrada había sumado.
    UPDATE lote l
       SET cantidad_disponible = l.cantidad_disponible - d.cantidad
      FROM detalle_movimiento d
     WHERE d.id_movimiento = p_id_movimiento AND d.id_lote = l.id_lote;

    PERFORM set_config('inventario.eliminar_entrada', 'on', true);
    DELETE FROM detalle_movimiento WHERE id_movimiento = p_id_movimiento;
    DELETE FROM movimiento WHERE id_movimiento = p_id_movimiento;
    PERFORM set_config('inventario.eliminar_entrada', 'off', true);

    -- Lotes que nacieron con esta entrada y ya no tienen movimientos.
    DELETE FROM lote l
     WHERE l.id_lote = ANY (v_lotes)
       AND NOT EXISTS (SELECT 1 FROM detalle_movimiento d WHERE d.id_lote = l.id_lote);
    GET DIAGNOSTICS p_lotes_eliminados = ROW_COUNT;
END;
$$;

COMMENT ON PROCEDURE sp_eliminar_entrada(INTEGER, INTEGER, VARCHAR, INTEGER) IS
    'RN-31: el Administrador elimina una entrada sin unidades consumidas; ajusta el lote y queda en la bitácora.';

-- Fin de 005_eliminar_entrada.sql
