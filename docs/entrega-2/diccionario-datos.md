# Fase 4 — Diccionario de datos

Coincide exactamente con [`sql/ddl/001_schema.sql`](../../sql/ddl/001_schema.sql). Si se modifica uno, debe actualizarse el otro.

## `rol`
Catálogo de roles de acceso al sistema.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_rol | INTEGER (IDENTITY) | — | ✅ | | NOT NULL | | auto | | Identificador del rol |
| nombre | VARCHAR | 50 | | | NOT NULL | ✅ | | | Nombre del rol (Administrador, Encargado de inventario, Usuario de consulta) |
| descripcion | VARCHAR | 255 | | | NULL | | | | Detalle del rol |

## `usuario`
Cuentas de acceso. RF-01 a RF-05.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_usuario | INTEGER (IDENTITY) | — | ✅ | | NOT NULL | | auto | | Identificador del usuario |
| id_rol | INTEGER | — | | → rol | NOT NULL | | | | Rol asignado (RN-14) |
| nombre | VARCHAR | 100 | | | NOT NULL | | | | Nombre completo de la persona |
| usuario | VARCHAR | 50 | | | NOT NULL | ✅ | | | Nombre de inicio de sesión |
| password_hash | VARCHAR | 255 | | | NOT NULL | | | | Hash de la contraseña (RN-15) — nunca texto plano |
| estado | BOOLEAN | — | | | NOT NULL | | TRUE | | Activo/inactivo (baja lógica) |
| fecha_creacion | TIMESTAMP | — | | | NOT NULL | | now() | | Auditoría de alta |

## `categoria`
Clasificación de productos. RN-13.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_categoria | INTEGER (IDENTITY) | — | ✅ | | NOT NULL | | auto | | Identificador |
| nombre | VARCHAR | 100 | | | NOT NULL | ✅ | | | Nombre de la categoría |
| descripcion | VARCHAR | 255 | | | NULL | | | | Detalle |
| estado | BOOLEAN | — | | | NOT NULL | | TRUE | | Activa/inactiva |

## `producto`
Catálogo de productos/insumos. RF-06 a RF-10.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_producto | INTEGER (IDENTITY) | — | ✅ | | NOT NULL | | auto | | Identificador |
| id_categoria | INTEGER | — | | → categoria | NOT NULL | | | | RN-13 |
| codigo | VARCHAR | 30 | | | NOT NULL | ✅ | | | Código interno |
| nombre | VARCHAR | 150 | | | NOT NULL | | | | Nombre del producto |
| descripcion | VARCHAR | 255 | | | NULL | | | | Detalle |
| unidad_medida | VARCHAR | 20 | | | NOT NULL | | | length(trim())>0 | Unidad de manejo |
| stock_minimo | NUMERIC | 10,2 | | | NOT NULL | | 0 | >=0 | RN-10, base de RN-11 |
| requiere_vencimiento | BOOLEAN | — | | | NOT NULL | | TRUE | | RN-07: si sus lotes deben tener fecha de vencimiento |
| estado | BOOLEAN | — | | | NOT NULL | | TRUE | | Activo/inactivo |

## `proveedor`
RF-11 a RF-13.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_proveedor | INTEGER (IDENTITY) | — | ✅ | | NOT NULL | | auto | | Identificador |
| nombre | VARCHAR | 150 | | | NOT NULL | | | | Razón social |
| nit | VARCHAR | 20 | | | NOT NULL | ✅ | | | Identificación tributaria |
| telefono | VARCHAR | 20 | | | NULL | | | | Contacto |
| correo | VARCHAR | 150 | | | NULL | | | | Contacto |
| direccion | VARCHAR | 255 | | | NULL | | | | Dirección física |
| estado | BOOLEAN | — | | | NOT NULL | | TRUE | | Activo/inactivo |

## `lote`
Control de lotes/vencimientos/existencia. RF-14 a RF-19.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_lote | INTEGER (IDENTITY) | — | ✅ | | NOT NULL | | auto | | Identificador técnico |
| id_producto | INTEGER | — | | → producto | NOT NULL | | | | RN-05 |
| id_proveedor | INTEGER | — | | → proveedor | NOT NULL | | | | RN-12 |
| numero_lote | VARCHAR | 50 | | | NOT NULL | ✅ (junto a id_producto) | | | Identificador de negocio del lote (RN-06: único por producto) |
| fecha_ingreso | DATE | — | | | NOT NULL | | CURRENT_DATE | | RF-17 |
| fecha_vencimiento | DATE | — | | | NULL | | | >= fecha_ingreso | RF-18, RN-07 (nulo si `producto.requiere_vencimiento = FALSE`) |
| cantidad_disponible | NUMERIC | 10,2 | | | NOT NULL | | 0 | >=0 | RN-01: nunca negativa |
| estado | BOOLEAN | — | | | NOT NULL | | TRUE | | Activo/inactivo/agotado |

## `movimiento`
Encabezado de entrada/salida. RF-20, RF-21, RF-26 a RF-28.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_movimiento | INTEGER (IDENTITY) | — | ✅ | | NOT NULL | | auto | | Identificador |
| id_usuario | INTEGER | — | | → usuario | NOT NULL | | | | RF-27, RN-08: responsable del movimiento |
| tipo_movimiento | VARCHAR | 10 | | | NOT NULL | | | IN ('ENTRADA','SALIDA') | RF-20/RF-21 |
| fecha_hora | TIMESTAMP | — | | | NOT NULL | | now() | | RF-26 |
| observacion | VARCHAR | 255 | | | NULL | | | | Nota libre |

## `detalle_movimiento`
Resuelve MOVIMIENTO↔LOTE (N:M conceptual). RN-18, RF-22, RF-23.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_detalle | INTEGER (IDENTITY) | — | ✅ | | NOT NULL | | auto | | Identificador |
| id_movimiento | INTEGER | — | | → movimiento | NOT NULL | | | | Movimiento al que pertenece |
| id_lote | INTEGER | — | | → lote | NOT NULL | | | | Lote afectado |
| cantidad | NUMERIC | 10,2 | | | NOT NULL | | | >0 | Cantidad afectada (usada para sumar/restar `lote.cantidad_disponible`) |
| precio_unitario | NUMERIC | 10,2 | | | NOT NULL | | 0 | >=0 | Valor de la operación |

## `examen_laboratorio`
Catálogo de exámenes clínicos. RF-36, RF-37.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_examen | INTEGER (IDENTITY) | — | ✅ | | NOT NULL | | auto | | Identificador |
| nombre_examen | VARCHAR | 150 | | | NOT NULL | | | | Nombre del examen |
| descripcion | VARCHAR | 255 | | | NULL | | | | Detalle |
| codigo_interno | VARCHAR | 30 | | | NOT NULL | ✅ | | | Código del examen |

## `proveedor_producto` (tabla puente — "Suministra")
RN-16, RF-39.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_proveedor | INTEGER | — | ✅ (compuesta) | → proveedor | NOT NULL | | | | |
| id_producto | INTEGER | — | ✅ (compuesta) | → producto | NOT NULL | | | | |
| precio_compra | NUMERIC | 10,2 | | | NOT NULL | | | >=0 | Precio pactado con ese proveedor |

## `examen_producto` (tabla puente — "Requiere")
RN-17, RF-38.

| Campo | Tipo | Tamaño | PK | FK | Nulo | Unique | Default | Check | Descripción |
|---|---|---|---|---|---|---|---|---|---|
| id_examen | INTEGER | — | ✅ (compuesta) | → examen_laboratorio | NOT NULL | | | | |
| id_producto | INTEGER | — | ✅ (compuesta) | → producto | NOT NULL | | | | |
| cantidad_requerida | NUMERIC | 10,2 | | | NOT NULL | | | >0 | Cantidad del insumo que consume ese examen |

---

## Matriz de restricciones explícitas

La consigna exige mínimo 15. Se cuentan solo las que existen literalmente en `001_schema.sql` (no se inflan):

| # | Restricción | Tabla | Campo(s) | Tipo | Regla de negocio asociada |
|---|---|---|---|---|---|
| 1 | pk_rol | rol | id_rol | PK | — |
| 2 | uq_rol_nombre | rol | nombre | UNIQUE | — |
| 3 | pk_usuario | usuario | id_usuario | PK | — |
| 4 | uq_usuario_usuario | usuario | usuario | UNIQUE | RF-01 |
| 5 | fk_usuario_rol | usuario | id_rol | FK | RN-14 |
| 6 | pk_categoria | categoria | id_categoria | PK | — |
| 7 | uq_categoria_nombre | categoria | nombre | UNIQUE | — |
| 8 | pk_producto | producto | id_producto | PK | — |
| 9 | uq_producto_codigo | producto | codigo | UNIQUE | — |
| 10 | ck_producto_unidad_medida | producto | unidad_medida | CHECK | — |
| 11 | ck_producto_stock_minimo | producto | stock_minimo | CHECK | RN-10 |
| 12 | fk_producto_categoria | producto | id_categoria | FK | RN-13 |
| 13 | pk_proveedor | proveedor | id_proveedor | PK | — |
| 14 | uq_proveedor_nit | proveedor | nit | UNIQUE | — |
| 15 | pk_lote | lote | id_lote | PK | — |
| 16 | uq_lote_producto_numero | lote | id_producto, numero_lote | UNIQUE | RN-06 |
| 17 | ck_lote_cantidad_disponible | lote | cantidad_disponible | CHECK | RN-01 |
| 18 | ck_lote_fecha_vencimiento | lote | fecha_vencimiento | CHECK | RN-07 |
| 19 | fk_lote_producto | lote | id_producto | FK | RN-05 |
| 20 | fk_lote_proveedor | lote | id_proveedor | FK | RN-12 |
| 21 | pk_movimiento | movimiento | id_movimiento | PK | — |
| 22 | ck_movimiento_tipo | movimiento | tipo_movimiento | CHECK | RF-20/RF-21 |
| 23 | fk_movimiento_usuario | movimiento | id_usuario | FK | RF-27, RN-08 |
| 24 | pk_detalle_movimiento | detalle_movimiento | id_detalle | PK | — |
| 25 | ck_detalle_cantidad | detalle_movimiento | cantidad | CHECK | — |
| 26 | ck_detalle_precio_unitario | detalle_movimiento | precio_unitario | CHECK | — |
| 27 | fk_detalle_movimiento | detalle_movimiento | id_movimiento | FK | RN-18 |
| 28 | fk_detalle_lote | detalle_movimiento | id_lote | FK | RN-18 |
| 29 | pk_examen_laboratorio | examen_laboratorio | id_examen | PK | — |
| 30 | uq_examen_codigo_interno | examen_laboratorio | codigo_interno | UNIQUE | — |
| 31 | pk_proveedor_producto | proveedor_producto | id_proveedor, id_producto | PK | RN-16 |
| 32 | ck_proveedor_producto_precio | proveedor_producto | precio_compra | CHECK | — |
| 33 | fk_proveedor_producto_proveedor | proveedor_producto | id_proveedor | FK | RN-16 |
| 34 | fk_proveedor_producto_producto | proveedor_producto | id_producto | FK | RN-16 |
| 35 | pk_examen_producto | examen_producto | id_examen, id_producto | PK | RN-17 |
| 36 | ck_examen_producto_cantidad | examen_producto | cantidad_requerida | CHECK | — |
| 37 | fk_examen_producto_examen | examen_producto | id_examen | FK | RN-17 |
| 38 | fk_examen_producto_producto | examen_producto | id_producto | FK | RN-17 |

**Total: 38 restricciones explícitas** (11 PK + 11 FK + 7 UNIQUE + 9 CHECK) — más del doble del mínimo de 15 exigido. No se cuentan los `NOT NULL` individuales (habría decenas más) para no inflar la cifra con algo trivial.
