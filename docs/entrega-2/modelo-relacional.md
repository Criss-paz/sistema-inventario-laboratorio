# Fase 2 — Modelo relacional

**Proyecto:** Sistema Web de Gestión y Control de Inventario — Laboratorio Privado Quetzaltenango
**SGBD:** PostgreSQL (decidido en Fase 1, ver `Bitacora-IA.md`)
**Convención de nombres:** `snake_case`, singular, sin prefijos de tipo de dato.
**Nota de corrección:** en el resumen de la Fase 1 dije "12 tablas"; al construir el modelo formal son **11** (9 entidades de la Entrega 1 + 2 tablas puente `proveedor_producto` y `examen_producto` — `detalle_movimiento` ya era una de las 9, no se suma aparte). Corrijo aquí el conteo.

## Cómo se transforma cada relación del ER

| Relación en el ER | Cardinalidad | Transformación al modelo relacional |
|---|---|---|
| ROL — USUARIO ("Tiene") | 1:N | FK `usuario.id_rol` → `rol.id_rol` (FK en el lado N) |
| CATEGORIA — PRODUCTO ("Clasifica") | 1:N | FK `producto.id_categoria` → `categoria.id_categoria` |
| USUARIO — MOVIMIENTO ("Registra") | 1:N | FK `movimiento.id_usuario` → `usuario.id_usuario` (RF-27, RN-08) |
| PRODUCTO — LOTE ("Posee") | 1:N | FK `lote.id_producto` → `producto.id_producto` |
| PROVEEDOR — LOTE ("Abastece") | 1:N | FK `lote.id_proveedor` → `proveedor.id_proveedor` |
| PROVEEDOR — PRODUCTO ("Suministra") | N:M | Tabla puente `proveedor_producto` con PK compuesta `(id_proveedor, id_producto)` + atributo propio `precio_compra` |
| EXAMEN_LABORATORIO — PRODUCTO ("Requiere") | N:M | Tabla puente `examen_producto` con PK compuesta `(id_examen, id_producto)` + atributo propio `cantidad_requerida` |
| MOVIMIENTO — LOTE (conceptual N:M, ya resuelta en el ER con `DETALLE_MOVIMIENTO`) | 1:N y 1:N | `detalle_movimiento` con PK propia `id_detalle` + FK `id_movimiento` + FK `id_lote` (dos relaciones 1:N, no requiere PK compuesta porque el ER ya trajo la entidad asociativa resuelta) |

Regla general aplicada: en toda relación 1:N la FK vive en la tabla del lado "N"; en toda relación N:M sin atributos propios se crearía una tabla puente con PK compuesta por ambas FK — aquí ambas N:M (`Suministra`, `Requiere`) sí tienen atributos propios (`precio_compra`, `cantidad_requerida`), así que esos atributos viajan a la tabla puente junto con las dos FK.

---

## 1. `rol`
**Propósito:** catálogo de roles de acceso (RN-14, RF-04, RF-05).
**PK:** `id_rol`. **FK:** ninguna.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_rol | INTEGER GENERATED ALWAYS AS IDENTITY | NOT NULL | — | PK | Identificador del rol |
| nombre | VARCHAR(50) | NOT NULL | — | UNIQUE | Nombre del rol (Administrador, Encargado de inventario, Usuario de consulta — RF-03 actores) |
| descripcion | VARCHAR(255) | NULL | — | — | Detalle del rol |

---

## 2. `usuario`
**Propósito:** cuentas de acceso al sistema (RF-01 a RF-05, RNF-04/05).
**PK:** `id_usuario`. **FK:** `id_rol` → `rol.id_rol`.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_usuario | INTEGER GENERATED ALWAYS AS IDENTITY | NOT NULL | — | PK | Identificador del usuario |
| id_rol | INTEGER | NOT NULL | — | FK → rol, ON DELETE RESTRICT, ON UPDATE CASCADE | RN-14: todo usuario debe tener rol |
| nombre | VARCHAR(100) | NOT NULL | — | — | Nombre completo de la persona |
| usuario | VARCHAR(50) | NOT NULL | — | UNIQUE | Nombre de inicio de sesión (RF-01) |
| password_hash | VARCHAR(255) | NOT NULL | — | — | Hash (nunca texto plano — RN-15, RNF-04/05) |
| estado | BOOLEAN | NOT NULL | TRUE | — | Activo/inactivo (baja lógica) |
| fecha_creacion | TIMESTAMP | NOT NULL | now() | — | Auditoría de alta del usuario |

`ON DELETE RESTRICT` en `id_rol`: un rol en uso no puede borrarse (evita usuarios huérfanos); si el equipo decide que los roles nunca se eliminan (solo se desactivan), este RESTRICT es una red de seguridad adicional, no la única defensa.

---

## 3. `categoria`
**Propósito:** clasificación de productos (RF-09, RF-10, RN-13).
**PK:** `id_categoria`. **FK:** ninguna.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_categoria | INTEGER GENERATED ALWAYS AS IDENTITY | NOT NULL | — | PK | Identificador |
| nombre | VARCHAR(100) | NOT NULL | — | UNIQUE | Nombre de la categoría |
| descripcion | VARCHAR(255) | NULL | — | — | Detalle |
| estado | BOOLEAN | NOT NULL | TRUE | — | Activa/inactiva |

---

## 4. `producto`
**Propósito:** catálogo de productos/insumos del laboratorio (RF-06 a RF-10).
**PK:** `id_producto`. **FK:** `id_categoria` → `categoria.id_categoria`.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_producto | INTEGER GENERATED ALWAYS AS IDENTITY | NOT NULL | — | PK | Identificador |
| id_categoria | INTEGER | NOT NULL | — | FK → categoria, ON DELETE RESTRICT, ON UPDATE CASCADE | RN-13 |
| codigo | VARCHAR(30) | NOT NULL | — | UNIQUE | Código interno del producto |
| nombre | VARCHAR(150) | NOT NULL | — | — | Nombre del producto |
| descripcion | VARCHAR(255) | NULL | — | — | Detalle |
| unidad_medida | VARCHAR(20) | NOT NULL | — | CHECK (length(trim(unidad_medida)) > 0) | Unidad de manejo (unidad, caja, ml, etc.) |
| stock_minimo | NUMERIC(10,2) | NOT NULL | 0 | CHECK (stock_minimo >= 0) | RN-10, base de RN-11 (inventario bajo) |
| requiere_vencimiento | BOOLEAN | NOT NULL | TRUE | — | RN-07: indica si los lotes de este producto deben registrar `fecha_vencimiento` |
| estado | BOOLEAN | NOT NULL | TRUE | — | Activo/inactivo |

`ON DELETE RESTRICT` en `id_categoria`: si se permitiera `CASCADE`, borrar una categoría borraría en cascada todos sus productos y, por arrastre, sus lotes y movimientos históricos — violaría RN-09 (los movimientos deben conservarse como historial). Por eso categorías y productos se dan de baja con `estado`, nunca con `DELETE` físico desde la aplicación.

---

## 5. `proveedor`
**Propósito:** proveedores del laboratorio (RF-11 a RF-13).
**PK:** `id_proveedor`. **FK:** ninguna.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_proveedor | INTEGER GENERATED ALWAYS AS IDENTITY | NOT NULL | — | PK | Identificador |
| nombre | VARCHAR(150) | NOT NULL | — | — | Razón social o nombre |
| nit | VARCHAR(20) | NOT NULL | — | UNIQUE | Identificación tributaria |
| telefono | VARCHAR(20) | NULL | — | — | Contacto |
| correo | VARCHAR(150) | NULL | — | — | Contacto |
| direccion | VARCHAR(255) | NULL | — | — | Dirección física |
| estado | BOOLEAN | NOT NULL | TRUE | — | Activo/inactivo |

---

## 6. `lote`
**Propósito:** control de lotes, vencimientos y existencia disponible (RF-14 a RF-19, RN-01, RN-05 a RN-07).
**PK:** `id_lote`. **FK:** `id_producto` → `producto.id_producto`; `id_proveedor` → `proveedor.id_proveedor`.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_lote | INTEGER GENERATED ALWAYS AS IDENTITY | NOT NULL | — | PK | Identificador técnico |
| id_producto | INTEGER | NOT NULL | — | FK → producto, ON DELETE RESTRICT, ON UPDATE CASCADE | RN-05: un producto puede tener múltiples lotes |
| id_proveedor | INTEGER | NOT NULL | — | FK → proveedor, ON DELETE RESTRICT, ON UPDATE CASCADE | RN-12 |
| numero_lote | VARCHAR(50) | NOT NULL | — | UNIQUE junto con id_producto (ver abajo) | Identificador de negocio del lote |
| fecha_ingreso | DATE | NOT NULL | CURRENT_DATE | — | RF-17 |
| fecha_vencimiento | DATE | NULL | — | CHECK (fecha_vencimiento IS NULL OR fecha_vencimiento >= fecha_ingreso) | RF-18, RN-07 — nulo si el producto no requiere control de vencimiento |
| cantidad_disponible | NUMERIC(10,2) | NOT NULL | 0 | CHECK (cantidad_disponible >= 0) | RN-01 — nunca negativa |
| estado | BOOLEAN | NOT NULL | TRUE | — | Activo/inactivo/agotado |

**Restricción compuesta:** `UNIQUE (id_producto, numero_lote)` — **no** `numero_lote` global único. RN-06 dice explícitamente que el número de lote debe identificar el lote "dentro del contexto del producto", es decir, dos productos distintos sí pueden compartir el mismo número de lote de fábrica; lo que no puede repetirse es el mismo número de lote dos veces para el mismo producto.

`fecha_vencimiento` nullable: RN-07 la exige *solo cuando el producto requiere control de vencimiento*, condición que ahora vive explícitamente en `producto.requiere_vencimiento`. Como la validación cruza dos tablas, no puede expresarse con un `CHECK` simple de PostgreSQL (los CHECK solo ven la fila propia): en la Entrega 2 se valida en la capa de lógica de negocio de la app web antes de insertar/actualizar un lote, y en la Entrega 3 se refuerza con un trigger `BEFORE INSERT/UPDATE` sobre `lote` que consulte `producto.requiere_vencimiento`.

---

## 7. `movimiento`
**Propósito:** encabezado de cada entrada/salida (RF-20, RF-21, RF-26 a RF-28).
**PK:** `id_movimiento`. **FK:** `id_usuario` → `usuario.id_usuario`.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_movimiento | INTEGER GENERATED ALWAYS AS IDENTITY | NOT NULL | — | PK | Identificador |
| id_usuario | INTEGER | NOT NULL | — | FK → usuario, ON DELETE RESTRICT, ON UPDATE CASCADE | RF-27, RN-08: todo movimiento debe tener usuario responsable |
| tipo_movimiento | VARCHAR(10) | NOT NULL | — | CHECK (tipo_movimiento IN ('ENTRADA','SALIDA')) | RF-20/RF-21 — dominio cerrado de 2 valores; no se crea tabla catálogo aparte (evita sobreingeniería, Regla 4) |
| fecha_hora | TIMESTAMP | NOT NULL | now() | — | RF-26 |
| observacion | VARCHAR(255) | NULL | — | — | Nota libre |

`ON DELETE RESTRICT` en `id_usuario`: un usuario con movimientos registrados no puede eliminarse físicamente (RN-09, historial); se da de baja con `estado`.
No se expondrá operación de `DELETE` sobre `movimiento` en la aplicación web — es historial de auditoría, solo INSERT/SELECT (RF-28, RF-34, RF-35, RNF-16).

---

## 8. `detalle_movimiento`
**Propósito:** resuelve la relación conceptual N:M entre `MOVIMIENTO` y `LOTE` — qué lote(s) y en qué cantidad afectó cada movimiento (RN-18).
**PK:** `id_detalle`. **FK:** `id_movimiento` → `movimiento.id_movimiento`; `id_lote` → `lote.id_lote`.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_detalle | INTEGER GENERATED ALWAYS AS IDENTITY | NOT NULL | — | PK | Identificador |
| id_movimiento | INTEGER | NOT NULL | — | FK → movimiento, ON DELETE RESTRICT, ON UPDATE CASCADE | Un movimiento puede tener varios detalles (varios lotes afectados) |
| id_lote | INTEGER | NOT NULL | — | FK → lote, ON DELETE RESTRICT, ON UPDATE CASCADE | Un lote puede aparecer en varios detalles a través del tiempo |
| cantidad | NUMERIC(10,2) | NOT NULL | — | CHECK (cantidad > 0) | RF-22/RF-23 la usan para sumar/restar `lote.cantidad_disponible` |
| precio_unitario | NUMERIC(10,2) | NOT NULL | 0 | CHECK (precio_unitario >= 0) | Valor de la operación |

`ON DELETE RESTRICT` en ambas FK (no `CASCADE`): si se borrara un `movimiento`, no queremos que sus `detalle_movimiento` desaparezcan en silencio arrastrando ajustes de inventario ya aplicados — de nuevo, en la práctica `movimiento` no se borra nunca desde la app.
Aquí es donde en la Entrega 3 vivirá el trigger que aplica RN-02/RN-03/RN-04 (sumar en ENTRADA, restar en SALIDA, y para SALIDA validar contra `lote.cantidad_disponible` antes de restar). En la Entrega 2 esa validación se hace en la capa de lógica de negocio de la app web, no en la base de datos todavía — así queda explícito para la defensa oral.

---

## 9. `examen_laboratorio`
**Propósito:** catálogo de exámenes clínicos (RF-36, RF-37).
**PK:** `id_examen`. **FK:** ninguna.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_examen | INTEGER GENERATED ALWAYS AS IDENTITY | NOT NULL | — | PK | Identificador |
| nombre_examen | VARCHAR(150) | NOT NULL | — | — | Nombre del examen |
| descripcion | VARCHAR(255) | NULL | — | — | Detalle |
| codigo_interno | VARCHAR(30) | NOT NULL | — | UNIQUE | Código del examen |

---

## 10. `proveedor_producto` (tabla puente — relación "Suministra")
**Propósito:** qué proveedores suministran qué productos y a qué precio (RN-16, RF-39).
**PK compuesta:** `(id_proveedor, id_producto)`. **FK:** `id_proveedor` → `proveedor.id_proveedor`; `id_producto` → `producto.id_producto`.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_proveedor | INTEGER | NOT NULL | — | PK (compuesta), FK → proveedor, ON DELETE CASCADE, ON UPDATE CASCADE | |
| id_producto | INTEGER | NOT NULL | — | PK (compuesta), FK → producto, ON DELETE CASCADE, ON UPDATE CASCADE | |
| precio_compra | NUMERIC(10,2) | NOT NULL | — | CHECK (precio_compra >= 0) | Precio pactado con ese proveedor para ese producto |

`ON DELETE CASCADE` aquí sí es correcto (a diferencia de `lote`/`movimiento`): esta tabla solo describe *qué relación comercial existe*, no historial de operaciones. Si un producto o proveedor se elimina físicamente, no tiene sentido conservar la fila de "quién lo suministraba".

---

## 11. `examen_producto` (tabla puente — relación "Requiere")
**Propósito:** insumos requeridos por cada examen y en qué cantidad (RN-17, RF-38).
**PK compuesta:** `(id_examen, id_producto)`. **FK:** `id_examen` → `examen_laboratorio.id_examen`; `id_producto` → `producto.id_producto`.

| Campo | Tipo | Nulo | Default | Restricciones | Descripción |
|---|---|---|---|---|---|
| id_examen | INTEGER | NOT NULL | — | PK (compuesta), FK → examen_laboratorio, ON DELETE CASCADE, ON UPDATE CASCADE | |
| id_producto | INTEGER | NOT NULL | — | PK (compuesta), FK → producto, ON DELETE CASCADE, ON UPDATE CASCADE | |
| cantidad_requerida | NUMERIC(10,2) | NOT NULL | — | CHECK (cantidad_requerida > 0) | Cantidad del insumo que consume ese examen |

---

## Resumen de integridad referencial

| Tabla hija | FK | Tabla padre | ON DELETE | ON UPDATE | Razón |
|---|---|---|---|---|---|
| usuario | id_rol | rol | RESTRICT | CASCADE | No dejar usuarios sin rol |
| producto | id_categoria | categoria | RESTRICT | CASCADE | No perder historial en cascada |
| lote | id_producto | producto | RESTRICT | CASCADE | Idem |
| lote | id_proveedor | proveedor | RESTRICT | CASCADE | Idem |
| movimiento | id_usuario | usuario | RESTRICT | CASCADE | RN-09: preservar historial |
| detalle_movimiento | id_movimiento | movimiento | RESTRICT | CASCADE | RN-09 |
| detalle_movimiento | id_lote | lote | RESTRICT | CASCADE | RN-09 |
| proveedor_producto | id_proveedor | proveedor | CASCADE | CASCADE | Solo describe relación comercial vigente |
| proveedor_producto | id_producto | producto | CASCADE | CASCADE | Idem |
| examen_producto | id_examen | examen_laboratorio | CASCADE | CASCADE | Idem |
| examen_producto | id_producto | producto | CASCADE | CASCADE | Idem |

**Patrón aplicado:** las tablas que forman parte del *historial transaccional* (`movimiento`, `detalle_movimiento`) y sus catálogos base (`rol`, `categoria`, `producto`, `proveedor`) usan `RESTRICT` — todo se da de baja con `estado`, nunca se borra físicamente, porque RN-09 exige conservar los movimientos. Las tablas puente que solo describen relaciones vigentes (`proveedor_producto`, `examen_producto`) usan `CASCADE` porque no tienen valor histórico propio.

---

## Decisiones cerradas (autorizadas por el equipo el 30/08/2026)

**1. `unidad_medida` queda como texto libre (`VARCHAR(20)`), no como catálogo aparte.**
Justificación: no hay ningún RF que pida administrar/mantener un catálogo de unidades (dar de alta, editar, desactivar una unidad de medida) — solo se usa como etiqueta descriptiva del producto. Crear una tabla `unidad_medida` para eso sería una entidad sin caso de uso propio, es decir, sobreingeniería (Regla 4). Si en una entrega futura surge el requerimiento de administrarlas, se normaliza entonces.

**2. `fecha_vencimiento` nula se resuelve agregando `producto.requiere_vencimiento` (BOOLEAN NOT NULL DEFAULT TRUE).**
Justificación: a diferencia del punto anterior, esto sí lo exige una regla de negocio explícita (RN-07), no es una entidad nueva sino un solo atributo en una tabla que ya existía — no viola Regla 4. Se agregó a `producto` (ver tabla arriba) y se documentó que su validación cruzada con `lote.fecha_vencimiento` se hace en la app en Entrega 2 y con trigger en Entrega 3, porque un `CHECK` de una sola tabla no puede mirar otra tabla.

**3. Ningún flujo de la aplicación web expondrá `DELETE` físico sobre `producto`, `categoria`, `proveedor`, `usuario`, `movimiento`, `lote` ni `detalle_movimiento`.**
Justificación: es la política que ya asumía el diseño de `ON DELETE RESTRICT` en el resumen de integridad referencial (RN-09: los movimientos deben conservarse como historial). Queda formalizado aquí como regla de arquitectura para la Fase 8 (arquitectura web): las bajas siempre son lógicas vía el campo `estado`; el único `DELETE` real permitido en la base son los `ON DELETE CASCADE` de las tablas puente (`proveedor_producto`, `examen_producto`), que no tienen valor histórico.
