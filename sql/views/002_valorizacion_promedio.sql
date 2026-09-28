-- =============================================================================
-- Archivo:      002_valorizacion_promedio.sql
-- Propósito:    Valorizar el inventario por COSTO PROMEDIO PONDERADO (móvil) y
--               generar el kardex de cada producto (RF-33 reportes de
--               inventario, RF-34 información histórica).
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ENTREGA3_BITACORA_IA.md para el registro de uso.
-- Descripción:  Método del promedio ponderado móvil (kardex):
--                 - Cada ENTRADA recalcula el costo promedio del producto:
--                     promedio = (valor del saldo + valor de la compra)
--                              / (cantidad del saldo + cantidad comprada)
--                 - Cada SALIDA se valoriza al costo promedio vigente en ese
--                   momento y no cambia el promedio.
--                 - Valor del inventario = saldo en unidades x costo promedio.
--               El cálculo es secuencial (cada fila depende del saldo
--               anterior), por eso es una función PL/pgSQL y no una consulta
--               de agregación. Nada se almacena: se calcula del historial
--               de movimientos cada vez (S7).
--
--               Permisos: la función es SECURITY INVOKER y lee la vista
--               vw_historial_movimientos, que rol_consulta ya puede consultar;
--               así el usuario de consulta obtiene reportes sin leer las
--               tablas de movimientos directamente.
-- Dependencias: sql/views/001_views.sql (vw_historial_movimientos,
--               vw_existencia_producto)
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 002_valorizacion_promedio.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- fn_kardex_promedio: una fila por movimiento, con el saldo después de él.
--   p_id_producto NULL = todos los productos (cada uno con su propio saldo).
-- -----------------------------------------------------------------------------
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
    -- Un movimiento puede tener varios detalles (una salida FEFO que toma
    -- de varios lotes): se agrupa para tratarlo como una sola operación.
    FOR r_mov IN
        SELECT h.id_producto, h.fecha_hora, h.id_movimiento, h.tipo_movimiento, h.observacion,
               sum(h.cantidad)                     AS cantidad,
               sum(h.cantidad * h.precio_unitario) AS valor
          FROM vw_historial_movimientos h
         WHERE p_id_producto IS NULL OR h.id_producto = p_id_producto
         GROUP BY h.id_producto, h.fecha_hora, h.id_movimiento, h.tipo_movimiento, h.observacion
         ORDER BY h.id_producto, h.fecha_hora, h.id_movimiento
    LOOP
        -- Cambio de producto: su kardex empieza en cero.
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
        ELSE
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
    'Kardex por costo promedio ponderado móvil: una fila por movimiento con el saldo y el promedio vigente';

-- -----------------------------------------------------------------------------
-- vw_valorizacion_inventario: valor actual del inventario por producto.
-- Toma la última fila del kardex de cada producto (su saldo actual). Los
-- productos sin movimientos aparecen con existencia y valor 0.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_valorizacion_inventario AS
WITH ultimo AS (
    SELECT DISTINCT ON (k.id_producto)
           k.id_producto, k.saldo_cantidad, k.costo_promedio, k.saldo_valor, k.fecha_hora
      FROM fn_kardex_promedio() k
     ORDER BY k.id_producto, k.fecha_hora DESC, k.id_movimiento DESC
)
SELECT e.id_producto,
       e.codigo,
       e.nombre,
       e.categoria,
       e.unidad_medida,
       e.estado,
       COALESCE(u.saldo_cantidad, 0)  AS existencia,
       e.existencia_vencida,
       COALESCE(u.costo_promedio, 0)  AS costo_promedio,
       COALESCE(u.saldo_valor, 0)     AS valor_inventario,
       u.fecha_hora                   AS ultimo_movimiento
  FROM vw_existencia_producto e
  LEFT JOIN ultimo u ON u.id_producto = e.id_producto;

COMMENT ON VIEW vw_valorizacion_inventario IS
    'Existencia y valor del inventario por producto a costo promedio ponderado (RF-33)';

-- Los roles se crean en sql/security/001_roles.sql. Si ya existen, este
-- script les da acceso a los objetos nuevos; si no, lo hará ese script.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rol_consulta') THEN
        REVOKE ALL ON FUNCTION fn_kardex_promedio(INTEGER) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION fn_kardex_promedio(INTEGER) TO rol_consulta;
        GRANT SELECT ON vw_valorizacion_inventario TO rol_consulta;
    END IF;
END;
$$;

-- Fin de 002_valorizacion_promedio.sql
