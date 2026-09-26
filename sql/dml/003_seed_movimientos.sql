-- =============================================================================
-- Archivo:      003_seed_movimientos.sql
-- Propósito:    Generar ~6 meses de historial de inventario: lotes, entradas
--               y salidas, con la existencia calculada por los triggers.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/Bitacora-IA.md para el registro de uso.
-- Descripción:  Resultado verificado: 117 lotes, 703 movimientos (117 entradas
--               + 586 salidas) y 703 detalles (consigna: 50 por tabla principal).
--
--               Cómo se garantiza la coherencia:
--               1. Todo lote se inserta con cantidad_disponible = 0.
--               2. Se arma una lista de eventos (una ENTRADA por lote y
--                  varias SALIDAS posteriores) y se inserta EN ORDEN DE FECHA.
--               3. La existencia la calcula trg_detalle_movimiento_existencia
--                  con cada detalle; si alguna salida excediera la existencia,
--                  el trigger abortaría el script completo (RN-04).
--               Resultado: la existencia de cada lote = entradas − salidas
--               del historial, sin ningún número escrito a mano.
--
--               Por qué INSERT directo y no CALL a los procedimientos: los
--               procedimientos registran con fecha now() (operación en vivo);
--               una carga histórica necesita fechas pasadas. Las reglas de
--               existencia se siguen aplicando porque viven en el trigger.
--
--               Escenarios que quedan listos para la demostración:
--                 - lotes vencidos con existencia (vw_lotes_por_vencer)
--                 - lotes que vencen en menos de 90 días
--                 - productos de alta rotación con inventario bajo
--                   (vw_inventario_bajo)
--               Es determinista: setseed() hace que random() genere siempre
--               la misma secuencia, así cada instalación produce los mismos
--               datos y los casos de prueba son reproducibles.
-- Dependencias: 001_schema.sql, 001_triggers.sql, 001_seed.sql,
--               002_seed_catalogos.sql y web/seed_usuarios.py (los
--               movimientos necesitan usuarios responsables, RN-08).
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 003_seed_movimientos.sql
-- =============================================================================

DO $$
DECLARE
    v_id_admin      usuario.id_usuario%TYPE;
    v_id_encargado  usuario.id_usuario%TYPE;
    v_id_movimiento movimiento.id_movimiento%TYPE;
    r_producto      RECORD;
    r_lote          RECORD;
    r_evento        RECORD;
    v_num_lotes     INTEGER;
    v_fecha_ingreso DATE;
    v_vencimiento   DATE;
    v_limite        DATE;
    v_cantidad      NUMERIC;
    v_restante      NUMERIC;
    v_salida        NUMERIC;
    v_fecha_salida  DATE;
    v_rotacion      NUMERIC;
    v_id_proveedor  proveedor.id_proveedor%TYPE;
    v_precio        NUMERIC;
    v_id_lote       lote.id_lote%TYPE;
    k               INTEGER;
    v_areas         TEXT[] := ARRAY['Consumo área de química clínica',
                                    'Consumo área de hematología',
                                    'Consumo área de microbiología',
                                    'Consumo área de inmunología',
                                    'Consumo toma de muestras',
                                    'Consumo área de uroanálisis'];
BEGIN
    SELECT id_usuario INTO v_id_admin     FROM usuario WHERE usuario = 'admin.dev';
    SELECT id_usuario INTO v_id_encargado FROM usuario WHERE usuario = 'encargado.dev';

    IF v_id_admin IS NULL OR v_id_encargado IS NULL THEN
        RAISE EXCEPTION 'Faltan los usuarios admin.dev / encargado.dev. Ejecute web/seed_usuarios.py antes de este script.';
    END IF;

    PERFORM setseed(0.2026);

    -- Eventos a insertar; se ordenan por fecha al final.
    CREATE TEMP TABLE tmp_evento (
        id_lote     INTEGER,
        tipo        VARCHAR(10),
        fecha_hora  TIMESTAMP,
        cantidad    NUMERIC(10,2),
        precio      NUMERIC(10,2),
        id_usuario  INTEGER,
        observacion VARCHAR(255)
    ) ON COMMIT DROP;

    -- -------------------------------------------------------------------------
    -- Los 4 lotes del catálogo de la Entrega 2, con sus mismos datos, ahora
    -- respaldados por una ENTRADA (antes tenían la existencia escrita a mano).
    -- -------------------------------------------------------------------------
    FOR r_lote IN
        SELECT p.id_producto, pr.id_proveedor, v.numero_lote, v.ingreso, v.vence, v.cantidad
          FROM (VALUES ('1707801', '1234567-8', 'L-2026-001', DATE '2026-07-01', DATE '2027-07-01', 1000),
                       ('1669829', '2345678-9', 'L-2026-002', DATE '2026-07-05', DATE '2027-01-05',  800),
                       ('GNCTM-A', '2345678-9', 'L-2026-003', DATE '2026-06-15', NULL,                50),
                       ('NIP040',  '3456789-0', 'L-2026-004', DATE '2026-07-10', DATE '2028-07-10',  600)
               ) AS v(codigo, nit, numero_lote, ingreso, vence, cantidad)
          JOIN producto  p  ON p.codigo = v.codigo
          JOIN proveedor pr ON pr.nit   = v.nit
    LOOP
        INSERT INTO lote (id_producto, id_proveedor, numero_lote, fecha_ingreso, fecha_vencimiento, cantidad_disponible)
        VALUES (r_lote.id_producto, r_lote.id_proveedor, r_lote.numero_lote, r_lote.ingreso, r_lote.vence, 0)
        RETURNING id_lote INTO v_id_lote;

        INSERT INTO tmp_evento
        SELECT v_id_lote, 'ENTRADA', r_lote.ingreso + TIME '08:30', r_lote.cantidad,
               COALESCE((SELECT precio_compra FROM proveedor_producto
                          WHERE id_producto = r_lote.id_producto AND id_proveedor = r_lote.id_proveedor), 0),
               v_id_admin, 'Carga inicial del catálogo (Entrega 2)';
    END LOOP;

    -- -------------------------------------------------------------------------
    -- Lotes generados: de 1 a 3 por producto activo, ingresados en los
    -- últimos 180 días.
    -- -------------------------------------------------------------------------
    FOR r_producto IN
        SELECT p.id_producto, p.codigo, p.stock_minimo, p.requiere_vencimiento, p.unidad_medida,
               row_number() OVER (ORDER BY p.id_producto) AS rn
          FROM producto p
         WHERE p.estado
         ORDER BY p.id_producto
    LOOP
        v_num_lotes := 1 + floor(random() * 3)::INTEGER;

        FOR k IN 1 .. v_num_lotes LOOP
            -- Lotes escalonados: el primero hace ~6 meses, los siguientes más recientes.
            v_fecha_ingreso := CURRENT_DATE - (190 - (k - 1) * 60 - floor(random() * 25))::INTEGER;

            IF r_producto.requiere_vencimiento THEN
                -- Vida útil entre 4 y 18 meses: algunos lotes antiguos quedan
                -- vencidos y otros vencen dentro de los próximos 90 días.
                v_vencimiento := v_fecha_ingreso + (120 + floor(random() * 420))::INTEGER;
            ELSE
                v_vencimiento := NULL;
            END IF;

            SELECT pp.id_proveedor, pp.precio_compra
              INTO v_id_proveedor, v_precio
              FROM proveedor_producto pp
             WHERE pp.id_producto = r_producto.id_producto
             ORDER BY pp.id_proveedor
             LIMIT 1 OFFSET (k - 1) % 2;

            IF v_id_proveedor IS NULL THEN
                SELECT pp.id_proveedor, pp.precio_compra
                  INTO v_id_proveedor, v_precio
                  FROM proveedor_producto pp
                 WHERE pp.id_producto = r_producto.id_producto
                 ORDER BY pp.id_proveedor
                 LIMIT 1;
            END IF;

            -- Cantidad de compra: entre 3 y 10 veces el stock mínimo.
            v_cantidad := round(GREATEST(r_producto.stock_minimo, 2) * (3 + random() * 7));

            INSERT INTO lote (id_producto, id_proveedor, numero_lote, fecha_ingreso, fecha_vencimiento, cantidad_disponible)
            VALUES (r_producto.id_producto, v_id_proveedor,
                    format('L-%s-%s%s', to_char(v_fecha_ingreso, 'YYMM'), lpad(r_producto.id_producto::TEXT, 3, '0'), k),
                    v_fecha_ingreso, v_vencimiento, 0)
            RETURNING id_lote INTO v_id_lote;

            INSERT INTO tmp_evento VALUES
                (v_id_lote, 'ENTRADA',
                 v_fecha_ingreso + TIME '08:00' + (floor(random() * 120) || ' minutes')::INTERVAL,
                 v_cantidad, COALESCE(v_precio, 0),
                 CASE WHEN random() < 0.7 THEN v_id_encargado ELSE v_id_admin END,
                 'Compra a proveedor');

            -- Salidas del lote. Productos "de alta rotación" (1 de cada 4)
            -- consumen casi todo: son los que aparecen en inventario bajo.
            v_rotacion := CASE WHEN r_producto.rn % 4 = 0 THEN 0.30 ELSE 0.12 END;
            v_restante := v_cantidad;
            v_limite   := LEAST(CURRENT_DATE - 1, COALESCE(v_vencimiento, CURRENT_DATE - 1));
            v_fecha_salida := v_fecha_ingreso;

            FOR s IN 1 .. 6 LOOP
                v_fecha_salida := v_fecha_salida + (3 + floor(random() * 20))::INTEGER;
                EXIT WHEN v_fecha_salida > v_limite;

                v_salida := LEAST(v_restante, GREATEST(1, round(v_cantidad * v_rotacion * (0.6 + random() * 0.8))));
                EXIT WHEN v_salida <= 0;

                INSERT INTO tmp_evento VALUES
                    (v_id_lote, 'SALIDA',
                     v_fecha_salida + TIME '09:00' + (floor(random() * 480) || ' minutes')::INTERVAL,
                     v_salida, 0,
                     CASE WHEN random() < 0.85 THEN v_id_encargado ELSE v_id_admin END,
                     v_areas[1 + floor(random() * array_length(v_areas, 1))::INTEGER]);

                v_restante := v_restante - v_salida;
            END LOOP;
        END LOOP;
    END LOOP;

    -- -------------------------------------------------------------------------
    -- Insertar los eventos en orden cronológico: un movimiento por evento,
    -- con su detalle. El trigger actualiza la existencia en cada INSERT.
    -- -------------------------------------------------------------------------
    FOR r_evento IN
        SELECT * FROM tmp_evento ORDER BY fecha_hora, tipo, id_lote
    LOOP
        INSERT INTO movimiento (id_usuario, tipo_movimiento, fecha_hora, observacion)
        VALUES (r_evento.id_usuario, r_evento.tipo, r_evento.fecha_hora, r_evento.observacion)
        RETURNING id_movimiento INTO v_id_movimiento;

        INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad, precio_unitario)
        VALUES (v_id_movimiento, r_evento.id_lote, r_evento.cantidad, r_evento.precio);
    END LOOP;
END;
$$;

-- Fin de 003_seed_movimientos.sql
