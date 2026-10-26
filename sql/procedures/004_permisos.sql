-- =============================================================================
-- Archivo:      004_permisos.sql
-- Propósito:    Rol de base de datos de cada rol de la aplicación.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  fn_rol_bd(id_rol): el rol de PostgreSQL que adopta la app
--               (SET ROLE) para un usuario de ese rol. Es el más bajo que
--               cubre todos sus permisos:
--                 Administrador, o algún permiso de nivel ADMINISTRADOR
--                   -> rol_administrador
--                 algún permiso de nivel ENCARGADO -> rol_encargado
--                 ningún permiso (solo consulta)   -> rol_consulta
--               La protección del rol Administrador está en
--               sql/triggers/005_rol_protegido.sql.
-- Reglas de negocio que materializa: RN-28.
-- Dependencias: sql/ddl/006_permisos.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 004_permisos.sql
-- =============================================================================

CREATE OR REPLACE FUNCTION fn_rol_bd(p_id_rol INTEGER)
RETURNS NAME
LANGUAGE sql
STABLE
AS $$
    SELECT CASE
             WHEN r.nombre = 'Administrador'
               OR EXISTS (SELECT 1 FROM rol_permiso rp JOIN permiso p ON p.codigo = rp.codigo
                           WHERE rp.id_rol = r.id_rol AND p.nivel_bd = 'ADMINISTRADOR')
               THEN 'rol_administrador'::NAME
             WHEN EXISTS (SELECT 1 FROM rol_permiso rp JOIN permiso p ON p.codigo = rp.codigo
                           WHERE rp.id_rol = r.id_rol AND p.nivel_bd = 'ENCARGADO')
               THEN 'rol_encargado'::NAME
             ELSE 'rol_consulta'::NAME
           END
      FROM rol r
     WHERE r.id_rol = p_id_rol;
$$;

COMMENT ON FUNCTION fn_rol_bd(INTEGER) IS
    'RN-28: rol de PostgreSQL más bajo que cubre los permisos del rol de la aplicación.';

-- Fin de 004_permisos.sql
