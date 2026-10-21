-- =============================================================================
-- Archivo:      003_correccion_entrada.sql
-- Propósito:    Privilegios de la corrección de entradas.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code).
-- Descripción:  Corregir una entrada cambia existencias y costos ya
--               registrados, así que es exclusivo del Administrador (igual
--               que en SIGAL). Ningún rol recibe UPDATE sobre
--               detalle_movimiento ni acceso a la tabla correccion_entrada: la
--               única vía es el procedimiento, que corre como SECURITY DEFINER.
--               Las correcciones se consultan por la vista, que pueden leer
--               los tres roles (transparencia del historial).
-- Dependencias: 001_roles.sql, procedures/003_correccion_entrada.sql,
--               views/005_correccion_entrada.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     como dueño de las funciones o superusuario:
--               psql -U usuario_app -d inventario_laboratorio -f 003_correccion_entrada.sql
-- =============================================================================

-- 1. Con los permisos de su dueño y search_path fijo (evita que un rol
--    suplante una tabla en otro esquema).
ALTER PROCEDURE sp_corregir_entrada(INTEGER, INTEGER, VARCHAR, NUMERIC, NUMERIC, INTEGER, VARCHAR, DATE, INTEGER)
    SECURITY DEFINER SET search_path = public, pg_temp;

-- 2. Nadie por defecto (PostgreSQL concede EXECUTE a PUBLIC al crear).
REVOKE ALL ON PROCEDURE sp_corregir_entrada(INTEGER, INTEGER, VARCHAR, NUMERIC, NUMERIC, INTEGER, VARCHAR, DATE, INTEGER) FROM PUBLIC;

-- 3. Corregir: solo el Administrador (RN-25).
GRANT EXECUTE ON PROCEDURE sp_corregir_entrada(INTEGER, INTEGER, VARCHAR, NUMERIC, NUMERIC, INTEGER, VARCHAR, DATE, INTEGER)
    TO rol_administrador;

-- 4. Consultar las correcciones: los tres roles (rol_encargado y
--    rol_administrador heredan de rol_consulta).
GRANT SELECT ON vw_correcciones_entrada TO rol_consulta;

-- Fin de 003_correccion_entrada.sql
