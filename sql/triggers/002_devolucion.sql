-- =============================================================================
-- Archivo:      002_devolucion.sql
-- Propósito:    Que una DEVOLUCION reponga la existencia del lote, y que nunca
--               devuelva más de lo que salió.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code).
-- Descripción:  Reemplaza fn_detalle_movimiento_existencia() para añadir la
--               rama DEVOLUCION, y agrega un trigger nuevo que valida el tope
--               devolvible por lote. Las ramas ENTRADA y SALIDA quedan
--               exactamente como estaban en 001_triggers.sql.
--
-- Reglas de negocio:
--   RN-21  Una devolución repone la existencia del lote del que salió el
--          producto (inverso de RN-04).
--   RN-22  No se puede devolver más de lo que esa salida sacó de ese lote,
--          descontando lo ya devuelto antes. Sin esta regla, una devolución
--          repetida inventaría existencia que nunca entró al laboratorio.
--
-- Dependencias: 001_schema.sql, 002_devolucion.sql (DDL), 001_triggers.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 002_devolucion.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Trigger 1 (reemplazo): existencia por lote, ahora con tres tipos.
-- DEVOLUCION suma igual que ENTRADA. La diferencia entre ambas no está aquí
-- sino en el trigger de tope (abajo) y en los informes.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_detalle_movimiento_existencia()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_tipo_movimiento  movimiento.tipo_movimiento%TYPE;
    v_disponible       lote.cantidad_disponible%TYPE;
    v_estado_lote      lote.estado%TYPE;
    v_numero_lote      lote.numero_lote%TYPE;
BEGIN
    SELECT m.tipo_movimiento
      INTO v_tipo_movimiento
      FROM movimiento m
     WHERE m.id_movimiento = NEW.id_movimiento;

    SELECT l.cantidad_disponible, l.estado, l.numero_lote
      INTO v_disponible, v_estado_lote, v_numero_lote
      FROM lote l
     WHERE l.id_lote = NEW.id_lote
       FOR UPDATE;

    IF v_tipo_movimiento IS NULL OR v_disponible IS NULL THEN
        RETURN NEW;
    END IF;

    IF NOT v_estado_lote THEN
        RAISE EXCEPTION 'El lote % está dado de baja y no admite movimientos.', v_numero_lote;
    END IF;

    IF v_tipo_movimiento IN ('ENTRADA', 'DEVOLUCION') THEN
        UPDATE lote
           SET cantidad_disponible = cantidad_disponible + NEW.cantidad
         WHERE id_lote = NEW.id_lote;

    ELSIF v_tipo_movimiento = 'SALIDA' THEN
        IF NEW.cantidad > v_disponible THEN
            RAISE EXCEPTION 'Existencia insuficiente en el lote %: disponible %, solicitado %.',
                            v_numero_lote, v_disponible, NEW.cantidad;
        END IF;

        UPDATE lote
           SET cantidad_disponible = cantidad_disponible - NEW.cantidad
         WHERE id_lote = NEW.id_lote;
    END IF;

    RETURN NEW;
END;
$$;

-- -----------------------------------------------------------------------------
-- Trigger nuevo: tope devolvible por lote (RN-22).
--
-- Corre DESPUÉS del de existencia y antes de insertar la fila. Para el lote
-- que se está devolviendo calcula:
--     sacado    = cantidad de ese lote en la salida de origen
--     devuelto  = cantidad de ese lote ya devuelta por devoluciones previas
--                 de esa misma salida
-- y rechaza si lo nuevo excede (sacado - devuelto).
--
-- Esto es lo que impide el fraude de "devolver" dos veces la misma salida, o
-- devolver un lote que esa salida nunca tocó.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_devolucion_tope()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_tipo       movimiento.tipo_movimiento%TYPE;
    v_origen     movimiento.id_movimiento_origen%TYPE;
    v_sacado     NUMERIC(10,2);
    v_devuelto   NUMERIC(10,2);
    v_numero     lote.numero_lote%TYPE;
BEGIN
    SELECT m.tipo_movimiento, m.id_movimiento_origen
      INTO v_tipo, v_origen
      FROM movimiento m
     WHERE m.id_movimiento = NEW.id_movimiento;

    -- Solo aplica a devoluciones; entradas y salidas pasan de largo.
    IF v_tipo IS DISTINCT FROM 'DEVOLUCION' THEN
        RETURN NEW;
    END IF;

    SELECT l.numero_lote INTO v_numero FROM lote l WHERE l.id_lote = NEW.id_lote;

    -- Cuánto sacó de este lote la salida que se está corrigiendo.
    SELECT coalesce(sum(d.cantidad), 0)
      INTO v_sacado
      FROM detalle_movimiento d
     WHERE d.id_movimiento = v_origen
       AND d.id_lote = NEW.id_lote;

    IF v_sacado = 0 THEN
        RAISE EXCEPTION
            'La salida #% no retiró el lote % : no hay nada que devolver de ese lote.',
            v_origen, v_numero;
    END IF;

    -- Cuánto de este lote ya se devolvió en devoluciones anteriores de la
    -- misma salida (excluyendo la fila que se está insertando ahora).
    SELECT coalesce(sum(d.cantidad), 0)
      INTO v_devuelto
      FROM detalle_movimiento d
      JOIN movimiento m ON m.id_movimiento = d.id_movimiento
     WHERE m.tipo_movimiento = 'DEVOLUCION'
       AND m.id_movimiento_origen = v_origen
       AND d.id_lote = NEW.id_lote
       AND d.id_detalle IS DISTINCT FROM NEW.id_detalle;

    IF NEW.cantidad > (v_sacado - v_devuelto) THEN
        RAISE EXCEPTION
            'No se puede devolver % del lote %: la salida #% retiró % y ya se habían devuelto %. Máximo devolvible: %.',
            NEW.cantidad, v_numero, v_origen, v_sacado, v_devuelto, (v_sacado - v_devuelto);
    END IF;

    RETURN NEW;
END;
$$;

-- El nombre empieza con "trg_z" a propósito: PostgreSQL dispara los triggers
-- BEFORE en orden alfabético, y este debe correr después del de existencia
-- para que el lote ya esté bloqueado con FOR UPDATE.
CREATE OR REPLACE TRIGGER trg_z_devolucion_tope
    BEFORE INSERT ON detalle_movimiento
    FOR EACH ROW
    EXECUTE FUNCTION fn_devolucion_tope();

-- Fin de 002_devolucion.sql
