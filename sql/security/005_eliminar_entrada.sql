-- =============================================================================
-- Archivo:      005_eliminar_entrada.sql
-- Propósito:    Privilegios de la eliminación de entradas.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  sp_eliminar_entrada corre como su dueño (SECURITY DEFINER,
--               search_path fijo): ningún rol tiene DELETE sobre movimiento,
--               detalle_movimiento ni lote, y así lo siguen sin tener. Solo
--               rol_administrador lo puede ejecutar; además, el procedimiento
--               exige que el usuario tenga el rol Administrador de la
--               aplicación (un rol personalizado de nivel administrador no
--               basta). Solo GRANT/REVOKE sobre objetos propios: lo ejecuta
--               el dueño de las tablas sin superusuario.
-- Reglas de negocio que materializa: RN-31.
-- Dependencias: sql/procedures/005_eliminar_entrada.sql, sql/security/001_roles.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 005_eliminar_entrada.sql
-- =============================================================================

ALTER PROCEDURE sp_eliminar_entrada(INTEGER, INTEGER, VARCHAR, INTEGER)
    SECURITY DEFINER SET search_path = public, pg_temp;

REVOKE ALL ON PROCEDURE sp_eliminar_entrada(INTEGER, INTEGER, VARCHAR, INTEGER) FROM PUBLIC;

GRANT EXECUTE ON PROCEDURE sp_eliminar_entrada(INTEGER, INTEGER, VARCHAR, INTEGER)
    TO rol_administrador;

-- Fin de 005_eliminar_entrada.sql
