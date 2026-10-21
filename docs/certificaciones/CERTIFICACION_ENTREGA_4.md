# Certificación de Calidad — Entrega 4

**Proyecto:** Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango
**Entrega:** Entrega 4 — Integración, documentación y defensa oral
**Estado:** BORRADOR, pendiente de la revisión y la firma de ambos integrantes

Revisión preparada el 20/10/2026 contra el repositorio, la base de datos con el inventario real (806 productos, 1,188 lotes, 5,839 movimientos) y una instalación desde cero en un esquema vacío (16 de 16 pasos de `INSTALL.md` sin errores, mismos números que la Entrega 3, inventario valorizado en Q524,714.36).

Por medio de la presente, los integrantes del equipo hacemos constar que la documentación y el código de la **Entrega 4** fueron revisados antes de su presentación. Puntos de la consigna (sección 8):

- [x] **Cumplimos la estructura de carpetas obligatoria** (sección 7): `README.md`, `.gitignore`, `.env.example`, `INSTALL.md`, `docs/` (entrega-1 a entrega-4, diagramas, certificaciones, bitacora-ia, casos-prueba), `sql/` (ddl, dml, views, triggers, procedures, security) y `web/`.
- [x] **Cumplimos los estándares SQL** (sección 6.2): 8 de 8. 17 de 17 scripts con encabezado, 12 de 12 FK con `ON DELETE` y `ON UPDATE`, migraciones aditivas probadas antes del commit. Detalle en `docs/entrega-4/ENTREGA4_ESTANDARES_CUMPLIMIENTO.md`.
- [ ] **Cumplimos los estándares de repositorio** (sección 6.1): R1, R2, R3, R6, R7 y R8 se cumplen. **R4** queda pendiente: commits propios de Cristopher Alexis Castellanos Paz en esta entrega. **R5:** el tag `entrega-4` se crea después de firmar.
- [x] **Cumplimos los estándares de aplicación** (sección 6.3): 6 de 6. Separación de capas, errores sin SQL crudo, validación en el servidor, consultas parametrizadas, código legible y documentado.
- [x] **La bitácora de IA está actualizada**, con 6 registros de esta entrega y la consolidada de todo el proyecto (`docs/bitacora-ia/ENTREGA4_BITACORA_IA.md`).
- [x] **Los casos de prueba fueron ejecutados y documentados:** 14 de 14 aprobados el 20/10/2026, con capturas (`docs/casos-prueba/casos-prueba-entrega-4.md`). Cubren los flujos U-01 a U-12 del manual de usuario, la restauración de un respaldo y la instalación desde cero. La regresión de la aplicación sumó 183 verificaciones sin fallas.
- [x] **No hay credenciales expuestas en el repositorio:** búsqueda con `git grep` de cadenas de conexión, contraseñas y claves de Neon sin resultados reales. Los respaldos descargados están excluidos por `.gitignore`.

Productos de la Entrega 4 (consigna, sección 11):

- [x] **Sistema web 100% completo**: 11 módulos, incluidos el respaldo de la base y el cambio de contraseña propio (`AVANCE_WEB.md`).
- [x] **CRUD en todas las tablas principales**, con la justificación de las operaciones que no se ofrecen a propósito (movimientos inmutables, lotes que nacen con la entrada): `docs/entrega-4/ENTREGA4_MATRIZ_TRAZABILIDAD.md`.
- [x] **Manuales técnico y de usuario** (`docs/entrega-4/ENTREGA4_MANUAL_TECNICO.md`, `ENTREGA4_MANUAL_USUARIO.md`).
- [ ] **Informe final y declaración de integridad**: redactados (`ENTREGA4_INFORME_FINAL.md`, `ENTREGA4_DECLARACION_INTEGRIDAD.md`); falta que la declaración lleve las firmas.
- [x] **Diagramas ER y relacional actualizados** con la devolución y la baja de exámenes, en editable, PNG y PDF.
- [ ] **Versión publicada al día**: falta aplicar `sql/ddl/003_examen_estado.sql` en Neon (y las migraciones de devolución, si faltan) y redesplegar en Render (manual técnico, sección 6.3). Después, abrir Exámenes, Respaldo y "Cambiar mi contraseña" en https://inventario-laboratorio-03s7.onrender.com con los 3 roles.

---

## Antes de firmar

1. Cristopher: revisar los manuales y repetir en la versión publicada, con su usuario, los flujos U-03 a U-07 del manual de usuario, y registrar el resultado con un commit propio (R4).
2. Quien administre Neon y Render: aplicar las migraciones, redesplegar, verificar y rotar la contraseña de Neon.
3. Ambos: marcar los puntos pendientes de arriba, firmar esta certificación y la declaración de integridad, y crear el tag:
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
| José Eduardo Escobar | 2690245346 | |
