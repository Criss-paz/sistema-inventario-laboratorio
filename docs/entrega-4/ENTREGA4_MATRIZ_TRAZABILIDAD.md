# Matriz de trazabilidad v3 — Entrega 4

Relaciona cada requerimiento de la Entrega 1 con dónde se implementa en la base de datos y en la aplicación web, y con la prueba que lo demuestra. Actualiza la versión 2 (`docs/entrega-3/ENTREGA3_MATRIZ_TRAZABILIDAD.md`).

**Estado general:** **39 de 39 requerimientos funcionales y los 18 no funcionales implementados.** El último pendiente, RNF-11 (respaldos), se completó en esta entrega. Además hay 6 reglas de negocio nuevas: RN-19 a RN-23 (devolución) y RN-24 (baja lógica de exámenes). Ningún requerimiento queda abierto.

Convenciones de la columna *Evidencia*:
- `CP4-xx`: caso de prueba de esta entrega (`docs/casos-prueba/casos-prueba-entrega-4.md`), ejecutado en el navegador siguiendo el manual de usuario.
- `CP3-xx` y `CP-xx`: casos de las entregas 3 y 2, que siguen vigentes.
- *Prueba automatizada*: verificación con el cliente de pruebas de Flask contra la base real con los 3 usuarios. La regresión de la Entrega 4 suma 183 verificaciones sin fallas.

---

## CRUD de las tablas principales

Qué operación ofrece la aplicación sobre cada tabla y por qué algunas no tienen todas. "Eliminar" es **baja lógica** en todos los catálogos, para que el historial siempre pueda mostrar a qué se refiere cada movimiento.

| Tabla | Crear | Consultar | Modificar | Eliminar | Dónde | Evidencia |
|---|---|---|---|---|---|---|
| `producto` | ✅ | ✅ | ✅ | ✅ baja lógica | Productos | CP4-03, CP4-11 |
| `categoria` | ✅ | ✅ | ✅ | ✅ baja lógica | Categorías | CP-06 a CP-10 |
| `proveedor` | ✅ | ✅ | ✅ | ✅ baja lógica | Proveedores | CP4-04, CP4-11 |
| `examen_laboratorio` | ✅ | ✅ | ✅ | ✅ baja lógica (Entrega 4) | Exámenes | CP4-07 |
| `usuario` | ✅ | ✅ | ✅ rol y contraseña | ✅ baja lógica | Usuarios y roles | CP4-09 |
| `proveedor_producto` (N:M) | ✅ | ✅ | ✅ precio | ✅ `DELETE` | Ficha del proveedor (Entrega 4) | CP4-04 |
| `examen_producto` (N:M) | ✅ | ✅ | quitar y volver a agregar | ✅ `DELETE` | Ficha del examen | CP4-07 |
| `lote` | ✅ con la primera entrada | ✅ | ✅ número, proveedor, fechas | ✅ baja lógica | Movimientos → Entrada; Lotes → Corregir datos | CP4-05, CP4-06 |
| `movimiento` + `detalle_movimiento` | ✅ entrada, salida, devolución | ✅ | ✖ por diseño | ✖ por diseño | Movimientos | CP4-05, CP4-06 |
| `rol` | — | ✅ | — | — | Usuarios y roles (tabla de permisos) | CP4-01 |

- **`movimiento` y `detalle_movimiento`:** no se modifican ni se borran por regla de negocio (RN-09). El trigger de inmutabilidad lo impide en la base, y una corrección se hace con una devolución (movimiento inverso, RN-19 a RN-22).
- **`lote`:** su existencia nunca se edita a mano (la mantiene el trigger), y nace con la entrada que lo trae, para que ningún lote tenga existencia sin un movimiento que la explique.
- **`rol`:** catálogo de configuración. Cada rol de la aplicación corresponde a un rol de PostgreSQL con sus privilegios; agregar uno exige crear también el rol de base de datos y sus permisos, así que se hace por script (`sql/security/`), no desde la pantalla.

---

## Requerimientos funcionales

### Usuarios, roles y acceso

| Requerimiento | Base de datos | Aplicación web | Evidencia |
|---|---|---|---|
| RF-01 Iniciar sesión | `usuario`, `rol` | `routes/auth.py::login` | CP-01, CP-02, CP-03, CP4-01 |
| RF-02 Cerrar sesión | — (sesión) | `routes/auth.py::logout` | CP-05, CP4-01 |
| RF-03 Administrar usuarios | `usuario`; `GRANT INSERT/UPDATE` por columna a `rol_administrador` | `routes/usuarios.py`: crear, editar, restablecer contraseña, desactivar; cada usuario cambia su propia contraseña (`auth.cambiar_contrasena`, CP4-02) | Prueba automatizada (19 casos), CP4-09 |
| RF-04 Asignar roles | `usuario.id_rol` → `rol` (FK) | Selector de rol en `usuarios/form.html` | Prueba automatizada, CP4-09 |
| RF-05 Control de acceso por rol | 3 roles de BD con privilegios distintos (`sql/security/001_roles.sql`); la app adopta el rol con `SET ROLE` | `auth.rol_requerido()` en rutas, `tiene_rol()` en plantillas, error 403 | CP3-06, CP3-07, CP4-01, CP4-10 |

### Catálogos

| Requerimiento | Base de datos | Aplicación web | Evidencia |
|---|---|---|---|
| RF-06 a RF-08 Registrar, modificar y consultar productos | `producto` (806 productos reales) | `routes/productos.py`, con búsqueda, filtro y existencia | CP-11 a CP-14, CP4-03 |
| RF-09 Clasificar productos por categoría | `producto.id_categoria` → `categoria` | Selector y filtro por categoría | CP-11, CP-14, CP4-03 |
| RF-10 Administrar categorías | `categoria` | `routes/categorias.py` | CP-06 a CP-10, CP4-11 |
| RF-11 a RF-13 Registrar, modificar y consultar proveedores | `proveedor` (26 reales + 24 de prueba) | `routes/proveedores.py`: CRUD, detalle con precios | Prueba automatizada, CP4-04, CP4-11 |
| RF-36, RF-37 Registrar y modificar exámenes | `examen_laboratorio` (50); `estado` para baja lógica (`ddl/003`, RN-24) | `routes/examenes.py`: CRUD con baja lógica | Prueba automatizada, CP4-07 |
| RF-38 Insumos requeridos por examen | `examen_producto` (114, RN-17) | Detalle del examen: agregar y quitar insumos, "alcanza para N pruebas" | Prueba automatizada, CP4-07 |
| RF-39 Productos por proveedor con precio | `proveedor_producto` (425, RN-16) | Ficha del proveedor: asignar producto con precio, cambiar el precio y quitar (Entrega 4) | Prueba automatizada, CP4-04 |

### Lotes y existencias

| Requerimiento | Base de datos | Aplicación web | Evidencia |
|---|---|---|---|
| RF-14 Registrar lotes | `lote`; `sp_registrar_entrada` crea el lote en su primera entrada | Formulario de entrada | CP3-01, CP4-05 |
| RF-15 Lote asociado a un producto | `lote.id_producto` (FK), `UNIQUE (id_producto, numero_lote)` | Detalle del lote | CP3-01, CP4-05 |
| RF-16 Lote asociado a un proveedor | `lote.id_proveedor` (FK) | Selector de proveedor en la entrada | CP3-01, CP4-05 |
| RF-17, RF-18 Fecha de ingreso y de vencimiento | `lote.fecha_ingreso`, `lote.fecha_vencimiento`, `ck_lote_fecha_vencimiento`, trigger `trg_lote_vencimiento` (RN-07) | Formulario de entrada; corrección de datos del lote (administrador) | CP3-04, CP4-05 |
| RF-19 Existencias por lote | `lote.cantidad_disponible` (solo la cambia el trigger), `vw_existencia_producto` | `routes/lotes.py`: existencia, vencidos, por vencer, historial del lote | CP3-01, CP3-02, CP4-06 |

### Movimientos de inventario

| Requerimiento | Base de datos | Aplicación web | Evidencia |
|---|---|---|---|
| RF-20 Registrar entradas | `sp_registrar_entrada` | `routes/movimientos.py::entrada` | CP3-01, CP4-05 |
| RF-21 Registrar salidas | `sp_registrar_salida` (FEFO: primero el lote que vence antes, sin lotes vencidos) | `routes/movimientos.py::salida` | CP3-02, CP4-06 |
| RF-22 Actualizar existencia tras una entrada | Trigger `trg_detalle_movimiento_existencia` (RN-02) | — (automático) | CP3-01, CP4-05 |
| RF-23 Actualizar existencia tras una salida | Mismo trigger (RN-03) | — (automático) | CP3-02, CP4-06 |
| RF-24 Impedir salida mayor a la existencia | `sp_registrar_salida` y el trigger (RN-04) | Muestra el mensaje de la base al usuario | CP3-03 |
| RF-25 Impedir existencia negativa | `ck_lote_cantidad_disponible CHECK (>= 0)` + trigger (RN-01) | — | CP3-03 |
| RF-26 Fecha y hora de cada movimiento | `movimiento.fecha_hora` | Historial y detalle | CP3-01, CP4-05 |
| RF-27 Usuario responsable | `movimiento.id_usuario` (FK, RN-08) | Columna "Responsable" | CP3-01, CP4-05 |
| RF-28 Historial de movimientos | `vw_historial_movimientos`; triggers `trg_movimiento_inmutable` y `trg_detalle_movimiento_inmutable` (RN-09) | Pestañas Todos / Entradas / Salidas con filtros | CP3-05, CP4-06 |

### Consultas y reportes

| Requerimiento | Base de datos | Aplicación web | Evidencia |
|---|---|---|---|
| RF-29 Inventario bajo | `vw_inventario_bajo` (RN-10, RN-11) | Reporte "Inventario bajo", indicador en Inicio | Prueba automatizada, CP4-08 |
| RF-30 Próximos a vencer | `vw_lotes_por_vencer` (90 días) | Reporte "Vencimientos", pestañas de Lotes, Inicio | Prueba automatizada, CP4-08 |
| RF-31 Buscar productos | Consultas con `ILIKE` parametrizadas | Buscador en Productos, Lotes, Movimientos, Proveedores y Exámenes | Prueba automatizada, CP4-03 |
| RF-32 Filtrar información de inventario | Consultas parametrizadas | Filtros por categoría, fechas, tipo de movimiento y estado del lote | Prueba automatizada, CP4-08 |
| RF-33 Generar reportes de inventario | `fn_kardex_promedio`, `vw_valorizacion_inventario` (costo promedio ponderado) | `routes/informes.py`: pantalla única con 9 tipos de reporte, CSV e impresión | CP3-08, CP4-08 |
| RF-34 Consultar información histórica | `fn_kardex_promedio` (kardex con saldo inicial por período) | Kardex por producto, historial de movimientos | CP3-08, CP4-08 |
| RF-35 Trazabilidad de operaciones | Cada detalle enlaza movimiento → lote → producto → proveedor; historial inmutable | Del movimiento al lote y del lote a sus movimientos | CP3-02, CP3-05, CP4-06 |

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
| RN-16 Producto–proveedor N:M con precio | `proveedor_producto`, administrable desde la ficha del proveedor | CP4-04 |
| RN-17 Examen–producto N:M con cantidad | `examen_producto` | CP4-07 |
| RN-18 Movimiento–lote N:M | `detalle_movimiento` (una salida FEFO puede tocar varios lotes) | CP3-02 |

---

## Requerimientos no funcionales

| Requerimiento | Implementación | Estado |
|---|---|---|
| RNF-01 Navegador web | Flask + plantillas HTML | ✅ |
| RNF-02 Base de datos relacional | PostgreSQL 18, 11 tablas en 3FN | ✅ |
| RNF-03 Autenticación | Login con sesión firmada | ✅ |
| RNF-04, RNF-05 Contraseñas con hash | `generate_password_hash` (scrypt) / `check_password_hash`; cambio de contraseña propio confirmando la actual (CP4-02) | ✅ |
| RNF-06 Acceso por roles | Doble capa: app (`rol_requerido`) y base de datos (`SET ROLE`) | ✅ |
| RNF-07, RNF-08 Integridad | Restricciones del DDL (PK, FK, UNIQUE, CHECK, NOT NULL), 5 triggers y 3 procedimientos atómicos | ✅ |
| RNF-09, RNF-10 Interfaz clara y mensajes | Los mensajes de las reglas de negocio llegan tal cual al usuario (SQLSTATE P0001); nunca se muestra SQL | ✅ |
| RNF-11 Respaldos | `web/respaldo.py` + Administración → Respaldo: archivo `.sql` restaurable con `psql` en una sola transacción. Procedimiento en el manual técnico, sección 7 (CP4-10, CP4-13) | ✅ Entrega 4 |
| RNF-12, RNF-13 Arquitectura mantenible y ampliable | Capas `config` / `db` / `routes` / `templates`; SQL separado por propósito | ✅ |
| RNF-14 Tiempo de respuesta | Listas paginadas; el kardex de los 806 productos se calcula en ~18 ms | ✅ |
| RNF-15 Validar antes de modificar inventario | Validación en el servidor + procedimientos + triggers | ✅ |
| RNF-16 Información para trazabilidad | Historial inmutable con usuario, fecha y lote | ✅ |
| RNF-17 Evitar accesos no autorizados | Rutas protegidas, 403, `SET ROLE`, redirección de login solo a rutas internas; desde la Entrega 4, encabezados de seguridad (CSP, X-Frame-Options, HSTS) y rechazo de POST de otro origen | ✅ |
| RNF-18 Interfaz adaptable | Diseño responsivo verificado a 1440 px y 390 px, sin desbordamiento horizontal (CP4-12) | ✅ |

---

## Devolución de salidas (agregada el 29/09/2026)

Reglas de negocio nuevas, propuestas por el equipo. No provienen de los 39 RF: nacen de una carencia detectada al usar el sistema, que una salida mal registrada no se podía corregir porque el historial es inmutable (RN-09).

| Regla | Qué exige | Dónde se implementa | Prueba |
|---|---|---|---|
| **RN-19** | Toda devolución corrige exactamente una salida y conserva el vínculo | `movimiento.id_movimiento_origen` + `fk_movimiento_origen` y el `CHECK ck_movimiento_devolucion` | CP3-09 |
| **RN-20** | Toda devolución declara por escrito su motivo | `movimiento.motivo`, exigido por el mismo CHECK y por `sp_registrar_devolucion` | CP3-10b |
| **RN-21** | La devolución repone la existencia del lote del que salió | `fn_detalle_movimiento_existencia`, rama `DEVOLUCION` | CP3-09, CP3-11 |
| **RN-22** | No se devuelve más de lo que salió, descontando lo ya devuelto | `fn_devolucion_tope` (trigger) y `fn_devolvible` (saldo por lote) | CP3-10, CP3-11 |
| **RN-23** | La devolución reingresa al costo promedio vigente, sin alterarlo | `fn_kardex_promedio`, rama `DEVOLUCION` (`views/004`) | CP3-12 |

| Requerimiento afectado | Cómo lo amplía la devolución |
|---|---|
| RF-28, RF-35 Historial y trazabilidad | La corrección de un error queda en el historial como movimiento propio, con su responsable, su motivo y el vínculo a lo corregido |
| RF-05 Control por rol | Registrar una devolución es escritura: solo Administrador y Encargado, en la app y en la base (CP3-12b) |
| RF-33, RF-34 Reportes | `vw_devoluciones` resume qué se devolvió, de qué salida y por qué |

---

## Agregado en la Entrega 4

| Pieza | Requerimiento o regla | Implementación | Prueba |
|---|---|---|---|
| Respaldo y restauración | RNF-11 | `web/respaldo.py`, `routes/respaldo.py`, Administración → Respaldo; restauración con `psql` | CP4-10, CP4-13 |
| Productos de cada proveedor | RF-39, RN-16 | Ficha del proveedor: asignar, cambiar precio y quitar (`proveedores.guardar_producto`, `quitar_producto`) | CP4-04 |
| Baja lógica de exámenes | RF-36, RF-37, **RN-24**: un examen de baja no aparece en el informe de pruebas, pero conserva su ficha e insumos | `sql/ddl/003_examen_estado.sql`, `examenes.alternar_estado`, filtro en `informes.pruebas` | CP4-07 |
| Cambiar mi contraseña | RF-03, RNF-04, RNF-17 | `auth.cambiar_contrasena`, sobre `db.conexion_sin_rol()` | CP4-02 |
| Encabezados de seguridad y verificación de origen | RNF-17 | `app.encabezados_de_seguridad`, `app.mismo_origen` | Prueba automatizada (16 verificaciones) |
| Devolución mostrada como reingreso en kardex, ficha del lote e Inicio | RN-21, RN-23 | `informes/kardex.html`, `lotes/detalle.html`, `reportes/inicio.html` | CP4-06, CP4-08 |
| Manuales técnico y de usuario | Consigna, Entrega 4 | `docs/entrega-4/` | CP4-01 a CP4-14 siguen sus flujos |
