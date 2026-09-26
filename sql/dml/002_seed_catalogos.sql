-- =============================================================================
-- Archivo:      002_seed_catalogos.sql
-- Propósito:    Ampliar los catálogos hasta el mínimo de 50 registros por
--               tabla principal (consigna, sección 5, requisito 7).
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/Bitacora-IA.md para el registro de uso.
-- Descripción:  Resultado tras 001 + 002:
--                 producto            57  (12 de 001 + 45 insumos reales de laboratorio clínico)
--                 examen_laboratorio  50  (4 de 001 + 46 exámenes reales)
--                 proveedor           50  (3 de 001 + 47 generados con patrón)
--                 categoria            9  (6 de 001 + 3)
--                 proveedor_producto 108, examen_producto 67
--               Por qué categoria, rol y usuario NO llegan a 50: son catálogos
--               de configuración, no de operación. Un laboratorio real tiene
--               3 roles y una decena de categorías; 50 serían relleno que no
--               prueba nada (criterio del equipo desde la Entrega 2). Las
--               tablas con volumen operativo (producto, proveedor, examen,
--               lote, movimiento, detalle) sí superan los 50.
--               Proveedores generados: un laboratorio privado no trabaja con
--               50 proveedores reales, así que los 47 adicionales se arman
--               combinando nombres y ciudades de Guatemala de forma
--               determinista (mismo resultado en cada instalación).
--               Las FK se resuelven por nombre/código (subconsultas), nunca
--               por id numérico, para no depender del orden de inserción.
-- Dependencias: 001_schema.sql, 001_triggers.sql, 001_seed.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 002_seed_catalogos.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Categorías nuevas (áreas que el catálogo real ya necesitaba).
-- -----------------------------------------------------------------------------
INSERT INTO categoria (nombre, descripcion) VALUES
    ('MICROBIOLOGIA', 'Medios de cultivo, tinciones e hisopos'),
    ('LIMPIEZA Y DESINFECCION', 'Desinfectantes y antisépticos de uso en el laboratorio'),
    ('PAPELERIA Y ETIQUETADO', 'Etiquetas de código de barras y papel para equipos');

-- -----------------------------------------------------------------------------
-- Productos: 45 insumos reales de un laboratorio clínico.
-- Columnas: categoría (por nombre), código, nombre, descripción, unidad,
-- stock mínimo, requiere vencimiento (RN-07: reactivos, medios y controles sí;
-- material, EPP y papelería no, igual que el criterio del catálogo de 001).
-- -----------------------------------------------------------------------------
INSERT INTO producto (id_categoria, codigo, nombre, descripcion, unidad_medida, stock_minimo, requiere_vencimiento)
SELECT c.id_categoria, v.codigo, v.nombre, v.descripcion, v.unidad, v.minimo, v.vence
  FROM (VALUES
    ('REACTIVOS', '1669837', 'MF TRIGLICERIDOS - TRIG',                  'Reactivo para triglicéridos séricos',               'Cartucho', 3,  TRUE),
    ('REACTIVOS', '1669845', 'MF CREATININA - CREA',                     'Reactivo para creatinina sérica',                   'Cartucho', 3,  TRUE),
    ('REACTIVOS', '1669853', 'MF UREA - BUN',                            'Reactivo para nitrógeno de urea',                   'Cartucho', 3,  TRUE),
    ('REACTIVOS', '1669861', 'MF ACIDO URICO - UA',                      'Reactivo para ácido úrico',                         'Cartucho', 2,  TRUE),
    ('REACTIVOS', '1669879', 'MF TGO / AST',                             'Reactivo para aspartato aminotransferasa',          'Cartucho', 2,  TRUE),
    ('REACTIVOS', '1669887', 'MF TGP / ALT',                             'Reactivo para alanina aminotransferasa',            'Cartucho', 2,  TRUE),
    ('REACTIVOS', '1669895', 'MF HDL COLESTEROL - HDL',                  'Reactivo para colesterol HDL',                      'Cartucho', 2,  TRUE),
    ('REACTIVOS', '1669903', 'MF BILIRRUBINA TOTAL - TBIL',              'Reactivo para bilirrubina total',                   'Cartucho', 2,  TRUE),
    ('REACTIVOS', 'DIL-HEM20', 'DILUYENTE HEMATOLOGIA 20 L',             'Diluyente isotónico para analizador hematológico',  'Galón',    2,  TRUE),
    ('REACTIVOS', 'LIS-HEM05', 'LISANTE HEMATOLOGIA 500 ML',             'Lisante para conteo diferencial',                   'Frasco',   3,  TRUE),
    ('REACTIVOS', 'PR-VIH12',  'PRUEBA RAPIDA VIH 1/2',                  'Caja de 25 pruebas inmunocromatográficas',          'Caja',     4,  TRUE),
    ('REACTIVOS', 'PR-HCG',    'PRUEBA RAPIDA HCG EMBARAZO',             'Caja de 50 cassettes para orina/suero',             'Caja',     4,  TRUE),
    ('REACTIVOS', 'PR-DNS1',   'PRUEBA RAPIDA DENGUE NS1',               'Caja de 25 pruebas',                                'Caja',     3,  TRUE),
    ('REACTIVOS', 'HEM-ANTIA', 'SUERO HEMOCLASIFICADOR ANTI-A 10 ML',    'Tipificación ABO',                                  'Frasco',   3,  TRUE),
    ('REACTIVOS', 'HEM-ANTIB', 'SUERO HEMOCLASIFICADOR ANTI-B 10 ML',    'Tipificación ABO',                                  'Frasco',   3,  TRUE),
    ('REACTIVOS', 'HEM-ANTID', 'SUERO HEMOCLASIFICADOR ANTI-D 10 ML',    'Tipificación Rh',                                   'Frasco',   3,  TRUE),
    ('REACTIVOS', 'TIR-OR10',  'TIRAS REACTIVAS ORINA 10 PARAMETROS',    'Frasco de 100 tiras',                               'Frasco',   5,  TRUE),
    ('REACTIVOS', 'VDRL-01',   'REACTIVO VDRL',                          'Antígeno para sífilis, 5 ml',                       'Frasco',   2,  TRUE),
    ('REACTIVOS', 'LTX-PCR',   'PCR LATEX',                              'Proteína C reactiva, 100 determinaciones',          'Frasco',   2,  TRUE),
    ('REACTIVOS', 'LTX-FR',    'FACTOR REUMATOIDEO LATEX',               '100 determinaciones',                               'Frasco',   2,  TRUE),
    ('REACTIVOS', 'LTX-ASO',   'ASO LATEX',                              'Antiestreptolisina O, 100 determinaciones',         'Frasco',   2,  TRUE),
    ('REACTIVOS', 'TP-PT',     'TIEMPO DE PROTROMBINA - TROMBOPLASTINA', 'Reactivo de coagulación, 10 x 4 ml',                'Kit',      2,  TRUE),
    ('MICROBIOLOGIA', 'AG-SANG', 'AGAR SANGRE BASE 500 G',               'Medio deshidratado',                                'Frasco',   1,  TRUE),
    ('MICROBIOLOGIA', 'AG-MAC',  'AGAR MACCONKEY 500 G',                 'Medio selectivo para gramnegativos',                'Frasco',   1,  TRUE),
    ('MICROBIOLOGIA', 'AG-MH',   'AGAR MUELLER HINTON 500 G',            'Medio para antibiograma',                           'Frasco',   1,  TRUE),
    ('MICROBIOLOGIA', 'TIN-GRAM','SET TINCION DE GRAM 4 X 250 ML',       'Cristal violeta, lugol, alcohol-acetona, safranina','Kit',      2,  TRUE),
    ('MICROBIOLOGIA', 'HIS-STU', 'HISOPO ESTERIL CON MEDIO STUART',      'Transporte de muestras microbiológicas',            'Caja',     3,  TRUE),
    ('MATERIAL PARA EL LABORATORIO', 'PIP-PAS3', 'PIPETA PASTEUR 3 ML',             'Caja de 500 unidades',             'Caja',     2,  FALSE),
    ('MATERIAL PARA EL LABORATORIO', 'PUN-200',  'PUNTAS AMARILLAS 200 UL',         'Bolsa de 1000 unidades',           'Bolsa',    3,  FALSE),
    ('MATERIAL PARA EL LABORATORIO', 'PUN-1000', 'PUNTAS AZULES 1000 UL',           'Bolsa de 1000 unidades',           'Bolsa',    3,  FALSE),
    ('MATERIAL PARA EL LABORATORIO', 'POR-2575', 'PORTAOBJETOS 25 X 75 MM',         'Caja de 72 unidades',              'Caja',     5,  FALSE),
    ('MATERIAL PARA EL LABORATORIO', 'CUB-2222', 'CUBREOBJETOS 22 X 22 MM',         'Caja de 100 unidades',             'Caja',     5,  FALSE),
    ('MATERIAL PARA EL LABORATORIO', 'GRA-50',   'TUBO CONICO 50 ML CON TAPON',     'Paquete de 25 unidades',           'Paquete',  4,  FALSE),
    ('EQUIPO DE PROTECCION PERSONAL', 'BAT-DES', 'BATA DESECHABLE MANGA LARGA',     'Talla única',                      'unidad',   50, FALSE),
    ('EQUIPO DE PROTECCION PERSONAL', 'GOR-DES', 'GORRO DESECHABLE',                'Paquete de 100 unidades',          'Paquete',  3,  FALSE),
    ('EQUIPO DE PROTECCION PERSONAL', 'GNCTS-A', 'GUANTE NITRILO CELESTE TALLA S - AROSA', 'Caja de 100 unidades',      'Caja',     10, FALSE),
    ('EQUIPO DE PROTECCION PERSONAL', 'LEN-PRO', 'LENTES DE PROTECCION',            'Policarbonato, antiempañante',     'unidad',   5,  FALSE),
    ('INSUMOS DE TOMA DE MUESTRA', 'TV5RSA',    'TUBO AL VACIO 5 ML TAPA ROJA',     'Sin aditivo, para suero',          'unidad',   200, FALSE),
    ('INSUMOS DE TOMA DE MUESTRA', 'TV27CIT',   'TUBO AL VACIO 2.7 ML CITRATO',     'Tapa celeste, para coagulación',   'unidad',   100, FALSE),
    ('INSUMOS DE TOMA DE MUESTRA', 'AGV-21G',   'AGUJA PARA TUBO AL VACIO 21G',     'Caja de 100 unidades',             'Caja',     5,  FALSE),
    ('INSUMOS DE TOMA DE MUESTRA', 'FRA-OR60',  'FRASCO RECOLECTOR DE ORINA 60 ML', 'Estéril, con tapa de rosca',       'unidad',   150, FALSE),
    ('INSUMOS DE TOMA DE MUESTRA', 'TOR-ALG',   'TORUNDAS DE ALGODON',              'Bolsa de 500 unidades',            'Bolsa',    5,  FALSE),
    ('LIMPIEZA Y DESINFECCION', 'ALC-ISO70',   'ALCOHOL ISOPROPILICO 70 %',        'Galón',                            'Galón',    2,  TRUE),
    ('LIMPIEZA Y DESINFECCION', 'HIP-SOD5',    'HIPOCLORITO DE SODIO 5 %',         'Galón',                            'Galón',    2,  TRUE),
    ('CALIBRADORES', 'CTL-QCN',                'CONTROL QUIMICA CLINICA NIVEL NORMAL',     'Suero control liofilizado, 5 ml', 'Frasco', 2, TRUE)
  ) AS v(categoria, codigo, nombre, descripcion, unidad, minimo, vence)
  JOIN categoria c ON c.nombre = v.categoria;

-- -----------------------------------------------------------------------------
-- Exámenes de laboratorio: 46 exámenes reales de un laboratorio clínico.
-- -----------------------------------------------------------------------------
INSERT INTO examen_laboratorio (nombre_examen, descripcion, codigo_interno) VALUES
    ('Creatinina', 'Función renal', 'EX-CRE-01'),
    ('Nitrógeno de urea (BUN)', 'Función renal', 'EX-BUN-01'),
    ('Ácido úrico', 'Metabolismo de purinas', 'EX-URI-01'),
    ('Triglicéridos', 'Lípidos séricos', 'EX-TRI-01'),
    ('Colesterol HDL', 'Lípidos séricos', 'EX-HDL-01'),
    ('TGO / AST', 'Función hepática', 'EX-AST-01'),
    ('TGP / ALT', 'Función hepática', 'EX-ALT-01'),
    ('Bilirrubina total', 'Función hepática', 'EX-BIL-01'),
    ('Perfil hepático', 'TGO, TGP y bilirrubinas', 'EX-PHE-01'),
    ('Perfil renal', 'Creatinina, BUN y ácido úrico', 'EX-PRE-01'),
    ('Glucosa postprandial', 'Glucosa 2 horas después de comer', 'EX-GLU-02'),
    ('Curva de tolerancia a la glucosa', 'Glucosa basal y a las 2 horas', 'EX-GLU-03'),
    ('Examen general de orina', 'Físico, químico y microscópico', 'EX-ORI-01'),
    ('Examen general de heces', 'Coproparasitológico', 'EX-HEC-01'),
    ('Sangre oculta en heces', 'Prueba inmunológica', 'EX-HEC-02'),
    ('Urocultivo', 'Cultivo de orina con antibiograma', 'EX-MIC-01'),
    ('Coprocultivo', 'Cultivo de heces', 'EX-MIC-02'),
    ('Cultivo de secreción', 'Cultivo de secreción con antibiograma', 'EX-MIC-03'),
    ('Tinción de Gram', 'Frote teñido', 'EX-MIC-04'),
    ('Prueba de VIH', 'Prueba rápida de tamizaje', 'EX-INM-01'),
    ('VDRL', 'Tamizaje de sífilis', 'EX-INM-02'),
    ('Prueba de embarazo en orina', 'hCG cualitativa', 'EX-INM-03'),
    ('Prueba de embarazo en sangre', 'hCG en suero', 'EX-INM-04'),
    ('Dengue NS1', 'Antígeno NS1', 'EX-INM-05'),
    ('Proteína C reactiva', 'PCR por látex', 'EX-INM-06'),
    ('Factor reumatoideo', 'FR por látex', 'EX-INM-07'),
    ('Antiestreptolisina O', 'ASO por látex', 'EX-INM-08'),
    ('Grupo sanguíneo y factor Rh', 'Tipificación ABO y Rh', 'EX-HEM-02'),
    ('Tiempo de protrombina', 'TP e INR', 'EX-COA-01'),
    ('Tiempo parcial de tromboplastina', 'TPT', 'EX-COA-02'),
    ('Fibrinógeno', 'Coagulación', 'EX-COA-03'),
    ('Velocidad de sedimentación', 'VSG', 'EX-HEM-03'),
    ('Frote periférico', 'Morfología celular', 'EX-HEM-04'),
    ('Recuento de plaquetas', 'Conteo plaquetario', 'EX-HEM-05'),
    ('Hemoglobina y hematocrito', 'Hb y Ht', 'EX-HEM-06'),
    ('Reticulocitos', 'Conteo de reticulocitos', 'EX-HEM-07'),
    ('Proteínas totales', 'Proteínas séricas', 'EX-QUI-01'),
    ('Albúmina', 'Proteína sérica', 'EX-QUI-02'),
    ('Fosfatasa alcalina', 'Función hepática y ósea', 'EX-QUI-03'),
    ('Amilasa', 'Función pancreática', 'EX-QUI-04'),
    ('Lipasa', 'Función pancreática', 'EX-QUI-05'),
    ('Calcio sérico', 'Electrolito', 'EX-QUI-06'),
    ('Electrolitos (Na, K, Cl)', 'Sodio, potasio y cloro', 'EX-QUI-07'),
    ('Hierro sérico', 'Metabolismo del hierro', 'EX-QUI-08'),
    ('TSH', 'Función tiroidea', 'EX-HOR-01'),
    ('Antígeno prostático (PSA)', 'Tamizaje prostático', 'EX-HOR-02');

-- -----------------------------------------------------------------------------
-- Proveedores: 47 adicionales, generados de forma determinista.
-- nombre  = tipo de empresa + rubro + región (sin repetir combinaciones)
-- nit     = número único derivado de i (formato ########-#)
-- -----------------------------------------------------------------------------
INSERT INTO proveedor (nombre, nit, telefono, correo, direccion)
SELECT format('%s %s %s, S.A.',
              (ARRAY['Distribuidora', 'Comercial', 'Importadora', 'Suministros', 'Droguería', 'Grupo'])[1 + i % 6],
              (ARRAY['Médica', 'Clínica', 'Diagnóstica', 'de Laboratorio', 'Hospitalaria', 'Biomédica', 'Científica', 'Analítica'])[1 + (i / 6) % 8],
              (ARRAY['del Altiplano', 'de Occidente', 'Xela', 'Centroamericana', 'Guatemalteca', 'del Pacífico', 'Maya'])[1 + i % 7]),
       format('%s-%s', 5000000 + i * 1373, i % 10),
       format('7%s', lpad((7760000 + i * 211)::TEXT, 7, '0')),
       format('ventas%s@proveedor%s.com.gt', i, i),
       format('%s calle %s-%s zona %s, %s',
              1 + i % 20, 1 + i % 15, 10 + i % 80, 1 + i % 12,
              (ARRAY['Quetzaltenango', 'Ciudad de Guatemala', 'San Marcos', 'Totonicapán', 'Retalhuleu', 'Huehuetenango', 'Mazatenango'])[1 + i % 7])
  FROM generate_series(1, 47) AS g(i);

-- -----------------------------------------------------------------------------
-- PROVEEDOR-PRODUCTO ("Suministra", RN-16): cada producto que aún no tiene
-- proveedor recibe 2, elegidos por posición; precio base según la unidad
-- (un galón o un kit cuesta más que una unidad suelta) y una variación de
-- hasta 15 % entre proveedores, como pasa en la realidad.
-- -----------------------------------------------------------------------------
INSERT INTO proveedor_producto (id_proveedor, id_producto, precio_compra)
SELECT pr.id_proveedor,
       p.id_producto,
       round(CASE p.unidad_medida
                 WHEN 'unidad'   THEN 2.50
                 WHEN 'Galón'    THEN 350.00
                 WHEN 'Kit'      THEN 420.00
                 WHEN 'Cartucho' THEN 90.00
                 WHEN 'Frasco'   THEN 180.00
                 ELSE 120.00
             END * (1 + ((p.rn + k) % 16) / 100.0), 2)
  FROM (SELECT id_producto, unidad_medida, row_number() OVER (ORDER BY id_producto) AS rn
          FROM producto
         WHERE id_producto NOT IN (SELECT id_producto FROM proveedor_producto)) p
 CROSS JOIN generate_series(0, 1) AS k
  JOIN (SELECT id_proveedor, row_number() OVER (ORDER BY id_proveedor) AS rn
          FROM proveedor) pr
    ON pr.rn = 1 + (p.rn * 3 + k * 17) % 50;

-- -----------------------------------------------------------------------------
-- EXAMEN-PRODUCTO ("Requiere", RN-17): insumos que consume cada examen.
-- Se resuelve por código de examen y código de producto.
-- -----------------------------------------------------------------------------
INSERT INTO examen_producto (id_examen, id_producto, cantidad_requerida)
SELECT e.id_examen, p.id_producto, v.cantidad
  FROM (VALUES
    ('EX-CRE-01', '1669845', 1.0), ('EX-CRE-01', 'TV5RSA', 1.0),
    ('EX-BUN-01', '1669853', 1.0), ('EX-BUN-01', 'TV5RSA', 1.0),
    ('EX-URI-01', '1669861', 1.0), ('EX-URI-01', 'TV5RSA', 1.0),
    ('EX-TRI-01', '1669837', 1.0), ('EX-TRI-01', 'TV5RSA', 1.0),
    ('EX-HDL-01', '1669895', 1.0), ('EX-HDL-01', 'TV5RSA', 1.0),
    ('EX-AST-01', '1669879', 1.0), ('EX-ALT-01', '1669887', 1.0),
    ('EX-BIL-01', '1669903', 1.0),
    ('EX-PHE-01', '1669879', 1.0), ('EX-PHE-01', '1669887', 1.0), ('EX-PHE-01', '1669903', 1.0), ('EX-PHE-01', 'TV5RSA', 1.0),
    ('EX-PRE-01', '1669845', 1.0), ('EX-PRE-01', '1669853', 1.0), ('EX-PRE-01', '1669861', 1.0), ('EX-PRE-01', 'TV5RSA', 1.0),
    ('EX-GLU-02', '1707801', 1.0), ('EX-GLU-03', '1707801', 2.0),
    ('EX-ORI-01', 'TIR-OR10', 1.0), ('EX-ORI-01', 'FRA-OR60', 1.0), ('EX-ORI-01', 'POR-2575', 1.0), ('EX-ORI-01', 'CUB-2222', 1.0),
    ('EX-HEC-01', 'POR-2575', 1.0), ('EX-HEC-01', 'CUB-2222', 1.0),
    ('EX-MIC-01', 'AG-SANG', 0.02), ('EX-MIC-01', 'AG-MAC', 0.02), ('EX-MIC-01', 'AG-MH', 0.02), ('EX-MIC-01', 'FRA-OR60', 1.0),
    ('EX-MIC-02', 'AG-MAC', 0.02), ('EX-MIC-02', 'HIS-STU', 1.0),
    ('EX-MIC-03', 'AG-SANG', 0.02), ('EX-MIC-03', 'HIS-STU', 1.0),
    ('EX-MIC-04', 'TIN-GRAM', 0.01), ('EX-MIC-04', 'POR-2575', 1.0),
    ('EX-INM-01', 'PR-VIH12', 1.0), ('EX-INM-02', 'VDRL-01', 0.05),
    ('EX-INM-03', 'PR-HCG', 1.0), ('EX-INM-03', 'FRA-OR60', 1.0),
    ('EX-INM-04', 'PR-HCG', 1.0), ('EX-INM-05', 'PR-DNS1', 1.0),
    ('EX-INM-06', 'LTX-PCR', 0.05), ('EX-INM-07', 'LTX-FR', 0.05), ('EX-INM-08', 'LTX-ASO', 0.05),
    ('EX-HEM-02', 'HEM-ANTIA', 0.05), ('EX-HEM-02', 'HEM-ANTIB', 0.05), ('EX-HEM-02', 'HEM-ANTID', 0.05),
    ('EX-COA-01', 'TP-PT', 0.1), ('EX-COA-01', 'TV27CIT', 1.0),
    ('EX-COA-02', 'TV27CIT', 1.0), ('EX-COA-03', 'TV27CIT', 1.0),
    ('EX-HEM-04', 'POR-2575', 1.0), ('EX-HEM-04', 'TV4MLEPET', 1.0),
    ('EX-HEM-05', 'DIL-HEM20', 0.01), ('EX-HEM-05', 'TV4MLEPET', 1.0),
    ('EX-HEM-06', 'DIL-HEM20', 0.01), ('EX-HEM-06', 'LIS-HEM05', 0.01), ('EX-HEM-06', 'TV4MLEPET', 1.0)
  ) AS v(codigo_examen, codigo_producto, cantidad)
  JOIN examen_laboratorio e ON e.codigo_interno = v.codigo_examen
  JOIN producto           p ON p.codigo         = v.codigo_producto;

-- Fin de 002_seed_catalogos.sql
