-- =============================================================================
-- Archivo:      003_seed_examenes.sql
-- Propósito:    Completar el catálogo de exámenes (50) y registrar qué insumos
--               del inventario real consume cada uno (examen_producto, RN-17).
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/Bitacora-IA.md para el registro de uso.
-- Descripción:  46 exámenes de un laboratorio clínico + los 4 de 001_seed.sql.
--               El inventario en papel no registra exámenes: la relación
--               examen-insumo se armó con reactivos y materiales reales del
--               catálogo (códigos del laboratorio). La cantidad requerida es
--               un consumo estimado por examen; en reactivos que rinden muchas
--               pruebas por empaque es una fracción (por ejemplo 0.01).
--               Las FK se resuelven por código, nunca por id.
-- Dependencias: 001_seed.sql, 002_carga_catalogo.sql
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 003_seed_examenes.sql
-- =============================================================================

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
    ('RPR (sífilis)', 'Tamizaje de sífilis', 'EX-INM-02'),
    ('Prueba de embarazo en orina', 'hCG cualitativa', 'EX-INM-03'),
    ('Prueba de embarazo en sangre', 'hCG en suero', 'EX-INM-04'),
    ('Dengue NS1', 'Antígeno NS1 e IgG/IgM', 'EX-INM-05'),
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
    ('Antígeno prostático libre (PSA libre)', 'Tamizaje prostático', 'EX-HOR-02');

-- -----------------------------------------------------------------------------
-- EXAMEN-PRODUCTO ("Requiere", RN-17), con códigos reales del laboratorio:
--   TCG4ML tubo con gel · TV4MLEPET tubo EDTA · TV3MLCSPET tubo citrato
--   PORTOBJ3X1F portaobjetos · CO100U cubreobjetos · NIP022 frasco de orina
--   Códigos numéricos de 7 dígitos: cartuchos de química seca (VITROS)
--   105-00xxxx-00: reactivos del analizador hematológico (M-52)
-- -----------------------------------------------------------------------------
INSERT INTO examen_producto (id_examen, id_producto, cantidad_requerida)
SELECT e.id_examen, p.id_producto, v.cantidad
  FROM (VALUES
    ('EX-GLU-01', '1707801', 1.0), ('EX-GLU-01', 'TCG4ML', 1.0),
    ('EX-LIP-01', '1669829', 1.0), ('EX-LIP-01', '1336544', 1.0), ('EX-LIP-01', '6801895', 1.0), ('EX-LIP-01', 'TCG4ML', 1.0),
    ('EX-HBA-01', 'HCFW', 1.0), ('EX-HBA-01', 'TV4MLEPET', 1.0),
    ('EX-HEM-01', 'TV4MLEPET', 1.0), ('EX-HEM-01', '105-004045-00', 0.01), ('EX-HEM-01', '105-003724-00', 0.01),
    ('EX-CRE-01', '6802584', 1.0), ('EX-CRE-01', 'TCG4ML', 1.0),
    ('EX-BUN-01', '8102204', 1.0), ('EX-BUN-01', 'TCG4ML', 1.0),
    ('EX-URI-01', '1943927', 1.0), ('EX-URI-01', 'TCG4ML', 1.0),
    ('EX-TRI-01', '1336544', 1.0), ('EX-TRI-01', 'TCG4ML', 1.0),
    ('EX-HDL-01', '6801895', 1.0), ('EX-HDL-01', 'TCG4ML', 1.0),
    ('EX-AST-01', '8433815', 1.0), ('EX-ALT-01', '6844288', 1.0),
    ('EX-BIL-01', '8159931', 1.0),
    ('EX-PHE-01', '8433815', 1.0), ('EX-PHE-01', '6844288', 1.0), ('EX-PHE-01', '8159931', 1.0), ('EX-PHE-01', 'TCG4ML', 1.0),
    ('EX-PRE-01', '6802584', 1.0), ('EX-PRE-01', '8102204', 1.0), ('EX-PRE-01', '1943927', 1.0), ('EX-PRE-01', 'TCG4ML', 1.0),
    ('EX-GLU-02', '1707801', 1.0), ('EX-GLU-02', 'TCG4ML', 1.0),
    ('EX-GLU-03', '1707801', 2.0), ('EX-GLU-03', 'GLPCT75GRD2MLA', 1.0), ('EX-GLU-03', 'TCG4ML', 2.0),
    ('EX-ORI-01', '231010101001', 1.0), ('EX-ORI-01', 'NIP022', 1.0), ('EX-ORI-01', 'PORTOBJ3X1F', 1.0), ('EX-ORI-01', 'CO100U', 1.0),
    ('EX-HEC-01', 'FHCP', 1.0), ('EX-HEC-01', 'PORTOBJ3X1F', 1.0), ('EX-HEC-01', 'CO100U', 1.0), ('EX-HEC-01', 'SLFPM1ML', 0.01),
    ('EX-HEC-02', 'FOBSOHCTK', 1.0), ('EX-HEC-02', 'FHCP', 1.0),
    ('EX-MIC-01', 'C5401', 0.05), ('EX-MIC-01', 'C6131', 0.05), ('EX-MIC-01', 'BRO120MLE', 1.0),
    ('EX-MIC-02', 'C6841', 0.05), ('EX-MIC-02', 'C7321', 0.05), ('EX-MIC-02', '111C', 1.0),
    ('EX-MIC-03', 'C5221', 0.05), ('EX-MIC-03', 'C6421', 0.05), ('EX-MIC-03', '108C', 1.0),
    ('EX-MIC-04', 'GCVS1ML', 0.01), ('EX-MIC-04', 'GSL1ML', 0.01), ('EX-MIC-04', 'GSD1ML', 0.01), ('EX-MIC-04', 'GSSC1ML', 0.01), ('EX-MIC-04', 'PORTOBJ3X1F', 1.0),
    ('EX-INM-01', '7D2343', 1.0), ('EX-INM-01', 'TCG4ML', 1.0),
    ('EX-INM-02', 'RPRK1P', 0.01), ('EX-INM-02', 'TCG4ML', 1.0),
    ('EX-INM-03', 'HCGCI', 1.0), ('EX-INM-03', 'NIP022', 1.0),
    ('EX-INM-04', 'HCGSCCTK', 1.0), ('EX-INM-04', 'TCG4ML', 1.0),
    ('EX-INM-05', '971025', 1.0), ('EX-INM-05', 'TCG4ML', 1.0),
    ('EX-INM-06', 'KPCRLCC1P', 0.01), ('EX-INM-07', 'KFRCC1P', 0.01), ('EX-INM-08', 'ALCCK', 0.01),
    ('EX-HEM-02', 'AAF1ML', 0.01), ('EX-HEM-02', 'ABF1ML', 0.01), ('EX-HEM-02', 'ADIGGIGM', 0.01), ('EX-HEM-02', 'TV4MLEPET', 1.0),
    ('EX-COA-01', 'TSTP1S', 0.1), ('EX-COA-01', 'TV3MLCSPET', 1.0),
    ('EX-COA-02', 'AFSLTPT1MS', 0.1), ('EX-COA-02', 'CC1MLS', 0.1), ('EX-COA-02', 'TV3MLCSPET', 1.0),
    ('EX-COA-03', 'MU1MLS', 0.1), ('EX-COA-03', 'TV3MLCSPET', 1.0),
    ('EX-HEM-03', 'TV4MLEPET', 1.0),
    ('EX-HEM-04', 'PORTOBJ3X1F', 1.0), ('EX-HEM-04', 'CDW1ML', 0.01), ('EX-HEM-04', 'TV4MLEPET', 1.0),
    ('EX-HEM-05', 'TV4MLEPET', 1.0), ('EX-HEM-05', '105-004045-00', 0.01),
    ('EX-HEM-06', 'TV4MLEPET', 1.0), ('EX-HEM-06', '105-004045-00', 0.01), ('EX-HEM-06', '105-004307-00', 0.01),
    ('EX-HEM-07', 'ADCT', 0.01), ('EX-HEM-07', 'PORTOBJ3X1F', 1.0), ('EX-HEM-07', 'TV4MLEPET', 1.0),
    ('EX-QUI-01', '8392292', 1.0), ('EX-QUI-01', 'TCG4ML', 1.0),
    ('EX-QUI-02', '1988211', 1.0), ('EX-QUI-02', 'TCG4ML', 1.0),
    ('EX-QUI-03', '1053180', 1.0), ('EX-QUI-04', '8112724', 1.0), ('EX-QUI-05', '8297749', 1.0),
    ('EX-QUI-06', '1450261', 1.0),
    ('EX-QUI-07', '8379034', 1.0), ('EX-QUI-07', '8157596', 1.0), ('EX-QUI-07', 'PNAKCLEP', 0.01),
    ('EX-QUI-08', '1515808', 1.0), ('EX-QUI-08', 'TCG4ML', 1.0),
    ('EX-HOR-01', 'STAIAPTSH', 1.0), ('EX-HOR-01', 'TCG4ML', 1.0),
    ('EX-HOR-02', 'STAIAPFPSA', 1.0), ('EX-HOR-02', 'TCG4ML', 1.0)
  ) AS v(codigo_examen, codigo_producto, cantidad)
  JOIN examen_laboratorio e ON e.codigo_interno = v.codigo_examen
  JOIN producto           p ON p.codigo         = v.codigo_producto;

-- Fin de 003_seed_examenes.sql
