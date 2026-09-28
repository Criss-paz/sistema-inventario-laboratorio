# sql/security

Roles y privilegios a nivel de motor de base de datos. Son distintos de la tabla `rol` del modelo, que controla el acceso dentro de la aplicación, pero están alineados uno a uno con ella.

**Estado:** implementado — Entrega 3. Se ejecuta **como `postgres`** (crear roles requiere superusuario).

| Rol de BD | Rol en la app (`rol.nombre`) | Puede | No puede |
|---|---|---|---|
| `rol_consulta` | Usuario de consulta | Leer catálogos, lotes, las 5 vistas y el kardex (`fn_kardex_promedio`) | Modificar nada, ver la tabla `usuario`, registrar movimientos |
| `rol_encargado` | Encargado de inventario | Todo lo de consulta + `CALL` a `sp_registrar_entrada` / `sp_registrar_salida` | Escribir directo en tablas, editar catálogos |
| `rol_administrador` | Administrador | Todo lo del encargado + alta/edición de catálogos, usuarios y datos de lote; `DELETE` solo en tablas puente | Leer `password_hash`, editar `cantidad_disponible`, insertar movimientos sin procedimiento, `DELETE` físico de catálogos |

Los roles se heredan en cadena: `consulta ⊂ encargado ⊂ administrador`. Cada uno recibe solo lo que agrega sobre el anterior.

**Decisiones de diseño** (detalladas en el encabezado de `001_roles.sql`):
- Los procedimientos son `SECURITY DEFINER`: el historial de movimientos solo se escribe por el camino que valida las reglas de negocio, para todos los roles.
- `GRANT UPDATE` por columna en `lote`: la existencia solo la cambia el trigger.
- `GRANT SELECT` por columna en `usuario`: ningún rol lee los hashes de contraseña.

**Prueba** (caso CP3-07 en `docs/casos-prueba/casos-prueba-entrega-3.md`):
```sql
-- conectado como usuario_app
SET ROLE rol_consulta;
SELECT * FROM vw_inventario_bajo;              -- OK
UPDATE producto SET stock_minimo = 1;          -- ERROR: permiso denegado
RESET ROLE;
```
