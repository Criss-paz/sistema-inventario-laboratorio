-- =============================================================================
-- Archivo:      005_correccion_entrada.sql
-- Propósito:    Consultar las correcciones de entradas con nombres legibles.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code).
-- Descripción:  vw_correcciones_entrada traduce el campo corregido y trae el
--               nombre de quien corrigió, sin exponer la tabla usuario
--               (mismo criterio que vw_historial_movimientos). La usa la ficha
--               de cada movimiento para mostrar qué se corrigió y por qué.
-- Dependencias: ddl/004_correccion_entrada.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 005_correccion_entrada.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- vw_correcciones_entrada: las correcciones con nombres legibles, para la
-- ficha del movimiento y la auditoría. Los roles leen por aquí, no la tabla.
-- Sus permisos están en security/003_correccion_entrada.sql.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_correcciones_entrada AS
SELECT c.id_correccion, c.id_movimiento, c.fecha_hora, c.campo,
       CASE c.campo WHEN 'cantidad' THEN 'Cantidad'
                    WHEN 'precio_unitario' THEN 'Precio unitario'
                    WHEN 'proveedor' THEN 'Proveedor'
                    WHEN 'numero_lote' THEN 'Número de lote'
                    WHEN 'fecha_vencimiento' THEN 'Vencimiento' END AS campo_legible,
       c.valor_anterior, c.valor_nuevo, c.motivo, u.nombre AS nombre_usuario
  FROM correccion_entrada c
  JOIN usuario u ON u.id_usuario = c.id_usuario;

-- Fin de 005_correccion_entrada.sql
