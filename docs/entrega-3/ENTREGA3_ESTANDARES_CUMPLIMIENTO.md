# Cumplimiento de estándares de calidad — Entrega 3

Actualiza `docs/entrega-2/estandares-cumplimiento.md` con lo construido en esta entrega. Cada fila cita dónde se verifica. Lo que **no** se cumple se declara.

---

## Sección 6.2 — Estándares de calidad SQL

| # | Estándar | Estado | Evidencia verificable |
|---|---|---|---|
| **S1** | Nomenclatura `snake_case` | ✅ Cumple | Tablas, columnas, vistas (`vw_*`), funciones (`fn_*`), procedimientos (`sp_*`), triggers (`trg_*`) y roles (`rol_*`) en `snake_case` con prefijo que indica el tipo de objeto. |
| **S2** | Un script, un propósito | ✅ Cumple | 10 scripts en 6 carpetas: `ddl/` (estructura), `dml/` (4 scripts de datos), `triggers/`, `procedures/`, `views/` (2) y `security/`. Ninguno mezcla propósitos: por ejemplo, los permisos de las vistas nuevas se otorgan en `security/001_roles.sql`. |
| **S3** | Encabezado con archivo, autor, descripción y dependencias | ✅ Cumple | Los **10 de 10** scripts SQL abren con el bloque *Archivo, Propósito, Proyecto, Autor, Descripción, Dependencias, SGBD, Ejecutar*. Los dos scripts generados (`002_carga_catalogo.sql`, `004_carga_movimientos.sql`) indican además que no se editan a mano y cuál es su generador. |
| **S4** | Integridad referencial con `ON DELETE` / `ON UPDATE` | ✅ Cumple | Sin cambios desde la Entrega 2: 11 de 11 FK con ambas cláusulas. |
| **S5** | Instalación: desplegado en internet | ✅ Cumple | Desplegado el 26/09/2026 en **https://inventario-laboratorio-03s7.onrender.com**: la app en Render (gunicorn) y la base en Neon (PostgreSQL 17), ambas en US East (Ohio). La base de producción se instaló con los mismos scripts del repositorio y quedó idéntica a la local (806 productos, 5,839 movimientos, 0 inconsistencias, Q524,714.36). Procedimiento reproducible en `INSTALL.md`, paso 8. |
| **S6** | Triggers y procedimientos con la regla de negocio explicada | ✅ Cumple | Cada trigger y procedimiento documenta en su encabezado y en comentarios la regla que aplica (RN-01 a RN-04, RN-07, RN-08, RN-09) y por qué se implementa así. La función de valorización explica el método del costo promedio ponderado con su fórmula. |
| **S7** | Sin redundancia | ✅ Cumple | Ninguna tabla guarda existencias por producto, faltantes, días para vencer ni costos promedio: todo se calcula en vistas y funciones (`vw_existencia_producto`, `vw_inventario_bajo`, `vw_lotes_por_vencer`, `fn_kardex_promedio`). La única cifra almacenada es `lote.cantidad_disponible`, que mantiene el trigger y se verifica contra el historial (0 diferencias en los 1,188 lotes). |
| **S8** | SQL generado por IA revisado y probado | ✅ Cumple | Cada objeto se probó en `BEGIN … ROLLBACK` contra la base real antes del commit (triggers, procedimientos, roles, vistas, kardex). La carga de datos se probó en un esquema aislado, y durante esa prueba el trigger de existencia detectó un error del propio generador, que se corrigió. Registro en `docs/bitacora-ia/ENTREGA3_BITACORA_IA.md`. |

**Resultado: los 8 estándares SQL se cumplen.** Respecto a la Entrega 2, S6 pasó de "no aplica" a "cumple" y S5 de "no cumple" a "cumple" con el despliegue en internet.

---

## Sección 6.3 — Estándares de código de aplicación

| # | Estándar | Estado | Evidencia verificable |
|---|---|---|---|
| **A1** | Separación de capas | ✅ Cumple | `config.py` (variables de entorno), `db.py` (único acceso a PostgreSQL, adopción del rol de BD, paginación, llamadas a procedimientos), `routes/` (10 módulos, uno por área), `templates/` (37 plantillas) y `static/` (estilos, fuentes, favicon). Las reglas de negocio viven en la base de datos, no en Python. |
| **A2** | Errores comprensibles, sin SQL crudo | ✅ Cumple | `db.mensaje_error()` muestra solo los mensajes de reglas de negocio (SQLSTATE P0001, escritos para el usuario) y reemplaza cualquier otro error por un texto genérico. Páginas propias para 403, 404 y 500. |
| **A3** | Validación de entrada | ✅ Cumple | Validación en el servidor en cada formulario: obligatorios, números con máximo 2 decimales, fechas, formato de NIT, correo, usuario y contraseña. El producto de las entradas y salidas debe existir y estar activo. |
| **A4** | Consultas parametrizadas | ✅ Cumple | Las 91 llamadas a la base pasan los datos del usuario como parámetros (`%s`). Las 15 consultas que se arman con f-string solo concatenan fragmentos fijos del código (condiciones del `WHERE` elegidas de una lista cerrada); ningún texto escrito por el usuario entra en el SQL. |
| **A5** | Código legible, responsabilidad única | ✅ Cumple | 86 funciones con nombres del dominio (`entrada`, `salida`, `alternar_estado`, `_es_ultimo_admin_activo`, `_producto_por_texto`). La más larga tiene 60 líneas (`informes.salidas`, casi toda consulta SQL). Macros de plantilla reutilizables (`_macros.html`, `_iconos.html`) en lugar de repetir HTML. |
| **A6** | Documentación de las funciones que acceden a la BD | ✅ Cumple | Los 14 módulos Python abren con un docstring que explica su responsabilidad, los requerimientos que cubren y qué rol puede usarlos. Las decisiones no obvias llevan comentario (por qué `SET ROLE` se confirma con `commit` inmediato, por qué las salidas se valorizan con el kardex). |

**Resultado: los 6 estándares de aplicación se cumplen.**
