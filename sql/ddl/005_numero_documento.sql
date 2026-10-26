-- =============================================================================
-- Archivo:      005_numero_documento.sql
-- Propósito:    Número de documento propio para cada movimiento: E000001
--               (entrada), S000001 (salida) y D000001 (devolución).
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ para el registro de uso.
-- Descripción:  Migración aditiva con relleno de datos. El laboratorio
--               identifica cada entrada y salida por su número de papel (y
--               SIGAL conservó esa numeración). Hasta ahora ese número solo
--               estaba dentro del texto de la observación ("Entrada E001790
--               (SIGAL)"); aquí pasa a su propia columna:
--                 1. Se agrega movimiento.numero_documento.
--                 2. Se rellena con el número que trae la observación; los
--                    movimientos sin número (registrados en la app) reciben
--                    el siguiente del correlativo, en orden de registro.
--                 3. Se limpia la observación: se quita el número y el origen
--                    ("registro en papel", "SIGAL"). En las salidas de SIGAL
--                    queda solo el área que pidió el insumo.
--                 4. NOT NULL, UNIQUE y un CHECK de formato y de prefijo.
--               Desde aquí, el trigger trg_movimiento_numero
--               (sql/triggers/004_numero_documento.sql) asigna el número a
--               cada movimiento nuevo.
--
--               El paso 3 modifica movimientos ya registrados. Es una
--               migración única, hecha por el dueño de las tablas: desactiva
--               trg_movimiento_inmutable (RN-09) solo dentro de esta
--               transacción y lo vuelve a activar antes del COMMIT. Ni la app
--               ni ningún rol pueden hacerlo.
--
-- Reglas de negocio que materializa:
--   RN-27  Cada movimiento tiene un número de documento único y correlativo
--          por tipo: E (entrada), S (salida), D (devolución), seis dígitos.
--
-- Dependencias: 001_schema.sql, 002_devolucion.sql y las cargas
--               dml/004_carga_movimientos.sql y dml/005_carga_sigal.sql
--               (ejecutar DESPUÉS de ellas: los números salen de su texto).
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 005_numero_documento.sql
-- =============================================================================

BEGIN;

ALTER TABLE movimiento ADD COLUMN IF NOT EXISTS numero_documento VARCHAR(7);

COMMENT ON COLUMN movimiento.numero_documento IS
    'Número de documento (RN-27): E/S/D + 6 dígitos, correlativo por tipo. Lo asigna trg_movimiento_numero.';

ALTER TABLE movimiento DISABLE TRIGGER trg_movimiento_inmutable;

-- 2a. El número que ya trae la observación (registro en papel y SIGAL).
UPDATE movimiento
   SET numero_documento = substring(observacion FROM '^(?:Entrada|Salida) ([ES][0-9]{6})')
 WHERE numero_documento IS NULL
   AND observacion ~ '^(Entrada|Salida) [ES][0-9]{6}';

-- 2b. Los que no traen número: el siguiente de su tipo, en orden de registro.
WITH sin_numero AS (
    SELECT m.id_movimiento,
           left(m.tipo_movimiento, 1) AS prefijo,
           row_number() OVER (PARTITION BY m.tipo_movimiento ORDER BY m.id_movimiento) AS n
      FROM movimiento m
     WHERE m.numero_documento IS NULL
), ultimo AS (
    SELECT left(tipo_movimiento, 1) AS prefijo,
           max(substring(numero_documento FROM 2)::INTEGER) AS maximo
      FROM movimiento
     WHERE numero_documento IS NOT NULL
     GROUP BY 1
)
UPDATE movimiento m
   SET numero_documento = s.prefijo || lpad((coalesce(u.maximo, 0) + s.n)::TEXT, 6, '0')
  FROM sin_numero s
  LEFT JOIN ultimo u ON u.prefijo = s.prefijo
 WHERE m.id_movimiento = s.id_movimiento;

-- 3. Observación sin el número ni el origen de la carga.
UPDATE movimiento
   SET observacion = NULL
 WHERE observacion ~ '^(Entrada|Salida) [ES][0-9]{6} \((registro en papel|SIGAL)\)$';

UPDATE movimiento                                   -- salidas de SIGAL: el área
   SET observacion = substring(observacion FROM '^Salida S[0-9]{6} \(SIGAL\), área (.+)$')
 WHERE observacion ~ '^Salida S[0-9]{6} \(SIGAL\), área .+$';

UPDATE movimiento                                   -- notas de la carga del papel
   SET observacion = upper(left(nota, 1)) || substring(nota FROM 2) || '.'
  FROM (SELECT id_movimiento,
               substring(observacion FROM '^Salida S[0-9]{6} \(registro en papel; (.+)\)$') AS nota
          FROM movimiento) x
 WHERE x.id_movimiento = movimiento.id_movimiento
   AND x.nota IS NOT NULL;

UPDATE movimiento d                                 -- devoluciones: la salida por su número
   SET observacion = 'Devolución de la salida ' || o.numero_documento
  FROM movimiento o
 WHERE o.id_movimiento = d.id_movimiento_origen
   AND d.tipo_movimiento = 'DEVOLUCION';

ALTER TABLE movimiento ENABLE TRIGGER trg_movimiento_inmutable;

-- 4. Restricciones.
ALTER TABLE movimiento ALTER COLUMN numero_documento SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_movimiento_numero_documento') THEN
        ALTER TABLE movimiento
            ADD CONSTRAINT uq_movimiento_numero_documento UNIQUE (numero_documento),
            ADD CONSTRAINT ck_movimiento_numero_documento CHECK (
                numero_documento ~ '^[ESD][0-9]{6}$'
                AND left(numero_documento, 1) = left(tipo_movimiento, 1));
    END IF;
END;
$$;

COMMIT;

-- Fin de 005_numero_documento.sql
