-- =============================================================================
-- Archivo:      001_seed.sql
-- Propósito:    Datos iniciales para demostrar el sistema
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
-- Descripción:  Roles, catálogo real de categorías y productos (curado a mano
--               por el equipo desde la interfaz web — ver
--               docs/entrega-2/casos-prueba/casos-prueba-entrega-2.md, CP-18),
--               proveedores, exámenes, relaciones N:M y lotes de ejemplo.
--               NO incluye la tabla `usuario`: esos registros se crean con
--               web/seed_usuarios.py porque las contraseñas deben hashearse
--               con la misma librería (werkzeug.security) que usa la app al
--               validar el login — nunca se escribe un hash a mano en SQL.
-- Dependencias: 001_schema.sql (debe ejecutarse primero)
-- Nota:         Set de demostración (no las 50 filas/tabla que pide el
--               requisito mínimo del sistema completo) — suficiente para
--               probar los 2 CRUD de la Entrega 2. Se amplía en Entrega 3.
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
    ('CALIBRADORES', 'Controles de calidad para equipos de análisis'),
    ('Anticoagulantes prueba 1', 'Ejemplo prueba 1');

-- Productos — catálogo real (códigos y nombres tal como los usa el laboratorio),
-- curado por el equipo vía CRUD web. id_categoria referenciado por posición de
-- inserción de arriba: 1=REACTIVOS, 2=MATERIAL PARA EL LABORATORIO,
-- 3=EQUIPO DE PROTECCION PERSONAL, 4=INSUMOS DE TOMA DE MUESTRA, 5=CALIBRADORES.
INSERT INTO producto (id_categoria, codigo, nombre, descripcion, unidad_medida, stock_minimo, requiere_vencimiento) VALUES
    (1, '1707801',    'MF GLUCOSA - GLU',                               'Reactivo para la detección de glucosa en sangre',            'Cartucho', 3,   TRUE),
    (1, '1669829',    'MF COLESTEROL - CHOL',                           'Reactivo para la detección de colesterol en sangre',         'Cartucho', 3,   TRUE),
    (1, 'HCFW',       'HbA1c CASSETTE FINECARE, WONDFO',                'Reactivo para la prueba de hemoglobina glicosilada',         'Caja',     3,   TRUE),
    (2, 'TE5ML1U',    'TUBO DE ENSAYO 5 ML (12X75MM)U',                 'Tubo de vidrio para muestras de diferentes',                 'unidad',   200, FALSE),
    (2, '370',        'PHOENIX CAJA PETRI 90X15 MM STSARDISH PACK 600', 'Caja petri para el área de bactereologia',                   'Caja',     2,   TRUE),
    (3, 'GNCTM-A',    'GUANTE NITRILO CELESTE TALLA M - AROSA',         'Caja de 100 unidades',                                       'Caja',     10,  FALSE),
    (3, 'MQNM-A',     'MASCARILLA QUIRÚRGICA NEGRA - MARCA AROSA',      'Caja de 50 unidades',                                        'Caja',     10,  FALSE),
    (4, 'NIP040',     'JERINGA DE 5*21*1 1/2',                          'Jeringa estéril con aguja',                                  'Caja',     5,   FALSE),
    (4, 'TV4MLEPET',  'TUBO AL VACÍO DE 4 ML. EDTA PET - AROSA',        'Tubo al vacío para examen del área de hematología',          'unidad',   200, FALSE),
    (5, 'AIAPMACMAC', 'AIA-PACK MULTI ANALYTE CONTROL MAC',             'Control MAC para equipo Tosoh',                              'ml',       2,   TRUE),
    (2, 'REA-999',    'Reactivo de prueba',                             NULL,                                                          'ml',       10,  FALSE),
    (1, '101010001',  'H13',                                            'TIRA DE ORINA',                                              'Caja',     0,   TRUE);

-- Exámenes de laboratorio
INSERT INTO examen_laboratorio (nombre_examen, descripcion, codigo_interno) VALUES
    ('Glucosa en ayunas', 'Determinación de glucosa sérica en ayunas', 'EX-GLU-01'),
    ('Perfil lipídico', 'Colesterol total, HDL, LDL, triglicéridos', 'EX-LIP-01'),
    ('Hemoglobina glicosilada (HbA1c)', 'Control de diabetes a largo plazo', 'EX-HBA-01'),
    ('Hematología completa', 'Conteo celular sanguíneo completo', 'EX-HEM-01');

-- Proveedores
INSERT INTO proveedor (nombre, nit, telefono, correo, direccion) VALUES
    ('Distribuidora Médica Quetzaltenango, S.A.', '1234567-8', '77761234', 'ventas@dmq.com.gt', '5a avenida 10-20 zona 1, Quetzaltenango'),
    ('Laboratorios Clínicos del Occidente', '2345678-9', '77762345', 'contacto@lco.com.gt', '12 calle 5-30 zona 3, Quetzaltenango'),
    ('Insumos Médicos Guatemala, S.A.', '3456789-0', '22223456', 'info@insumosmedicosgt.com', '18 calle 24-56 zona 12, Ciudad de Guatemala');

-- Relación PROVEEDOR-PRODUCTO ("Suministra") — a qué precio suministra cada proveedor cada producto
-- (id_producto referenciado por posición de inserción arriba: 1=MF GLUCOSA, 2=MF COLESTEROL,
-- 6=GUANTE NITRILO, 7=MASCARILLA, 8=JERINGA, 9=TUBO AL VACÍO, 4=TUBO DE ENSAYO)
INSERT INTO proveedor_producto (id_proveedor, id_producto, precio_compra) VALUES
    (1, 1, 85.50), (1, 2, 92.00), (2, 1, 88.00),
    (2, 6, 45.00), (2, 7, 30.00),
    (3, 8, 0.75), (3, 9, 3.20), (3, 4, 1.10);

-- Relación EXAMEN-PRODUCTO ("Requiere") — insumos necesarios por examen
INSERT INTO examen_producto (id_examen, id_producto, cantidad_requerida) VALUES
    (1, 1, 2.0),   -- Glucosa en ayunas requiere MF GLUCOSA
    (1, 8, 1.0),   -- y una jeringa
    (2, 2, 3.0),   -- Perfil lipídico requiere MF COLESTEROL
    (3, 3, 1.5),   -- HbA1c requiere su cassette
    (4, 9, 1.0);   -- Hematología requiere tubo EDTA

-- Lotes de ejemplo (id_producto, id_proveedor referenciados por posición de inserción arriba)
INSERT INTO lote (id_producto, id_proveedor, numero_lote, fecha_ingreso, fecha_vencimiento, cantidad_disponible) VALUES
    (1, 1, 'L-2026-001', '2026-07-01', '2027-07-01', 1000.00),
    (2, 2, 'L-2026-002', '2026-07-05', '2027-01-05', 800.00),
    (6, 2, 'L-2026-003', '2026-06-15', NULL, 50.00),  -- EPP no requiere vencimiento
    (8, 3, 'L-2026-004', '2026-07-10', '2028-07-10', 600.00);

-- Fin de 001_seed.sql
