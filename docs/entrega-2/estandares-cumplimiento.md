# Cumplimiento de estándares de calidad — Entrega 2

Este documento demuestra, estándar por estándar, dónde se cumplen las **Secciones 6.2 (calidad SQL)** y **6.3 (código de aplicación)** de la consigna oficial. Es el respaldo del criterio *"Estándares SQL + estándares web"* de la rúbrica de la Entrega 2.

Cada fila cita el archivo concreto donde se verifica. Los estándares que **no** se cumplen se marcan como tales: esta tabla no infla nada.

---

## Sección 6.2 — Estándares de calidad SQL

| # | Estándar | Estado | Evidencia verificable |
|---|---|---|---|
| **S1** | Nomenclatura: `snake_case` uniforme en tablas y columnas | ✅ Cumple | Las **11 tablas** y las **58 columnas** de `sql/ddl/001_schema.sql` están en `snake_case`. Ninguna usa mayúsculas, camelCase ni prefijos de tipo. Regla declarada en `modelo-relacional.md` (línea 5). |
| **S2** | Un script, un propósito: separar DDL, DML, vistas, triggers, procedimientos y seguridad | ✅ Cumple | Seis carpetas separadas bajo `sql/`. Hoy con contenido: `ddl/001_schema.sql` (solo estructura) y `dml/001_seed.sql` (solo datos). `views/`, `triggers/`, `procedures/` y `security/` existen con un `README.md` que declara su estado — se llenan en la Entrega 3. Ningún script mezcla propósitos. |
| **S3** | Encabezado con archivo, autor, descripción y dependencias | ✅ Cumple | Los dos scripts abren con un bloque de comentario que declara *Archivo, Propósito, Proyecto, Autor, Descripción, Dependencias, SGBD y Ejecutar*. Ver `001_schema.sql` líneas 1-16 y `001_seed.sql` líneas 1-17. |
| **S4** | Integridad referencial: toda FK con `ON DELETE` / `ON UPDATE` definida y documentada | ✅ Cumple | **11 de 11 FK** llevan ambas cláusulas. La justificación de cada una está en la tabla *"Resumen de integridad referencial"* de `modelo-relacional.md`: `RESTRICT` en el historial transaccional (RN-09), `CASCADE` solo en las dos tablas puente, que no tienen valor histórico. |
| **S5** | Instalación: desplegado en internet | ❌ **No cumple** | La aplicación solo corre en local (`INSTALL.md`). No hay despliegue público. Se planifica para la Entrega 4, cuando la rúbrica evalúa *"Instalación desde cero + app completa operativa"*. Se declara aquí abiertamente en lugar de omitirlo. |
| **S6** | Comentarios: triggers y procedimientos con la regla de negocio explicada | ➖ No aplica aún | No existen triggers ni procedimientos: la rúbrica los sitúa en la Entrega 3. Las reglas que los originarán (RN-01 a RN-04 y RN-07) ya están escritas y ubicadas en `modelo-relacional.md`, en las secciones de `lote` y `detalle_movimiento`. |
| **S7** | Sin redundancia: no duplicar datos calculables | ✅ Cumple | Demostrado formalmente con la normalización a 3FN (`normalizacion-3fn.md`). Ninguna tabla guarda un valor derivable de otra: `lote` no repite `nombre_producto` ni `nombre_categoria`, solo la FK `id_producto`. |
| **S8** | Validación IA: SQL generado por IA revisado y probado antes del commit | ✅ Cumple | `docs/entrega-2/Bitacora-IA.md` registra 14 sesiones con el campo *Validación del grupo* en cada una. El DDL y el DML se ejecutaron contra PostgreSQL 18 real antes de darse por buenos, y esa ejecución detectó y corrigió dos defectos reales (driver `psycopg2` → `psycopg`, y el `GRANT` de schema faltante en PostgreSQL 15+). |

**Resultado: 6 cumplen, 1 no cumple (S5), 1 no aplica todavía (S6).**

---

## Sección 6.3 — Estándares de código de aplicación

> La consigna marca el bloque completo de la Sección 6.3 para la **Entrega 4**. Se documenta aquí lo que ya está implementado, porque la rúbrica de la Entrega 2 sí pondera *"estándares web"* dentro de Calidad y estándares.

| # | Estándar | Estado | Evidencia verificable |
|---|---|---|---|
| **A1** | Separación de capas: configuración de BD separada de la interfaz | ✅ Cumple | Cuatro capas con responsabilidad propia: `config.py` (26 líneas, solo lee variables de entorno), `db.py` (73 líneas, único punto de acceso a PostgreSQL), `routes/*.py` (lógica por módulo) y `templates/` (presentación). `app.py` solo ensambla la aplicación: no contiene SQL ni reglas de negocio. |
| **A2** | Manejo de errores: mensajes comprensibles, sin exponer errores SQL crudos | ✅ Cumple | Los **6** `execute()` de la aplicación están dentro de un `try/except`. Los errores concretos de PostgreSQL se traducen a español: `UniqueViolation` → *"Ya existe una categoría llamada X"*; `ForeignKeyViolation` → *"La categoría seleccionada ya no existe"*. Además hay páginas 404 y 500 propias registradas en `app.py`, para que nunca se muestre un traceback. |
| **A3** | Validación de entrada: tipos, campos requeridos y formatos | ✅ Cumple | Validación **en el servidor**, no solo el `required` de HTML. `productos.py::_validar_formulario()` comprueba campos obligatorios, que `id_categoria` sea numérico y que `stock_minimo` sea un número ≥ 0 (refuerza `ck_producto_stock_minimo`). `auth.py::login` rechaza usuario o contraseña vacíos antes de tocar la base. |
| **A4** | Consultas parametrizadas: prevenir inyección SQL | ✅ Cumple | **Cero** concatenaciones de SQL con datos del usuario en todo el proyecto. Las 17 consultas usan marcadores `%s` o `%(nombre)s` a través de `db.py`. Ninguna ruta abre su propia conexión ni construye SQL con f-strings. |
| **A5** | Código legible: nombres descriptivos, funciones con responsabilidad única | ✅ Cumple | Nombres en español coherentes con el dominio (`listar`, `nuevo`, `editar`, `alternar_estado`, `_categorias_activas`). Ninguna función supera las 45 líneas. El archivo más grande es `productos.py` con 173 líneas. |
| **A6** | Documentación: comentarios en las funciones que acceden a la BD | ✅ Cumple | Los **7 módulos** de `web/` abren con un docstring que explica su responsabilidad y el estándar que aplican. `db.py` documenta sus 4 funciones de acceso a datos (9 docstrings en total), incluyendo por qué se usa `psycopg` v3 y no `psycopg2`. |

**Resultado: los 6 estándares de aplicación se cumplen.**

---

## Resumen

| Bloque | Cumplen | No cumplen | No aplican aún |
|---|---|---|---|
| Sección 6.2 — SQL | 6 | 1 (S5, despliegue) | 1 (S6, triggers) |
| Sección 6.3 — Aplicación | 6 | 0 | 0 |

**El único incumplimiento es S5 (desplegado en internet)**, y está planificado para la Entrega 4, que es donde la rúbrica lo evalúa.

Verificado el 01/09/2026 sobre el tag `entrega-2`.
