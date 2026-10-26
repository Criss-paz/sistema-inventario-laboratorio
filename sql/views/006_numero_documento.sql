-- =============================================================================
-- Archivo:      006_numero_documento.sql
-- Propósito:    Exponer el número de documento en el historial.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  Agrega al final de vw_historial_movimientos el número de
--               documento del movimiento y, en las devoluciones, el de la
--               salida que corrigen (CREATE OR REPLACE VIEW solo admite
--               columnas nuevas al final). Los permisos de la vista se
--               conservan.
-- Dependencias: sql/views/003_devolucion.sql, sql/ddl/005_numero_documento.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 006_numero_documento.sql
-- =============================================================================

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
       m.motivo,
       m.numero_documento,
       o.numero_documento                  AS numero_origen
  FROM movimiento m
  JOIN usuario            u ON u.id_usuario    = m.id_usuario
  JOIN detalle_movimiento d ON d.id_movimiento = m.id_movimiento
  JOIN lote               l ON l.id_lote       = d.id_lote
  JOIN producto           p ON p.id_producto   = l.id_producto
  LEFT JOIN movimiento    o ON o.id_movimiento = m.id_movimiento_origen;

-- Fin de 006_numero_documento.sql
