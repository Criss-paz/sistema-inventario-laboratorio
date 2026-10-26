-- =============================================================================
-- Archivo:      004_permisos_bitacora.sql
-- Propósito:    Privilegios de los permisos configurables y de la bitácora.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  - rol_administrador administra roles y sus permisos (la app
--                 solo deja hacerlo a quien tiene el permiso USUARIOS).
--               - La bitácora: solo se lee por la vista, y solo el nivel
--                 administrador (la app pide el permiso BITACORA). Nadie
--                 tiene INSERT sobre bitacora: la escriben los triggers y
--                 fn_registrar_evento, que corren como SECURITY DEFINER.
--               - Cualquier rol puede registrar su cierre de sesión.
--               Solo contiene GRANT/REVOKE sobre objetos propios: lo puede
--               ejecutar el dueño de las tablas (usuario_app en local,
--               neondb_owner en Neon) sin superusuario.
-- Dependencias: sql/ddl/006_permisos.sql, sql/ddl/007_bitacora.sql,
--               sql/procedures/004_permisos.sql, sql/triggers/006_bitacora.sql,
--               sql/views/007_bitacora.sql, sql/security/001_roles.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 004_permisos_bitacora.sql
-- =============================================================================

REVOKE ALL ON permiso, rol_permiso, bitacora, vw_bitacora FROM PUBLIC;
REVOKE ALL ON FUNCTION fn_rol_bd(INTEGER), fn_bitacora(), fn_registrar_evento(VARCHAR, VARCHAR) FROM PUBLIC;

-- Roles y permisos.
GRANT SELECT ON permiso TO rol_administrador;
GRANT SELECT, INSERT, DELETE ON rol_permiso TO rol_administrador;
GRANT INSERT (nombre, descripcion), UPDATE (nombre, descripcion), DELETE ON rol TO rol_administrador;
GRANT EXECUTE ON FUNCTION fn_rol_bd(INTEGER) TO rol_administrador;

-- Bitácora.
GRANT SELECT ON vw_bitacora TO rol_administrador;
GRANT EXECUTE ON FUNCTION fn_registrar_evento(VARCHAR, VARCHAR) TO rol_consulta;

-- Fin de 004_permisos_bitacora.sql
