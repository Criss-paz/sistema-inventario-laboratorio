-- =============================================================================
-- Archivo:      001_triggers.sql
-- Propósito:    Triggers que aplican reglas de negocio que un CHECK/FK no puede
--               expresar porque cruzan tablas o dependen del tipo de operación.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/Bitacora-IA.md para el registro de uso.
-- Descripción:  3 triggers:
--                 1. trg_detalle_movimiento_existencia  → RN-01, RN-02, RN-03, RN-04
--                 2. trg_movimiento_inmutable /
--                    trg_detalle_movimiento_inmutable    → RN-09
--                 3. trg_lote_vencimiento                → RN-07
-- Dependencias: sql/ddl/001_schema.sql (las tablas deben existir).
--               Ejecutar ANTES de sql/dml/ si el seed registra movimientos,
--               para que la existencia de los lotes se calcule por trigger.
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 001_triggers.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Trigger 1: actualizar la existencia del lote al registrar un detalle de
-- movimiento.
--
-- Regla de negocio:
--   RN-02  Una ENTRADA suma la cantidad a lote.cantidad_disponible.
--   RN-03  Una SALIDA resta la cantidad de lote.cantidad_disponible.
--   RN-04  No se puede sacar más de lo que hay: la SALIDA se rechaza con un
--          mensaje claro en vez de dejar que falle el CHECK genérico.
--   RN-01  La existencia nunca es negativa (lo garantiza RN-04 aquí y, como
--          última defensa, el CHECK ck_lote_cantidad_disponible del DDL).
--
-- Por qué trigger y no la app: la existencia debe ser correcta sin importar
-- quién inserte el detalle (app web, procedimiento, psql). Si la regla viviera
-- solo en Python, un INSERT directo dejaría el inventario descuadrado.
--
-- Por qué SELECT ... FOR UPDATE: bloquea la fila del lote hasta el fin de la
-- transacción. Sin el bloqueo, dos salidas simultáneas podrían leer la misma
-- existencia y ambas pasar la validación de RN-04.
--
-- Nota S7 (sin redundancia): cantidad_disponible es un valor derivable (suma
-- de entradas − salidas). Se almacena a propósito porque se consulta en cada
-- salida y en cada listado; este trigger es el ÚNICO camino que lo modifica
-- a partir de movimientos, así que nunca se desincroniza del historial.
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

    -- Si el lote o el movimiento no existen, la FK lo rechaza después; aquí
    -- solo se evita trabajar con NULL.
    IF v_tipo_movimiento IS NULL OR v_disponible IS NULL THEN
        RETURN NEW;
    END IF;

    IF NOT v_estado_lote THEN
        RAISE EXCEPTION 'El lote % está dado de baja y no admite movimientos.', v_numero_lote
            USING ERRCODE = 'check_violation';
    END IF;

    IF v_tipo_movimiento = 'ENTRADA' THEN
        UPDATE lote
           SET cantidad_disponible = cantidad_disponible + NEW.cantidad
         WHERE id_lote = NEW.id_lote;

    ELSIF v_tipo_movimiento = 'SALIDA' THEN
        IF NEW.cantidad > v_disponible THEN
            RAISE EXCEPTION 'Existencia insuficiente en el lote %: disponible %, solicitado %.',
                            v_numero_lote, v_disponible, NEW.cantidad
                USING ERRCODE = 'check_violation';
        END IF;

        UPDATE lote
           SET cantidad_disponible = cantidad_disponible - NEW.cantidad
         WHERE id_lote = NEW.id_lote;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_detalle_movimiento_existencia
    BEFORE INSERT ON detalle_movimiento
    FOR EACH ROW
    EXECUTE FUNCTION fn_detalle_movimiento_existencia();

-- -----------------------------------------------------------------------------
-- Trigger 2: el historial de movimientos es de solo inserción.
--
-- Regla de negocio:
--   RN-09  Los movimientos se conservan como historial.
--
-- El DDL ya impide borrar un movimiento que tenga detalle (ON DELETE RESTRICT),
-- pero no impide EDITARLO. Si se permitiera cambiar la cantidad de un detalle
-- o el tipo de un movimiento, la existencia del lote (calculada por el
-- trigger 1 en el momento del INSERT) dejaría de coincidir con el historial.
-- Un error de registro se corrige con un movimiento inverso (una ENTRADA que
-- compensa una SALIDA equivocada, o viceversa), que queda también en el
-- historial con su responsable (RN-08).
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_historial_inmutable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Los movimientos de inventario no se pueden modificar ni eliminar (tabla %). Registre un movimiento inverso para corregir.',
                    TG_TABLE_NAME
        USING ERRCODE = 'restrict_violation';
END;
$$;

CREATE OR REPLACE TRIGGER trg_movimiento_inmutable
    BEFORE UPDATE OR DELETE ON movimiento
    FOR EACH ROW
    EXECUTE FUNCTION fn_historial_inmutable();

CREATE OR REPLACE TRIGGER trg_detalle_movimiento_inmutable
    BEFORE UPDATE OR DELETE ON detalle_movimiento
    FOR EACH ROW
    EXECUTE FUNCTION fn_historial_inmutable();

-- -----------------------------------------------------------------------------
-- Trigger 3: fecha de vencimiento obligatoria según el producto.
--
-- Regla de negocio:
--   RN-07  Los lotes de un producto con requiere_vencimiento = TRUE deben
--          registrar fecha_vencimiento.
--
-- Por qué trigger: la condición está en producto y el dato en lote. Un CHECK
-- de PostgreSQL solo ve la fila propia, así que no puede cruzar las dos
-- tablas (decisión documentada en docs/entrega-2/modelo-relacional.md).
--
-- Solo se exige la fecha cuando falta; si el producto NO requiere
-- vencimiento y aun así se captura una fecha, se permite (no es incorrecto
-- conocerla). El CHECK ck_lote_fecha_vencimiento ya valida que no sea
-- anterior a fecha_ingreso.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_lote_vencimiento()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_requiere_vencimiento  producto.requiere_vencimiento%TYPE;
    v_nombre_producto       producto.nombre%TYPE;
BEGIN
    SELECT p.requiere_vencimiento, p.nombre
      INTO v_requiere_vencimiento, v_nombre_producto
      FROM producto p
     WHERE p.id_producto = NEW.id_producto;

    IF v_requiere_vencimiento AND NEW.fecha_vencimiento IS NULL THEN
        RAISE EXCEPTION 'El producto "%" requiere fecha de vencimiento en sus lotes.', v_nombre_producto
            USING ERRCODE = 'not_null_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_lote_vencimiento
    BEFORE INSERT OR UPDATE OF id_producto, fecha_vencimiento ON lote
    FOR EACH ROW
    EXECUTE FUNCTION fn_lote_vencimiento();

-- Fin de 001_triggers.sql
