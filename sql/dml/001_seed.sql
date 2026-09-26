-- =============================================================================
-- Archivo:      001_seed.sql
-- Propósito:    Datos iniciales para demostrar el sistema
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
-- Descripción:  Roles, categorías base (curadas por el equipo desde la
--               interfaz web — ver docs/casos-prueba/casos-prueba-entrega-2.md,
--               CP-18) y los 4 exámenes de la Entrega 2.
--               NO incluye la tabla `usuario`: esos registros se crean con
--               web/seed_usuarios.py porque las contraseñas deben hashearse
--               con la misma librería (werkzeug.security) que usa la app al
--               validar el login — nunca se escribe un hash a mano en SQL.
-- Dependencias: 001_schema.sql (debe ejecutarse primero)
-- Nota:         Base de la Entrega 2. El volumen de 50 registros por tabla
--               principal lo completan 002_carga_catalogo.sql,
--               003_seed_examenes.sql y 004_carga_movimientos.sql (Entrega 3).
-- =============================================================================

-- Roles (coinciden con los 3 actores de la Entrega 1)
INSERT INTO rol (nombre, descripcion) VALUES
    ('Administrador', 'Administra usuarios, roles, productos, categorías, proveedores, inventario, movimientos y reportes'),
    ('Encargado de inventario', 'Registra entradas y salidas; consulta productos, lotes y existencias'),
    ('Usuario de consulta', 'Acceso limitado a consultas, sin capacidad de modificar información crítica');

-- Categorías — catálogo real del laboratorio, curado por el equipo vía CRUD web.
INSERT INTO categoria (nombre, descripcion) VALUES
    ('REACTIVOS', 'Sustancias químicas usadas en análisis de laboratorio'),
    ('MATERIAL PARA EL LABORATORIO', 'Tubos, pipetas y material general'),
    ('EQUIPO DE PROTECCION PERSONAL', 'Guantes, mascarillas, batas'),
    ('INSUMOS DE TOMA DE MUESTRA', 'Jeringas, torundas, ligas, tubos de recolección'),
    ('CALIBRADORES', 'Controles de calidad para equipos de análisis');

-- Exámenes de laboratorio
INSERT INTO examen_laboratorio (nombre_examen, descripcion, codigo_interno) VALUES
    ('Glucosa en ayunas', 'Determinación de glucosa sérica en ayunas', 'EX-GLU-01'),
    ('Perfil lipídico', 'Colesterol total, HDL, LDL, triglicéridos', 'EX-LIP-01'),
    ('Hemoglobina glicosilada (HbA1c)', 'Control de diabetes a largo plazo', 'EX-HBA-01'),
    ('Hematología completa', 'Conteo celular sanguíneo completo', 'EX-HEM-01');

-- Productos, proveedores, lotes y movimientos: vienen del inventario real del
-- laboratorio (002_carga_catalogo.sql y 004_carga_movimientos.sql). Los 12
-- productos y 3 proveedores de ejemplo de la Entrega 2 se retiraron: los
-- productos reales ya incluyen esos códigos, con sus datos verdaderos.
-- Cada lote nace en 0 y lo carga una ENTRADA registrada en el historial,
-- para que la existencia siempre esté respaldada por movimientos (RN-02, RN-09).

-- Fin de 001_seed.sql
