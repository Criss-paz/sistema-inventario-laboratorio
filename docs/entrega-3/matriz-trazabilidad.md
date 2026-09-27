# Matriz de trazabilidad v2 — Entrega 3

Relaciona cada requerimiento de la Entrega 1 con dónde se implementa en la base de datos y en la aplicación web, y con la prueba que lo demuestra. Reemplaza a la versión 1 (`docs/entrega-2/matriz-trazabilidad.md`), que marcaba como pendientes casi todos los requerimientos de operación.

**Estado general:** 39 de 39 requerimientos funcionales implementados. Pendientes: RNF-11 (respaldos, Entrega 4) y el despliegue en internet (estándar S5).

Convenciones de la columna *Evidencia*:
- `CP3-xx`: caso de prueba de esta entrega (`docs/casos-prueba/casos-prueba-entrega-3.md`).
- `CP-xx`: caso de prueba de la Entrega 2, que sigue vigente.
- *Prueba automatizada*: verificación con el cliente de pruebas de Flask contra la base real, entrando como los 3 usuarios (142 verificaciones generales y 19 del módulo de usuarios, 0 fallos, 26/09/2026). Las escrituras se revierten para no alterar el inventario.

---

## Requerimientos funcionales

### Usuarios, roles y acceso

| Requerimiento | Base de datos | Aplicación web | Evidencia |
|---|---|---|---|
| RF-01 Iniciar sesión | `usuario`, `rol` | `routes/auth.py::login` | CP-01, CP-02, CP-03 |
| RF-02 Cerrar sesión | — (sesión) | `routes/auth.py::logout` | CP-05 |
| RF-03 Administrar usuarios | `usuario`; `GRANT INSERT/UPDATE` por columna a `rol_administrador` | `routes/usuarios.py`: crear, editar, restablecer contraseña, desactivar | Prueba automatizada (19 casos) |
| RF-04 Asignar roles | `usuario.id_rol` → `rol` (FK) | Selector de rol en `usuarios/form.html` | Prueba automatizada |
| RF-05 Control de acceso por rol | 3 roles de BD con privilegios distintos (`sql/security/001_roles.sql`); la app adopta el rol con `SET ROLE` | `auth.rol_requerido()` en rutas, `tiene_rol()` en plantillas, error 403 | CP3-06, CP3-07 |

### Catálogos

| Requerimiento | Base de datos | Aplicación web | Evidencia |
|---|---|---|---|
| RF-06 a RF-08 Registrar, modificar y consultar productos | `producto` (806 productos reales) | `routes/productos.py`, con búsqueda, filtro y existencia | CP-11 a CP-14 |
| RF-09 Clasificar productos por categoría | `producto.id_categoria` → `categoria` | Selector y filtro por categoría | CP-11, CP-14 |
| RF-10 Administrar categorías | `categoria` | `routes/categorias.py` | CP-06 a CP-10 |
| RF-11 a RF-13 Registrar, modificar y consultar proveedores | `proveedor` (26 reales + 24 de prueba) | `routes/proveedores.py`: CRUD, detalle con precios | Prueba automatizada |
| RF-36, RF-37 Registrar y modificar exámenes | `examen_laboratorio` (50) | `routes/examenes.py` | Prueba automatizada |
| RF-38 Insumos requeridos por examen | `examen_producto` (114, RN-17) | Detalle del examen: agregar y quitar insumos, "alcanza para N pruebas" | Prueba automatizada |
| RF-39 Productos por proveedor con precio | `proveedor_producto` (425, RN-16) | Detalle del proveedor | Prueba automatizada |

### Lotes y existencias

| Requerimiento | Base de datos | Aplicación web | Evidencia |
|---|---|---|---|
| RF-14 Registrar lotes | `lote`; `sp_registrar_entrada` crea el lote en su primera entrada | Formulario de entrada | CP3-01 |
| RF-15 Lote asociado a un producto | `lote.id_producto` (FK), `UNIQUE (id_producto, numero_lote)` | Detalle del lote | CP3-01 |
| RF-16 Lote asociado a un proveedor | `lote.id_proveedor` (FK) | Selector de proveedor en la entrada | CP3-01 |
| RF-17, RF-18 Fecha de ingreso y de vencimiento | `lote.fecha_ingreso`, `lote.fecha_vencimiento`, `ck_lote_fecha_vencimiento`, trigger `trg_lote_vencimiento` (RN-07) | Formulario de entrada; corrección de datos del lote (administrador) | CP3-04 |
| RF-19 Existencias por lote | `lote.cantidad_disponible` (solo la cambia el trigger), `vw_existencia_producto` | `routes/lotes.py`: existencia, vencidos, por vencer, historial del lote | CP3-01, CP3-02 |

### Movimientos de inventario

| Requerimiento | Base de datos | Aplicación web | Evidencia |
|---|---|---|---|
| RF-20 Registrar entradas | `sp_registrar_entrada` | `routes/movimientos.py::entrada` | CP3-01 |
| RF-21 Registrar salidas | `sp_registrar_salida` (FEFO: primero el lote que vence antes, sin lotes vencidos) | `routes/movimientos.py::salida` | CP3-02 |
| RF-22 Actualizar existencia tras una entrada | Trigger `trg_detalle_movimiento_existencia` (RN-02) | — (automático) | CP3-01 |
| RF-23 Actualizar existencia tras una salida | Mismo trigger (RN-03) | — (automático) | CP3-02 |
| RF-24 Impedir salida mayor a la existencia | `sp_registrar_salida` y el trigger (RN-04) | Muestra el mensaje de la base al usuario | CP3-03 |
| RF-25 Impedir existencia negativa | `ck_lote_cantidad_disponible CHECK (>= 0)` + trigger (RN-01) | — | CP3-03 |
| RF-26 Fecha y hora de cada movimiento | `movimiento.fecha_hora` | Historial y detalle | CP3-01 |
| RF-27 Usuario responsable | `movimiento.id_usuario` (FK, RN-08) | Columna "Responsable" | CP3-01 |
| RF-28 Historial de movimientos | `vw_historial_movimientos`; triggers `trg_movimiento_inmutable` y `trg_detalle_movimiento_inmutable` (RN-09) | Pestañas Todos / Entradas / Salidas con filtros | CP3-05 |

### Consultas y reportes

| Requerimiento | Base de datos | Aplicación web | Evidencia |
|---|---|---|---|
| RF-29 Inventario bajo | `vw_inventario_bajo` (RN-10, RN-11) | Reporte "Inventario bajo", indicador en Inicio | Prueba automatizada |
| RF-30 Próximos a vencer | `vw_lotes_por_vencer` (90 días) | Reporte "Vencimientos", pestañas de Lotes, Inicio | Prueba automatizada |
| RF-31 Buscar productos | Consultas con `ILIKE` parametrizadas | Buscador en Productos, Lotes, Movimientos, Proveedores y Exámenes | Prueba automatizada |
| RF-32 Filtrar información de inventario | Consultas parametrizadas | Filtros por categoría, fechas, tipo de movimiento y estado del lote | Prueba automatizada |
| RF-33 Generar reportes de inventario | `fn_kardex_promedio`, `vw_valorizacion_inventario` (costo promedio ponderado) | `routes/informes.py`: pantalla única con 9 tipos de reporte, CSV e impresión | CP3-08 |
| RF-34 Consultar información histórica | `fn_kardex_promedio` (kardex con saldo inicial por período) | Kardex por producto, historial de movimientos | CP3-08 |
| RF-35 Trazabilidad de operaciones | Cada detalle enlaza movimiento → lote → producto → proveedor; historial inmutable | Del movimiento al lote y del lote a sus movimientos | CP3-02, CP3-05 |

---

## Reglas de negocio

| Regla | Dónde se garantiza | Evidencia |
|---|---|---|
| RN-01 Existencia nunca negativa | `CHECK (cantidad_disponible >= 0)` + trigger de existencia | CP3-03 |
| RN-02 La entrada incrementa el lote | `trg_detalle_movimiento_existencia` | CP3-01 |
| RN-03 La salida disminuye el lote | `trg_detalle_movimiento_existencia` | CP3-02 |
| RN-04 Salida no mayor a la existencia | `sp_registrar_salida` (por producto) + trigger (por lote) | CP3-03 |
| RN-05 Un producto con varios lotes | FK `lote.id_producto` | CP3-02 |
| RN-06 Número de lote identificable por producto | `UNIQUE (id_producto, numero_lote)` | CP3-01 |
| RN-07 Vencimiento obligatorio si el producto lo requiere | `trg_lote_vencimiento` | CP3-04 |
| RN-08 Movimiento ligado a su usuario | FK `movimiento.id_usuario`; `fn_validar_usuario_activo` | CP3-01 |
| RN-09 Historial conservado | Triggers de inmutabilidad; ningún rol tiene `UPDATE`/`DELETE` sobre movimientos | CP3-05 |
| RN-10, RN-11 Stock mínimo e inventario bajo | `producto.stock_minimo`, `vw_inventario_bajo` (compara con existencia utilizable) | Prueba automatizada |
| RN-12 Proveedor con varios lotes | FK `lote.id_proveedor` | Reporte de proveedores |
| RN-13 Categoría con varios productos | FK `producto.id_categoria` | CP-11 |
| RN-14 Usuario con un rol | FK `usuario.id_rol` `NOT NULL` | Prueba automatizada |
| RN-15 Contraseña con hash | `werkzeug.security`; ningún rol de BD puede leer `password_hash` | CP3-07 |
| RN-16 Producto–proveedor N:M con precio | `proveedor_producto` | Detalle del proveedor |
| RN-17 Examen–producto N:M con cantidad | `examen_producto` | Detalle del examen |
| RN-18 Movimiento–lote N:M | `detalle_movimiento` (una salida FEFO puede tocar varios lotes) | CP3-02 |

---

## Requerimientos no funcionales

| Requerimiento | Implementación | Estado |
|---|---|---|
| RNF-01 Navegador web | Flask + plantillas HTML | ✅ |
| RNF-02 Base de datos relacional | PostgreSQL 18, 11 tablas en 3FN | ✅ |
| RNF-03 Autenticación | Login con sesión firmada | ✅ |
| RNF-04, RNF-05 Contraseñas con hash | `generate_password_hash` / `check_password_hash` | ✅ |
| RNF-06 Acceso por roles | Doble capa: app (`rol_requerido`) y base de datos (`SET ROLE`) | ✅ |
| RNF-07, RNF-08 Integridad | 38 restricciones del DDL + 4 triggers + procedimientos | ✅ |
| RNF-09, RNF-10 Interfaz clara y mensajes | Los mensajes de las reglas de negocio llegan tal cual al usuario (SQLSTATE P0001); nunca se muestra SQL | ✅ |
| RNF-11 Respaldos | — | ⏳ Entrega 4 |
| RNF-12, RNF-13 Arquitectura mantenible y ampliable | Capas `config` / `db` / `routes` / `templates`; SQL separado por propósito | ✅ |
| RNF-14 Tiempo de respuesta | Listas paginadas; el kardex de los 806 productos se calcula en ~18 ms | ✅ |
| RNF-15 Validar antes de modificar inventario | Validación en el servidor + procedimientos + triggers | ✅ |
| RNF-16 Información para trazabilidad | Historial inmutable con usuario, fecha y lote | ✅ |
| RNF-17 Evitar accesos no autorizados | Rutas protegidas, 403, `SET ROLE`, redirección de login solo a rutas internas | ✅ |
| RNF-18 Interfaz adaptable | Diseño responsivo verificado a 1440 px y 390 px | ✅ |
