# Avance de la aplicación web — Entrega 2

**Meta de la rúbrica para esta entrega:** ≈30% (login + 2 CRUD funcionales).
**Stack:** Python 3 + Flask + PostgreSQL (driver `psycopg` v3 — se probó `psycopg2-binary` primero pero no tiene wheel para Python 3.14 en Windows), decidido el 30/08/2026 — ver `docs/entrega-2/Bitacora-IA.md`.

## Módulos implementados
| Módulo | Estado | Detalle |
|---|---|---|
| Login | ✅ Implementado | `web/routes/auth.py` — valida usuario/contraseña contra `usuario`/`rol`, hash con `werkzeug.security`, sesión firmada con `APP_SECRET`, mensaje de error genérico (no revela si el usuario existe), redirige a `next` tras iniciar sesión |
| Logout | ✅ Implementado | Limpia la sesión, requiere POST (evita cierre de sesión por link/CSRF trivial) |
| Layout | ✅ Implementado | `web/templates/base.html` — encabezado con navegación activa, usuario+rol, mensajes flash con auto-cierre, tarjetas de resumen (KPI) en los listados, confirmación antes de desactivar/activar registros, páginas de error 404/500 con el mismo estilo de la app |
| Control de acceso | ⏳ Parcial | `login_required` protege todas las rutas de Categorías/Productos. El control **por rol** (qué puede hacer cada rol) es explícitamente de Entrega 3 en la rúbrica — no se implementó todavía |
| CRUD 1 — Categorías | ✅ Implementado | Listar, crear, editar, activar/desactivar (baja lógica) — persiste en `categoria` |
| CRUD 2 — Productos | ✅ Implementado | Listar, crear, editar, activar/desactivar — persiste en `producto`, con FK real a `categoria` (selector, no texto libre) |

## Por qué Categorías + Productos (y no Lote/Movimiento)
Lote y Movimiento dependen de reglas de negocio (RN-01 a RN-04: nunca negativo, entrada suma, salida resta, no exceder existencia) que la propia rúbrica asigna a triggers/procedimientos de **Entrega 3**. Construir su CRUD ahora sin esas reglas en la base de datos sería exponer una pantalla que puede dejar el inventario en un estado inconsistente. Categorías y Productos son las dos entidades base sin ese riesgo, y Productos ya demuestra una FK real (selector de categoría), que es lo que pide la revisión funcional de esta entrega.

## Validaciones implementadas
- Campos obligatorios verificados en el servidor antes de tocar la BD (no solo `required` de HTML).
- Duplicados: `codigo` de producto y `nombre` de categoría son `UNIQUE` — el error de PostgreSQL (`UniqueViolation`) se captura y se muestra como mensaje claro, nunca como el error SQL crudo.
- `stock_minimo` se valida como número ≥ 0 en el servidor (refuerza `ck_producto_stock_minimo`).
- Consultas 100% parametrizadas (`db.py`) — ninguna ruta concatena SQL con datos del usuario.

## Conexión a la base de datos
`web/config.py` lee `.env` (nunca credenciales en el código); `web/db.py` centraliza la conexión y las consultas — ninguna ruta abre su propia conexión ni escribe SQL crudo.

## Pendiente (fuera del alcance de Entrega 2, según la rúbrica)
- Módulos de Proveedores, Lotes, Movimientos, Exámenes → Entrega 3 (junto con triggers/procedimientos que sí les aplican).
- Control de acceso por rol dentro de la app → Entrega 3.
- Vistas, triggers, procedimientos, roles de PostgreSQL → Entrega 3.
- Ampliar `sql/dml/001_seed.sql` hasta el mínimo de 50 registros por tabla principal exigido para el sistema completo → progresivo hasta Entrega 3/4.

## Cómo ejecutar
Ver `INSTALL.md` (pasos 1-6). Resumen:
```bash
psql -U usuario_app -d inventario_laboratorio -f sql/ddl/001_schema.sql
psql -U usuario_app -d inventario_laboratorio -f sql/dml/001_seed.sql
cd web && pip install -r requirements.txt && python seed_usuarios.py && python app.py
```

## Evidencia de pruebas
**Ejecutado el 30/08/2026** contra PostgreSQL 18 + Python 3.14 real (el equipo instaló ambos). Los 15 casos de `docs/casos-prueba/casos-prueba-entrega-2.md` pasaron, incluyendo un reinicio real del servidor para confirmar que los datos persisten en PostgreSQL y no en memoria (CP-15). Durante la ejecución se encontraron y corrigieron 2 problemas reales:
1. `psycopg2-binary` no tiene wheel precompilado para Python 3.14 en Windows (pide Visual C++ Build Tools) → se migró a `psycopg` (v3), que sí trae wheel para 3.14.
2. PostgreSQL 15+ ya no da permiso de `CREATE` en el schema `public` a un usuario que no es dueño de la BD → se agregó el `GRANT ALL ON SCHEMA public` a `INSTALL.md`.

Ambos quedaron corregidos en el código y en `INSTALL.md` antes de que nadie más los sufra. Detalle completo de la sesión de pruebas en `docs/entrega-2/Bitacora-IA.md`.

## Cierre de la entrega (01/09/2026)
Auditoría final contra la consigna antes de taggear (detalle en `docs/entrega-2/Bitacora-IA.md`):
- Diagrama ER corregido: la relación `Registra` conectaba USUARIO con PRODUCTO, pero la FK real es `movimiento.id_usuario` — ahora es **USUARIO (1) — Registra — (N) MOVIMIENTO**. Se agregó también el atributo `requiere_vencimiento` a PRODUCTO. PNG y PDF re-exportados.
- `CERTIFICACION_ENTREGA_2.md` firmada por ambos integrantes.
- Rutas rotas corregidas en `README.md` (nombres reales de los archivos del diagrama) y en el encabezado de `sql/dml/001_seed.sql`.
- Tag `entrega-2` creado y publicado.

## Pruebas manuales del equipo (además de las automatizadas)
El equipo inició sesión manualmente en el navegador con los 3 usuarios de prueba (`admin.dev`, `encargado.dev`, `consulta.dev`) y usó el CRUD web para curar el catálogo completo con datos reales del laboratorio: las 5 categorías y los 10 productos del seed inicial (genéricos) se editaron uno por uno hasta reflejar el catálogo real (códigos, nombres y unidades tal como los maneja el laboratorio), y se agregó un producto adicional. Todo verificado directamente en PostgreSQL. Detalle en `docs/casos-prueba/casos-prueba-entrega-2.md` (CP-16, CP-17, CP-18). `sql/dml/001_seed.sql` se actualizó para que una instalación desde cero cargue directamente este catálogo real, no datos de ejemplo genéricos.
