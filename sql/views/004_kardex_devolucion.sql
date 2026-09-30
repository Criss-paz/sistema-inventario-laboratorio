-- =============================================================================
-- Archivo:      004_kardex_devolucion.sql
-- Propósito:    Que el kardex valorice correctamente las devoluciones.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code).
--
-- Descripción:  CORRIGE UNA REGRESIÓN introducida por 002_devolucion.sql.
--               fn_kardex_promedio decidía con `IF tipo = 'ENTRADA' ... ELSE`,
--               y ese ELSE capturaba todo lo que no fuera entrada. Al aparecer
--               el tipo DEVOLUCION, el kardex lo trataba como salida: RESTABA
--               la cantidad en vez de sumarla.
--
--               Efecto medido antes de la corrección (producto 393):
--                   saldo del kardex     2.00
--                   existencia real      4.00
--               La diferencia es el doble de lo devuelto: restó 1 donde debía
--               sumar 1. Con ello quedaban mal la valorización del inventario
--               y el cuadre contable compras − consumo = existencia.
--
--               Cómo se valoriza una devolución: reingresa al costo promedio
--               vigente, el mismo al que la salida la descargó. Así el promedio
--               no se altera (entra al precio al que salió) y el saldo vuelve
--               exactamente al valor que tenía antes del error. Es el
--               tratamiento estándar de una devolución al almacén bajo costo
--               promedio ponderado móvil.
--
-- Regla de negocio:
--   RN-23  Una devolución reingresa al costo promedio vigente en ese momento;
--          no recalcula el promedio ni introduce un costo nuevo.
--
-- Dependencias: 002_valorizacion_promedio.sql, 002_devolucion.sql (DDL),
--               003_devolucion.sql (vistas)
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 004_kardex_devolucion.sql
-- =============================================================================

CREATE OR REPLACE FUNCTION fn_kardex_promedio(p_id_producto INTEGER DEFAULT NULL)
RETURNS TABLE (
    id_producto            INTEGER,
    fecha_hora             TIMESTAMP,
    id_movimiento          INTEGER,
    tipo_movimiento        VARCHAR,
    observacion            VARCHAR,
    cantidad_entrada       NUMERIC,
    costo_unitario_entrada NUMERIC,
    total_entrada          NUMERIC,
    cantidad_salida        NUMERIC,
    costo_unitario_salida  NUMERIC,
    total_salida           NUMERIC,
    saldo_cantidad         NUMERIC,
    costo_promedio         NUMERIC,
    saldo_valor            NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
#variable_conflict use_column
DECLARE
    r_mov        RECORD;
    v_producto   INTEGER;
    v_cantidad   NUMERIC := 0;   -- saldo en unidades
    v_valor      NUMERIC := 0;   -- saldo en quetzales (sin redondear)
    v_promedio   NUMERIC := 0;   -- costo promedio vigente
BEGIN
    FOR r_mov IN
        SELECT h.id_producto, h.fecha_hora, h.id_movimiento, h.tipo_movimiento, h.observacion,
               sum(h.cantidad)                     AS cantidad,
               sum(h.cantidad * h.precio_unitario) AS valor
          FROM vw_historial_movimientos h
         WHERE p_id_producto IS NULL OR h.id_producto = p_id_producto
         GROUP BY h.id_producto, h.fecha_hora, h.id_movimiento, h.tipo_movimiento, h.observacion
         ORDER BY h.id_producto, h.fecha_hora, h.id_movimiento
    LOOP
        IF v_producto IS DISTINCT FROM r_mov.id_producto THEN
            v_producto := r_mov.id_producto;
            v_cantidad := 0;
            v_valor    := 0;
            v_promedio := 0;
        END IF;

        id_producto     := r_mov.id_producto;
        fecha_hora      := r_mov.fecha_hora;
        id_movimiento   := r_mov.id_movimiento;
        tipo_movimiento := r_mov.tipo_movimiento;
        observacion     := r_mov.observacion;

        IF r_mov.tipo_movimiento = 'ENTRADA' THEN
            -- Compra: recalcula el promedio con el costo real de la factura.
            v_cantidad := v_cantidad + r_mov.cantidad;
            v_valor    := v_valor + r_mov.valor;
            IF v_cantidad > 0 THEN
                v_promedio := v_valor / v_cantidad;
            END IF;

            cantidad_entrada       := r_mov.cantidad;
            costo_unitario_entrada := round(r_mov.valor / r_mov.cantidad, 4);
            total_entrada          := round(r_mov.valor, 2);
            cantidad_salida        := NULL;
            costo_unitario_salida  := NULL;
            total_salida           := NULL;

        ELSIF r_mov.tipo_movimiento = 'DEVOLUCION' THEN
            -- Reingreso de una salida equivocada (RN-23). Se registra en la
            -- columna de entradas porque suma al saldo, pero al promedio
            -- vigente: no trae costo propio, así que el promedio no cambia.
            cantidad_entrada       := r_mov.cantidad;
            costo_unitario_entrada := round(v_promedio, 4);
            total_entrada          := round(r_mov.cantidad * v_promedio, 2);
            cantidad_salida        := NULL;
            costo_unitario_salida  := NULL;
            total_salida           := NULL;

            v_cantidad := v_cantidad + r_mov.cantidad;
            v_valor    := v_valor + r_mov.cantidad * v_promedio;

        ELSE
            -- SALIDA: se descarga al promedio vigente.
            cantidad_salida       := r_mov.cantidad;
            costo_unitario_salida := round(v_promedio, 4);
            total_salida          := round(r_mov.cantidad * v_promedio, 2);
            cantidad_entrada       := NULL;
            costo_unitario_entrada := NULL;
            total_entrada          := NULL;

            v_cantidad := v_cantidad - r_mov.cantidad;
            v_valor    := v_valor - r_mov.cantidad * v_promedio;
            -- Sin existencia no queda valor: evita residuos de redondeo.
            IF v_cantidad = 0 THEN
                v_valor := 0;
            END IF;
        END IF;

        saldo_cantidad := v_cantidad;
        costo_promedio := round(v_promedio, 4);
        saldo_valor    := round(v_valor, 2);
        RETURN NEXT;
    END LOOP;
END;
$$;

COMMENT ON FUNCTION fn_kardex_promedio(INTEGER) IS
    'Kardex por costo promedio ponderado móvil: una fila por movimiento con el saldo y el promedio vigente. Las devoluciones reingresan al promedio vigente (RN-23).';

-- Fin de 004_kardex_devolucion.sql
