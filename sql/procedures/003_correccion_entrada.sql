-- =============================================================================
-- Archivo:      003_correccion_entrada.sql
-- Propósito:    Corregir los datos de una entrada en una sola operación atómica
--               y dejar registrada cada corrección.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code).
-- Descripción:  sp_corregir_entrada recibe los valores correctos; los que
--               vienen en NULL no se tocan. Por cada campo que de verdad
--               cambia, inserta una fila en correccion_entrada (valor anterior,
--               nuevo, motivo, usuario) y aplica el cambio:
--                 - cantidad y precio_unitario: en detalle_movimiento (el
--                   trigger ajusta la existencia del lote por la diferencia);
--                 - proveedor, número de lote y vencimiento: en lote. Son datos
--                   del lote, así que valen para todas sus entradas.
--               Todo o nada: si un cambio falla (existencia negativa, número de
--               lote repetido, vencimiento faltante), no queda ninguno.
--
--               El kardex y la valorización se recalculan solos, porque se
--               calculan desde el historial (fn_kardex_promedio).
--
--               No se corrige el producto ni la fecha de la entrada: cambiar
--               el producto mueve existencia entre productos y se hace con una
--               salida y una entrada nuevas, con su observación.
--
-- Reglas de negocio:
--   RN-25  Una entrada se corrige, no se elimina; cada corrección se registra.
--   RN-26  Motivo obligatorio (mínimo 10 caracteres) y usuario responsable.
--   RN-01  La existencia no queda negativa (trg_z_correccion_existencia).
--   RN-06  El número de lote corregido no puede repetir otro del mismo producto.
--   RN-07  Si el producto requiere vencimiento, no se puede dejar sin fecha.
--
-- Dependencias: ddl/004_correccion_entrada.sql, triggers/003_correccion_entrada.sql,
--               procedures/001_procedures.sql (fn_validar_usuario_activo)
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 003_correccion_entrada.sql
-- =============================================================================

CREATE OR REPLACE PROCEDURE sp_corregir_entrada(
    p_id_usuario         INTEGER,
    p_id_movimiento      INTEGER,
    p_motivo             VARCHAR,
    p_cantidad           NUMERIC DEFAULT NULL,
    p_precio_unitario    NUMERIC DEFAULT NULL,
    p_id_proveedor       INTEGER DEFAULT NULL,
    p_numero_lote        VARCHAR DEFAULT NULL,
    p_fecha_vencimiento  DATE    DEFAULT NULL,
    INOUT p_cambios      INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_tipo        movimiento.tipo_movimiento%TYPE;
    v_det         detalle_movimiento%ROWTYPE;
    v_lote        lote%ROWTYPE;
    v_motivo      VARCHAR := trim(coalesce(p_motivo, ''));
    v_numero      VARCHAR := nullif(trim(coalesce(p_numero_lote, '')), '');
    v_nombre_ant  proveedor.nombre%TYPE;
    v_nombre_nvo  proveedor.nombre%TYPE;
BEGIN
    p_cambios := 0;
    PERFORM fn_validar_usuario_activo(p_id_usuario);

    IF length(v_motivo) < 10 THEN
        RAISE EXCEPTION 'Escriba el motivo de la corrección (al menos 10 caracteres).';
    END IF;

    SELECT m.tipo_movimiento INTO v_tipo FROM movimiento m WHERE m.id_movimiento = p_id_movimiento;
    IF v_tipo IS NULL THEN
        RAISE EXCEPTION 'El movimiento #% no existe.', p_id_movimiento;
    END IF;
    IF v_tipo <> 'ENTRADA' THEN
        RAISE EXCEPTION 'Solo se pueden corregir entradas. El movimiento #% es de tipo %; una salida equivocada se corrige con una devolución.',
                        p_id_movimiento, v_tipo;
    END IF;

    -- Una entrada tiene un único detalle (sp_registrar_entrada).
    SELECT * INTO v_det FROM detalle_movimiento d WHERE d.id_movimiento = p_id_movimiento FOR UPDATE;
    SELECT * INTO v_lote FROM lote l WHERE l.id_lote = v_det.id_lote FOR UPDATE;

    -- La variable solo vive en esta transacción: al terminar, el historial
    -- vuelve a ser inmutable aunque algo falle.
    PERFORM set_config('inventario.correccion_entrada', 'on', true);

    -- Cantidad (el trigger ajusta la existencia del lote).
    IF p_cantidad IS NOT NULL AND p_cantidad <> v_det.cantidad THEN
        IF p_cantidad <= 0 THEN
            RAISE EXCEPTION 'La cantidad corregida debe ser mayor que cero.';
        END IF;
        INSERT INTO correccion_entrada (id_movimiento, id_usuario, campo, valor_anterior, valor_nuevo, motivo)
        VALUES (p_id_movimiento, p_id_usuario, 'cantidad', v_det.cantidad::text, round(p_cantidad, 2)::text, v_motivo);
        UPDATE detalle_movimiento SET cantidad = p_cantidad WHERE id_detalle = v_det.id_detalle;
        p_cambios := p_cambios + 1;
    END IF;

    -- Precio unitario de compra.
    IF p_precio_unitario IS NOT NULL AND p_precio_unitario <> v_det.precio_unitario THEN
        IF p_precio_unitario < 0 THEN
            RAISE EXCEPTION 'El precio unitario no puede ser negativo.';
        END IF;
        INSERT INTO correccion_entrada (id_movimiento, id_usuario, campo, valor_anterior, valor_nuevo, motivo)
        VALUES (p_id_movimiento, p_id_usuario, 'precio_unitario', v_det.precio_unitario::text, round(p_precio_unitario, 2)::text, v_motivo);
        UPDATE detalle_movimiento SET precio_unitario = p_precio_unitario WHERE id_detalle = v_det.id_detalle;
        p_cambios := p_cambios + 1;
    END IF;

    PERFORM set_config('inventario.correccion_entrada', 'off', true);

    -- Proveedor (dato del lote).
    IF p_id_proveedor IS NOT NULL AND p_id_proveedor <> v_lote.id_proveedor THEN
        SELECT nombre INTO v_nombre_nvo FROM proveedor WHERE id_proveedor = p_id_proveedor AND estado;
        IF v_nombre_nvo IS NULL THEN
            RAISE EXCEPTION 'El proveedor elegido no existe o está dado de baja.';
        END IF;
        SELECT nombre INTO v_nombre_ant FROM proveedor WHERE id_proveedor = v_lote.id_proveedor;
        INSERT INTO correccion_entrada (id_movimiento, id_usuario, campo, valor_anterior, valor_nuevo, motivo)
        VALUES (p_id_movimiento, p_id_usuario, 'proveedor', v_nombre_ant, v_nombre_nvo, v_motivo);
        UPDATE lote SET id_proveedor = p_id_proveedor WHERE id_lote = v_lote.id_lote;
        p_cambios := p_cambios + 1;
    END IF;

    -- Número de lote (RN-06: único por producto).
    IF v_numero IS NOT NULL AND v_numero <> v_lote.numero_lote THEN
        IF EXISTS (SELECT 1 FROM lote l WHERE l.id_producto = v_lote.id_producto
                                          AND l.numero_lote = v_numero AND l.id_lote <> v_lote.id_lote) THEN
            RAISE EXCEPTION 'El producto ya tiene otro lote con el número %. Si la mercadería es de ese lote, registre la corrección de cantidad y una entrada nueva en el lote correcto.', v_numero;
        END IF;
        INSERT INTO correccion_entrada (id_movimiento, id_usuario, campo, valor_anterior, valor_nuevo, motivo)
        VALUES (p_id_movimiento, p_id_usuario, 'numero_lote', v_lote.numero_lote, v_numero, v_motivo);
        UPDATE lote SET numero_lote = v_numero WHERE id_lote = v_lote.id_lote;
        p_cambios := p_cambios + 1;
    END IF;

    -- Vencimiento (RN-07 lo vigila trg_lote_vencimiento; el CHECK, que no sea
    -- anterior al ingreso).
    IF p_fecha_vencimiento IS NOT NULL AND p_fecha_vencimiento IS DISTINCT FROM v_lote.fecha_vencimiento THEN
        IF p_fecha_vencimiento < v_lote.fecha_ingreso THEN
            RAISE EXCEPTION 'La fecha de vencimiento (%) no puede ser anterior al ingreso del lote (%).',
                            to_char(p_fecha_vencimiento, 'DD/MM/YYYY'), to_char(v_lote.fecha_ingreso, 'DD/MM/YYYY');
        END IF;
        INSERT INTO correccion_entrada (id_movimiento, id_usuario, campo, valor_anterior, valor_nuevo, motivo)
        VALUES (p_id_movimiento, p_id_usuario, 'fecha_vencimiento',
                to_char(v_lote.fecha_vencimiento, 'DD/MM/YYYY'), to_char(p_fecha_vencimiento, 'DD/MM/YYYY'), v_motivo);
        UPDATE lote SET fecha_vencimiento = p_fecha_vencimiento WHERE id_lote = v_lote.id_lote;
        p_cambios := p_cambios + 1;
    END IF;

    IF p_cambios = 0 THEN
        RAISE EXCEPTION 'No hay nada que corregir: los datos son iguales a los registrados.';
    END IF;
END;
$$;

-- Fin de 003_correccion_entrada.sql
