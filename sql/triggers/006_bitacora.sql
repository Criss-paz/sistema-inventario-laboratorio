-- =============================================================================
-- Archivo:      006_bitacora.sql
-- Propósito:    Escribir en la bitácora cada cambio de datos (RN-30).
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  fn_bitacora() es un trigger AFTER genérico. Sus argumentos
--               dicen qué columna identifica al registro y cuál lo describe
--               para una persona (por ejemplo id_producto y nombre). Corre
--               como SECURITY DEFINER: ningún rol tiene INSERT sobre
--               bitacora, así que nadie puede escribir ni alterar entradas
--               por su cuenta.
--               Qué se audita:
--                 categoria, producto, proveedor, examen_laboratorio,
--                 proveedor_producto, examen_producto, usuario, rol,
--                 rol_permiso    crear, modificar y eliminar
--                 lote           solo los datos que corrige una persona
--                                (la existencia la mueven las entradas y
--                                salidas, que ya se auditan)
--                 movimiento     cada entrada, salida y devolución
--                 correccion_entrada  cada dato corregido
--               fn_registrar_evento(): eventos de la app que no cambian
--               datos (cierre de sesión, descarga de respaldo).
--               trg_bitacora_inmutable: la bitácora no se modifica ni borra.
-- Reglas de negocio que materializa: RN-30.
-- Dependencias: sql/ddl/007_bitacora.sql, sql/ddl/006_permisos.sql,
--               sql/ddl/004_correccion_entrada.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 006_bitacora.sql
-- =============================================================================

CREATE OR REPLACE FUNCTION fn_bitacora()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_viejo   JSONB;
    v_nuevo   JSONB;
    v_detalle JSONB;
    v_campo   TEXT;
BEGIN
    -- Nunca se guarda la contraseña ni su hash.
    IF TG_OP <> 'INSERT' THEN v_viejo := to_jsonb(OLD) - 'password_hash'; END IF;
    IF TG_OP <> 'DELETE' THEN v_nuevo := to_jsonb(NEW) - 'password_hash'; END IF;

    IF TG_OP = 'UPDATE' THEN
        v_detalle := '{}';
        FOR v_campo IN SELECT jsonb_object_keys(v_nuevo) LOOP
            IF v_nuevo -> v_campo IS DISTINCT FROM v_viejo -> v_campo THEN
                v_detalle := v_detalle || jsonb_build_object(v_campo,
                    jsonb_build_object('antes', v_viejo -> v_campo, 'despues', v_nuevo -> v_campo));
            END IF;
        END LOOP;
        IF to_jsonb(NEW) -> 'password_hash' IS DISTINCT FROM to_jsonb(OLD) -> 'password_hash' THEN
            v_detalle := v_detalle || '{"contraseña": {"antes": null, "despues": "(cambiada)"}}';
        END IF;
        IF v_detalle = '{}' THEN
            RETURN NULL;                       -- no cambió nada
        END IF;
    ELSE
        v_detalle := coalesce(v_nuevo, v_viejo);
    END IF;

    INSERT INTO bitacora (id_usuario, accion, entidad, id_registro, referencia, detalle)
    VALUES (nullif(current_setting('app.id_usuario', true), '')::INTEGER,
            CASE TG_OP WHEN 'INSERT' THEN 'CREAR' WHEN 'UPDATE' THEN 'MODIFICAR' ELSE 'ELIMINAR' END,
            TG_TABLE_NAME,
            coalesce(v_nuevo, v_viejo) ->> TG_ARGV[0],
            left(coalesce(v_nuevo, v_viejo) ->> TG_ARGV[1], 150),
            v_detalle);
    RETURN NULL;
END;
$$;

COMMENT ON FUNCTION fn_bitacora() IS
    'RN-30: registra en la bitácora el cambio. Argumentos: columna identificadora, columna descriptiva.';

-- Catálogos, usuarios y roles: crear, modificar y eliminar.
CREATE OR REPLACE TRIGGER trg_bitacora_categoria AFTER INSERT OR UPDATE OR DELETE ON categoria
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_categoria', 'nombre');
CREATE OR REPLACE TRIGGER trg_bitacora_producto AFTER INSERT OR UPDATE OR DELETE ON producto
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_producto', 'nombre');
CREATE OR REPLACE TRIGGER trg_bitacora_proveedor AFTER INSERT OR UPDATE OR DELETE ON proveedor
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_proveedor', 'nombre');
CREATE OR REPLACE TRIGGER trg_bitacora_examen AFTER INSERT OR UPDATE OR DELETE ON examen_laboratorio
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_examen', 'nombre_examen');
CREATE OR REPLACE TRIGGER trg_bitacora_proveedor_producto AFTER INSERT OR UPDATE OR DELETE ON proveedor_producto
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_proveedor', 'id_producto');
CREATE OR REPLACE TRIGGER trg_bitacora_examen_producto AFTER INSERT OR UPDATE OR DELETE ON examen_producto
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_examen', 'id_producto');
CREATE OR REPLACE TRIGGER trg_bitacora_usuario AFTER INSERT OR UPDATE OR DELETE ON usuario
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_usuario', 'usuario');
CREATE OR REPLACE TRIGGER trg_bitacora_rol AFTER INSERT OR UPDATE OR DELETE ON rol
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_rol', 'nombre');
CREATE OR REPLACE TRIGGER trg_bitacora_rol_permiso AFTER INSERT OR DELETE ON rol_permiso
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_rol', 'codigo');

-- Lote: solo lo que corrige una persona, no la existencia.
CREATE OR REPLACE TRIGGER trg_bitacora_lote
    AFTER UPDATE OF id_proveedor, numero_lote, fecha_ingreso, fecha_vencimiento, estado ON lote
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_lote', 'numero_lote');

-- Movimientos y correcciones: solo se crean (son inmutables).
CREATE OR REPLACE TRIGGER trg_bitacora_movimiento AFTER INSERT ON movimiento
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_movimiento', 'numero_documento');
CREATE OR REPLACE TRIGGER trg_bitacora_correccion AFTER INSERT ON correccion_entrada
    FOR EACH ROW EXECUTE FUNCTION fn_bitacora('id_movimiento', 'campo');

-- Eventos de la app que no cambian datos.
CREATE OR REPLACE FUNCTION fn_registrar_evento(p_accion VARCHAR, p_referencia VARCHAR DEFAULT NULL)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    -- Los inicios de sesión los escribe la app antes de adoptar un rol;
    -- desde un rol solo se pueden registrar estos dos eventos.
    IF p_accion NOT IN ('CERRAR_SESION', 'DESCARGAR_RESPALDO') THEN
        RAISE EXCEPTION 'Evento de bitácora no permitido: %.', p_accion;
    END IF;
    INSERT INTO bitacora (id_usuario, accion, entidad, referencia)
    VALUES (nullif(current_setting('app.id_usuario', true), '')::INTEGER, p_accion,
            CASE p_accion WHEN 'DESCARGAR_RESPALDO' THEN 'respaldo' ELSE 'sesion' END,
            left(p_referencia, 150));
END;
$$;

COMMENT ON FUNCTION fn_registrar_evento(VARCHAR, VARCHAR) IS
    'RN-30: registra un cierre de sesión o una descarga de respaldo a nombre del usuario de la conexión.';

CREATE OR REPLACE FUNCTION fn_bitacora_inmutable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'La bitácora no se puede modificar ni borrar.';
END;
$$;

CREATE OR REPLACE TRIGGER trg_bitacora_inmutable
    BEFORE UPDATE OR DELETE ON bitacora
    FOR EACH ROW
    EXECUTE FUNCTION fn_bitacora_inmutable();

-- Fin de 006_bitacora.sql
