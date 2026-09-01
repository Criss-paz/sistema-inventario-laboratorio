# Bitácora de Utilización de IA — Entrega 2

## Proyecto
Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango

## Entrega
Entrega 2 — Diseño lógico, diccionario e implementación base

## Propósito
Continúa el registro iniciado en `docs/bitacora-ia/Bitacora-IA.md` (Entrega 1). La IA se utiliza como apoyo de análisis y documentación; toda propuesta es revisada y validada por el equipo antes de incorporarse.

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026

**Herramienta:** Claude Code (Claude Sonnet 5)

**Objetivo:** Corregir observaciones del ingeniero sobre la Entrega 1 antes de iniciar la Entrega 2: (1) relación confusa USUARIO→PRODUCTO en el diagrama ER, (2) mezcla de atributos de llave foránea dentro del modelo conceptual Chen, (3) carpetas `sql/` y `web/` declaradas en el README pero inexistentes.

**Prompt utilizado:**
El usuario pidió analizar el proyecto, corregir las observaciones del ingeniero (lista "No cumple / débil") e iniciar la Fase 1 (auditoría) de la Entrega 2 según una consigna detallada de 24 secciones.

**Resultado obtenido:**
Se inspeccionó el XML de `DIAGRAMA-ER-LAB.drawio` y se identificó un bloque de 10 celdas (prefijo `PjxAiM5xKQoVbdMgcQq8-*`) agregado después del modelo original, que superponía atributos de FK duplicados sobre las entidades — incluyendo un `id_usuario` conectado erróneamente a `PRODUCTO` en vez de a `MOVIMIENTO`. Se eliminó ese bloque completo. Se crearon las carpetas `sql/ddl`, `sql/dml`, `sql/views`, `sql/triggers`, `sql/procedures`, `sql/security`, `web/`, `docs/entrega-2`, `docs/entrega-3`, `docs/entrega-4` y `docs/casos-prueba`, cada una con un `README.md` de estado (sin generar DDL ni código web, según instrucción explícita del usuario).

**Validación del grupo:**
Pendiente de revisión visual por el equipo: el `.drawio` corregido debe reabrirse en app.diagrams.net y volver a exportarse a PNG/PDF (la IA no puede renderizar el archivo `.drawio` directamente). El equipo debe confirmar que la relación `USUARIO —(Registra)→ MOVIMIENTO` (RF-27, RN-08) se ve correctamente y que ya no aparece ningún atributo de `PRODUCTO` relacionado con `USUARIO`.

**Estándares aplicados:** Coherencia ER ↔ requerimientos (RF-27, RN-08); notación Chen conceptual pura (sin atributos de FK); estructura de repositorio declarada en el README.

**Responsable:** Equipo (pendiente confirmar nombre del integrante que valida el diagrama re-exportado).

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026

**Herramienta:** Claude Code (Claude Sonnet 5)

**Objetivo:** Definir el SGBD para la Entrega 2, dado que la Entrega 1 lo dejó como "a definir" en el README mientras que la bitácora de Entrega 1 mencionaba Oracle y el `.env.example` usaba el puerto por defecto de MySQL (3306) — una inconsistencia entre tres archivos señalada por el ingeniero.

**Prompt utilizado:**
Se solicitó a la IA recomendar un SGBD entre MySQL, PostgreSQL, SQL Server y Oracle, evaluando facilidad de instalación, soporte de restricciones/triggers/procedimientos/roles y facilidad de defensa académica, sin decidir unilateralmente.

**Resultado obtenido:**
La IA presentó las 4 opciones con sus criterios (Oracle por ser la intención original registrada en la Entrega 1; PostgreSQL como recomendación por balance de estándares/CHECK/triggers/instalación simple; MySQL por coincidir con el `.env.example` previo; SQL Server para stack Microsoft) y pidió al equipo elegir.

**Validación del grupo:**
El equipo eligió **PostgreSQL**. Se actualizaron `README.md` (sección SGBD) y `.env.example` (`DB_PORT=3306` → `5432`) para reflejar la decisión de forma consistente en todo el repositorio.

**Estándares aplicados:** Consistencia de configuración entre `README.md`, `.env.example` y esta bitácora (hallazgo del ingeniero resuelto).

**Responsable:** José Eduardo Escobar (usuario que confirmó la decisión en esta sesión).

---

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026

**Herramienta:** Claude Code (Claude Sonnet 5)

**Objetivo:** Cerrar el resto de hallazgos de la auditoría Fase 1 antes de pasar a Fase 2: nombre truncado de un integrante en `README.md`/`CERTIFICACION_ENTREGA_1.md`, y referencia desactualizada al diagrama (`.jpg` en vez de `.png`) dentro de `ENTREGA1_PROPUESTA.docx`.

**Prompt utilizado:**
"Corrige todo lo que encontraste en la auditoría, antes de pasar a fase 2."

**Resultado obtenido:**
- Se buscó el nombre completo del integrante "Cristopher" en el propio DOCX de la propuesta (sección de firmas) y se encontró completo: **Cristopher Alexis Castellanos Paz**. Se corrigió en `README.md` y en `CERTIFICACION_ENTREGA_1.md`.
- Se buscó el apellido completo del segundo integrante ("José Eduardo Escobar Já...") en el DOCX, su metadata (`docProps/core.xml`) y en `Gantt-Proyecto.xlsx`; en ningún archivo del repositorio aparece completo — el propio DOCX fuente ya lo tiene truncado. **No se inventó el apellido faltante** (Regla 1 del equipo); se dejó marcado con ⚠️ en ambos archivos hasta que el equipo lo confirme.
- Se corrigió, dentro de `word/document.xml` del propio `ENTREGA1_PROPUESTA.docx`, la referencia `docs/diagramas/DIAGRAMA ER LAB.jpg` → `docs/diagramas/DIAGRAMA-ER-LAB.png` (edición directa del XML interno del .docx, verificada reabriendo el archivo como zip/XML válido tras el cambio). No se pudo regenerar `ENTREGA1_PROPUESTA.pdf` a partir del .docx corregido: no hay LibreOffice/Word disponible en este entorno para exportarlo.
- No se pudo re-exportar `DIAGRAMA-ER-LAB.drawio.png`/`.pdf` a partir del `.drawio` ya corregido: no hay un renderizador de draw.io disponible en este entorno (se requiere la app de escritorio o app.diagrams.net).

**Validación del grupo:**
José Eduardo Escobar confirmó que el apellido completo es **Escobar** (sin segundo apellido) — se corrigió a "José Eduardo Escobar" en `README.md` y `CERTIFICACION_ENTREGA_1.md`. Pendiente aún: (1) alguien con la app draw.io debe reabrir el `.drawio` corregido y reexportar PNG/PDF, (2) opcionalmente regenerar el PDF de la propuesta desde el .docx corregido (no bloqueante).

**Estándares aplicados:** No inventar datos no verificables en el repositorio (Regla 1); trazabilidad de cada cambio a su archivo fuente.

**Responsable:** José Eduardo Escobar.

---

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026

**Herramienta:** Claude Code (Claude Sonnet 5)

**Objetivo:** Construir el modelo relacional (Fase 2) derivado del modelo conceptual Chen ya auditado en la Fase 1, con PostgreSQL como motor definitivo.

**Prompt utilizado:**
"avanza a la fase 2" (siguiendo la consigna oficial de 15 fases entregada previamente por el usuario, sección 7 — Modelo relacional).

**Resultado obtenido:**
Se generó `docs/entrega-2/modelo-relacional.md`: 11 tablas (9 entidades + 2 tablas puente `proveedor_producto` y `examen_producto`), cada una con PK, FK, columnas, tipos de dato PostgreSQL, NULL/NOT NULL, UNIQUE, CHECK, DEFAULT y reglas ON DELETE/ON UPDATE justificadas contra las reglas de negocio (RN-01 a RN-18) y los requerimientos funcionales (RF-01 a RF-39). Se documentó explícitamente la transformación de cada relación del ER (1:N y N:M) al modelo relacional, y se dejaron 3 preguntas abiertas para el equipo (unidad de medida, validación de `fecha_vencimiento`, confirmación de que no habrá `DELETE` físico expuesto en la web).

**Validación del grupo:**
El usuario pidió detener el desarrollo después de esta fase ("necesito solo hasta la fase 2") y solicitó una revisión de completitud del propio repositorio, no solo del documento. Se corrigieron 4 elementos que quedaban desalineados: el árbol de carpetas del `README.md` (le faltaban `docs/entrega-2/3/4`), faltaba una sección "Documentación de Entrega 2" en el README, el estado del README seguía diciendo solo "Entrega 1", y `docs/entrega-2/README.md` seguía siendo un placeholder genérico sin reflejar lo ya hecho. Las 3 preguntas abiertas del modelo relacional (unidad de medida, `fecha_vencimiento`, política de DELETE) siguen pendientes de respuesta del equipo — no se decidieron unilateralmente.

**Estándares aplicados:** Trazabilidad completa RF/RN → tabla/columna/restricción; snake_case; un archivo por fase (no se mezcló con DDL ni con normalización); consistencia entre README raíz y subcarpetas.

**Responsable:** José Eduardo Escobar.

---

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026

**Herramienta:** Claude Code (Claude Sonnet 5)

**Objetivo:** Cerrar las 3 preguntas abiertas que quedaron al final de `modelo-relacional.md` (unidad de medida, `fecha_vencimiento`, política de DELETE), con autorización explícita del usuario para que la IA decidiera.

**Prompt utilizado:**
"puedes tu corregir las 3 opciones. doy la autorizacion."

**Resultado obtenido:**
1. `unidad_medida` se mantiene como texto libre (no se crea tabla catálogo) — no hay RF que requiera administrarla como catálogo independiente.
2. Se agregó `producto.requiere_vencimiento` (BOOLEAN NOT NULL DEFAULT TRUE) para materializar RN-07; la validación cruzada con `lote.fecha_vencimiento` queda para app (Entrega 2) y trigger (Entrega 3), documentado en `modelo-relacional.md`.
3. Se formalizó como política de arquitectura: ningún flujo web expondrá `DELETE` físico sobre las tablas de catálogo/historial — todas las bajas son lógicas vía `estado`.

**Validación del grupo:**
Autorización explícita del usuario para que la IA resolviera estos 3 puntos ("doy la autorización"), a diferencia de la decisión de SGBD, que el usuario tomó él mismo entre opciones presentadas. Ninguna de las tres decisiones agrega entidades ni tablas nuevas fuera de las 9 originales + 2 puente ya auditadas.

**Estándares aplicados:** Regla 4 (no sobreingeniería) aplicada para descartar el catálogo de unidades; trazabilidad a RN-07 para `requiere_vencimiento`; consistencia con el patrón `ON DELETE RESTRICT` ya definido en el resumen de integridad referencial.

**Responsable:** José Eduardo Escobar (autorizó la delegación de la decisión a la IA).

---

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026

**Herramienta:** Claude Code (Claude Sonnet 5)

**Objetivo:** El usuario compartió el documento oficial de la rúbrica del catedrático ("Proyecto - Base de datos.pdf", Universidad Mariano Gálvez) y pidió analizar en detalle qué faltaba para cubrir realmente la Entrega 2 oficial (no solo la "Fase 2" interna de modelo relacional). Tras el análisis, autorizó completar todo lo que faltaba.

**Prompt utilizado:**
"segun esto, debo cubrir hasta la fase 2.. analizalo detalladamente y dime que es lo que me hace falta. para realizarlo." — seguido de la elección del equipo entre las opciones presentadas (repo Git real existente en otra parte; stack web Python + Flask).

**Resultado obtenido:**
Se generó el resto de la Entrega 2 completa:
- `docs/entrega-2/normalizacion-3fn.md` — normalización 3FN con dependencias funcionales, usando un ejemplo completo (tabla plana hipotética → 1FN → 2FN → 3FN) que reconstruye exactamente las 6 tablas centrales del modelo real, más verificación de las 5 tablas restantes.
- `docs/entrega-2/diccionario-datos.md` — diccionario de las 11 tablas + matriz de 38 restricciones explícitas (mínimo exigido: 15).
- `sql/ddl/001_schema.sql` — DDL completo con encabezado, comentarios por regla de negocio, 11 tablas, 38 restricciones nombradas, e índices de apoyo.
- `sql/dml/001_seed.sql` — datos de prueba (roles, categorías, proveedores, productos, exámenes, relaciones N:M, lotes) — sin usuarios.
- `web/` — aplicación Flask completa: `config.py`, `db.py` (consultas parametrizadas), `routes/auth.py` (login/logout), `routes/categorias.py` y `routes/productos.py` (2 CRUD con baja lógica, no DELETE físico), plantillas HTML, `seed_usuarios.py` (crea usuarios de prueba con hash real de `werkzeug.security`, separado del DML por seguridad de formato de hash).
- `INSTALL.md` reescrito con pasos reales; `AVANCE_WEB.md`, `docs/entrega-2/matriz-trazabilidad.md`, `docs/casos-prueba/casos-prueba-entrega-2.md` (15 casos) y `docs/certificaciones/CERTIFICACION_ENTREGA_2.md` (borrador sin firmar) — todos nuevos.

**Validación del grupo:**
El usuario decidió el stack web (Python + Flask) entre 4 opciones presentadas y confirmó que el repositorio Git real existe fuera de este entorno (en GitHub/GitLab), por lo que estos archivos deben trasladarse allá antes de poder taggear `entrega-2`. **Pendiente y explícito**: se verificó que este entorno de desarrollo no tiene Python ni PostgreSQL instalados, así que nada de este código se ha ejecutado — el DDL nunca corrió contra una base de datos real, el login y los 2 CRUD nunca se probaron en un navegador. Los 15 casos de prueba quedaron con "PENDIENTE DE EJECUCIÓN" a propósito, no se inventó ningún resultado. La certificación de Entrega 2 se dejó como borrador sin firma real.

**Estándares aplicados:** S1 (snake_case), S2 (un script por propósito), S3 (encabezados con autor/descripción/dependencias), S4 (ON DELETE/ON UPDATE documentados), S7 (sin redundancia, verificado con 3FN), S8 (este mismo registro es la validación pendiente de "SQL generado por IA revisado y probado antes del commit" — falta la parte de "probado"); A1 (separación de capas), A2 (sin errores SQL crudos), A3 (validación de entrada), A4 (consultas parametrizadas).

**Responsable:** José Eduardo Escobar y Cristopher Alexis Castellanos Paz (pendiente ejecutar y validar funcionalmente antes de firmar la certificación).

---

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026

**Herramienta:** Claude Code (Claude Sonnet 5)

**Objetivo:** El usuario instaló Python y PostgreSQL en su máquina y pidió continuar. Se ejecutó realmente todo lo que hasta entonces estaba documentado como "pendiente de ejecución": creación de la BD, DDL, seed, entorno virtual, dependencias, usuarios de prueba, y la aplicación Flask, con pruebas HTTP automatizadas de los 15 casos de prueba.

**Prompt utilizado:**
"YA TENGO INSTALADO PYHTON Y POSGRES QUE REALIZO AHORA" y, tras pedir la contraseña del superusuario `postgres`, el usuario decidió crear la BD/usuario él mismo en su terminal, pero luego compartió la contraseña ("1234 ES LA CONTRASEÑA...") y se le pidió autorización para continuar directamente.

**Resultado obtenido:**
- Se confirmó que Python 3.14.7 y PostgreSQL 18.6 estaban instalados (con rutas completas, ya que el PATH de esta sesión de herramienta estaba desactualizado).
- Se creó la base de datos `inventario_laboratorio`, el usuario `usuario_app` y el `GRANT` de schema `public` (necesario en PostgreSQL 15+, no estaba en la versión original de `INSTALL.md` — corregido).
- Se ejecutó `001_schema.sql` (11 tablas + 6 índices, sin errores) y `001_seed.sql` (35 filas, sin errores).
- Se creó `.env` real (con `DB_PASSWORD=1234` y un `APP_SECRET` aleatorio) y se confirmó que ya estaba en `.gitignore`.
- Se creó el entorno virtual e intentó instalar `psycopg2-binary`: **falló** — no tiene wheel para Python 3.14 en Windows (pide Visual C++ Build Tools). Se migró todo el código (`db.py`, `routes/categorias.py`, `routes/productos.py`, `seed_usuarios.py`, `requirements.txt`) a `psycopg` (v3), que sí tiene wheel para 3.14. Se corrigió también `.gitignore` (le faltaba `.venv/`).
- Se ejecutó `seed_usuarios.py` (3 usuarios creados con hash real) y se levantó `python app.py` como proceso en segundo plano.
- Se ejecutaron los 15 casos de prueba con `Invoke-WebRequest` contra el servidor real, verificando además varios resultados directamente en PostgreSQL con `psql`. **15/15 pasaron**, incluyendo un reinicio real del servidor (CP-15) para confirmar persistencia en BD y no en memoria.

**Validación del grupo:**
El usuario autorizó dar la contraseña del superusuario `postgres` para que la IA ejecutara la creación de la BD directamente, en vez de hacerlo él mismo en su terminal como se había planteado inicialmente. Todos los resultados de esta entrada son verificables por el equipo: los 15 casos de prueba documentan cómo se comprobó cada uno (respuesta HTTP y/o consulta SQL directa), no hay ningún resultado inventado.

**Estándares aplicados:** S8 (SQL/código generado por IA, ahora sí revisado y probado antes de commit); A2/A3/A4 verificados en ejecución real, no solo en el código; se corrigieron 2 defectos reales encontrados durante la ejecución (driver psycopg2→psycopg, `GRANT` de schema faltante) antes de que el equipo los sufriera.

**Responsable:** José Eduardo Escobar (autorizó compartir la contraseña de desarrollo y continuar la ejecución).

---

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026 · **Objetivo:** mejorar la interfaz visual (paleta, tablas, formularios, login) tras la validación funcional del equipo. **Resultado:** rediseño de `web/static/style.css` y ajustes menores en las plantillas (badges de estado, pestaña activa en el menú, login centrado). **Validación:** confirmado con el servidor real que login y ambos CRUD siguen respondiendo 200 tras el cambio. **Responsable:** José Eduardo Escobar.

---

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026

**Objetivo:** Registrar las pruebas manuales que el equipo realizó por su cuenta en el navegador, adicionales a las 15 automatizadas.

**Reportado por el equipo:** inicio de sesión manual con los 3 usuarios de prueba (`admin.dev`, `encargado.dev`, `consulta.dev`) y creación de un producto adicional desde el formulario web.

**Validación:** la creación del producto se confirmó de forma independiente contra la base de datos — apareció una fila que no correspondía a ninguna de las pruebas anteriores (`id_producto=13, codigo='101010001', nombre='H13'`), consistente con lo reportado. El inicio de sesión con los 3 roles no deja rastro verificable en la base de datos (no hay columna de último login en el modelo actual), así que esa parte queda registrada como reportada por el equipo, no verificada por consulta directa — se documenta así de forma honesta en `docs/casos-prueba/casos-prueba-entrega-2.md` (CP-16, CP-17).

**Responsable:** José Eduardo Escobar y Cristopher Alexis Castellanos Paz (pruebas manuales realizadas por el equipo).

---

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026 · **Objetivo:** llevar la interfaz a un acabado "profesional" (pedido explícito del usuario para cerrar la Entrega 2). **Resultado:** tarjetas de resumen (KPI) en los listados, confirmación antes de dar de baja/alta un registro (`onsubmit` + `tojson` para evitar romper el diálogo si el nombre trae comillas), mensajes flash con auto-cierre, favicon, fondo de login con degradado, y páginas de error 404/500 propias (registradas en `app.py`, refuerzan el estándar A2 de no exponer errores crudos). **Validación:** confirmado con el servidor real — login, ambos CRUD y una ruta inexistente (404) siguen respondiendo correctamente tras el cambio; también se registró en el log del servidor uso manual extenso del equipo durante esta sesión (ediciones y altas/bajas de categorías y productos), consistente con las pruebas manuales reportadas antes. **Responsable:** José Eduardo Escobar.

---

---

### Registro de Bitácora IA

**Fecha:** 30/08/2026 · **Objetivo:** el usuario pidió detectar todas las modificaciones manuales hechas en el navegador desde la sesión anterior y reordenar la documentación en consecuencia. **Detección:** se comparó el estado actual de `categoria` y `producto` contra el seed original vía `psql`. Las 5 categorías y los 10 productos genéricos del seed fueron reemplazados uno por uno, desde el CRUD web, por el catálogo real del laboratorio (nombres, descripciones, unidades y códigos reales); `proveedor`, `examen_laboratorio`, `lote` y `usuario` quedaron sin cambios (no tienen CRUD todavía). **Resultado:** `sql/dml/001_seed.sql` se regeneró con el catálogo real para que una instalación desde cero lo cargue directamente; se agregó el caso CP-18 a `casos-prueba-entrega-2.md` con la evidencia verificada en PostgreSQL; se actualizó `AVANCE_WEB.md`. **Responsable:** José Eduardo Escobar (curó el catálogo real vía la interfaz web).

---

---



### Registro de Bitácora IA — Auditoría de cierre

| Campo | Detalle |
|---|---|
| **Fecha** | 01/09/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Auditar el repositorio completo contra la consigna oficial del proyecto (Secciones 5, 6 y 7, y la rúbrica de la Entrega 2) antes de crear el tag `entrega-2`, e identificar todo lo que costara puntos. |
| **Prompt utilizado** | "Quiero que seas un analizador" + el PDF de la consigna, con alcance acotado por el equipo a *cerrar la Entrega 2 hoy* y entregar análisis + plan de corrección. |
| **Resultado obtenido** | Verificó el cumplimiento de los requisitos mínimos (9 entidades principales + 2 tablas puente, 3 relaciones N:M resueltas, **38 restricciones explícitas** contra las 15 exigidas, 3FN documentada, consultas parametrizadas en toda la app) y reportó 11 hallazgos. Bloqueantes: (1) faltaba el tag `entrega-2`; (2) el diagrama ER conectaba la relación `Registra` entre USUARIO y PRODUCTO, cuando la FK real del DDL es `movimiento.id_usuario`; (3) faltaba el atributo `requiere_vencimiento` en PRODUCTO; (4) PNG/PDF del ER desactualizados respecto al `.drawio`; (5) certificación firmada por un solo integrante; (6) `README.md` enlazaba nombres de archivo del diagrama que no existen; (7) el encabezado de `sql/dml/001_seed.sql` citaba una ruta inexistente de casos de prueba. No bloqueantes: seed por debajo de 50 registros/tabla, grupo de 2 integrantes, y despliegue en internet (S5) pendiente para la Entrega 4. |
| **Validación del grupo** | El equipo revisó los 11 hallazgos uno por uno y aprobó el plan de corrección. **La corrección del diagrama ER (hallazgos 2 y 3) la hizo el equipo a mano en draw.io**, no la IA: la IA solo señaló la incoherencia contra el DDL y el equipo reconectó el rombo `Registra` a MOVIMIENTO, agregó `requiere_vencimiento` y re-exportó PNG y PDF. Se rechazó ampliar el seed a 50 registros dentro de esta entrega: el criterio del equipo es que el catálogo real del laboratorio vale más que relleno sintético para los 2 CRUD que se ponderan aquí, y el volumen se completa con el DML de la Entrega 3 — quedó documentado como diferido, no como omitido. La IA **no** ejecutó la base de datos en esta sesión, así que el resultado 15/15 de las pruebas del 30/08 se mantuvo como evidencia previa del equipo y no se re-verificó ni se presentó como re-verificado. |
| **Estándares aplicados** | R3 (commits descriptivos en formato convencional), R4 (participación visible: los commits de cierre quedan a nombre de Cristopher, frente al commit único de José Eduardo del 31/08), R5 (tag `entrega-2`), R8 (acceso del catedrático), D1/D4 (rutas y referencias de la documentación verificadas una por una), D3 (diagrama ER en editable + PNG + PDF coherentes entre sí y con el DDL), S3 (encabezados SQL con dependencias correctas). |
| **Responsable** | Cristopher Alexis Castellanos Paz |

---

### Registro de Bitácora IA — Diagrama relacional y normalización en Excel

| Campo | Detalle |
|---|---|
| **Fecha** | 01/09/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | El equipo planteó que el catedrático enseñó la normalización en hoja de cálculo (tabla original → identificar en qué forma normal está → aplicar 1FN, 2FN y 3FN mostrando las tablas de cada paso) y preguntó si el entregable debía tener ese formato. |
| **Prompt utilizado** | "Para la normalización el ingeniero quería que la hiciéramos en Excel... ahí estaba la tabla original y se identificaba si estaba ya en alguna de sus 3 formas normales... y así hasta llegar a su tercera forma normal, pero no sé qué opinas." |
| **Resultado obtenido** | La IA verificó que la consigna (requisito 5.3) no exige formato para la normalización, y que `normalizacion-3fn.md` ya seguía el mismo procedimiento del ejercicio de clase. Recomendó conservar el `.md` y **añadir** la versión en hoja de cálculo. Al revisar el estándar **D3** ("Diagramas: ER y relacional en editable + PNG/PDF") detectó además un hallazgo nuevo: el modelo relacional solo existía como documento markdown, sin diagrama — `docs/diagramas/` únicamente contenía el ER. Generó `ENTREGA2_NORMALIZACION_3FN.xlsx` (tabla original sin normalizar, análisis de forma normal en cada etapa, tablas resultantes de 1FN/2FN/3FN y verificación final de las 11 tablas) y `DIAGRAMA-RELACIONAL.drawio` (11 tablas con columnas, tipos, PK/FK/UNIQUE/CHECK y las 11 relaciones con su ON DELETE). |
| **Validación del grupo** | El equipo decidió incorporar ambos archivos y mover el tag `entrega-2` para incluirlos. La exportación a PNG y PDF del diagrama relacional la hizo el equipo a mano en draw.io, igual que con el ER — la IA no puede renderizar `.drawio`. El contenido del Excel se contrastó celda por celda contra `normalizacion-3fn.md` y `sql/ddl/001_schema.sql` para que las tres fuentes digan lo mismo. |
| **Estándares aplicados** | D3 (diagramas ER **y relacional** en editable + PNG/PDF — el hallazgo que motivó el diagrama), D2 (nombre de archivo con la entrega: `ENTREGA2_...`), requisito 5.3 (normalización hasta 3FN demostrada con ejemplo). |
| **Responsable** | Cristopher Alexis Castellanos Paz |

---

## Declaración
La IA se utilizó como apoyo de análisis, corrección de inconsistencias documentales y organización de carpetas — no como sustituto de las decisiones del equipo. Toda propuesta fue presentada con su justificación antes de aplicarse, y las decisiones de fondo (SGBD) fueron tomadas por el equipo.
