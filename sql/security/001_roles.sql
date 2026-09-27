-- =============================================================================
-- Archivo:      001_roles.sql
-- Propósito:    Roles de base de datos con privilegios diferenciados
--               (mínimo de 3 que pide la consigna, sección 5 requisito 6).
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/Bitacora-IA.md para el registro de uso.
-- Descripción:  Crea 3 roles de grupo (NOLOGIN), uno por cada rol de la tabla
--               `rol` (actores de la Entrega 1), y les asigna privilegios
--               mínimos (principio de menor privilegio):
--
--                 Privilegio                        admin  encargado  consulta
--                 --------------------------------  -----  ---------  --------
--                 Ver catálogos, lotes y vistas       ✔        ✔         ✔
--                 Ver historial de movimientos        ✔        ✔         ✔
--                 Registrar entradas/salidas (CALL)   ✔        ✔         ✘
--                 Alta/edición de catálogos           ✔        ✘         ✘
--                 Alta/edición de usuarios            ✔        ✘         ✘
--                 Leer password_hash                  ✘        ✘         ✘
--                 INSERT directo en movimientos       ✘        ✘         ✘
--                 Modificar cantidad_disponible       ✘        ✘         ✘
--                 DELETE físico (salvo tablas puente) ✘        ✘         ✘
--
-- Decisiones:
--   1. Movimientos solo por procedimiento. Ningún rol (ni el administrador)
--      tiene INSERT sobre movimiento/detalle_movimiento: la única forma de
--      registrar inventario es CALL sp_registrar_entrada / sp_registrar_salida,
--      que se ejecutan como SECURITY DEFINER (con los permisos de su dueño).
--      Así el historial solo entra por el camino que valida RN-04, RN-07, RN-08.
--   2. cantidad_disponible no se puede editar a mano: el administrador tiene
--      UPDATE en `lote` solo sobre las columnas que corrige un humano
--      (GRANT UPDATE por columna). La existencia solo cambia por el trigger.
--   3. password_hash: ningún rol lo lee. El login lo valida la app con el
--      usuario de conexión ANTES de adoptar el rol del usuario (SET ROLE).
--   4. Sin DELETE: coherente con la política de bajas lógicas (campo
--      `estado`, docs/entrega-2/modelo-relacional.md). Única excepción: las
--      tablas puente proveedor_producto y examen_producto (sin historial).
--
-- Uso desde la app web: después del login, la app ejecuta
--   SET ROLE rol_administrador | rol_encargado | rol_consulta
-- en su conexión, según el rol del usuario. Así la base de datos aplica los
-- permisos aunque la interfaz tuviera un error (defensa en profundidad).
--
-- Dependencias: sql/ddl/001_schema.sql, sql/triggers/001_triggers.sql,
--               sql/procedures/001_procedures.sql, sql/views/001_views.sql,
--               sql/views/002_valorizacion_promedio.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     como superusuario (CREATE ROLE requiere ese privilegio):
--               psql -U postgres -d inventario_laboratorio -f 001_roles.sql
-- Probar:       psql -U usuario_app -d inventario_laboratorio
--               SET ROLE rol_consulta;  SELECT * FROM vw_inventario_bajo;  -- OK
--               UPDATE producto SET stock_minimo = 1;   -- permiso denegado
--               RESET ROLE;
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Crear los roles (idempotente: se puede volver a ejecutar sin error).
--    NOLOGIN: nadie se conecta directamente con ellos; se adoptan con SET ROLE.
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_rol TEXT;
BEGIN
    FOREACH v_rol IN ARRAY ARRAY['rol_administrador', 'rol_encargado', 'rol_consulta'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = v_rol) THEN
            EXECUTE format('CREATE ROLE %I NOLOGIN', v_rol);
        END IF;
    END LOOP;
END;
$$;

COMMENT ON ROLE rol_administrador IS 'Administrador: catálogos, usuarios, lotes y movimientos (por procedimiento)';
COMMENT ON ROLE rol_encargado     IS 'Encargado de inventario: registra entradas/salidas y consulta';
COMMENT ON ROLE rol_consulta      IS 'Usuario de consulta: solo lectura, sin datos de usuarios';

-- La app se conecta con el usuario dueño de las tablas (usuario_app en la
-- instalación local, el dueño del proyecto en Neon) y adopta uno de estos
-- roles tras el login. Se toma el dueño de `producto` para no depender del
-- nombre del usuario en cada servidor.
DO $$
DECLARE
    v_duenio NAME;
BEGIN
    SELECT tableowner INTO v_duenio FROM pg_tables WHERE schemaname = 'public' AND tablename = 'producto';
    EXECUTE format('GRANT rol_administrador, rol_encargado, rol_consulta TO %I', v_duenio);
END;
$$;

-- -----------------------------------------------------------------------------
-- 2. Punto de partida limpio: nada es público.
--    PostgreSQL da EXECUTE a PUBLIC sobre toda función nueva por defecto; se
--    revoca para que solo los roles autorizados puedan llamar procedimientos.
-- -----------------------------------------------------------------------------
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL PROCEDURES IN SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

GRANT USAGE ON SCHEMA public TO rol_administrador, rol_encargado, rol_consulta;

-- -----------------------------------------------------------------------------
-- 3. Procedimientos como SECURITY DEFINER (decisión 1).
--    SET search_path fijo: evita que un rol cree un objeto con el mismo nombre
--    en otro esquema y lo "cuele" dentro del procedimiento privilegiado.
-- -----------------------------------------------------------------------------
ALTER PROCEDURE sp_registrar_entrada(INTEGER, INTEGER, INTEGER, VARCHAR, DATE, NUMERIC, NUMERIC, VARCHAR, INTEGER)
    SECURITY DEFINER SET search_path = public, pg_temp;
ALTER PROCEDURE sp_registrar_salida(INTEGER, INTEGER, NUMERIC, VARCHAR, INTEGER)
    SECURITY DEFINER SET search_path = public, pg_temp;

-- -----------------------------------------------------------------------------
-- 4. rol_consulta — solo lectura.
--    Sin acceso a `usuario` ni a `rol`, ni a movimientos crudos: el historial
--    lo ve por la vista, que muestra el nombre del responsable pero no el hash.
-- -----------------------------------------------------------------------------
GRANT SELECT ON categoria, producto, proveedor, lote,
                examen_laboratorio, proveedor_producto, examen_producto
    TO rol_consulta;

GRANT SELECT ON vw_existencia_producto, vw_inventario_bajo,
                vw_lotes_por_vencer, vw_historial_movimientos,
                vw_valorizacion_inventario
    TO rol_consulta;

-- Reportes valorizados (sql/views/002_valorizacion_promedio.sql): kardex a
-- costo promedio ponderado. Lee vw_historial_movimientos como el invocador.
GRANT EXECUTE ON FUNCTION fn_kardex_promedio(INTEGER) TO rol_consulta;

-- -----------------------------------------------------------------------------
-- 5. rol_encargado — todo lo de consulta + registrar entradas y salidas.
--    GRANT de un rol a otro: el encargado hereda los permisos de consulta.
-- -----------------------------------------------------------------------------
GRANT rol_consulta TO rol_encargado;

GRANT EXECUTE ON PROCEDURE sp_registrar_entrada(INTEGER, INTEGER, INTEGER, VARCHAR, DATE, NUMERIC, NUMERIC, VARCHAR, INTEGER),
                           sp_registrar_salida(INTEGER, INTEGER, NUMERIC, VARCHAR, INTEGER)
    TO rol_encargado;

-- -----------------------------------------------------------------------------
-- 6. rol_administrador — todo lo del encargado + mantenimiento de catálogos
--    y usuarios. Sin DELETE salvo en tablas puente (decisión 4).
-- -----------------------------------------------------------------------------
GRANT rol_encargado TO rol_administrador;

GRANT INSERT, UPDATE ON categoria, producto, proveedor, examen_laboratorio
    TO rol_administrador;

GRANT SELECT, INSERT, UPDATE, DELETE ON proveedor_producto, examen_producto
    TO rol_administrador;

GRANT SELECT ON rol TO rol_administrador;

-- usuario: puede ver y editar todo MENOS leer el hash (decisión 3). Para
-- cambiar una contraseña sí puede escribir password_hash (UPDATE por columna),
-- que la app genera con werkzeug.security antes de enviarla.
GRANT SELECT (id_usuario, id_rol, nombre, usuario, estado, fecha_creacion)
    ON usuario TO rol_administrador;
GRANT INSERT (id_rol, nombre, usuario, password_hash, estado)
    ON usuario TO rol_administrador;
GRANT UPDATE (id_rol, nombre, usuario, password_hash, estado)
    ON usuario TO rol_administrador;

-- lote: corrige datos del lote o lo da de baja, pero NO su existencia
-- (decisión 2). Los lotes nuevos nacen por sp_registrar_entrada.
GRANT UPDATE (id_proveedor, numero_lote, fecha_ingreso, fecha_vencimiento, estado)
    ON lote TO rol_administrador;

-- Fin de 001_roles.sql
