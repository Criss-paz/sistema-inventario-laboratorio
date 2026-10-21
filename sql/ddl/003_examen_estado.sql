-- =============================================================================
-- Archivo:      003_examen_estado.sql
-- Propósito:    Permitir dar de baja un examen de laboratorio sin borrarlo.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  Migración aditiva sobre 001_schema.sql. examen_laboratorio era
--               el único catálogo sin columna `estado`, así que un examen que
--               el laboratorio deja de ofrecer no tenía forma de retirarse.
--               Se usa baja lógica, igual que en categoria, producto,
--               proveedor y usuario:
--                 - el examen y sus insumos (examen_producto) se conservan,
--                   por si se vuelve a ofrecer;
--                 - las listas e informes de trabajo muestran solo los activos.
--               No se agrega DELETE: los roles de la app no tienen ese
--               privilegio sobre tablas de catálogo (sql/security/001_roles.sql).
--
-- Reglas de negocio que materializa:
--   RN-24  Un examen dado de baja deja de aparecer en el informe de pruebas
--          disponibles, pero conserva su ficha y sus insumos.
--
-- Dependencias: 001_schema.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 003_examen_estado.sql
-- =============================================================================

BEGIN;

-- DEFAULT TRUE: los 50 exámenes ya cargados quedan activos sin un UPDATE aparte.
-- IF NOT EXISTS hace el script reejecutable (útil al desplegar en Neon).
ALTER TABLE examen_laboratorio
    ADD COLUMN IF NOT EXISTS estado BOOLEAN NOT NULL DEFAULT TRUE;

COMMENT ON COLUMN examen_laboratorio.estado IS
    'TRUE = el laboratorio ofrece el examen. FALSE = baja lógica (RN-24).';

COMMIT;

-- Fin de 003_examen_estado.sql
