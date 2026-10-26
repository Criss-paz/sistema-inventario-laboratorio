-- =============================================================================
-- Archivo:      007_bitacora.sql
-- Propósito:    Bitácora de auditoría: quién hizo qué y cuándo.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  Migración aditiva. Una fila por acción:
--                 - Cambios en los datos (crear, modificar, eliminar): los
--                   escriben los triggers de sql/triggers/006_bitacora.sql,
--                   así que quedan registrados sin importar desde dónde se
--                   hagan. Al modificar se guardan solo los campos que
--                   cambiaron, con su valor anterior y el nuevo.
--                 - Eventos de la aplicación: inicio de sesión (correcto o
--                   fallido), cierre de sesión y descarga de respaldo.
--               El usuario responsable lo informa la app en cada conexión
--               (set_config('app.id_usuario', ...)); si un cambio se hace
--               fuera de la app, id_usuario queda NULL ("Sistema").
--               Nunca se guarda una contraseña ni su hash: solo que cambió.
--               La tabla solo crece (trg_bitacora_inmutable).
--
-- Reglas de negocio que materializa:
--   RN-30  Toda creación, modificación o eliminación de datos y todo inicio
--          y cierre de sesión queda en la bitácora con su responsable y
--          fecha; la bitácora no se modifica ni se borra.
--
-- Dependencias: 001_schema.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 007_bitacora.sql
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bitacora (
    id_bitacora  BIGINT       GENERATED ALWAYS AS IDENTITY,
    fecha_hora   TIMESTAMP    NOT NULL DEFAULT now(),
    id_usuario   INTEGER,
    accion       VARCHAR(20)  NOT NULL,
    entidad      VARCHAR(40)  NOT NULL,
    id_registro  VARCHAR(40),
    referencia   VARCHAR(150),
    detalle      JSONB,
    CONSTRAINT pk_bitacora PRIMARY KEY (id_bitacora),
    -- RESTRICT: un usuario con historial no se borra (se desactiva).
    CONSTRAINT fk_bitacora_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_bitacora_accion CHECK (accion IN (
        'CREAR', 'MODIFICAR', 'ELIMINAR',
        'INICIAR_SESION', 'SESION_FALLIDA', 'CERRAR_SESION', 'DESCARGAR_RESPALDO'))
);

COMMENT ON TABLE bitacora IS
    'Auditoría (RN-30): quién hizo qué y cuándo. Solo crece; nunca guarda contraseñas.';
COMMENT ON COLUMN bitacora.entidad IS 'Tabla afectada (producto, movimiento, ...) o "sesion" / "respaldo".';
COMMENT ON COLUMN bitacora.detalle IS
    'CREAR/ELIMINAR: la fila completa. MODIFICAR: {campo: {antes, despues}} solo de lo que cambió.';

-- La pantalla filtra por fecha, por usuario y por registro.
CREATE INDEX IF NOT EXISTS ix_bitacora_fecha   ON bitacora (fecha_hora DESC);
CREATE INDEX IF NOT EXISTS ix_bitacora_usuario ON bitacora (id_usuario);
CREATE INDEX IF NOT EXISTS ix_bitacora_entidad ON bitacora (entidad, id_registro);

COMMIT;

-- Fin de 007_bitacora.sql
