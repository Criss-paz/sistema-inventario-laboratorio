# sql/ddl

Scripts de definición de datos (CREATE TABLE, restricciones PK/FK/CHECK/UNIQUE, identidades).

**Estado:** implementado desde la Entrega 2.

| Script | Contenido |
|---|---|
| `001_schema.sql` | Las 11 tablas del modelo relacional en 3FN, con 38 restricciones explícitas (PK, FK con `ON DELETE`/`ON UPDATE`, `UNIQUE`, `CHECK`) e índices en las llaves foráneas. |

Detalle de cada tabla y restricción: `docs/entrega-2/diccionario-datos.md` y `docs/entrega-2/modelo-relacional.md`. Orden de instalación: `INSTALL.md`, paso 3.

## Entrega 3 y 4 (migraciones)

Migraciones aditivas: se aplican sobre una base existente sin borrar datos, en el orden de `INSTALL.md`, paso 3.

| Script | Contenido |
|---|---|
| `002_devolucion.sql` | Tipo `DEVOLUCION`, `id_movimiento_origen` (FK a la salida corregida) y `motivo`, con su CHECK (RN-19, RN-20) |
| `003_examen_estado.sql` | `examen_laboratorio.estado` para la baja lógica de exámenes (RN-24) |
| `004_correccion_entrada.sql` | Tabla `correccion_entrada`: cada dato corregido de una entrada (RN-25, RN-26) |
| `005_numero_documento.sql` | `movimiento.numero_documento` (E/S/D + 6 dígitos, UNIQUE y CHECK), relleno desde el texto de la observación y limpieza de ese texto (RN-27). Va **después** de `dml/004` y `dml/005` |
| `006_permisos.sql` | Tablas `permiso` y `rol_permiso`, con el reparto inicial de permisos de los 3 roles (RN-28, RN-29) |
| `007_bitacora.sql` | Tabla `bitacora` de auditoría (RN-30) |

Total: 15 tablas y 17 FK, todas con `ON DELETE` y `ON UPDATE` explícitos.
