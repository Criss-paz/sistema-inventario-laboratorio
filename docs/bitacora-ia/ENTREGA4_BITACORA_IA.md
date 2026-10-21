# Bitácora de Utilización de IA — Entrega 4 (y consolidada)

## Proyecto
Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango

## Entrega
Entrega 4 — Integración, documentación y defensa oral

## Propósito
Este archivo tiene dos partes:
- **Parte 1:** registra el uso de IA en la Entrega 4 y continúa `ENTREGA3_BITACORA_IA.md`.
- **Parte 2:** consolida todas las entregas, como pide la rúbrica ("certificación y bitácora consolidada").

Las bitácoras de cada entrega se conservan sin cambios en su ubicación original.

---

# Parte 1 — Registros de la Entrega 4

### Registro de Bitácora IA — Diagnóstico de la Entrega 4

| Campo | Detalle |
|---|---|
| **Fecha** | 20/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Ponerse al día con el repositorio después de la Entrega 3 y determinar qué faltaba para la Entrega 4 según la consigna. |
| **Prompt utilizado** | "Puedes entrar al repo … y ponerte al día como lo tenemos", seguido del PDF de la consigna: "lo que necesito en la entrega 4, iniciemos". |
| **Resultado obtenido** | Sincronización del repositorio local (11 commits nuevos de Cristopher y el tag `entrega-3`). Diagnóstico contra la rúbrica de la Entrega 4, tabla por tabla, del CRUD de la aplicación. Dos brechas: `proveedor_producto` solo se llenaba con la carga inicial (aunque la pantalla decía que "los precios se registran con cada entrada") y `examen_laboratorio` no tenía forma de darse de baja. Además, RNF-11 (respaldos) seguía pendiente y faltaban todos los documentos de la entrega. |
| **Validación del grupo** | Se confirmó en el código que ningún procedimiento ni pantalla escribía en `proveedor_producto` (solo `sql/dml/002_carga_catalogo.sql`). El equipo aprobó cerrar las dos brechas y tomar como referencia de ideas el proyecto SIGAL del integrante José Eduardo Escobar. |
| **Estándares aplicados** | D4 (trazabilidad: cada brecha se ligó a su requerimiento: RF-39, RF-36/37, RNF-11). |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — CRUD de proveedor–producto y baja lógica de exámenes

| Campo | Detalle |
|---|---|
| **Fecha** | 20/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Completar el CRUD de las tablas principales (criterio de 0.5 pts de la rúbrica). |
| **Prompt utilizado** | "Necesitamos que completes toda la fase 4". |
| **Resultado obtenido** | **Proveedor–producto:** en la ficha del proveedor, el Administrador asigna un producto con su precio, lo cambia (`INSERT … ON CONFLICT DO UPDATE`) o lo quita. **Exámenes:** migración aditiva `sql/ddl/003_examen_estado.sql` (columna `estado`, `DEFAULT TRUE`, reejecutable), botones Dar de baja y Activar, y el informe de pruebas filtra los exámenes inactivos (regla nueva RN-24). |
| **Validación del grupo** | Se aplicó primero la migración en la base local. Pruebas con los 3 roles: 12 verificaciones de proveedor–producto y 14 de exámenes (permisos 403, validaciones, CSV, reactivación), dejando la base como estaba. **Corrección:** la IA numeró la regla como RN-23, pero ese número ya identificaba la valorización de devoluciones; se renumeró a RN-24 en un commit aparte. **Hallazgo:** la base de desarrollo no tenía las 6 migraciones de devolución de la Entrega 3; se aplicaron y verificaron. |
| **Estándares aplicados** | S1, S2, S3 (encabezado completo en `ddl/003`), S8; A2, A3, A4, A6. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Respaldo de la base de datos (RNF-11)

| Campo | Detalle |
|---|---|
| **Fecha** | 20/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Implementar el respaldo y la restauración de la base, último requerimiento pendiente. |
| **Prompt utilizado** | El mismo de la entrada anterior, con el repositorio SIGAL como ejemplo ("puedes tomar de ejemplo este repo"). |
| **Resultado obtenido** | `web/respaldo.py` (capa de servicio, también ejecutable por línea de comandos) y la pantalla Administración → Respaldo, solo para el Administrador. Genera un `.sql` con bloques `COPY` (el formato de `pg_dump`), leído en una sola foto `REPEATABLE READ` de solo lectura. Al restaurar apaga los triggers solo durante la carga, todo en una transacción, y ajusta las identidades. **De SIGAL se tomó la idea**, no el código: SIGAL usa `pg_dump` con un plan B en Python, y aquí se usa directamente el plan B, porque Render no trae un `pg_dump` compatible con Neon 17. |
| **Validación del grupo** | Se restauró el respaldo en un esquema aislado con tablas y triggers y se comparó tabla por tabla con un hash md5 de todas las filas: **11 de 11 idénticas**, triggers activos otra vez y secuencias en el valor correcto (CP4-13). **Corrección:** la primera versión de la pantalla respondía 403, porque contaba filas de `movimiento`, que el rol administrador no puede leer directamente. Se dejaron los permisos como estaban y se cuenta desde `vw_historial_movimientos`. **Corrección:** `respaldo.py` abría su propia conexión, contra la regla de `db.py`; se movió a `db.conexion_sin_rol()` y se verificó que el archivo generado fuera idéntico. |
| **Estándares aplicados** | A1 (servicio separado de la ruta), A2 (`RespaldoError` con mensaje para el usuario), A4 (identificadores con `psycopg.sql.Identifier`), A6, S7 (solo datos; la estructura se reinstala desde `sql/`), S8, R6 (`.gitignore` excluye los respaldos descargados). |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Seguridad: cambio de contraseña y encabezados

| Campo | Detalle |
|---|---|
| **Fecha** | 20/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Incorporar las protecciones de SIGAL que aplican a este sistema. |
| **Prompt utilizado** | Continuación de "completa toda la fase 4" con SIGAL como ejemplo. |
| **Resultado obtenido** | "Cambiar mi contraseña" para los 3 roles, confirmando la actual. Encabezados `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` y HSTS en producción. Rechazo de los POST con `Origin` ajeno, como segunda barrera contra CSRF. **Se descartaron** el bloqueo por intentos fallidos (con 2 procesos de gunicorn, un contador en memoria no sería confiable y una tabla nueva excedía el alcance) y la verificación en dos pasos de SIGAL. Quedan como trabajo futuro en el manual técnico. |
| **Validación del grupo** | 16 verificaciones: contraseña actual incorrecta, menos de 8 caracteres, confirmación distinta, contraseña igual a la anterior; la contraseña vieja deja de servir y la nueva entra; encabezados presentes; un POST de otro origen recibe 403 sin cambiar nada. Se revisó que la CSP no rompiera los scripts en línea propios. Regresión de las 43 pantallas con los 3 roles: 129 verificaciones, 0 fallas. |
| **Estándares aplicados** | A1, A2, A3, A6; RNF-04, RNF-17. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Casos de prueba de la Entrega 4 y defectos encontrados

| Campo | Detalle |
|---|---|
| **Fecha** | 20/10/2026 |
| **Herramienta** | Claude Code (Opus) + Playwright 1.64 conduciendo Microsoft Edge |
| **Objetivo** | Verificar en el navegador cada flujo del manual de usuario, la instalación desde cero y la restauración del respaldo. |
| **Prompt utilizado** | Continuación de "completa toda la fase 4". |
| **Resultado obtenido** | 14 casos, CP4-01 a CP4-14, con 30 capturas y 2 transcripciones (`docs/casos-prueba/evidencias-entrega-4/`). **14 de 14 aprobados.** La instalación desde cero en un esquema vacío corrió los 16 pasos de `INSTALL.md` en 12 s, con los mismos números de la Entrega 3 (Q524,714.36). |
| **Validación del grupo** | **Las pruebas encontraron 3 defectos** que la revisión del código no había visto: (1) el kardex mostraba la devolución en las columnas de Salidas, porque la plantilla repetía el patrón `if ENTRADA … else` que la Entrega 3 ya había corregido en SQL; (2) la ficha del lote mostraba la devolución con "−"; (3) la etiqueta decía "Devolucion" sin tilde. Se corrigieron y se volvieron a tomar las capturas. **Error del propio guion de prueba:** el primer intento hacía clic en el primer botón de envío de la página, que era "Cerrar sesión"; se detectó porque el resultado no tenía sentido y se corrigió antes de registrar resultados. También se midió (no se supuso) que en un celular de 390 px la página no se desborda. |
| **Estándares aplicados** | S8, D1, D4; casos con resultado obtenido copiado del sistema (`CP4-resultados.json`). |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Documentación final y diagramas

| Campo | Detalle |
|---|---|
| **Fecha** | 20/10/2026 |
| **Herramienta** | Claude Code (Opus); visor de diagrams.net en Edge para exportar los diagramas |
| **Objetivo** | Producir los documentos de la Entrega 4 y actualizar los diagramas. |
| **Prompt utilizado** | Continuación de "completa toda la fase 4". |
| **Resultado obtenido** | Manual de usuario (12 flujos con capturas), manual técnico (11 secciones, con respaldo, actualización de una base existente y mantenimiento), informe final, declaración de integridad, matriz de trazabilidad v3 con la tabla de CRUD por tabla, cumplimiento de estándares (6.1 a 6.4), guía de defensa, esta bitácora y el borrador de la certificación. `INSTALL.md` se actualizó: la verificación rápida esperaba 5 vistas y 4 triggers, cuando hoy hay 6 y 5. Diagramas: el relacional gana `id_movimiento_origen` (con su autorreferencia), `motivo`, el dominio `DEVOLUCION` y `examen_laboratorio.estado`; el ER gana la relación recursiva *Corrige* y los atributos nuevos. PNG y PDF reexportados. |
| **Validación del grupo** | Cada afirmación de los manuales se contrastó con la interfaz real: se corrigieron 4 etiquetas ("Entrar", "Corregir datos", los nombres de las pestañas de Lotes). Las cifras del documento de estándares se midieron sobre el código: 17/17 encabezados SQL, 12/12 FK, 16/16 módulos con docstring, 116 llamadas a la base. Se eliminaron del informe dos afirmaciones que no se podían respaldar: un total de restricciones y una "autorización del catedrático" no documentada. La respuesta sobre normalización de la guía se reescribió para que coincida con el ejemplo real de la Entrega 2. Se verificó la exportación de los diagramas: 1 página y todo el texto presente en los PDF. **Error corregido:** la primera exportación a PDF salía en blanco. También se quitó de la bitácora de la Entrega 2 la mención en texto de la contraseña local de la base (R6). |
| **Estándares aplicados** | D1, D2 (prefijo `ENTREGA4_`), D3, D4, R2, R6. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Interfaz con el diseño de SIGAL

| Campo | Detalle |
|---|---|
| **Fecha** | 21/10/2026 |
| **Herramienta** | Claude Code (Opus) + Playwright con Edge para verificar |
| **Objetivo** | Que la aplicación tenga el diseño y la experiencia de SIGAL, proyecto del integrante José Eduardo Escobar que nació de este sistema, sin cambiar la base de datos ni la lógica. |
| **Prompt utilizado** | "Yo necesitaba que lo dejaras similar a SIGAL, ya que SIGAL fue una idea nacida de este proyecto … tomando en cuenta todo lo que tienes ya trabajado en este sistema". Antes de empezar, la IA preguntó el alcance; el equipo eligió **diseño y experiencia** (no los módulos de SIGAL, que habrían cambiado el modelo de datos a días de la entrega) y **conservar el nombre** del sistema. |
| **Resultado obtenido** | Nueva `style.css` a partir del sistema visual de SIGAL, conservando los nombres de clase de las 40 plantillas: tinta y ámbar, Schibsted Grotesk y JetBrains Mono, tema claro y oscuro. `base.html` con menú oscuro, barra superior con búsqueda `Ctrl K` y menú de usuario. `app.js`, sin librerías: tema, menús, avisos flotantes, búsqueda y fichas emergentes. Panel "Bodega hoy" con indicadores, calendario de vencimientos, *Reponer primero* y actividad reciente, todo desde las vistas de la base. Inicio de sesión dividido; productos con medidor de existencia; ruta `reportes.buscar` (JSON). |
| **Validación del grupo** | Capturas de cada pantalla en claro, oscuro y celular, revisadas una por una. Se corrigió:<br>• un desfase entre las columnas del Panel;<br>• la tabla de productos, demasiado ancha (de 11 a 7 columnas);<br>• un bloque informativo sin estilo en la devolución;<br>• un plural ("0 unidad").<br>Regresión: 183 verificaciones, 0 fallas. `Ctrl K` (incluido `Enter` hacia el kardex), el tema que se recuerda, el menú y las fichas del calendario se probaron en Edge. Los 12 flujos del manual se ejecutaron otra vez con la interfaz nueva (12 de 12) y sus capturas reemplazaron las del manual. Dos fallas de los guiones de prueba (un clic que cayó en un punto del calendario y una lectura de dirección antes de terminar la navegación) se identificaron como errores del guion, no de la aplicación. |
| **Estándares aplicados** | A1 (estilos y comportamiento en `static/`, sin lógica de negocio), A2 (avisos sin texto técnico), A4 (búsqueda parametrizada), A6; S7 (las cifras del Panel salen de vistas); D1, D3; R6 (la búsqueda exige sesión). La declaración de integridad indica qué se tomó de SIGAL. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Corrección de entradas con registro

| Campo | Detalle |
|---|---|
| **Fecha** | 21/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Poder corregir los datos de una entrada mal digitada sin eliminarla. |
| **Prompt utilizado** | "Las entradas tienes que corregir porque no se pueden eliminar, solo corregir datos, entonces enfócate en ello también". La IA mostró cómo lo hace SIGAL (edición directa, sin rastro) y preguntó; el equipo eligió **corregir con registro** para no romper RN-09. |
| **Resultado obtenido** | Tabla `correccion_entrada` (ddl/004), triggers/003 (excepción controlada en la inmutabilidad, ajuste del lote por la diferencia, correcciones inmutables), `sp_corregir_entrada` (procedures/003), `vw_correcciones_entrada` (views/005), permisos solo para el Administrador (security/003) y la pantalla *Corregir entrada* con la tabla de correcciones en la ficha. Reglas nuevas RN-25 y RN-26. |
| **Validación del grupo** | Pruebas en `psql` dentro de `BEGIN … ROLLBACK`: subir, bajar de más (mensaje con el mínimo posible), precio, vencimiento, errores de validación, permisos por rol, y `UPDATE` y `DELETE` directos aun con la variable de sesión activa. **Corrección:** el trigger referenciaba `NEW.id_lote` en una sola condición; al borrar una corrección daba un error técnico en vez del mensaje de inmutabilidad. Se anidaron los `IF`. **Corrección:** la vista quedó al principio dentro del script del procedimiento; se movió a `views/005` (S2). **Error de la prueba automatizada:** una versión suponía valores viejos de la entrada CP4B y registró 2 correcciones reales; quedan en la base de desarrollo, como exige RN-25, y la prueba se corrigió (documentado en los casos de prueba). Prueba final: 16 verificaciones y CP4-15 en Edge. |
| **Estándares aplicados** | S1–S4 (FK con `RESTRICT`), S6, S7 (el kardex se recalcula desde el historial), S8; A2, A3, A4, A6. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Inventario al día con los datos de SIGAL

| Campo | Detalle |
|---|---|
| **Fecha** | 21/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Cargar lo que el laboratorio registró en SIGAL después del 23/09/2026. |
| **Prompt utilizado** | "Si yo tengo una base de datos puedes aplicarla? … SIGAL se está trabajando con ello". El equipo entregó un respaldo `pg_dump` de SIGAL y eligió **agregar lo nuevo** (no reemplazar). |
| **Resultado obtenido** | El respaldo quedó fuera del repositorio: se movió a la carpeta ignorada y se agregó el patrón a `.gitignore`. `sql/dml/generar_carga_sigal.py` reutiliza las reglas de `generar_carga.py` y genera `005_carga_sigal.sql`: 205 entradas, 516 salidas, 108 lotes, 8 productos y 1 proveedor nuevos. También genera `ENTREGA4_REPORTE_CARGA_SIGAL.md`. |
| **Validación del grupo** | Se confirmó que SIGAL conserva la numeración del papel (código E/S idéntico), para no duplicar. 12 registros antiguos sin equivalente resultaron ser servicios o rechazos de la Entrega 3 y se dejaron fuera. Se revisó que el script no publique nombres de personas (solo áreas y empresas). Se respaldó la base antes de cargar. Resultado: 0 lotes incoherentes; **804 de 813** productos con la misma existencia que SIGAL. Las 9 diferencias se explicaron: 2 entradas rechazadas por vencimiento anterior al ingreso, y 7 productos en los que el contador de SIGAL no coincide con sus propios movimientos (este sistema sí). Instalación desde cero de los 21 pasos: 814 productos, 6,560 movimientos y Q600,338.34. |
| **Estándares aplicados** | S2, S3 (script generado con encabezado), S7, S8; R6 (respaldo fuera del repositorio, sin datos personales). |
| **Responsable** | José Eduardo Escobar |

---

### Pendiente de registrar por el equipo

| Acción | Responsable |
|---|---|
| Revisión del manual de usuario contra la versión publicada en Render, y su registro aquí | Cristopher Alexis Castellanos Paz |
| Aplicación de `sql/ddl/003_examen_estado.sql` en Neon y redespliegue en Render | Quien administre las cuentas (José Eduardo Escobar) |

---

# Parte 2 — Bitácora consolidada del proyecto

| Entrega | Archivo original | Registros | Herramientas | Responsables |
|---|---|---|---|---|
| 1 — Análisis, propuesta y diseño conceptual | `docs/bitacora-ia/Bitacora-IA.md` | 5 actividades | IA como apoyo de análisis y redacción | Equipo |
| 2 — Diseño lógico e implementación base | `docs/entrega-2/Bitacora-IA.md` | 13 | Claude Code (Opus) | José Eduardo Escobar, Cristopher Alexis Castellanos Paz |
| 3 — Implementación avanzada, seguridad y pruebas | `docs/bitacora-ia/ENTREGA3_BITACORA_IA.md` | 10 | Claude, Claude Code (Opus) | José Eduardo Escobar (8), Cristopher Alexis Castellanos Paz (2) |
| 4 — Integración, documentación y defensa | este archivo | 9 | Claude Code (Opus), Playwright | José Eduardo Escobar |

### Para qué se usó la IA en cada etapa

| Etapa | Uso principal | Qué decidió el equipo |
|---|---|---|
| Análisis (E1) | Ordenar el problema, redactar requerimientos, proponer entidades | Alcance del sistema; qué módulos sí y cuáles no |
| Diseño (E2) | Modelo relacional, normalización, diccionario, DDL, primeros CRUD | PostgreSQL como SGBD; normalización en hoja de cálculo, como la enseñó el catedrático |
| Implementación (E3) | Triggers, procedimientos, roles, carga de los datos reales, web al 70%, despliegue | Usar el inventario real; qué errores del papel corregir y cuáles rechazar; anonimizar proveedores individuales; publicar en Render y Neon |
| Cierre (E4) | Completar el CRUD, respaldo, seguridad, interfaz de SIGAL, corrección de entradas, carga de SIGAL, pruebas en navegador, manuales | Baja lógica en lugar de borrado; no ofrecer la restauración desde la app; qué protecciones de SIGAL aplicar y cuáles no; diseño de SIGAL sí, módulos no; corregir entradas con registro y no con edición directa; agregar (no reemplazar) los datos de SIGAL |

### Errores de la IA detectados por la validación del equipo

| Entrega | Error | Cómo se detectó |
|---|---|---|
| 1 | El SGBD quedó como "Oracle" en la intención inicial | Revisión en la Entrega 2; se decidió PostgreSQL |
| 3 | El generador de la carga producía una salida mayor a la existencia | El propio trigger de existencia rechazó la carga |
| 3 | `fn_kardex_promedio` restaba las devoluciones | Saldo del kardex (2.00) distinto de la existencia real (4.00) |
| 4 | Regla numerada RN-23, número ya usado | Búsqueda del número en todo el repositorio |
| 4 | Pantalla de respaldo con 403 por un permiso que no existe | Prueba con el rol administrador |
| 4 | Plantillas que mostraban la devolución como salida | Casos CP4-06 y CP4-08 en el navegador |
| 4 | Etiquetas y afirmaciones de los documentos que no coincidían con el sistema | Contraste de cada afirmación con la interfaz y el código |
| 4 | Trigger de inmutabilidad con un error técnico al borrar una corrección | Prueba de `DELETE` en `psql` |
| 4 | Prueba automatizada que registró correcciones reales por suponer valores viejos | Conteo de correcciones antes y después |

### Lección del proyecto

La IA aceleró mucho la escritura, pero los errores que importaban los encontraron **las pruebas contra la base de datos real y el navegador**, no la revisión del texto generado. Por eso cada entrega ejecutó sus casos antes de cerrar, y cada resultado registrado es lo que el sistema respondió.

---

## Declaración
La IA se usó como apoyo de implementación, prueba y documentación, no como sustituto de las decisiones del equipo. Toda propuesta se revisó y se probó contra la base de datos antes de incorporarse, y lo que se corrigió o rechazó queda registrado arriba.
