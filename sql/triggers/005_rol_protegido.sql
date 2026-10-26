-- =============================================================================
-- Archivo:      005_rol_protegido.sql
-- Propósito:    El rol Administrador no se renombra ni se elimina.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  La app y fn_rol_bd reconocen al Administrador por su nombre;
--               si se renombrara o eliminara, nadie tendría todos los
--               permisos. Este trigger lo impide aunque se intente desde SQL.
-- Reglas de negocio que materializa: RN-29.
-- Dependencias: sql/ddl/006_permisos.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 005_rol_protegido.sql
-- =============================================================================

CREATE OR REPLACE FUNCTION fn_rol_protegido()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.nombre = 'Administrador'
       AND (TG_OP = 'DELETE' OR NEW.nombre IS DISTINCT FROM OLD.nombre) THEN
        RAISE EXCEPTION 'El rol Administrador no se puede renombrar ni eliminar: siempre debe existir quien administre el sistema.';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$;

CREATE OR REPLACE TRIGGER trg_rol_protegido
    BEFORE UPDATE OR DELETE ON rol
    FOR EACH ROW
    EXECUTE FUNCTION fn_rol_protegido();

-- Fin de 005_rol_protegido.sql
