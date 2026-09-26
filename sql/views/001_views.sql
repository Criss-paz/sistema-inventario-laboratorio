-- =============================================================================
-- Archivo:      001_views.sql
-- Propósito:    Vistas de consulta del inventario: existencias, inventario
--               bajo, lotes por vencer e historial de movimientos.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/Bitacora-IA.md para el registro de uso.
-- Descripción:  4 vistas:
--                 1. vw_existencia_producto    → RF-08, RF-19, RF-32
--                 2. vw_inventario_bajo        → RF-29, RN-10, RN-11
--                 3. vw_lotes_por_vencer       → RF-30, RN-07
--                 4. vw_historial_movimientos  → RF-26 a RF-28, RF-34, RF-35
--               Estándar S7 (sin redundancia): la existencia por producto, el
--               faltante contra el mínimo y los días para vencer son datos
--               calculables; no se guardan en ninguna tabla, se derivan aquí.
-- Dependencias: sql/ddl/001_schema.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 001_views.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Vista 1: existencia consolidada por producto.
--
-- Suma la existencia de todos los lotes activos del producto y la separa en:
--   existencia_utilizable  lotes sin vencer (o de productos que no vencen)
--   existencia_vencida     lotes con fecha_vencimiento ya pasada
-- La utilizable es la que cuenta para despachar (sp_registrar_salida) y para
-- decidir si hay inventario bajo; la vencida se muestra aparte porque sigue
-- ocupando espacio físico y hay que darla de baja.
--
-- LEFT JOIN: un producto sin lotes aparece con existencia 0 (no desaparece
-- del listado, que es justo cuando más importa verlo).
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_existencia_producto AS
SELECT p.id_producto,
       p.codigo,
       p.nombre,
       c.nombre                                          AS categoria,
       p.unidad_medida,
       p.stock_minimo,
       p.requiere_vencimiento,
       p.estado,
       COALESCE(sum(l.cantidad_disponible)
                FILTER (WHERE l.fecha_vencimiento IS NULL
                           OR l.fecha_vencimiento >= CURRENT_DATE), 0)
                                                         AS existencia_utilizable,
       COALESCE(sum(l.cantidad_disponible)
                FILTER (WHERE l.fecha_vencimiento < CURRENT_DATE), 0)
                                                         AS existencia_vencida,
       count(l.id_lote) FILTER (WHERE l.cantidad_disponible > 0)
                                                         AS lotes_con_existencia
  FROM producto p
  JOIN categoria c ON c.id_categoria = p.id_categoria
  LEFT JOIN lote l ON l.id_producto = p.id_producto
                  AND l.estado
 GROUP BY p.id_producto, c.nombre;

-- -----------------------------------------------------------------------------
-- Vista 2: productos con inventario bajo.
--
-- Regla de negocio:
--   RN-11  "Una existencia igual o inferior al stock mínimo deberá
--          identificarse como inventario bajo" → comparación con <=, tal
--          como está redactada la regla en la Entrega 1.
--   Se compara la existencia UTILIZABLE: un reactivo vencido no sirve para
--   trabajar, así que no debe ocultar que hay que reponer.
--   Solo productos activos: uno dado de baja ya no se repone.
--   faltante = cuánto hay que reponer para volver al mínimo.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_inventario_bajo AS
SELECT e.id_producto,
       e.codigo,
       e.nombre,
       e.categoria,
       e.unidad_medida,
       e.stock_minimo,
       e.existencia_utilizable,
       e.existencia_vencida,
       GREATEST(e.stock_minimo - e.existencia_utilizable, 0) AS faltante
  FROM vw_existencia_producto e
 WHERE e.estado
   AND e.existencia_utilizable <= e.stock_minimo;

-- -----------------------------------------------------------------------------
-- Vista 3: lotes vencidos o próximos a vencer.
--
-- Regla de negocio:
--   RF-30  Consultar productos próximos a vencer.
--   Horizonte: 90 días. La Entrega 1 no fija un número; 90 días es la
--   decisión del equipo porque cubre el tiempo típico de pedir y recibir
--   reactivos de un proveedor. Se cambia en un solo lugar (el INTERVAL).
--   Incluye los lotes YA vencidos que aún tienen existencia (situacion =
--   'VENCIDO'): son los más urgentes de atender (dar de baja).
--   Solo lotes activos con existencia > 0: un lote vacío no genera alerta.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_lotes_por_vencer AS
SELECT l.id_lote,
       l.numero_lote,
       p.id_producto,
       p.codigo,
       p.nombre                                    AS producto,
       pr.nombre                                   AS proveedor,
       l.fecha_ingreso,
       l.fecha_vencimiento,
       l.cantidad_disponible,
       p.unidad_medida,
       (l.fecha_vencimiento - CURRENT_DATE)        AS dias_para_vencer,
       CASE WHEN l.fecha_vencimiento < CURRENT_DATE THEN 'VENCIDO'
            ELSE 'POR VENCER'
       END                                         AS situacion
  FROM lote l
  JOIN producto  p  ON p.id_producto   = l.id_producto
  JOIN proveedor pr ON pr.id_proveedor = l.id_proveedor
 WHERE l.estado
   AND l.cantidad_disponible > 0
   AND l.fecha_vencimiento IS NOT NULL
   AND l.fecha_vencimiento <= CURRENT_DATE + INTERVAL '90 days';

-- -----------------------------------------------------------------------------
-- Vista 4: historial de movimientos, una fila por lote afectado.
--
-- Regla de negocio:
--   RF-26  fecha y hora de cada movimiento.
--   RF-27  usuario responsable (RN-08).
--   RF-28, RF-34, RF-35  historial y trazabilidad: qué entró o salió, de qué
--          lote, de qué producto, quién lo hizo y cuándo.
--   Une las 6 tablas que el usuario tendría que cruzar a mano; la app solo
--   filtra sobre esta vista.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_historial_movimientos AS
SELECT m.id_movimiento,
       m.fecha_hora,
       m.tipo_movimiento,
       u.usuario                           AS usuario,
       u.nombre                            AS nombre_usuario,
       d.id_detalle,
       l.id_lote,
       l.numero_lote,
       p.id_producto,
       p.codigo,
       p.nombre                            AS producto,
       d.cantidad,
       p.unidad_medida,
       d.precio_unitario,
       round(d.cantidad * d.precio_unitario, 2) AS subtotal,
       m.observacion
  FROM movimiento m
  JOIN usuario            u ON u.id_usuario    = m.id_usuario
  JOIN detalle_movimiento d ON d.id_movimiento = m.id_movimiento
  JOIN lote               l ON l.id_lote       = d.id_lote
  JOIN producto           p ON p.id_producto   = l.id_producto;

-- Fin de 001_views.sql
