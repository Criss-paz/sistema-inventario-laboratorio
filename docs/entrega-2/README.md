# docs/entrega-2

Documentación de la Entrega 2 — Diseño lógico, diccionario e implementación base (semanas 4-5).

## Contenido
- [x] Auditoría de la Entrega 1
- [x] Decisión de SGBD: PostgreSQL
- [x] Decisión de stack web: Python + Flask
- [x] `modelo-relacional.md` — modelo relacional (11 tablas)
- [x] `../diagramas/DIAGRAMA-RELACIONAL.drawio` (+ PNG/PDF) — diagrama del modelo relacional, exigido por el estándar D3 junto al ER
- [x] `normalizacion-3fn.md` — normalización 3FN con ejemplo completo (DF), cadena 1FN → 2FN → 3FN
- [x] `ENTREGA2_NORMALIZACION_3FN.xlsx` — la misma normalización en hoja de cálculo, con el formato de los ejercicios de clase (tabla original → análisis de forma normal → tablas de cada paso)
- [x] `diccionario-datos.md` — diccionario completo + matriz de 38 restricciones
- [x] DDL ejecutable (`sql/ddl/001_schema.sql`)
- [x] Datos de prueba (`sql/dml/001_seed.sql` + `web/seed_usuarios.py`)
- [x] Aplicación web: login + layout + 2 CRUD (Categorías, Productos) en `web/`
- [x] `AVANCE_WEB.md` (raíz del repo)
- [x] `matriz-trazabilidad.md` — v1
- [x] `estandares-cumplimiento.md` — cumplimiento de las Secciones 6.2 (SQL) y 6.3 (aplicación) estándar por estándar, con evidencia
- [x] Casos de prueba ejecutados (`docs/casos-prueba/casos-prueba-entrega-2.md`) — 15 automatizados + 3 manuales en navegador
- [x] `CERTIFICACION_ENTREGA_2.md` — firmada por ambos integrantes
- [x] DDL/DML/app **ejecutados de verdad** contra PostgreSQL 18 + Python 3.14 (30/08/2026) — 15/15 casos de prueba pasaron
- [x] Auditoría de cierre contra la consigna (01/09/2026) — ver `Bitacora-IA.md`
- [x] Diagrama ER corregido (relación `Registra`: USUARIO → MOVIMIENTO) y re-exportado a PNG/PDF
- [x] Tag `entrega-2` creado y publicado

## Diferido a la Entrega 3 (con justificación)
- [ ] Ampliar `sql/dml/001_seed.sql` al mínimo de 50 registros por tabla principal (Sección 5.7 de la consigna). Hoy el seed carga el catálogo **real** del laboratorio (6 categorías, 12 productos, 3 proveedores, 4 lotes), suficiente para los 2 CRUD que pondera esta entrega; el volumen se completa junto con el DML de la Entrega 3.
- [ ] Vistas, triggers, procedimientos y los 3 roles de PostgreSQL (`sql/views/`, `sql/triggers/`, `sql/procedures/`, `sql/security/`).
- [ ] Control de acceso por rol dentro de la app (la rúbrica lo pondera en Entrega 3, no aquí).

**Estado:** cerrada. Contenido completo, verificado por ejecución real y auditado contra la consigna antes del tag.
