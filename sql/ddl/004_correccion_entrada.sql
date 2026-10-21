-- =============================================================================
-- Archivo:      004_correccion_entrada.sql
-- Propósito:    Registro de las correcciones hechas a una entrada.
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  Migración aditiva. Una entrada mal digitada (cantidad,
--               precio, proveedor, número de lote o vencimiento) no se borra:
--               se corrige con sp_corregir_entrada (ver
--               sql/procedures/003_correccion_entrada.sql), y cada campo
--               corregido deja aquí una fila con el valor anterior, el nuevo,
--               el motivo, quién y cuándo. Así el historial sigue completo
--               (RN-09): se ve lo que se registró y lo que se corrigió.
--
--               La tabla solo crece: el trigger trg_correccion_inmutable
--               (sql/triggers/003_correccion_entrada.sql) impide modificar o
--               borrar una corrección.
--
-- Reglas de negocio que materializa:
--   RN-25  Una entrada no se elimina; sus datos se corrigen y cada corrección
--          queda registrada con el valor anterior y el nuevo.
--   RN-26  Toda corrección declara su motivo por escrito (mínimo 10
--          caracteres) y queda ligada al usuario que la hizo.
--
-- Dependencias: 001_schema.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 004_correccion_entrada.sql
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS correccion_entrada (
    id_correccion   INTEGER GENERATED ALWAYS AS IDENTITY,
    id_movimiento   INTEGER      NOT NULL,
    id_usuario      INTEGER      NOT NULL,
    fecha_hora      TIMESTAMP    NOT NULL DEFAULT now(),
    campo           VARCHAR(30)  NOT NULL,
    valor_anterior  VARCHAR(150),
    valor_nuevo     VARCHAR(150),
    motivo          VARCHAR(255) NOT NULL,
    CONSTRAINT pk_correccion_entrada PRIMARY KEY (id_correccion),
    -- RESTRICT: el historial no se borra, y la corrección es parte de él.
    CONSTRAINT fk_correccion_entrada_movimiento FOREIGN KEY (id_movimiento)
        REFERENCES movimiento (id_movimiento) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_correccion_entrada_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_correccion_entrada_campo
        CHECK (campo IN ('cantidad', 'precio_unitario', 'proveedor', 'numero_lote', 'fecha_vencimiento')),
    CONSTRAINT ck_correccion_entrada_motivo CHECK (length(trim(motivo)) >= 10),
    -- Una "corrección" que no cambia nada no aporta al historial.
    CONSTRAINT ck_correccion_entrada_cambio CHECK (valor_anterior IS DISTINCT FROM valor_nuevo)
);

COMMENT ON TABLE correccion_entrada IS
    'Correcciones de entradas (RN-25, RN-26): una fila por campo corregido, con su valor anterior y el nuevo.';

-- La ficha del movimiento pregunta "¿qué correcciones tiene esta entrada?".
CREATE INDEX IF NOT EXISTS ix_correccion_entrada_movimiento ON correccion_entrada (id_movimiento);

COMMIT;

-- Fin de 004_correccion_entrada.sql
