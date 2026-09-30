-- =============================================================================
-- Archivo:      002_devolucion.sql
-- Propósito:    Privilegios de la devolución: quién puede registrarla y quién
--               solo consultarla.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code).
-- Descripción:  Mantiene el mismo criterio de 001_roles.sql: ningún rol tiene
--               INSERT sobre `movimiento`. La única vía para devolver es el
--               procedimiento, que corre como SECURITY DEFINER y solo está
--               concedido a los dos roles que pueden mover inventario.
--
--               Devolver corrige un error de inventario, así que se trata como
--               una operación de escritura: Administrador y Encargado. El rol
--               de consulta puede ver qué se devolvió (fn_devolvible) pero no
--               ejecutarla.
--
-- Dependencias: 001_roles.sql, 002_devolucion.sql (DDL, triggers y procedures)
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     como superusuario o dueño de las funciones:
--               psql -U postgres -d inventario_laboratorio -f 002_devolucion.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. SECURITY DEFINER con search_path fijo.
-- El procedimiento se ejecuta con los permisos de su dueño (que sí puede
-- insertar en `movimiento`), no con los del rol que lo llama. El search_path
-- fijo evita que un rol cree un objeto con el mismo nombre en otro esquema y
-- logre que el procedimiento lo use en su lugar.
-- -----------------------------------------------------------------------------
ALTER PROCEDURE sp_registrar_devolucion(INTEGER, INTEGER, VARCHAR, INTEGER[], NUMERIC[], INTEGER)
    SECURITY DEFINER SET search_path = public, pg_temp;

-- fn_devolvible también va como SECURITY DEFINER, aunque solo lea: consulta
-- `movimiento` y `detalle_movimiento` directamente, y por diseño de
-- 001_roles.sql ningún rol tiene SELECT sobre esas tablas (el historial se lee
-- por vistas). Sin esto, PostgreSQL responde "permiso denegado a la tabla
-- detalle_movimiento" y la app devuelve un 403 al abrir la pantalla.
ALTER FUNCTION fn_devolvible(INTEGER)
    SECURITY DEFINER SET search_path = public, pg_temp;

-- -----------------------------------------------------------------------------
-- 2. Nadie por defecto.
-- PostgreSQL concede EXECUTE a PUBLIC al crear una rutina; se revoca primero
-- para que el GRANT siguiente sea la única fuente de permiso.
-- -----------------------------------------------------------------------------
REVOKE ALL ON PROCEDURE sp_registrar_devolucion(INTEGER, INTEGER, VARCHAR, INTEGER[], NUMERIC[], INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION  fn_devolvible(INTEGER) FROM PUBLIC;

-- -----------------------------------------------------------------------------
-- 3. Registrar una devolución: solo quien puede mover inventario.
-- -----------------------------------------------------------------------------
GRANT EXECUTE ON PROCEDURE sp_registrar_devolucion(INTEGER, INTEGER, VARCHAR, INTEGER[], NUMERIC[], INTEGER)
    TO rol_encargado;
-- rol_administrador hereda de rol_encargado (GRANT rol_encargado TO
-- rol_administrador en 001_roles.sql), así que no hace falta repetirlo.

-- -----------------------------------------------------------------------------
-- 4. Consultar qué queda por devolver: los tres roles.
-- Es información de solo lectura y la pantalla de detalle de un movimiento la
-- muestra a cualquiera que pueda ver el historial.
-- -----------------------------------------------------------------------------
GRANT EXECUTE ON FUNCTION fn_devolvible(INTEGER) TO rol_consulta;
-- rol_encargado y rol_administrador la heredan por la cadena de roles.

-- -----------------------------------------------------------------------------
-- 5. Las dos columnas nuevas de `movimiento` se leen a través de las vistas,
-- que ya tienen sus permisos en 001_roles.sql. No se concede SELECT directo
-- sobre la tabla: el criterio de 001_roles.sql se mantiene intacto.
-- -----------------------------------------------------------------------------

-- Fin de 002_devolucion.sql
