# Bitácora de Utilización de IA — Entrega 3

## Proyecto
Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango

## Entrega
Entrega 3 — Implementación avanzada, seguridad y pruebas

## Propósito
Continúa el registro de `docs/entrega-2/Bitacora-IA.md`. La IA se utiliza como apoyo de implementación y documentación; toda propuesta es revisada y validada por el equipo antes de incorporarse.

---

### Registro de Bitácora IA

| Campo | Detalle |
|---|---|
| **Fecha** | 26/09/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Implementar la lógica de negocio en la base de datos: triggers de existencia, inmutabilidad del historial y vencimiento; procedimientos de entrada y salida con FEFO; vistas de consulta. |
| **Prompt utilizado** | "Iniciemos con la fase 3", con la consigna de la Entrega 3 (PDF) como contexto. |
| **Resultado obtenido** | `sql/triggers/001_triggers.sql` (existencia por lote con bloqueo `FOR UPDATE`, historial inmutable RN-09, vencimiento obligatorio RN-07), `sql/procedures/001_procedures.sql` (`sp_registrar_entrada`, `sp_registrar_salida` con FEFO y exclusión de lotes vencidos) y `sql/views/001_views.sql` (existencia, inventario bajo, lotes por vencer, historial). Todos los errores de negocio usan `RAISE EXCEPTION` sin código propio (SQLSTATE P0001) para que la web muestre solo esos mensajes. |
| **Validación del grupo** | Cada objeto se probó dentro de `BEGIN … ROLLBACK` contra la base real: 9 casos de triggers, 10 de procedimientos y revisión de las 4 vistas. |
| **Estándares aplicados** | S7 (datos derivados calculados, no almacenados), RN-01, RN-04, RN-07, RN-09, RF-24, RF-26 a RF-30. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA

| Campo | Detalle |
|---|---|
| **Fecha** | 26/09/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Crear los 3 roles de base de datos con privilegios diferenciados (consigna, sección 5, requisito 6). |
| **Prompt utilizado** | Continuación de la fase 3 ("continúa"). |
| **Resultado obtenido** | `sql/security/001_roles.sql`: `rol_consulta ⊂ rol_encargado ⊂ rol_administrador`, procedimientos `SECURITY DEFINER` con `search_path` fijo, `GRANT` por columna para que ningún rol lea `password_hash` ni edite `cantidad_disponible`. |
| **Validación del grupo** | El equipo ejecutó el script como `postgres`. Se probaron 16 casos de permiso (permitidos y denegados) con `SET ROLE`. |
| **Estándares aplicados** | Menor privilegio, defensa en profundidad, RN-15. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA

| Campo | Detalle |
|---|---|
| **Fecha** | 26/09/2026 |
| **Herramienta** | Claude (conversión) y Claude Code (Opus) (carga) |
| **Objetivo** | Poblar la base con datos reales en lugar de datos de prueba generados. El laboratorio lleva el inventario en papel; para la entrega de inventario trimestral el equipo transcribió los registros a Excel. |
| **Prompt utilizado** | Conversión: el equipo pidió a Claude pasar el Excel a un archivo de texto. Carga: "y si te paso unos registros que se obtuvieron para la entrega de inventario trimestral… se puede trabajar con esto?" |
| **Resultado obtenido** | La IA recomendó trabajar con el Excel original y no con la conversión a texto, porque una conversión hecha por IA puede alterar valores sin avisar. Escribió `sql/dml/generar_carga.py`, que lee el Excel, aplica las reglas de la base (CHECK, triggers, FEFO) y genera `002_carga_catalogo.sql`, `004_carga_movimientos.sql` y `docs/entrega-3/reporte-carga-datos.md`. Resultado: 806 productos, 1,188 lotes y 5,839 movimientos reales. La carga detectó errores del papel: 65 salidas anotadas antes que su entrada, una salida que dejaba existencia negativa, una entrada recibida ya vencida y un producto anotado en dos unidades distintas. Durante la prueba, el trigger de existencia detectó un error del propio generador (horas que desordenaban salidas y entradas); se corrigió. |
| **Validación del grupo** | Decisiones tomadas por el equipo: mover las salidas anotadas antes que su entrada a la fecha de esa entrada, anonimizar a los proveedores que son personas y completar 50 proveedores con 24 de prueba inactivos. Verificado en una instalación aislada: 0 lotes con existencia distinta a entradas − salidas, y los 278 productos con existencia coinciden con el Excel. **Pendiente:** revisar la clasificación por categoría y los hallazgos del reporte con el personal del laboratorio. |
| **Estándares aplicados** | Consigna sección 5, requisito 7 (50 registros por tabla principal), R6 (sin datos sensibles en el repositorio: el Excel queda fuera por `.gitignore`), RN-01, RN-07. |
| **Responsable** | José Eduardo Escobar |

---

## Declaración
La IA se utilizó como apoyo de implementación y documentación, no como sustituto de las decisiones del equipo. Las decisiones sobre los datos reales (qué corregir, qué rechazar, qué anonimizar) las tomó el equipo con la justificación presentada por la IA.
