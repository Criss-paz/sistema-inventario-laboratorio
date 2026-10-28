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
| **Validación del grupo** | Se confirmó en el código que ningún procedimiento ni pantalla escribía en `proveedor_producto` (solo `sql/dml/002_carga_catalogo.sql`). El equipo aprobó cerrar las dos brechas y tomar como referencia de ideas otro proyecto del integrante José Eduardo Escobar, nacido de este sistema (en adelante, *el proyecto de referencia*). |
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
| **Prompt utilizado** | El mismo de la entrada anterior, con el repositorio del proyecto de referencia como ejemplo ("puedes tomar de ejemplo este repo"). |
| **Resultado obtenido** | `web/respaldo.py` (capa de servicio, también ejecutable por línea de comandos) y la pantalla Administración → Respaldo, solo para el Administrador. Genera un `.sql` con bloques `COPY` (el formato de `pg_dump`), leído en una sola foto `REPEATABLE READ` de solo lectura. Al restaurar apaga los triggers solo durante la carga, todo en una transacción, y ajusta las identidades. **Del proyecto de referencia se tomó la idea**, no el código: ese proyecto usa `pg_dump` con un plan B en Python, y aquí se usa directamente el plan B, porque Render no trae un `pg_dump` compatible con Neon 17. |
| **Validación del grupo** | Se restauró el respaldo en un esquema aislado con tablas y triggers y se comparó tabla por tabla con un hash md5 de todas las filas: **11 de 11 idénticas**, triggers activos otra vez y secuencias en el valor correcto (CP4-13). **Corrección:** la primera versión de la pantalla respondía 403, porque contaba filas de `movimiento`, que el rol administrador no puede leer directamente. Se dejaron los permisos como estaban y se cuenta desde `vw_historial_movimientos`. **Corrección:** `respaldo.py` abría su propia conexión, contra la regla de `db.py`; se movió a `db.conexion_sin_rol()` y se verificó que el archivo generado fuera idéntico. |
| **Estándares aplicados** | A1 (servicio separado de la ruta), A2 (`RespaldoError` con mensaje para el usuario), A4 (identificadores con `psycopg.sql.Identifier`), A6, S7 (solo datos; la estructura se reinstala desde `sql/`), S8, R6 (`.gitignore` excluye los respaldos descargados). |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Seguridad: cambio de contraseña y encabezados

| Campo | Detalle |
|---|---|
| **Fecha** | 20/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Incorporar las protecciones del proyecto de referencia que aplican a este sistema. |
| **Prompt utilizado** | Continuación de "completa toda la fase 4" con el proyecto de referencia como ejemplo. |
| **Resultado obtenido** | "Cambiar mi contraseña" para los 3 roles, confirmando la actual. Encabezados `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` y HSTS en producción. Rechazo de los POST con `Origin` ajeno, como segunda barrera contra CSRF. **Se descartaron** el bloqueo por intentos fallidos (con 2 procesos de gunicorn, un contador en memoria no sería confiable y una tabla nueva excedía el alcance) y la verificación en dos pasos del proyecto de referencia. Quedan como trabajo futuro en el manual técnico. |
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

### Registro de Bitácora IA — Interfaz con el diseño del proyecto de referencia

| Campo | Detalle |
|---|---|
| **Fecha** | 21/10/2026 |
| **Herramienta** | Claude Code (Opus) + Playwright con Edge para verificar |
| **Objetivo** | Que la aplicación tenga el diseño y la experiencia del proyecto de referencia, del integrante José Eduardo Escobar, que nació de este sistema, sin cambiar la base de datos ni la lógica. |
| **Prompt utilizado** | "Yo necesitaba que lo dejaras similar a [el proyecto de referencia], ya que [ese proyecto] fue una idea nacida de este proyecto … tomando en cuenta todo lo que tienes ya trabajado en este sistema". Antes de empezar, la IA preguntó el alcance; el equipo eligió **diseño y experiencia** (no los módulos del proyecto de referencia, que habrían cambiado el modelo de datos a días de la entrega) y **conservar el nombre** del sistema. |
| **Resultado obtenido** | Nueva `style.css` a partir del sistema visual del proyecto de referencia, conservando los nombres de clase de las 40 plantillas: tinta y ámbar, Schibsted Grotesk y JetBrains Mono, tema claro y oscuro. `base.html` con menú oscuro, barra superior con búsqueda `Ctrl K` y menú de usuario. `app.js`, sin librerías: tema, menús, avisos flotantes, búsqueda y fichas emergentes. Panel "Bodega hoy" con indicadores, calendario de vencimientos, *Reponer primero* y actividad reciente, todo desde las vistas de la base. Inicio de sesión dividido; productos con medidor de existencia; ruta `reportes.buscar` (JSON). |
| **Validación del grupo** | Capturas de cada pantalla en claro, oscuro y celular, revisadas una por una. Se corrigió:<br>• un desfase entre las columnas del Panel;<br>• la tabla de productos, demasiado ancha (de 11 a 7 columnas);<br>• un bloque informativo sin estilo en la devolución;<br>• un plural ("0 unidad").<br>Regresión: 183 verificaciones, 0 fallas. `Ctrl K` (incluido `Enter` hacia el kardex), el tema que se recuerda, el menú y las fichas del calendario se probaron en Edge. Los 12 flujos del manual se ejecutaron otra vez con la interfaz nueva (12 de 12) y sus capturas reemplazaron las del manual. Dos fallas de los guiones de prueba (un clic que cayó en un punto del calendario y una lectura de dirección antes de terminar la navegación) se identificaron como errores del guion, no de la aplicación. |
| **Estándares aplicados** | A1 (estilos y comportamiento en `static/`, sin lógica de negocio), A2 (avisos sin texto técnico), A4 (búsqueda parametrizada), A6; S7 (las cifras del Panel salen de vistas); D1, D3; R6 (la búsqueda exige sesión). La declaración de integridad indica qué se tomó del proyecto de referencia. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Corrección de entradas con registro

| Campo | Detalle |
|---|---|
| **Fecha** | 21/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Poder corregir los datos de una entrada mal digitada sin eliminarla. |
| **Prompt utilizado** | "Las entradas tienes que corregir porque no se pueden eliminar, solo corregir datos, entonces enfócate en ello también". La IA mostró cómo lo hace el proyecto de referencia (edición directa, sin rastro) y preguntó; el equipo eligió **corregir con registro** para no romper RN-09. |
| **Resultado obtenido** | Tabla `correccion_entrada` (ddl/004), triggers/003 (excepción controlada en la inmutabilidad, ajuste del lote por la diferencia, correcciones inmutables), `sp_corregir_entrada` (procedures/003), `vw_correcciones_entrada` (views/005), permisos solo para el Administrador (security/003) y la pantalla *Corregir entrada* con la tabla de correcciones en la ficha. Reglas nuevas RN-25 y RN-26. |
| **Validación del grupo** | Pruebas en `psql` dentro de `BEGIN … ROLLBACK`: subir, bajar de más (mensaje con el mínimo posible), precio, vencimiento, errores de validación, permisos por rol, y `UPDATE` y `DELETE` directos aun con la variable de sesión activa. **Corrección:** el trigger referenciaba `NEW.id_lote` en una sola condición; al borrar una corrección daba un error técnico en vez del mensaje de inmutabilidad. Se anidaron los `IF`. **Corrección:** la vista quedó al principio dentro del script del procedimiento; se movió a `views/005` (S2). **Error de la prueba automatizada:** una versión suponía valores viejos de la entrada CP4B y registró 2 correcciones reales; quedan en la base de desarrollo, como exige RN-25, y la prueba se corrigió (documentado en los casos de prueba). Prueba final: 16 verificaciones y CP4-15 en Edge. |
| **Estándares aplicados** | S1–S4 (FK con `RESTRICT`), S6, S7 (el kardex se recalcula desde el historial), S8; A2, A3, A4, A6. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Inventario al día: movimientos del 24/09 al 21/10/2026

| Campo | Detalle |
|---|---|
| **Fecha** | 21/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Continuar el inventario real cargado en la Entrega 3 (registro en papel que el equipo pasó a Excel para la entrega de inventario trimestral, ver `ENTREGA3_BITACORA_IA.md`) con lo que el laboratorio registró después del 23/09/2026. Ese tramo ya no se anotó en papel ni en el Excel: el laboratorio lo llevó en el sistema de bodega del proyecto de referencia, con la misma numeración E/S del papel. |
| **Prompt utilizado** | "Si yo tengo una base de datos puedes aplicarla? … [el sistema de bodega] se está trabajando con ello". El equipo entregó un respaldo `pg_dump` de esa base de datos y eligió **agregar lo nuevo** (no reemplazar). |
| **Resultado obtenido** | El respaldo quedó fuera del repositorio: se movió a la carpeta ignorada y se agregó el patrón a `.gitignore`. Un generador en `sql/dml/` reutiliza las reglas de `generar_carga.py` (las mismas de la carga del Excel en la Entrega 3: categorías, proveedores, FEFO) y produce el script `005` de `sql/dml/`: 205 entradas, 516 salidas, 108 lotes, 8 productos y 1 proveedor nuevos, y el reporte de la carga en `docs/entrega-4/`. |
| **Validación del grupo** | Se confirmó que el respaldo conserva la numeración del papel (código E/S idéntico al del Excel de la Entrega 3), para no duplicar. 12 registros antiguos sin equivalente resultaron ser servicios o rechazos de la Entrega 3 y se dejaron fuera. Se revisó que el script no publique nombres de personas (solo áreas y empresas). Se respaldó la base antes de cargar. Resultado: 0 lotes incoherentes; **804 de 813** productos con la misma existencia que la base de origen. Las 9 diferencias se explicaron: 2 entradas rechazadas por vencimiento anterior al ingreso, y 7 productos en los que el contador de existencia de la base de origen no coincide con sus propios movimientos (este sistema sí). Instalación desde cero de los 21 pasos: 814 productos, 6,560 movimientos y Q600,338.34. |
| **Estándares aplicados** | S2, S3 (script generado con encabezado), S7, S8; R6 (respaldo fuera del repositorio, sin datos personales). |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Número de documento para cada movimiento

| Campo | Detalle |
|---|---|
| **Fecha** | 26/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Que cada entrada y salida se identifique como en el laboratorio (E000001, S000001) y no por un número interno, y que la observación no repita de dónde se cargó el dato. |
| **Prompt utilizado** | "Cómo quito todo eso de las entradas y salidas … solo necesito que diga entrada y el número de entrada E00001 por ejemplo, al igual que salida S00001". La IA propuso dos alcances; el equipo eligió **número propio continuo** (los cargados conservan el suyo y los nuevos siguen el correlativo). |
| **Resultado obtenido** | `ddl/005_numero_documento.sql`: columna `movimiento.numero_documento` (NOT NULL, UNIQUE, CHECK de formato y de prefijo según el tipo, RN-27), relleno con el número que traía el texto de la observación y limpieza de ese texto (en las salidas queda el área). `triggers/004`: el número de cada movimiento nuevo, con un candado por tipo para que dos registros simultáneos no tomen el mismo y sin huecos si un registro falla. `views/006`: el número en `vw_historial_movimientos`. En la web: columna N.º en historial y lote, título de la ficha, kardex y su CSV, Panel y búsqueda `Ctrl K` por número. |
| **Validación del grupo** | Antes de migrar se comprobó que ningún código se repetía en el texto de las observaciones, y se respaldó la base. La migración desactiva el trigger de historial inmutable solo dentro de su transacción (único caso, documentado en el script). Una entrada y una salida nuevas, dentro de `BEGIN … ROLLBACK`, recibieron E001793 y S004790. **Corrección:** al probar en `psql`, `CALL` no admite subconsultas como argumento; se usaron variables. Instalación desde cero de 33 pasos: numeración de E000001 a E001790 y ninguna observación con el origen de la carga. En Neon: 0 movimientos sin número. |
| **Estándares aplicados** | S1, S2 (un script por propósito: ddl, trigger y vista por separado), S3, S6, S8; A1, A4; D1. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Roles con permisos editables

| Campo | Detalle |
|---|---|
| **Fecha** | 26/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Que el administrador pueda dar y quitar accesos a cada rol y crear roles nuevos, en lugar del reparto fijo en el código. |
| **Prompt utilizado** | "En los roles de usuario no puedo agregar opciones o quitar accesos". La IA mostró cómo lo resuelve el proyecto de referencia (permisos guardados como datos) y preguntó el alcance; el equipo eligió **editar accesos y crear roles**. |
| **Resultado obtenido** | `ddl/006_permisos.sql`: tablas `permiso` (11 permisos, cada uno con el nivel de PostgreSQL que necesita) y `rol_permiso` (N:M), con el reparto anterior como datos iniciales (RN-28). `procedures/004`: `fn_rol_bd`, que elige el rol de PostgreSQL más bajo que cubre los permisos del rol. `triggers/005`: el rol Administrador no se renombra ni se elimina (RN-29). En la web: `permiso_requerido()` y `tiene_permiso()` reemplazan los roles fijos en las 12 rutas y las plantillas; la tabla de permisos con casillas, y crear, renombrar y eliminar roles. Cada petición lee los permisos de la base: un cambio rige sin volver a iniciar sesión, y un usuario desactivado pierde la sesión. |
| **Validación del grupo** | Se mantuvieron las dos capas de control de acceso: la app aplica el permiso exacto y la base, por `SET ROLE`, el nivel. Prueba de 31 verificaciones: conceder un permiso a Consulta abre la pantalla sin volver a entrar y sube su rol de BD; quitarlo lo devuelve a 403; un rol con usuarios no se elimina; el Administrador no se renombra; nadie le quita a su propio rol el acceso a esta pantalla. **Corrección:** el primer diseño tomaba el rol de la sesión, que no existe en las sesiones abiertas antes de la actualización; se cambió por el que se lee de la base en cada petición. |
| **Estándares aplicados** | S1–S4 (FK con `ON DELETE CASCADE` justificado en `rol_permiso`), S6, S8; A1, A2, A3, A6; R6. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Bitácora de auditoría

| Campo | Detalle |
|---|---|
| **Fecha** | 26/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Saber quién hizo qué y cuándo en el sistema. |
| **Prompt utilizado** | "Necesito también agregar una bitácora, para ver quién hizo qué". |
| **Resultado obtenido** | `ddl/007_bitacora.sql`: tabla `bitacora` (RN-30). `triggers/006`: un trigger genérico `SECURITY DEFINER` en 12 tablas que guarda la fila creada o eliminada y, al modificar, solo los campos que cambiaron con su valor anterior y nuevo; nunca la contraseña. La app informa el usuario en cada conexión (`app.id_usuario`) y registra inicios de sesión, intentos fallidos, cierres y descargas de respaldo. `views/007` y la pantalla Administración → Bitácora, con filtros, frases legibles ("Concedió «Registrar salidas» al rol …") y CSV. La bitácora no se modifica ni se borra. El respaldo incluye las 3 tablas nuevas. |
| **Validación del grupo** | Se decidió auditar en la base y no solo en la app, para que quede registrado aunque el cambio se haga fuera de la aplicación (aparece como "Sistema"). Se excluyó la existencia de los lotes, que ya registran los movimientos, para no llenar la bitácora con cada entrada y salida dos veces. Se comprobó que ningún registro contiene el hash de una contraseña y que un `UPDATE` directo se rechaza. **Correcciones:** un rol eliminado aparecía como "rol #6"; ahora su nombre se toma de la propia bitácora. Una contraseña cambiada mostraba un valor anterior vacío; ahora solo dice "(cambiada)". En Neon se aplicaron las 3 migraciones en una sola ejecución del SQL Editor (68 instrucciones sin error) antes del redespliegue. |
| **Estándares aplicados** | S2, S3, S6, S8; A1, A2, A4, A6; R6 (sin contraseñas ni hashes en la bitácora). |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Revisión de cierre, instalación en segundo equipo y verificación de flujos

| Campo | Detalle |
|---|---|
| **Fecha** | 26/10/2026 |
| **Herramienta** | Antigravity (Google DeepMind) |
| **Objetivo** | Revisar el repositorio y los documentos de la Entrega 4 contra la consigna, actualizar la base de datos local del segundo equipo desde cero siguiendo `INSTALL.md`, verificar los flujos del manual de usuario y las pantallas nuevas (numeración, roles con permisos editables y bitácora) y cerrar la certificación. |
| **Prompt utilizado** | Se adjuntó el PDF de lineamientos del proyecto y se pidió: "tengo este proyecto con otro compañero, bien ahorita vamos ya por la entrega 4 puedes revisar el sistema, los documentos y carpetas para ver qué hace falta y me dices… haz todo lo que tú dices y mira lo que haga falta, el tag aún no lo hagas". |
| **Resultado obtenido** | 1) Auditoría completa del repositorio contra las secciones 6, 7, 8 y 11 de la consigna. Se detectaron y corrigieron 4 desajustes menores de documentación (`web/README.md` seguía indicando 70% y 11 módulos; `INSTALL.md` decía Entrega 3 en su encabezado; `README.md` y `docs/entrega-4/README.md` citaban 12 flujos en vez de los 15 actuales U-01 a U-15; `sql/dml/README.md` no sumaba `DEVOLUCION` en su consulta de coherencia). 2) Reconstrucción desde cero de la base local `inventario_laboratorio` en el segundo equipo (PostgreSQL 18.6, Python 3.13.14) en 11.0 s: 15 tablas, 8 vistas, 22 triggers, 814 productos, 1,296 lotes, 6,560 movimientos (`E000001` a `E001790`), 0 lotes incoherentes e inventario valorizado en Q600,338.34. 3) Verificación de los flujos U-01 a U-07, CP4-17 a CP4-19 y el despliegue en Render, registrada en `docs/casos-prueba/casos-prueba-entrega-4.md`. |
| **Validación del grupo** | En el segundo equipo la base seguía en la versión de la Entrega 3 (11 tablas y 5 vistas); tras ejecutar los pasos de `INSTALL.md` quedó idéntica a la instalación limpia y a producción (mismos conteos y Q600,338.34). Se comprobó que en una instalación limpia sin la salida de prueba de producción la última salida es `S004787` (en producción es `S004788` por la salida #5840 anulada antes de la carga de SIGAL). También se verificó que al conceder `REGISTRAR_SALIDAS` al rol Usuario de consulta su sesión abierta pasa de 403 a 200 sin volver a iniciar sesión, que al retirarlo vuelve a 403, y que ambos cambios quedan en la bitácora. |
| **Estándares aplicados** | R4 (commits propios de ambos integrantes), S5, S8, D1, D4; consigna, secciones 8 y 9.2. |
| **Responsable** | Cristopher Alexis Castellanos Paz |

---

### Registro de Bitácora IA — Eliminación de entradas por el Administrador

| Campo | Detalle |
|---|---|
| **Fecha** | 27/10/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Que el Administrador pueda eliminar una entrada registrada por error desde la aplicación y que el inventario se ajuste solo. |
| **Prompt utilizado** | Primero: "Como no se puede eliminar entradas únicamente desde la base de datos, dame el código para hacerlo desde el editor SQL en Neon". La IA entregó un bloque `DO` con protecciones y registro en la bitácora. Después: "¿Se puede agregar que el único que puede eliminar las entradas es el admin y que automáticamente, cuando elimine la entrada, ajuste el inventario?" |
| **Resultado obtenido** | `triggers/007`: segunda excepción controlada en `fn_historial_inmutable` (solo `DELETE` de entradas y su detalle mientras corre el procedimiento). `procedures/005`: `sp_eliminar_entrada`, que exige el rol Administrador, motivo, que no haya correcciones y que ninguna unidad haya salido; registra en la bitácora antes de borrar, resta del lote y borra el lote vacío (RN-31). `security/005`: solo `rol_administrador`. En la web: `solo_administrador`, botón en la ficha y pantalla de confirmación que muestra cómo queda cada lote. |
| **Validación del grupo** | Se decidió que fuera solo el rol Administrador y no un permiso concedible, como pidió el equipo, y se verifica también dentro del procedimiento. Se mantuvo la regla de no dejar existencias negativas: si ya salió algo, se rechaza y se ofrece Corregir entrada. Pruebas en `psql` con `BEGIN … ROLLBACK` y 17 verificaciones en la app. **Corrección:** la primera versión del procedimiento usaba `r` como variable y como alias de la tabla rol, y PostgreSQL lo rechazó; se renombró el alias. Instalación desde cero: 36 de 36 pasos. |
| **Estándares aplicados** | S2, S3, S6, S8; A2, A3, A4, A6; R6. |
| **Responsable** | José Eduardo Escobar |

---

# Parte 2 — Bitácora consolidada del proyecto

| Entrega | Archivo original | Registros | Herramientas | Responsables |
|---|---|---|---|---|
| 1 — Análisis, propuesta y diseño conceptual | `docs/bitacora-ia/Bitacora-IA.md` | 5 actividades | IA como apoyo de análisis y redacción | Equipo |
| 2 — Diseño lógico e implementación base | `docs/entrega-2/Bitacora-IA.md` | 13 | Claude Code (Opus) | José Eduardo Escobar, Cristopher Alexis Castellanos Paz |
| 3 — Implementación avanzada, seguridad y pruebas | `docs/bitacora-ia/ENTREGA3_BITACORA_IA.md` | 10 | Claude, Claude Code (Opus) | José Eduardo Escobar (8), Cristopher Alexis Castellanos Paz (2) |
| 4 — Integración, documentación y defensa | este archivo | 14 | Claude Code (Opus), Antigravity, Playwright | José Eduardo Escobar (13), Cristopher Alexis Castellanos Paz (1) |

### Para qué se usó la IA en cada etapa

| Etapa | Uso principal | Qué decidió el equipo |
|---|---|---|
| Análisis (E1) | Ordenar el problema, redactar requerimientos, proponer entidades | Alcance del sistema; qué módulos sí y cuáles no |
| Diseño (E2) | Modelo relacional, normalización, diccionario, DDL, primeros CRUD | PostgreSQL como SGBD; normalización en hoja de cálculo, como la enseñó el catedrático |
| Implementación (E3) | Triggers, procedimientos, roles, carga de los datos reales, web al 70%, despliegue | Usar el inventario real; qué errores del papel corregir y cuáles rechazar; anonimizar proveedores individuales; publicar en Render y Neon |
| Cierre (E4) | Completar el CRUD, respaldo, seguridad, interfaz nueva, corrección de entradas, inventario al día (24/09 al 21/10), número de documento, permisos editables, bitácora de auditoría, pruebas en navegador, manuales | Baja lógica en lugar de borrado; no ofrecer la restauración desde la app; qué protecciones del proyecto de referencia aplicar y cuáles no; su diseño sí, sus módulos no; corregir entradas con registro y no con edición directa; agregar (no reemplazar) los movimientos nuevos |

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
| 4 | Control de permisos que dependía de un dato de sesión inexistente en sesiones viejas | Revisión del flujo de sesiones abiertas antes de la actualización |
| 4 | Bitácora con "rol #6" y un valor anterior vacío en las contraseñas | Revisión visual de la pantalla en el navegador |

### Lección del proyecto

La IA aceleró mucho la escritura, pero los errores que importaban los encontraron **las pruebas contra la base de datos real y el navegador**, no la revisión del texto generado. Por eso cada entrega ejecutó sus casos antes de cerrar, y cada resultado registrado es lo que el sistema respondió.

---

## Declaración
La IA se usó como apoyo de implementación, prueba y documentación, no como sustituto de las decisiones del equipo. Toda propuesta se revisó y se probó contra la base de datos antes de incorporarse, y lo que se corrigió o rechazó queda registrado arriba.
