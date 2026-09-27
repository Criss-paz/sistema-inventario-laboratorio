# sql/ddl

Scripts de definición de datos (CREATE TABLE, restricciones PK/FK/CHECK/UNIQUE, identidades).

**Estado:** implementado desde la Entrega 2.

| Script | Contenido |
|---|---|
| `001_schema.sql` | Las 11 tablas del modelo relacional en 3FN, con 38 restricciones explícitas (PK, FK con `ON DELETE`/`ON UPDATE`, `UNIQUE`, `CHECK`) e índices en las llaves foráneas. |

Detalle de cada tabla y restricción: `docs/entrega-2/diccionario-datos.md` y `docs/entrega-2/modelo-relacional.md`. Orden de instalación: `INSTALL.md`, paso 3.
