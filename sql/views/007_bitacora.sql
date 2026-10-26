-- =============================================================================
-- Archivo:      007_bitacora.sql
-- Propósito:    Bitácora con el nombre del responsable, para la pantalla.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  Une la bitácora con el usuario responsable. Sin usuario
--               (cambio hecho fuera de la app) se muestra "Sistema".
-- Dependencias: sql/ddl/007_bitacora.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 007_bitacora.sql
-- =============================================================================

CREATE OR REPLACE VIEW vw_bitacora AS
SELECT b.id_bitacora,
       b.fecha_hora,
       b.id_usuario,
       coalesce(u.usuario, 'sistema')  AS usuario,
       coalesce(u.nombre, 'Sistema')   AS nombre_usuario,
       b.accion,
       b.entidad,
       b.id_registro,
       b.referencia,
       b.detalle
  FROM bitacora b
  LEFT JOIN usuario u ON u.id_usuario = b.id_usuario;

COMMENT ON VIEW vw_bitacora IS 'Bitácora (RN-30) con el nombre del responsable.';

-- Fin de 007_bitacora.sql
