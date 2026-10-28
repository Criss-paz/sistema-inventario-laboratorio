# Certificación de Calidad — Entrega 4

**Proyecto:** Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango
**Entrega:** Entrega 4 — Integración, documentación y defensa oral
**Estado:** firmada por ambos integrantes (26/10/2026)

Revisión preparada del 20 al 26/10/2026 contra el repositorio, la base de datos con el inventario real al 21/10/2026 (814 productos, 1,296 lotes, 6,560 movimientos numerados de E000001 a E001790) y una instalación desde cero verificada en los dos equipos del grupo (36 scripts SQL y `seed_usuarios.py` de `INSTALL.md` sin errores, 0 lotes incoherentes, inventario valorizado en Q600,338.34).

Por medio de la presente, los integrantes del equipo hacemos constar que la documentación y el código de la **Entrega 4** fueron revisados antes de su presentación. Puntos de la consigna (sección 8):

- [x] **Cumplimos la estructura de carpetas obligatoria** (sección 7): `README.md`, `.gitignore`, `.env.example`, `INSTALL.md`, `docs/` (entrega-1 a entrega-4, diagramas, certificaciones, bitacora-ia, casos-prueba), `sql/` (ddl, dml, views, triggers, procedures, security) y `web/`.
- [x] **Cumplimos los estándares SQL** (sección 6.2): 8 de 8. 36 de 36 scripts con encabezado, 17 de 17 FK con `ON DELETE` y `ON UPDATE`, migraciones aditivas probadas antes del commit. Detalle en `docs/entrega-4/ENTREGA4_ESTANDARES_CUMPLIMIENTO.md`.
- [x] **Cumplimos los estándares de repositorio** (sección 6.1): R1, R2, R3, R4, R6, R7 y R8 se cumplen (con commits propios de ambos integrantes también en esta entrega). **R5:** el tag `entrega-4` se crea al cerrar esta firma.
- [x] **Cumplimos los estándares de aplicación** (sección 6.3): 6 de 6. Separación de capas, errores sin SQL crudo, validación en el servidor, consultas parametrizadas, código legible y documentado.
- [x] **La bitácora de IA está actualizada**, con 14 registros de esta entrega y la consolidada de todo el proyecto (`docs/bitacora-ia/ENTREGA4_BITACORA_IA.md`).
- [x] **Los casos de prueba fueron ejecutados y documentados:** 20 de 20 aprobados (20 al 27/10/2026), con capturas (`docs/casos-prueba/casos-prueba-entrega-4.md`). Cubren los flujos U-01 a U-16 del manual de usuario, la corrección y la eliminación de entradas, la carga de los movimientos del 24/09 al 21/10, el número de documento, los roles con permisos editables, la bitácora, la restauración de un respaldo y la instalación desde cero. La regresión de la aplicación sumó 256 verificaciones sin fallas. La eliminación de entradas por el Administrador (CP4-20) se agregó el 27/10/2026, después de las firmas.
- [x] **No hay credenciales expuestas en el repositorio:** búsqueda con `git grep` de cadenas de conexión, contraseñas y claves de Neon sin resultados reales. Los respaldos descargados están excluidos por `.gitignore`.

Productos de la Entrega 4 (consigna, sección 11):

- [x] **Sistema web 100% completo**: 12 módulos, incluidos el respaldo de la base, el cambio de contraseña propio, la corrección de entradas con registro, el número de documento E/S/D, los permisos editables por rol y la bitácora de auditoría (`AVANCE_WEB.md`).
- [x] **Inventario al día** con los movimientos de SIGAL del 24/09 al 21/10/2026, verificado contra SIGAL (`docs/entrega-4/ENTREGA4_REPORTE_CARGA_SIGAL.md`).
- [x] **CRUD en todas las tablas principales**, con la justificación de las operaciones que no se ofrecen a propósito (movimientos inmutables, lotes que nacen con la entrada): `docs/entrega-4/ENTREGA4_MATRIZ_TRAZABILIDAD.md`.
- [x] **Manuales técnico y de usuario** (`docs/entrega-4/ENTREGA4_MANUAL_TECNICO.md`, `ENTREGA4_MANUAL_USUARIO.md`).
- [x] **Informe final y declaración de integridad**: redactados y firmados por ambos integrantes (`ENTREGA4_INFORME_FINAL.md`, `ENTREGA4_DECLARACION_INTEGRIDAD.md`).
- [x] **Diagramas ER y relacional actualizados** con la devolución, la baja de exámenes, la corrección de entradas, el número de documento, los permisos por rol y la bitácora (15 tablas), en editable, PNG y PDF.
- [x] **Versión publicada al día** (21/10/2026): Neon tiene todas las migraciones, la corrección de entradas y la carga de SIGAL (721 movimientos; 814 productos, 6,562 movimientos e inventario valorizado en Q600,338.34, igual que la instalación desde cero). Antes de cargar se anuló con una devolución la salida de prueba #5840, que había dejado un lote en 0. Render publica la última versión. El 26/10/2026 se aplicaron en Neon el número de documento, los permisos y la bitácora (0 movimientos sin número, 14 permisos asignados) y se redesplegó Render.

---

## Cierre de entrega (tag)

1. Verificación en el segundo equipo y en la versión publicada completada y registrada el 26/10/2026 (R4).
2. Certificación y declaración de integridad firmadas por ambos integrantes; para publicar el tag de cierre:
   ```bash
   git tag -a entrega-4 -m "Entrega 4 — Integración, documentación y defensa oral"
   git push origin entrega-4
   ```
   Fecha límite: **03/11/2026** (−0.25 pts por día de retraso).

---

## Añadido el 27/10/2026, después de firmar lo anterior

Tras la presentación del sistema, el catedrático observó que alguien podría conectarse e intentar hacer o deshacer varios ingresos o salidas, y sugirió implementar *tokens*, mencionando OAuth 2.0. El equipo analizó la observación e incorporó lo siguiente:

- [x] **Token CSRF** en los 27 formularios POST (`web/seguridad.py`).
- [x] **Token de un solo uso** en las cinco operaciones que mueven inventario: el mismo movimiento no se registra dos veces, ni recargando con F5 ni reenviando una petición capturada.
- [x] **Bloqueo tras cinco intentos fallidos**, contado desde la bitácora por usuario y dirección de origen.
- [x] **Probado:** casos CP4-21 a CP4-24, 4 de 4 pasaron, sobre la base reconstruida desde cero siguiendo `INSTALL.md`.
- [x] **Documentado:** [`ENTREGA4_SEGURIDAD_WEB.md`](../entrega-4/ENTREGA4_SEGURIDAD_WEB.md), que explica además por qué **OAuth 2.0 no aplica** a una aplicación monolítica sin terceros, y en qué caso sí tendría sentido.
- [x] **Presentación del sistema** añadida al repositorio: `docs/entrega-4/ENTREGA4_PRESENTACION.pptx`, 18 diapositivas.

Durante las pruebas se detectaron y corrigieron **dos defectos del propio diseño**: contar los intentos sólo por usuario habría permitido bloquear al administrador a propósito, y registrar los intentos ya bloqueados reiniciaba la ventana, de modo que el bloqueo nunca caducaba. Ambos quedaron corregidos y documentados.

Hacemos constar que esta funcionalidad se agregó después de firmar los puntos anteriores y que se probó con el mismo rigor que el resto de la entrega.

---

## Firmas

| Nombre completo | Carné | Firma |
|---|---|---|
| Cristopher Alexis Castellanos Paz | 2690245972 | Cristopher Alexis Castellanos Paz — firmado el 26/10/2026 |
| José Eduardo Escobar | 2690245346 | José Eduardo Escobar — firmado el 26/10/2026 |
