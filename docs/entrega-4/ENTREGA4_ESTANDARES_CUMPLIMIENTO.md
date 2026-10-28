# Cumplimiento de estándares de calidad — Entrega 4

Revisión final de los estándares de la consigna (sección 6) sobre el repositorio al cierre del proyecto. Actualiza `docs/entrega-3/ENTREGA3_ESTANDARES_CUMPLIMIENTO.md`. Cada fila cita dónde se verifica, y las cifras se midieron sobre el código el 26/10/2026. Lo que no se cumple, o depende de una acción pendiente, se declara.

---

## 6.1 Estándares del repositorio Git

| # | Estándar | Estado | Evidencia verificable |
|---|---|---|---|
| **R1** | Estructura de carpetas | ✅ Cumple | `README.md`, `.gitignore`, `.env.example`, `INSTALL.md`; `docs/` con `entrega-1` a `entrega-4`, `diagramas`, `certificaciones`, `bitacora-ia` y `casos-prueba`; `sql/` con `ddl`, `dml`, `views`, `triggers`, `procedures` y `security`; `web/`. |
| **R2** | README.md | ✅ Cumple | Nombre del proyecto, integrantes con carné, SGBD, instalación (enlace a `INSTALL.md`), aplicación en línea, documentos de cada entrega y estado. |
| **R3** | Commits descriptivos | ✅ Cumple | Prefijos convencionales con ámbito: `feat(respaldo): …`, `fix(web): …`, `docs(diagramas): …`, `test(casos): …`. El cuerpo explica el porqué de cada cambio. |
| **R4** | Participación visible | ✅ Cumple | Hay commits propios de ambos integrantes a lo largo del proyecto y en esta entrega: implementación, migraciones y pruebas iniciales por José Eduardo Escobar; reconstrucción desde cero en el segundo equipo, verificación de los flujos del manual y de las pantallas nuevas (numeración, permisos por rol y bitácora), correcciones de documentación y cierre por Cristopher Alexis Castellanos Paz (`Criss-paz`). |
| **R5** | Tags por entrega | ⏳ Al cierre | `entrega-1`, `entrega-2` y `entrega-3` publicados. `entrega-4` se crea al cierre, después de las firmas. |
| **R6** | Sin credenciales | ✅ Cumple | Búsqueda en todo el repositorio (`git grep`) de cadenas de conexión con contraseña, `DB_PASSWORD=`, `APP_SECRET=` y claves de Neon (`npg_…`): solo aparecen los valores ficticios de `.env.example`. En esta entrega se quitó de `docs/entrega-2/Bitacora-IA.md` la mención en texto de la contraseña local de la base. Las contraseñas de `web/seed_usuarios.py` son de desarrollo y no funcionan en producción. |
| **R7** | .gitignore | ✅ Cumple | Excluye `.env`, entornos virtuales, `__pycache__`, temporales y la carpeta con los Excel del laboratorio. |
| **R8** | Acceso al catedrático | ✅ Cumple | Repositorio público: https://github.com/Criss-paz/sistema-inventario-laboratorio |

## 6.2 Estándares de calidad SQL

| # | Estándar | Estado | Evidencia verificable |
|---|---|---|---|
| **S1** | Nomenclatura `snake_case` | ✅ Cumple | Tablas, columnas y objetos en `snake_case`, con prefijo según el tipo: `vw_` vistas, `fn_` funciones, `sp_` procedimientos, `trg_` triggers, `rol_` roles, `pk_`/`fk_`/`uq_`/`ck_` restricciones, `ix_` índices. Las columnas y tablas nuevas (`id_movimiento_origen`, `motivo`, `examen_laboratorio.estado`, `numero_documento`, `permiso`, `rol_permiso`, `bitacora`) siguen la misma regla. |
| **S2** | Un script, un propósito | ✅ Cumple | 36 scripts en las 6 carpetas, uno por propósito y por versión: `ddl/001–007`, `dml/001–005`, `triggers/001–007`, `procedures/001–005`, `views/001–007`, `security/001–005`. Cada funcionalidad nueva separa su tabla, su trigger, su vista y sus permisos (por ejemplo, la bitácora: `ddl/007`, `triggers/006`, `views/007`, `security/004`). La migración de la Entrega 4 (`ddl/003_examen_estado.sql`) solo altera estructura; sus permisos no necesitan script porque los `GRANT` son por tabla. |
| **S3** | Encabezado | ✅ Cumple | **36 de 36** scripts abren con *Archivo, Propósito, Proyecto, Autor, Descripción, Dependencias, SGBD, Ejecutar*. Los que materializan reglas las listan (por ejemplo, RN-24 en `ddl/003` y RN-30 en `ddl/007`). |
| **S4** | Integridad referencial | ✅ Cumple | **17 de 17** FK con `ON DELETE` y `ON UPDATE` explícitos: las 11 del esquema, `fk_movimiento_origen`, las 2 de `correccion_entrada`, la de `bitacora` (todas `ON DELETE RESTRICT ON UPDATE CASCADE`, justificado: el historial no se borra) y las 2 de `rol_permiso` (`CASCADE` hacia `rol`, porque los permisos de un rol eliminado no tienen sentido; `RESTRICT` hacia `permiso`, que es un catálogo fijo). |
| **S5** | Desplegado en internet | ✅ Cumple | https://inventario-laboratorio-03s7.onrender.com (Render + Neon), con todas las migraciones aplicadas el 26/10/2026. La instalación desde cero se volvió a verificar ese día en ambos equipos (CP4-14: 33 scripts sin errores, mismos totales y Q600,338.34). |
| **S6** | Regla de negocio explicada | ✅ Cumple | Los 22 triggers y los 5 procedimientos citan en su encabezado y en comentarios la regla que aplican (RN-01 a RN-09, RN-19 a RN-31) y el porqué (por ejemplo, el prefijo `trg_z_` que fija el orden de disparo). |
| **S7** | Sin redundancia | ✅ Cumple | Existencias por producto, inventario bajo, días para vencer, costos promedio y valorización se calculan en vistas y funciones. La única cifra derivada que se almacena es `lote.cantidad_disponible`, que mantiene el trigger: 0 lotes incoherentes con su historial (CP4-14). El respaldo guarda solo datos; la estructura se reinstala desde `sql/`. |
| **S8** | SQL de IA revisado y probado | ✅ Cumple | La corrección de entradas se probó en `psql` dentro de `BEGIN … ROLLBACK` (aumentar, bajar de más, precio, vencimiento, permisos, intento de `DELETE` aun con la variable de sesión activa); una falla del trigger con `DELETE` se detectó y corrigió así. La carga de SIGAL se aplicó tras un respaldo y se verificó contra SIGAL (804 de 813 productos idénticos, diferencias explicadas) y con una instalación desde cero de los 21 pasos. La migración `ddl/003` se aplicó primero en la base local y se probó con la app (14 verificaciones) antes del commit. Las seis migraciones de la devolución, que faltaban en la base de desarrollo, se aplicaron y verificaron. El respaldo se probó restaurándolo en un esquema aislado (11 de 11 tablas idénticas). La instalación completa se probó desde cero en otro esquema. Registro en `docs/bitacora-ia/ENTREGA4_BITACORA_IA.md`. El número de documento se probó con una entrada y una salida nuevas dentro de `BEGIN … ROLLBACK` (E001793, S004790); los permisos y la bitácora, con 31 verificaciones que incluyen un `UPDATE` directo a la bitácora (rechazado). Las 10 migraciones del 26/10/2026 se aplicaron primero en la base local, después de un respaldo, y se instalaron desde cero en un esquema aparte (33 pasos) antes de llevarlas a Neon. La eliminación de entradas (27/10/2026) se probó en `psql` dentro de `BEGIN … ROLLBACK` (encargado rechazado, entrada consumida rechazada, `DELETE` directo con la variable activa negado por permisos, salida protegida por el trigger) y con 17 verificaciones en la app; instalación desde cero de 36 pasos. |

**Resultado: los 8 estándares SQL se cumplen.**

## 6.3 Estándares de código de aplicación

| # | Estándar | Estado | Evidencia verificable |
|---|---|---|---|
| **A1** | Separación de capas | ✅ Cumple | `config.py` (entorno), `db.py` (único acceso a PostgreSQL, incluida la conexión sin rol, que antes abría `respaldo.py` por su cuenta y se movió aquí), `respaldo.py` (servicio sin Flask), `routes/` (12 módulos), `templates/` (43 plantillas), `static/` (`style.css` con el diseño de SIGAL y `app.js` solo para comportamiento de interfaz: tema, menús, avisos y búsqueda). Las reglas de negocio viven en la base. |
| **A2** | Errores comprensibles, sin SQL crudo | ✅ Cumple | `db.mensaje_error()` deja pasar solo los mensajes de negocio (`P0001`) y "su rol no tiene permiso"; todo lo demás se reemplaza por un texto genérico. Páginas propias para 403, 404 y 500. El respaldo traduce sus fallas a `RespaldoError` con mensaje para el usuario. |
| **A3** | Validación de entrada | ✅ Cumple | Validación en el servidor de cada formulario nuevo: precio ≥ 0 con 2 decimales y producto activo (proveedor–producto); largo mínimo, confirmación y contraseña distinta de la anterior (cambio de contraseña); existencia del examen antes de cambiar su estado. Las validaciones HTML (`required`, `minlength`) son ayuda, no la defensa. |
| **A4** | Consultas parametrizadas | ✅ Cumple | Las 128 llamadas a la base desde `routes/` y `app.py` pasan los datos del usuario como parámetros. Las consultas armadas con f-string solo combinan fragmentos fijos del código, y el respaldo compone identificadores con `psycopg.sql.Identifier` a partir de una lista fija de tablas. |
| **A5** | Código legible, responsabilidad única | ✅ Cumple | 17 módulos y 134 funciones con nombres del dominio (`guardar_producto`, `alternar_estado`, `guardar_permisos`, `_verificar_tablas`). Las más largas son `create_app` (100 líneas, casi todo funciones internas de 5 a 12 líneas), `movimientos.corregir` (84), `movimientos.devolucion` y `respaldo.generar` (80 cada una, una sola tarea). |
| **A6** | Documentación de funciones que acceden a la BD | ✅ Cumple | **17 de 17** módulos con docstring que explica su responsabilidad, los requerimientos y quién puede usarlos. Las funciones con decisiones no obvias lo explican: `conexion_sin_rol` (por qué y quién la usa), `generar` (por qué `REPEATABLE READ`), `mismo_origen` (por qué además de `SameSite`), `_acceso` (por qué los permisos se leen antes de `SET ROLE`), `bitacora._describir` (cómo se traduce cada registro). |

**Resultado: los 6 estándares de aplicación se cumplen.**

## 6.4 Estándares de documentación

| # | Estándar | Estado | Evidencia verificable |
|---|---|---|---|
| **D1** | Ortografía | ✅ Cumple | Los documentos de la Entrega 4 se revisaron con tildes y signos completos. Se corrigieron el `README.md` (encabezados escritos sin tildes desde la Entrega 1) y la etiqueta "Devolucion" de la interfaz. |
| **D2** | Versionado por entrega | ✅ Cumple | `docs/entrega-4/ENTREGA4_MANUAL_USUARIO.md`, `ENTREGA4_MANUAL_TECNICO.md`, `ENTREGA4_INFORME_FINAL.md`, `ENTREGA4_DECLARACION_INTEGRIDAD.md`, `ENTREGA4_MATRIZ_TRAZABILIDAD.md`, `ENTREGA4_ESTANDARES_CUMPLIMIENTO.md`, `ENTREGA4_GUIA_DEFENSA.md`; `docs/bitacora-ia/ENTREGA4_BITACORA_IA.md`; `docs/certificaciones/CERTIFICACION_ENTREGA_4.md`. |
| **D3** | Diagramas editables + PNG/PDF | ✅ Cumple | `docs/diagramas/`: ER (Chen) y relacional en `.drawio`, `.png` y `.pdf`, **actualizados en esta entrega** con la devolución (relación recursiva *Corrige*, `id_movimiento_origen`, `motivo`), `examen_laboratorio.estado`, `correccion_entrada`, `movimiento.numero_documento`, `permiso`, `rol_permiso` y `bitacora` (15 tablas). |
| **D4** | Matriz de trazabilidad actualizada | ✅ Cumple | `ENTREGA4_MATRIZ_TRAZABILIDAD.md` (v3): 39 RF, 18 RNF y 31 RN con su implementación y su prueba, más la tabla de CRUD por tabla. |

---

## Pendientes declarados

| Pendiente | Estándar | Responsable |
|---|---|---|
| Tag `entrega-4` en el commit de cierre (certificación y declaración ya firmadas por ambos integrantes) | R5 | Ambos integrantes |


