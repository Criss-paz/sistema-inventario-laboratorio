# Avance de la aplicación web — Entrega 4

**Meta de la rúbrica para esta entrega:** 100% (todos los módulos y CRUD en todas las tablas principales).
**Avance declarado: 100%.** Los 39 requerimientos funcionales y los 18 no funcionales tienen pantalla o están cubiertos por la base de datos. El último pendiente, el respaldo (RNF-11), se completó el 20/10/2026.
**En línea:** https://inventario-laboratorio-03s7.onrender.com (Render + Neon, desplegada el 26/09/2026).
**Stack:** Python 3.14 + Flask 3 + PostgreSQL 18 (driver `psycopg` v3). Sin frameworks de interfaz: HTML, CSS y JavaScript propios.

## Módulos

| Módulo | Estado | Qué hace | Quién lo usa |
|---|---|---|---|
| Login / logout | ✅ | Sesión firmada, contraseña con hash, mensaje genérico ante error, redirección solo a rutas internas | Todos |
| Inicio | ✅ | Resumen del inventario: productos con existencia, inventario bajo, lotes vencidos y por vencer, últimos movimientos | Todos |
| Movimientos | ✅ | Pestañas Todos / Entradas / Salidas con filtros por fecha y búsqueda. Registrar entrada (crea o alimenta un lote) y salida (FEFO) llamando a los procedimientos almacenados. Corregir una entrada mal digitada, con registro de cada cambio (Entrega 4) | Consultar: todos. Registrar: administrador y encargado. Corregir entradas: administrador |
| Lotes | ✅ | Existencia por lote, vencidos, por vencer y la ficha de cada lote con sus movimientos. Corregir número, vencimiento o dar de baja (nunca la existencia) | Consultar: todos. Corregir: administrador |
| Productos | ✅ | CRUD con búsqueda, filtro por categoría, paginación y existencia en vivo | Consultar: todos. Editar: administrador |
| Exámenes | ✅ | CRUD con baja lógica (Entrega 4), insumos que consume cada examen y para cuántas pruebas alcanza la existencia | Consultar: todos. Editar: administrador |
| Proveedores | ✅ | CRUD con baja lógica; en la ficha, asignar productos con su precio, cambiar el precio y quitarlos (Entrega 4) | Consultar: todos. Editar: administrador |
| Categorías | ✅ | CRUD con baja lógica | Consultar: todos. Editar: administrador |
| Reportes | ✅ | Pantalla única: el usuario elige Inventario, Entradas, Salidas, Kardex, Proveedores, Pruebas, Catálogo de productos, Inventario bajo o Vencimientos. Todos en CSV e impresión | Todos |
| Usuarios y roles | ✅ | Crear usuarios, cambiar rol, restablecer contraseña, desactivar; tabla de permisos por rol | Administrador |
| Mi contraseña | ✅ | Cada usuario cambia su contraseña confirmando la actual (Entrega 4) | Todos |
| Respaldo | ✅ | Descarga de un respaldo completo `.sql`, restaurable con `psql` (RNF-11, Entrega 4) | Administrador |

## Control de acceso por rol (RF-05)

Dos capas independientes:

1. **En la aplicación.** `routes/auth.py::rol_requerido()` protege cada ruta (responde 403 si el rol no corresponde) y las plantillas muestran solo los botones que el rol puede usar (`tiene_rol()`).
2. **En la base de datos.** Después del login, cada petición ejecuta `SET ROLE rol_administrador | rol_encargado | rol_consulta` (`web/db.py`). Aunque la interfaz tuviera un error, PostgreSQL niega lo que el rol no permite. Ningún rol puede leer `password_hash`, editar `cantidad_disponible` ni insertar movimientos sin pasar por los procedimientos.

| Rol | Puede |
|---|---|
| Administrador | Todo, incluidos catálogos, corrección de lotes y usuarios |
| Encargado de inventario | Consultar y registrar entradas y salidas |
| Usuario de consulta | Solo consultar y generar reportes |

## Reglas de negocio visibles en la interfaz

Los mensajes de los triggers y procedimientos (SQLSTATE P0001) llegan tal cual al usuario; cualquier otro error se reemplaza por un mensaje genérico (A2). Ejemplos:
- *"Existencia insuficiente de "CUVETTES FOR URISED": disponible 26.00 (sin contar lotes vencidos), solicitado 99999."*
- *"El producto "AIA-PACK CA19-9 CALIBRATOR SET" requiere fecha de vencimiento en sus lotes."*

## Reportes y método de valuación

El inventario se valoriza por **costo promedio ponderado móvil**, calculado en la base de datos (`fn_kardex_promedio`, `vw_valorizacion_inventario`):
- cada compra recalcula el costo promedio: (valor del saldo + valor de la compra) ÷ (cantidad del saldo + cantidad comprada);
- cada salida se valoriza al promedio vigente ese día;
- el reporte de inventario muestra código de producto, producto, presentación, existencia actual, precio unitario y precio total.

Comprobación contable con los datos reales (marzo a septiembre de 2026): compras Q3,811,436.54 − costo de lo consumido Q3,286,722.24 = Q524,714.30, frente a un inventario valorizado de Q524,714.36. La diferencia de Q0.06 viene del redondeo de cada salida.

## Datos

La base se carga con el inventario real del laboratorio: los registros en papel (marzo a septiembre de 2026) y lo registrado en SIGAL del 24/09 al 21/10/2026. En total, 814 productos, 1,296 lotes y 6,560 movimientos, valorizados en Q600,338.34. Los errores que tenía el papel y cómo se trataron están en `docs/entrega-3/ENTREGA3_REPORTE_CARGA_DATOS.md`.

## Interfaz

Desde el 21/10/2026 sigue el diseño de **SIGAL** (Sistema de Gestión y Almacenaje de Laboratorio), proyecto nacido de este sistema:

- **Apariencia:** menú lateral oscuro por tarea; tinta y ámbar como colores de estructura y acción; rojo, naranja y verde solo para estados del inventario. Tipografías Schibsted Grotesk y JetBrains Mono, alojadas en la app (licencia SIL OFL) para funcionar sin internet.
- **Tema claro y oscuro:** se recuerda en cada navegador.
- **Barra superior:** búsqueda rápida `Ctrl K` de pantallas y productos (ruta `reportes.buscar`, JSON) y menú de usuario con *Cambiar mi contraseña* y *Cerrar sesión*.
- **Avisos:** notificaciones flotantes; las de error se quedan hasta que se cierran.
- **Panel "Bodega hoy":**
  - indicadores: con existencias, valor en bodega, vencen en 90 días, bajo el mínimo y agotados;
  - calendario de vencimientos con un punto por lote;
  - *Reponer primero*, por el consumo de 60 días;
  - actividad reciente.
- **Listas:** etiquetas de estado de color, filtros tipo chip y, en Productos, medidor de existencia contra el mínimo.

El comportamiento vive en `web/static/app.js`, sin librerías y como mejora progresiva: si no carga, todo sigue funcionando con enlaces y formularios. Se verificó a 1440 px y a 390 px (celular), en tema claro y oscuro, con foco visible para teclado. El rediseño no tocó la base, las rutas ni los permisos: después del cambio, las 183 verificaciones de regresión y los 12 flujos del manual (CP4) volvieron a pasar.

## Validaciones

- Validación en el servidor antes de tocar la base (A3): campos obligatorios, números, fechas, formato de NIT, correo, usuario y contraseña (mínimo 8 caracteres y confirmación).
- Consultas 100% parametrizadas (A4); los filtros de tipo "lista fija" salen de diccionarios del código, nunca del texto del usuario.
- Duplicados (código, NIT, número de lote, usuario) se informan con un mensaje claro.

## Devolución de salidas (añadido el 29/09/2026)

Pedido del equipo tras la Entrega 3: poder corregir una salida registrada por error
sin romper el historial.

| Pieza | Archivo | Qué hace |
|---|---|---|
| DDL | `sql/ddl/002_devolucion.sql` | Tipo `DEVOLUCION`, columnas `id_movimiento_origen` y `motivo`, y un CHECK que las hace obligatorias solo en devoluciones |
| Triggers | `sql/triggers/002_devolucion.sql` | La devolución repone existencia (RN-21) y nunca devuelve más de lo que salió, descontando lo ya devuelto (RN-22) |
| Procedimiento | `sql/procedures/002_devolucion.sql` | `sp_registrar_devolucion` (atómico) y `fn_devolvible` (saldo por lote) |
| Vistas | `sql/views/003_devolucion.sql` | `vw_historial_movimientos` amplía dos columnas; `vw_devoluciones` para auditoría |
| Seguridad | `sql/security/002_devolucion.sql` | `SECURITY DEFINER` y permisos: registrar solo Administrador y Encargado |
| Web | `web/routes/movimientos.py::devolucion` + `templates/movimientos/devolucion.html` | Pantalla con motivo obligatorio y cantidad editable por lote |

**Por qué un movimiento inverso y no un UPDATE:** el trigger `trg_historial_inmutable`
prohíbe modificar o borrar un movimiento (RN-09), y su propio mensaje indica
"Registre un movimiento inverso para corregir". La devolución es ese movimiento,
con dos datos que una entrada común no tiene: a qué salida corrige y por qué.

Admite devolución **total** (el caso habitual) y **parcial** por lote. La salida
original queda intacta y ambos movimientos permanecen en el historial.

## Evidencia de pruebas

- **Casos de la Entrega 3:** `docs/casos-prueba/casos-prueba-entrega-3.md`. 8 de 8 pasaron el 28/09/2026 en el navegador, sobre una instalación desde cero en otro equipo, con capturas en `docs/casos-prueba/evidencias-entrega-3/`.
- **Pruebas automatizadas de la app (26/09/2026):** 142 verificaciones con los 3 usuarios (páginas, permisos por rol, formularios, mensajes de la base, reportes y CSV) y 19 del módulo de usuarios. 0 fallos. Las escrituras se revierten para no alterar el inventario.

## Cómo ejecutar

Ver `INSTALL.md`. En Windows, antes de ejecutar los scripts SQL: `$env:PGCLIENTENCODING = "UTF8"`.

```bash
cd web
.venv\Scripts\python.exe app.py      # http://localhost:8080
```

## Despliegue

La aplicación está publicada en Render y la base de datos en Neon (PostgreSQL 17), ambas en US East (Ohio). Se verificó en producción con los 3 usuarios: 48 comprobaciones de páginas, permisos por rol, cookie de sesión solo por HTTPS, rechazo de las contraseñas de desarrollo y valor del inventario idéntico al local (Q524,714.36). Procedimiento en `INSTALL.md`, paso 8.

## Entrega 4 (20/10/2026)

| Cambio | Detalle |
|---|---|
| CRUD de proveedor–producto | Era la única tabla principal sin pantalla de escritura: solo la llenaba la carga inicial |
| Baja lógica de exámenes | `sql/ddl/003_examen_estado.sql`; el informe de pruebas muestra solo los activos (RN-24) |
| Respaldo | `web/respaldo.py` + Administración → Respaldo; probado con una restauración real (11 de 11 tablas idénticas) |
| Seguridad | Cambio de contraseña propio, encabezados CSP, X-Frame-Options y HSTS, rechazo de POST de otro origen |
| Corrección de entradas | Una entrada no se borra: el Administrador corrige cantidad, precio, proveedor, lote o vencimiento con motivo, y cada cambio queda en `correccion_entrada` (RN-25, RN-26) |
| Datos al día | Movimientos de SIGAL del 24/09 al 21/10/2026 (`sql/dml/005_carga_sigal.sql`) |
| Correcciones | La devolución se mostraba como salida en el kardex, la ficha del lote e Inicio; "Devolución" sin tilde |

CRUD por tabla y su justificación: `docs/entrega-4/ENTREGA4_MATRIZ_TRAZABILIDAD.md`. Casos de prueba: `docs/casos-prueba/casos-prueba-entrega-4.md` (14 de 14 aprobados). Manual de usuario: `docs/entrega-4/ENTREGA4_MANUAL_USUARIO.md`.
