-- =============================================================================
-- Archivo:      001_procedures.sql
-- Propósito:    Procedimientos almacenados para registrar entradas y salidas
--               de inventario como una sola operación atómica.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/Bitacora-IA.md para el registro de uso.
-- Descripción:  2 procedimientos:
--                 1. sp_registrar_entrada → RF-20, RF-22, RF-14, RN-02, RN-05, RN-06, RN-08
--                 2. sp_registrar_salida  → RF-21, RF-23, RF-25, RN-03, RN-04, RN-08
--               Ambos crean el encabezado (movimiento) y su detalle en la misma
--               llamada; la actualización de lote.cantidad_disponible la hace
--               el trigger trg_detalle_movimiento_existencia, no estos
--               procedimientos (una sola fuente de verdad para la existencia).
-- Errores:      las violaciones de reglas de negocio se lanzan con
--               RAISE EXCEPTION sin ERRCODE (SQLSTATE P0001) y mensaje para el
--               usuario final, igual que en sql/triggers/001_triggers.sql.
-- Atomicidad:   un CALL se ejecuta dentro de la transacción de quien lo llama.
--               Si cualquier paso falla, PostgreSQL deshace TODO lo que hizo el
--               procedimiento: nunca queda un movimiento sin detalle ni un lote
--               creado sin su entrada. Por eso no hay COMMIT dentro.
-- Dependencias: sql/ddl/001_schema.sql, sql/triggers/001_triggers.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 001_procedures.sql
-- Uso:          CALL sp_registrar_entrada(1, 1, 1, 'L-2026-010', '2027-12-31', 100, 85.50, 'Compra', NULL);
--               CALL sp_registrar_salida(2, 1, 25, 'Consumo área química', NULL);
--               (el último argumento NULL es el parámetro INOUT que devuelve
--               el id_movimiento generado).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Validación compartida: el usuario que registra debe existir y estar activo.
--
-- Regla de negocio:
--   RN-08  Todo movimiento debe tener un usuario responsable. La FK garantiza
--          que exista, pero no que siga activo: un usuario dado de baja
--          (estado = FALSE) no debe poder seguir moviendo inventario.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_validar_usuario_activo(p_id_usuario INTEGER)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1
                     FROM usuario u
                    WHERE u.id_usuario = p_id_usuario
                      AND u.estado) THEN
        RAISE EXCEPTION 'El usuario que registra el movimiento no existe o está inactivo.';
    END IF;
END;
$$;

-- -----------------------------------------------------------------------------
-- Procedimiento 1: registrar la entrada de un producto al inventario.
--
-- Regla de negocio:
--   RF-20/RF-22  Registrar entradas con su detalle.
--   RN-05/RN-06  La mercadería entra por lote. Si el lote (producto +
--                número de lote) ya existe, la entrada se suma a ese lote;
--                si no, se crea con existencia 0 y la entrada lo carga.
--                Así el lote nunca "nace" con una existencia que no esté
--                respaldada por un movimiento en el historial.
--   RN-02        La suma a la existencia la hace el trigger del detalle.
--   RN-07        Si el lote es nuevo, trg_lote_vencimiento exige la fecha
--                de vencimiento cuando el producto la requiere.
--
-- Parámetros:
--   p_fecha_vencimiento  solo se usa al crear un lote nuevo; si el lote ya
--                        existe se conserva su fecha original.
--   p_id_movimiento      INOUT: se pasa NULL y devuelve el id generado.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_registrar_entrada(
    p_id_usuario         INTEGER,
    p_id_producto        INTEGER,
    p_id_proveedor       INTEGER,
    p_numero_lote        VARCHAR,
    p_fecha_vencimiento  DATE,
    p_cantidad           NUMERIC,
    p_precio_unitario    NUMERIC,
    p_observacion        VARCHAR,
    INOUT p_id_movimiento INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_lote  lote.id_lote%TYPE;
BEGIN
    PERFORM fn_validar_usuario_activo(p_id_usuario);

    IF p_cantidad IS NULL OR p_cantidad <= 0 THEN
        RAISE EXCEPTION 'La cantidad de la entrada debe ser mayor que cero.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM producto p
                    WHERE p.id_producto = p_id_producto AND p.estado) THEN
        RAISE EXCEPTION 'El producto no existe o está dado de baja.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM proveedor pr
                    WHERE pr.id_proveedor = p_id_proveedor AND pr.estado) THEN
        RAISE EXCEPTION 'El proveedor no existe o está dado de baja.';
    END IF;

    IF p_numero_lote IS NULL OR length(trim(p_numero_lote)) = 0 THEN
        RAISE EXCEPTION 'El número de lote es obligatorio.';
    END IF;

    -- RN-06: el lote se identifica por producto + número de lote.
    SELECT l.id_lote
      INTO v_id_lote
      FROM lote l
     WHERE l.id_producto = p_id_producto
       AND l.numero_lote = trim(p_numero_lote);

    IF v_id_lote IS NULL THEN
        INSERT INTO lote (id_producto, id_proveedor, numero_lote,
                          fecha_vencimiento, cantidad_disponible)
        VALUES (p_id_producto, p_id_proveedor, trim(p_numero_lote),
                p_fecha_vencimiento, 0)
        RETURNING id_lote INTO v_id_lote;
    END IF;

    INSERT INTO movimiento (id_usuario, tipo_movimiento, observacion)
    VALUES (p_id_usuario, 'ENTRADA', p_observacion)
    RETURNING id_movimiento INTO p_id_movimiento;

    -- El trigger trg_detalle_movimiento_existencia suma la cantidad (RN-02).
    INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad, precio_unitario)
    VALUES (p_id_movimiento, v_id_lote, p_cantidad, COALESCE(p_precio_unitario, 0));
END;
$$;

-- -----------------------------------------------------------------------------
-- Procedimiento 2: registrar la salida de un producto, eligiendo los lotes
-- automáticamente.
--
-- Regla de negocio:
--   RF-21/RF-23  Registrar salidas con su detalle.
--   RF-25/RN-04  No sacar más de lo disponible: se valida contra la existencia
--                TOTAL utilizable del producto antes de tocar ningún lote,
--                para dar un solo mensaje claro en vez de fallar a medias.
--   FEFO         (First Expired, First Out) — práctica estándar en
--                laboratorios clínicos: se consume primero el lote que vence
--                antes, para no desperdiciar reactivos por vencimiento. Los
--                lotes sin fecha (productos que no vencen) van al final, y
--                entre iguales el más antiguo por fecha de ingreso.
--   Seguridad del paciente: los lotes YA vencidos no se consideran
--                utilizables, así que nunca se despachan.
--   RN-18        Si un solo lote no alcanza, la salida se reparte en varios
--                lotes: un detalle_movimiento por cada lote afectado.
--   RN-03        La resta en cada lote la hace el trigger del detalle.
--
-- Bloqueo: los lotes candidatos se leen con FOR UPDATE para que otra salida
-- simultánea del mismo producto espere y no valide contra una existencia
-- que está a punto de cambiar.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_registrar_salida(
    p_id_usuario     INTEGER,
    p_id_producto    INTEGER,
    p_cantidad       NUMERIC,
    p_observacion    VARCHAR,
    INOUT p_id_movimiento INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_nombre_producto  producto.nombre%TYPE;
    v_disponible_total NUMERIC := 0;
    v_pendiente        NUMERIC;
    v_tomar            NUMERIC;
    r_lote             RECORD;
BEGIN
    PERFORM fn_validar_usuario_activo(p_id_usuario);

    IF p_cantidad IS NULL OR p_cantidad <= 0 THEN
        RAISE EXCEPTION 'La cantidad de la salida debe ser mayor que cero.';
    END IF;

    SELECT p.nombre
      INTO v_nombre_producto
      FROM producto p
     WHERE p.id_producto = p_id_producto
       AND p.estado;

    IF v_nombre_producto IS NULL THEN
        RAISE EXCEPTION 'El producto no existe o está dado de baja.';
    END IF;

    -- Bloquea los lotes utilizables del producto y suma su existencia.
    -- (FOR UPDATE no admite funciones de agregado, por eso se bloquea en un
    -- PERFORM aparte y luego se suma.)
    PERFORM 1
       FROM lote l
      WHERE l.id_producto = p_id_producto
        AND l.estado
        AND l.cantidad_disponible > 0
        AND (l.fecha_vencimiento IS NULL OR l.fecha_vencimiento >= CURRENT_DATE)
        FOR UPDATE;

    SELECT COALESCE(sum(l.cantidad_disponible), 0)
      INTO v_disponible_total
      FROM lote l
     WHERE l.id_producto = p_id_producto
       AND l.estado
       AND l.cantidad_disponible > 0
       AND (l.fecha_vencimiento IS NULL OR l.fecha_vencimiento >= CURRENT_DATE);

    IF p_cantidad > v_disponible_total THEN
        RAISE EXCEPTION 'Existencia insuficiente de "%": disponible % (sin contar lotes vencidos), solicitado %.',
                        v_nombre_producto, v_disponible_total, p_cantidad;
    END IF;

    INSERT INTO movimiento (id_usuario, tipo_movimiento, observacion)
    VALUES (p_id_usuario, 'SALIDA', p_observacion)
    RETURNING id_movimiento INTO p_id_movimiento;

    v_pendiente := p_cantidad;

    FOR r_lote IN
        SELECT l.id_lote, l.cantidad_disponible
          FROM lote l
         WHERE l.id_producto = p_id_producto
           AND l.estado
           AND l.cantidad_disponible > 0
           AND (l.fecha_vencimiento IS NULL OR l.fecha_vencimiento >= CURRENT_DATE)
         ORDER BY l.fecha_vencimiento ASC NULLS LAST,
                  l.fecha_ingreso ASC,
                  l.id_lote ASC
    LOOP
        EXIT WHEN v_pendiente <= 0;

        v_tomar := LEAST(v_pendiente, r_lote.cantidad_disponible);

        -- El trigger trg_detalle_movimiento_existencia resta la cantidad (RN-03).
        INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad)
        VALUES (p_id_movimiento, r_lote.id_lote, v_tomar);

        v_pendiente := v_pendiente - v_tomar;
    END LOOP;
END;
$$;

-- Fin de 001_procedures.sql
