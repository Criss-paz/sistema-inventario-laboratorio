-- =============================================================================
-- Archivo:      003_devolucion.sql
-- Propósito:    Exponer el motivo y la salida corregida en el historial.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code).
-- Descripción:  Recrea vw_historial_movimientos añadiendo las dos columnas de
--               002_devolucion.sql, y agrega vw_devoluciones para el informe.
--               Las 16 columnas originales quedan igual y en el mismo orden,
--               así que ninguna consulta existente se rompe.
--
--               Se mantiene el criterio de 001_roles.sql: los roles leen el
--               historial por la vista, nunca por la tabla `movimiento`.
--
-- Dependencias: 001_views.sql, 002_devolucion.sql (DDL)
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 003_devolucion.sql
-- =============================================================================

-- CREATE OR REPLACE VIEW no admite quitar ni reordenar columnas, pero sí
-- añadirlas al final: por eso las dos nuevas van después de `observacion`.
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
       m.observacion,
       m.id_movimiento_origen,
       m.motivo
  FROM movimiento m
  JOIN usuario            u ON u.id_usuario    = m.id_usuario
  JOIN detalle_movimiento d ON d.id_movimiento = m.id_movimiento
  JOIN lote               l ON l.id_lote       = d.id_lote
  JOIN producto           p ON p.id_producto   = l.id_producto;

-- -----------------------------------------------------------------------------
-- vw_devoluciones — una fila por devolución, para el informe y la auditoría.
-- Responde de un vistazo: qué se devolvió, de qué salida, por qué y quién.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_devoluciones AS
SELECT dev.id_movimiento,
       dev.fecha_hora,
       dev.motivo,
       u.nombre                          AS registrada_por,
       ori.id_movimiento                 AS id_salida_corregida,
       ori.fecha_hora                    AS fecha_salida,
       uo.nombre                         AS salida_registrada_por,
       count(d.id_detalle)               AS lotes_devueltos,
       sum(d.cantidad)                   AS total_devuelto
  FROM movimiento dev
  JOIN usuario            u   ON u.id_usuario     = dev.id_usuario
  JOIN movimiento         ori ON ori.id_movimiento = dev.id_movimiento_origen
  JOIN usuario            uo  ON uo.id_usuario    = ori.id_usuario
  JOIN detalle_movimiento d   ON d.id_movimiento  = dev.id_movimiento
 WHERE dev.tipo_movimiento = 'DEVOLUCION'
 GROUP BY dev.id_movimiento, dev.fecha_hora, dev.motivo, u.nombre,
          ori.id_movimiento, ori.fecha_hora, uo.nombre;

-- Mismo criterio de lectura que el resto de vistas (001_roles.sql).
GRANT SELECT ON vw_devoluciones TO rol_consulta;

-- Fin de 003_devolucion.sql
