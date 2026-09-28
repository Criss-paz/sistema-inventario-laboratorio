# Certificación de Calidad — Entrega 3

**Proyecto:** Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango
**Entrega:** Entrega 3 — Implementación avanzada, seguridad y pruebas
**Fecha de revisión:** 26/09/2026 (José Eduardo Escobar) y 28/09/2026 (Cristopher Alexis Castellanos Paz)

Revisión del 26/09/2026, contra el repositorio y la base de datos real: 806 productos, 50 proveedores, 50 exámenes, 1,188 lotes y 5,839 movimientos; 3 roles de base de datos, 4 triggers y 5 vistas instalados; ningún `.env`, Excel del laboratorio ni contraseña real versionado.

Revisión del 28/09/2026, sobre una instalación desde cero en un segundo equipo siguiendo `INSTALL.md`: los 11 scripts SQL corrieron sin errores, la base quedó con los mismos números (0 lotes incoherentes con el historial, inventario valorizado en Q524,714.36) y los 8 casos de prueba pasaron en el navegador y en `psql`.

Por medio de la presente, los integrantes del equipo hacemos constar que la documentación y el código de la **Entrega 3** fueron revisados antes de su presentación. Estado real de cada punto:

- [x] **Estructura de carpetas obligatoria** (consigna, sección 7): `README.md`, `.gitignore`, `.env.example`, `INSTALL.md`, `docs/` (entrega-1 a entrega-4, diagramas, certificaciones, bitacora-ia, casos-prueba), `sql/` (ddl, dml, views, triggers, procedures, security) y `web/`.
- [x] **Estándares de repositorio** (sección 6.1): README con integrantes, SGBD, instalación y enlaces (R2); commits descriptivos con prefijo `feat`, `fix`, `docs`, `test` (R3); commits de ambos integrantes (R4); tags `entrega-1` y `entrega-2` publicados y `entrega-3` al cierre (R5); sin credenciales y con `.env.example` (R6); `.gitignore` para entorno, temporales y datos del laboratorio (R7); repositorio público (R8).
- [x] **Datos (DML):** más de 50 registros por tabla principal, con el inventario real del laboratorio (806 productos, 50 proveedores, 50 exámenes, 1,188 lotes, 5,839 movimientos). Excepción justificada: `categoria`, `rol` y `usuario` son catálogos de configuración. Los errores del registro en papel se documentan en `docs/entrega-3/reporte-carga-datos.md`.
- [x] **Vistas:** existencia, inventario bajo, lotes por vencer, historial y valorización a costo promedio ponderado (`sql/views/`).
- [x] **Triggers:** existencia por lote, historial inmutable y vencimiento obligatorio (`sql/triggers/001_triggers.sql`).
- [x] **Procedimientos:** `sp_registrar_entrada` y `sp_registrar_salida` con FEFO (`sql/procedures/001_procedures.sql`).
- [x] **Seguridad:** 3 roles de base de datos con privilegios diferenciados (`sql/security/001_roles.sql`), aplicados por la app con `SET ROLE`.
- [x] **Aplicación web al 70%:** módulos principales y control de acceso por rol (`AVANCE_WEB.md`).
- [x] **Matriz de trazabilidad** actualizada (`docs/entrega-3/matriz-trazabilidad.md`).
- [x] **Estándares** SQL y web revisados (`docs/entrega-3/estandares-cumplimiento.md`): se cumplen los 8 SQL y los 6 de aplicación.
- [x] **Despliegue en internet (S5):** https://inventario-laboratorio-03s7.onrender.com, verificado con los 3 roles el 26/09/2026.
- [x] **Bitácora de IA** actualizada (`docs/entrega-3/Bitacora-IA.md`).
- [x] **Los 8 casos de prueba fueron ejecutados por el equipo** con capturas de evidencia: 8 de 8 pasaron el 28/09/2026 (`docs/casos-prueba/casos-prueba-entrega-3.md`, `docs/casos-prueba/evidencias-entrega-3/`).
- [x] **Participación visible de ambos integrantes** en los commits de esta entrega (R4): implementación por José Eduardo Escobar; instalación desde cero, ejecución de los casos de prueba, correcciones y cierre por Cristopher Alexis Castellanos Paz.
- [x] No hay credenciales en el repositorio: `.env` no se versiona y los datos crudos del laboratorio (Excel) están excluidos por `.gitignore`. Los proveedores que son personas individuales se publican anonimizados.

---

## Firmas
Se dio el visto bueno para la entrega de este proyecto; ambos integrantes revisamos el contenido listado arriba.

| Nombre completo | Carné | Firma |
|---|---|---|
| Cristopher Alexis Castellanos Paz | 2690245972 | |
| José Eduardo Escobar | 2690245346 | X (26/09/2026) |
