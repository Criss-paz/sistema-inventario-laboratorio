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

### Registro de Bitácora IA

| Campo | Detalle |
|---|---|
| **Fecha** | 26/09/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Llevar la aplicación web al 70%: control de acceso por rol y módulos principales. |
| **Prompt utilizado** | "Sí, por favor continuemos" (continuar con la web después de cargar los datos reales). Luego: "donde verifico los usuarios y los roles, eso no lo veo" y "no me despliega las salidas aparte y las entradas aparte". |
| **Resultado obtenido** | Control de acceso en dos capas: `rol_requerido()` en la app y `SET ROLE` en cada conexión, para que PostgreSQL aplique los permisos aunque la app fallara. Módulos de Movimientos (entradas y salidas por procedimiento, con pestañas separadas), Lotes, Proveedores, Exámenes, Usuarios y roles, y búsqueda y paginación en Productos. Los mensajes de los triggers llegan tal cual al usuario. Se corrigió además una redirección abierta en el login (`?next=` a sitios externos). |
| **Validación del grupo** | Pruebas automatizadas con los 3 usuarios contra la base real, con las escrituras revertidas. El equipo detectó dos faltantes que la IA no había cubierto: el módulo de usuarios (RF-03, RF-04) y la separación visible de entradas y salidas. Ambos se agregaron. |
| **Estándares aplicados** | RF-03 a RF-05, RF-11 a RF-28, RF-36 a RF-39, A2, A3, A4, RNF-06, RNF-17. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA

| Campo | Detalle |
|---|---|
| **Fecha** | 26/09/2026 |
| **Herramienta** | Claude Code (Opus) con las skills de diseño redesign-skill, frontend-design, impeccable y ui-ux-pro-max |
| **Objetivo** | Rediseñar la interfaz para que se vea profesional. |
| **Prompt utilizado** | "¿Puedes rediseñar para que se vea profesional utilizando todas las skill?" |
| **Resultado obtenido** | Tipografía Atkinson Hyperlegible (legible para códigos y lotes), alojada en la app; menú lateral por tarea; íconos SVG propios en lugar de emojis; un solo color de acento y colores de estado; login en dos paneles; números de lote con aspecto de etiqueta de reactivo. |
| **Validación del grupo** | Revisión con capturas reales en escritorio (1440 px) y celular (390 px). Se corrigieron los problemas que aparecieron: desborde horizontal en celular, fechas partidas en dos líneas, botones apilados y unidades sin concordancia ("2 unidad"). |
| **Estándares aplicados** | RNF-09, RNF-18, A1. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA

| Campo | Detalle |
|---|---|
| **Fecha** | 26/09/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Generar reportes de inventario con valuación por costo promedio ponderado. |
| **Prompt utilizado** | "…generar reportes, en el cual se despliegue… el inventario, reporte de entradas, reporte de salidas, método de inventario que sea calculado por promedio ponderado". Corrección posterior: el inventario debe mostrar código, producto, presentación, precio unitario, precio total y existencias actuales, y debe haber una sola opción de reportes donde el usuario elija el tipo. |
| **Resultado obtenido** | En la base: `fn_kardex_promedio` (promedio ponderado móvil) y `vw_valorizacion_inventario`. En la web: pantalla única de reportes con 9 tipos (inventario, entradas, salidas, kardex, proveedores, pruebas, catálogo, inventario bajo, vencimientos), CSV para Excel e impresión. |
| **Validación del grupo** | El promedio se comprobó a mano (colesterol HDL: 7 a Q900 + 5 a Q600 = Q775). El saldo del kardex coincide con la existencia de los 806 productos. Comprobación contable: compras − costo de lo consumido = inventario valorizado, con una diferencia de Q0.06 por redondeo. El equipo corrigió las columnas del reporte de inventario y pidió unificar los reportes en una sola pantalla. |
| **Estándares aplicados** | RF-33, RF-34, S6, S7. |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA

| Campo | Detalle |
|---|---|
| **Fecha** | 26/09/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Documentación de cierre: matriz de trazabilidad v2, casos de prueba, `AVANCE_WEB.md`, estándares y README. |
| **Prompt utilizado** | "Sí, puedes iniciar, necesitamos avanzar por favor." |
| **Resultado obtenido** | Matriz con los 39 RF, 18 RN y 18 RNF. 8 casos de prueba sobre un producto de prueba (`PRUEBA-CP3`) para no alterar el inventario real. Estándares actualizados: S6 pasa a "cumple"; S5 (despliegue) sigue pendiente y se declara. |
| **Validación del grupo** | Los resultados esperados de los 8 casos salen de ejecutarlos contra la base real en una transacción revertida. **Pendiente:** la ejecución manual de los casos con capturas, a cargo de Cristopher Alexis Castellanos Paz. |
| **Estándares aplicados** | Consigna, sección 5 (casos de prueba y matriz de trazabilidad). |
| **Responsable** | José Eduardo Escobar |

---

### Registro de Bitácora IA — Despliegue en producción

| Campo | Detalle |
|---|---|
| **Fecha** | 26/09/2026 |
| **Herramienta** | Claude Code (Opus) |
| **Objetivo** | Publicar el sistema en internet (estándar S5) con la base de datos en la nube, conservando las reglas de negocio, la seguridad por roles y los datos reales. |
| **Prompt utilizado** | "Sí necesito con Render y Neon, pero como el repositorio lo tiene Cris, ¿puedo trabajarlo yo?", seguido de la guía paso a paso y la decisión de publicar el inventario real completo. |
| **Resultado obtenido** | Aplicación en **https://inventario-laboratorio-03s7.onrender.com**: Flask con gunicorn en Render y PostgreSQL 17 en Neon, ambos en US East (Ohio). Procedimiento reproducible en `INSTALL.md`, paso 8. |
| **Responsable** | José Eduardo Escobar (cuentas de Render y Neon); IA como apoyo técnico |

**Decisiones técnicas y su justificación**

| Decisión | Alternativas consideradas | Por qué se eligió |
|---|---|---|
| Render (app) + Neon (base de datos) | Render con su propia base; Railway; Supabase | Neon ofrece PostgreSQL completo, con triggers, funciones PL/pgSQL y `CREATE ROLE`, que el proyecto necesita. El plan gratuito de Render no incluye una base persistente a largo plazo. |
| Misma región (Ohio) para ambos | Regiones distintas | Cada petición hace varias consultas; en la misma región la latencia entre app y base es de milisegundos. En producción las páginas responden en 0.2 a 1.2 s. |
| Conexión **directa**, sin el pooler de Neon | Conexión con pooling (PgBouncer) | La app adopta el rol de cada usuario con `SET ROLE` por conexión. En modo transacción, el pooler puede entregar esa conexión a otra petición y romper el control de acceso. Se priorizó la seguridad sobre la escalabilidad. |
| Despliegue desde la URL pública del repositorio | Conectar la cuenta de GitHub del dueño; hacer un fork | El repositorio pertenece a otro integrante. La URL pública permite desplegar sin pedir permisos sobre su cuenta ni mantener una copia paralela. Costo: cada despliegue se dispara a mano. |
| `DATABASE_URL`, `APP_SECRET` y `APP_ENV` como variables de entorno | Archivo de configuración versionado | Ninguna credencial entra al repositorio (R6). |
| Usuarios de producción con contraseñas aleatorias | Reutilizar los de `seed_usuarios.py` | Las contraseñas de desarrollo son públicas en el repositorio; en producción se generaron nuevas y se entregaron por un canal privado. |
| Script de roles independiente del nombre del usuario | Mantener `GRANT … TO usuario_app` | En Neon el dueño se llama `neondb_owner`. El script otorga los roles al dueño de las tablas, lo que permite usar el mismo archivo en local y en la nube. |

**Riesgos identificados y mitigación**

| Riesgo | Mitigación |
|---|---|
| Falsificación de la sesión | La app no arranca en producción sin `APP_SECRET` propia. Cookie de sesión `HttpOnly`, `SameSite=Lax` y `Secure` (solo HTTPS). |
| URL incorrectas detrás del proxy de Render | `ProxyFix` toma el esquema y el host reales de `X-Forwarded-*`. |
| Uso del servidor de desarrollo en internet | gunicorn con 2 workers y tiempo límite de 60 s. |
| Exposición de datos del laboratorio | Publicación autorizada por el equipo (inventario real). Todo el contenido exige inicio de sesión, y los proveedores que son personas siguen anonimizados. |
| Credencial de la base compartida durante la configuración | Queda pendiente rotar la contraseña de Neon (**Reset password**) y actualizar `DATABASE_URL` en Render. |
| Instancia gratuita que se apaga tras 15 min sin uso | Documentado. Antes de la defensa se abre la página con un minuto de anticipación. |

**Validación del grupo**
- La base de Neon se instaló con los mismos scripts del repositorio y se comparó con la local: 806 productos, 1,188 lotes, 5,839 movimientos, 0 inconsistencias entre lotes e historial, 0 textos corruptos y el mismo valor de inventario (Q524,714.36).
- Permisos en la base de producción: `rol_consulta` no puede modificar productos y `rol_administrador` no puede leer contraseñas.
- Prueba del sitio público con los 3 usuarios: 48 comprobaciones de carga de páginas, permisos por rol (403 donde corresponde), cookie segura, rechazo de las contraseñas de desarrollo, reportes y exportación CSV. La única diferencia detectada fue un error del propio script de prueba (buscaba el encabezado `Location` con mayúscula), no de la aplicación.

**Estándares aplicados:** S5, R6, A1, RNF-01, RNF-06, RNF-17.

---

## Declaración
La IA se utilizó como apoyo de implementación y documentación, no como sustituto de las decisiones del equipo. Las decisiones sobre los datos reales (qué corregir, qué rechazar, qué anonimizar) las tomó el equipo con la justificación presentada por la IA.
