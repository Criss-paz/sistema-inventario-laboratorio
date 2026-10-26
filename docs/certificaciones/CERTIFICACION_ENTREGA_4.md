# Certificación de Calidad — Entrega 4

**Proyecto:** Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango
**Entrega:** Entrega 4 — Integración, documentación y defensa oral
**Estado:** firmada por José Eduardo Escobar (26/10/2026); pendiente la firma de Cristopher Alexis Castellanos Paz

Revisión preparada del 20 al 26/10/2026 contra el repositorio, la base de datos con el inventario real al 21/10/2026 (814 productos, 1,296 lotes, 6,560 movimientos numerados de E000001 a E001790) y una instalación desde cero en un esquema vacío (33 de 33 pasos de `INSTALL.md` sin errores, 0 lotes incoherentes, inventario valorizado en Q600,338.34).

Por medio de la presente, los integrantes del equipo hacemos constar que la documentación y el código de la **Entrega 4** fueron revisados antes de su presentación. Puntos de la consigna (sección 8):

- [x] **Cumplimos la estructura de carpetas obligatoria** (sección 7): `README.md`, `.gitignore`, `.env.example`, `INSTALL.md`, `docs/` (entrega-1 a entrega-4, diagramas, certificaciones, bitacora-ia, casos-prueba), `sql/` (ddl, dml, views, triggers, procedures, security) y `web/`.
- [x] **Cumplimos los estándares SQL** (sección 6.2): 8 de 8. 33 de 33 scripts con encabezado, 17 de 17 FK con `ON DELETE` y `ON UPDATE`, migraciones aditivas probadas antes del commit. Detalle en `docs/entrega-4/ENTREGA4_ESTANDARES_CUMPLIMIENTO.md`.
- [ ] **Cumplimos los estándares de repositorio** (sección 6.1): R1, R2, R3, R6, R7 y R8 se cumplen. **R4** queda pendiente: commits propios de Cristopher Alexis Castellanos Paz en esta entrega. **R5:** el tag `entrega-4` se crea después de firmar.
- [x] **Cumplimos los estándares de aplicación** (sección 6.3): 6 de 6. Separación de capas, errores sin SQL crudo, validación en el servidor, consultas parametrizadas, código legible y documentado.
- [x] **La bitácora de IA está actualizada**, con 12 registros de esta entrega y la consolidada de todo el proyecto (`docs/bitacora-ia/ENTREGA4_BITACORA_IA.md`).
- [x] **Los casos de prueba fueron ejecutados y documentados:** 19 de 19 aprobados (20 al 26/10/2026), con capturas (`docs/casos-prueba/casos-prueba-entrega-4.md`). Cubren los flujos U-01 a U-15 del manual de usuario, la corrección de entradas, la carga de los movimientos del 24/09 al 21/10, el número de documento, los roles con permisos editables, la bitácora, la restauración de un respaldo y la instalación desde cero. La regresión de la aplicación sumó 239 verificaciones sin fallas.
- [x] **No hay credenciales expuestas en el repositorio:** búsqueda con `git grep` de cadenas de conexión, contraseñas y claves de Neon sin resultados reales. Los respaldos descargados están excluidos por `.gitignore`.

Productos de la Entrega 4 (consigna, sección 11):

- [x] **Sistema web 100% completo**: 12 módulos, incluidos el respaldo de la base, el cambio de contraseña propio, la corrección de entradas con registro, el número de documento E/S/D, los permisos editables por rol y la bitácora de auditoría (`AVANCE_WEB.md`).
- [x] **Inventario al día** con los movimientos de SIGAL del 24/09 al 21/10/2026, verificado contra SIGAL (`docs/entrega-4/ENTREGA4_REPORTE_CARGA_SIGAL.md`).
- [x] **CRUD en todas las tablas principales**, con la justificación de las operaciones que no se ofrecen a propósito (movimientos inmutables, lotes que nacen con la entrada): `docs/entrega-4/ENTREGA4_MATRIZ_TRAZABILIDAD.md`.
- [x] **Manuales técnico y de usuario** (`docs/entrega-4/ENTREGA4_MANUAL_TECNICO.md`, `ENTREGA4_MANUAL_USUARIO.md`).
- [ ] **Informe final y declaración de integridad**: redactados (`ENTREGA4_INFORME_FINAL.md`, `ENTREGA4_DECLARACION_INTEGRIDAD.md`); falta que la declaración lleve las firmas.
- [x] **Diagramas ER y relacional actualizados** con la devolución, la baja de exámenes, la corrección de entradas, el número de documento, los permisos por rol y la bitácora (15 tablas), en editable, PNG y PDF.
- [x] **Versión publicada al día** (21/10/2026): Neon tiene todas las migraciones, la corrección de entradas y la carga de SIGAL (721 movimientos; 814 productos, 6,562 movimientos e inventario valorizado en Q600,338.34, igual que la instalación desde cero). Antes de cargar se anuló con una devolución la salida de prueba #5840, que había dejado un lote en 0. Render publica la última versión. El 26/10/2026 se aplicaron en Neon el número de documento, los permisos y la bitácora (0 movimientos sin número, 14 permisos asignados) y se redesplegó Render.

---

## Antes de firmar

1. Cristopher: revisar los manuales y repetir en la versión publicada, con su usuario, los flujos U-03 a U-07 del manual de usuario, y registrar el resultado con un commit propio (R4).
2. Ambos: marcar los puntos pendientes de arriba, firmar esta certificación y la declaración de integridad, y crear el tag:
   ```bash
   git tag -a entrega-4 -m "Entrega 4 — Integración, documentación y defensa oral"
   git push origin entrega-4
   ```
   Fecha límite: **03/11/2026** (−0.25 pts por día de retraso).

---

## Firmas

| Nombre completo | Carné | Firma |
|---|---|---|
| Cristopher Alexis Castellanos Paz | 2690245972 | |
| José Eduardo Escobar | 2690245346 | José Eduardo Escobar — firmado el 26/10/2026 |
