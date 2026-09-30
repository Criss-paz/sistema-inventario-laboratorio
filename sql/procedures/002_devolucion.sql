-- =============================================================================
-- Archivo:      002_devolucion.sql
-- Propósito:    Registrar la devolución de una salida equivocada en una sola
--               operación atómica.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code).
-- Descripción:  sp_registrar_devolucion devuelve al inventario lo que sacó una
--               salida previa, lote por lote y en las mismas cantidades, o una
--               parte si se indica. Deja el motivo escrito y el vínculo con la
--               salida corregida.
--
--               Por qué un procedimiento y no INSERTs desde la aplicación:
--               una devolución toca `movimiento` y N filas de
--               `detalle_movimiento`, y debe ser todo o nada. Si el trigger de
--               tope rechaza el tercer lote, los dos primeros no pueden quedar
--               devueltos. El procedimiento envuelve todo en una transacción y
--               la aplicación solo pasa parámetros.
--
-- Reglas de negocio:
--   RN-19  La devolución conserva el vínculo con la salida que corrige.
--   RN-20  La devolución exige un motivo escrito.
--   RN-22  No se devuelve más de lo que salió (lo vigila fn_devolucion_tope).
--   RN-08  Queda registrado qué usuario la hizo.
--
-- Dependencias: 002_devolucion.sql (DDL y triggers), 001_procedures.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 002_devolucion.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- fn_devolvible(p_id_movimiento)
-- Qué queda por devolver de una salida, lote por lote. La usan la pantalla de
-- devolución (para proponer cantidades) y el informe de la salida.
-- Devuelve solo los lotes con saldo pendiente.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_devolvible(p_id_movimiento INTEGER)
RETURNS TABLE (
    id_lote      INTEGER,
    numero_lote  VARCHAR,
    producto     VARCHAR,
    sacado       NUMERIC,
    devuelto     NUMERIC,
    devolvible   NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT s.id_lote,
           l.numero_lote,
           p.nombre,
           s.sacado,
           coalesce(dev.devuelto, 0)            AS devuelto,
           s.sacado - coalesce(dev.devuelto, 0) AS devolvible
      FROM (SELECT d.id_lote, sum(d.cantidad) AS sacado
              FROM detalle_movimiento d
             WHERE d.id_movimiento = p_id_movimiento
             GROUP BY d.id_lote) s
      JOIN lote     l ON l.id_lote = s.id_lote
      JOIN producto p ON p.id_producto = l.id_producto
      LEFT JOIN (
            SELECT d.id_lote, sum(d.cantidad) AS devuelto
              FROM detalle_movimiento d
              JOIN movimiento m ON m.id_movimiento = d.id_movimiento
             WHERE m.tipo_movimiento = 'DEVOLUCION'
               AND m.id_movimiento_origen = p_id_movimiento
             GROUP BY d.id_lote) dev ON dev.id_lote = s.id_lote
     WHERE s.sacado - coalesce(dev.devuelto, 0) > 0
     ORDER BY l.numero_lote;
$$;


-- -----------------------------------------------------------------------------
-- sp_registrar_devolucion
--
-- p_id_lotes / p_cantidades son dos arreglos paralelos: la posición i dice
-- cuánto devolver del lote i. Si se pasan vacíos o NULL, se devuelve TODO lo
-- que quede pendiente de esa salida (el caso habitual: "esta salida no debió
-- existir").
-- -----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_registrar_devolucion(
    p_id_usuario           INTEGER,
    p_id_movimiento_origen INTEGER,
    p_motivo               VARCHAR,
    p_id_lotes             INTEGER[] DEFAULT NULL,
    p_cantidades           NUMERIC[] DEFAULT NULL,
    INOUT p_id_movimiento  INTEGER   DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_tipo_origen movimiento.tipo_movimiento%TYPE;
    v_filas       INTEGER := 0;
    r             RECORD;
    i             INTEGER;
BEGIN
    PERFORM fn_validar_usuario_activo(p_id_usuario);

    IF p_motivo IS NULL OR length(trim(p_motivo)) = 0 THEN
        RAISE EXCEPTION 'Debe indicar el motivo de la devolución.';
    END IF;

    SELECT m.tipo_movimiento
      INTO v_tipo_origen
      FROM movimiento m
     WHERE m.id_movimiento = p_id_movimiento_origen;

    IF v_tipo_origen IS NULL THEN
        RAISE EXCEPTION 'El movimiento #% no existe.', p_id_movimiento_origen;
    END IF;

    -- Solo se devuelve una salida. Devolver una entrada sería una salida, y
    -- devolver una devolución sería volver a sacar: ambos casos tienen su
    -- propia pantalla y no deben confundirse aquí.
    IF v_tipo_origen <> 'SALIDA' THEN
        RAISE EXCEPTION
            'Solo se puede devolver una SALIDA. El movimiento #% es de tipo %.',
            p_id_movimiento_origen, v_tipo_origen;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM fn_devolvible(p_id_movimiento_origen)) THEN
        RAISE EXCEPTION
            'La salida #% ya fue devuelta por completo.', p_id_movimiento_origen;
    END IF;

    INSERT INTO movimiento (id_usuario, tipo_movimiento, observacion,
                            id_movimiento_origen, motivo)
    VALUES (p_id_usuario, 'DEVOLUCION',
            'Devolución de la salida #' || p_id_movimiento_origen,
            p_id_movimiento_origen, trim(p_motivo))
    RETURNING id_movimiento INTO p_id_movimiento;

    IF p_id_lotes IS NULL OR array_length(p_id_lotes, 1) IS NULL THEN
        -- Devolución total: todo el saldo pendiente, lote por lote.
        FOR r IN SELECT d.id_lote, d.devolvible FROM fn_devolvible(p_id_movimiento_origen) d
        LOOP
            INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad)
            VALUES (p_id_movimiento, r.id_lote, r.devolvible);
            v_filas := v_filas + 1;
        END LOOP;
    ELSE
        -- Devolución parcial: solo los lotes y cantidades indicados.
        IF array_length(p_id_lotes, 1) IS DISTINCT FROM array_length(p_cantidades, 1) THEN
            RAISE EXCEPTION 'Cada lote debe tener su cantidad: se recibieron % lotes y % cantidades.',
                            array_length(p_id_lotes, 1), array_length(p_cantidades, 1);
        END IF;

        FOR i IN 1 .. array_length(p_id_lotes, 1) LOOP
            -- Una cantidad en cero significa "de este lote no devuelvo nada".
            CONTINUE WHEN p_cantidades[i] IS NULL OR p_cantidades[i] = 0;

            IF p_cantidades[i] < 0 THEN
                RAISE EXCEPTION 'La cantidad a devolver no puede ser negativa (lote %).', p_id_lotes[i];
            END IF;

            -- El trigger trg_z_devolucion_tope valida el máximo (RN-22) y
            -- trg_detalle_movimiento_existencia repone la existencia (RN-21).
            INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad)
            VALUES (p_id_movimiento, p_id_lotes[i], p_cantidades[i]);
            v_filas := v_filas + 1;
        END LOOP;
    END IF;

    IF v_filas = 0 THEN
        RAISE EXCEPTION 'No se indicó ninguna cantidad a devolver.';
    END IF;
END;
$$;

-- Fin de 002_devolucion.sql
