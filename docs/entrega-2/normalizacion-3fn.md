# Fase 3 — Normalización hasta 3FN

No basta con decir "está en 3FN porque cada tabla tiene PK". Aquí se demuestra con dependencias funcionales (DF) reales, usando como ejemplo la parte más compleja del modelo: el registro de un movimiento de inventario y lo que afecta.

## Situación inicial (sin normalizar)

Antes del sistema, este es exactamente el tipo de reporte plano que el laboratorio llevaría en una hoja de Excel (el problema que describe la Entrega 1, sección "Identificación del problema"): una fila por cada línea de movimiento, con todo mezclado.

**`registro_inventario_plano`**

| id_movimiento | fecha_hora | tipo_movimiento | id_usuario | nombre_usuario | id_lote | numero_lote | id_producto | nombre_producto | id_categoria | nombre_categoria | cantidad | precio_unitario |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-08-20 09:00 | ENTRADA | 3 | José Escobar | 10 | L-2026-01 | 55 | Reactivo A | 7 | Reactivos | 20 | 15.50 |
| 1 | 2026-08-20 09:00 | ENTRADA | 3 | José Escobar | 11 | L-2026-02 | 56 | Reactivo B | 7 | Reactivos | 5 | 30.00 |
| 2 | 2026-08-21 14:10 | SALIDA | 5 | Cristopher Paz | 10 | L-2026-01 | 55 | Reactivo A | 7 | Reactivos | 3 | 15.50 |

**Nota sobre 1FN antes de empezar:** si en vez de esto tuviéramos una sola fila por movimiento con una celda tipo `lotes_afectados = "L-2026-01:20, L-2026-02:5"`, eso ya violaría 1FN (valores no atómicos/multivaluados en una celda). La tabla de arriba ya asume la corrección de eso: una fila por cada par (movimiento, lote) afectado — que es, literalmente, el grano que ya tiene `DETALLE_MOVIMIENTO` en el modelo real.

## Dependencias funcionales identificadas

Clave candidata de esta tabla plana: **(id_movimiento, id_lote)** — porque `cantidad` y `precio_unitario` son propios de esa combinación específica (un mismo lote puede recibir cantidades distintas en movimientos distintos).

```
id_movimiento              → fecha_hora, tipo_movimiento, id_usuario
id_usuario                 → nombre_usuario
id_lote                    → numero_lote, id_producto
id_producto                → nombre_producto, id_categoria
id_categoria                → nombre_categoria
(id_movimiento, id_lote)   → cantidad, precio_unitario
```

## Paso a 2FN — eliminar dependencias parciales

2FN exige que ningún atributo no-clave dependa de **solo una parte** de una clave compuesta. Aquí:
- `fecha_hora`, `tipo_movimiento`, `id_usuario`, `nombre_usuario` dependen únicamente de `id_movimiento` (mitad de la clave) → **dependencia parcial**.
- `numero_lote`, `id_producto`, `nombre_producto`, `id_categoria`, `nombre_categoria` dependen únicamente de `id_lote` (la otra mitad) → **dependencia parcial**.
- Solo `cantidad` y `precio_unitario` de verdad necesitan la clave completa.

**Se extraen dos tablas** y queda una tabla puente con lo que sí depende de la clave completa:

```
MOVIMIENTO(id_movimiento, fecha_hora, tipo_movimiento, id_usuario, nombre_usuario)
LOTE(id_lote, numero_lote, id_producto, nombre_producto, id_categoria, nombre_categoria)
DETALLE_MOVIMIENTO(id_movimiento, id_lote, cantidad, precio_unitario)
```

Ya no hay dependencias parciales: en `MOVIMIENTO`, todo depende de `id_movimiento` completo; en `LOTE`, todo depende de `id_lote` completo.

## Paso a 3FN — eliminar dependencias transitivas

3FN exige que ningún atributo no-clave dependa de otro atributo no-clave (dependencia transitiva vía la clave).

- En `MOVIMIENTO`: `nombre_usuario` no depende de `id_movimiento` directamente, depende de `id_usuario` — y `id_usuario` depende de `id_movimiento`. Es decir: `id_movimiento → id_usuario → nombre_usuario`. **Dependencia transitiva.**
  → Se extrae `USUARIO(id_usuario, nombre_usuario)`, y `MOVIMIENTO` se queda solo con la FK `id_usuario`.

- En `LOTE`: `nombre_producto` e `id_categoria` no dependen de `id_lote` directamente, dependen de `id_producto` (`id_lote → id_producto → nombre_producto`). Y dentro de eso, `nombre_categoria` depende de `id_categoria`, no de `id_producto` (`id_producto → id_categoria → nombre_categoria`). **Dos niveles de dependencia transitiva.**
  → Se extraen `PRODUCTO(id_producto, nombre_producto, id_categoria)` y `CATEGORIA(id_categoria, nombre_categoria)`, y `LOTE` se queda solo con la FK `id_producto`.

## Resultado final (3FN)

```
ROL(id_rol, nombre, descripcion)
USUARIO(id_usuario, id_rol[FK], nombre, usuario, password_hash, estado, fecha_creacion)
CATEGORIA(id_categoria, nombre, descripcion, estado)
PRODUCTO(id_producto, id_categoria[FK], codigo, nombre, descripcion, unidad_medida, stock_minimo, requiere_vencimiento, estado)
LOTE(id_lote, id_producto[FK], id_proveedor[FK], numero_lote, fecha_ingreso, fecha_vencimiento, cantidad_disponible, estado)
MOVIMIENTO(id_movimiento, id_usuario[FK], tipo_movimiento, fecha_hora, observacion)
DETALLE_MOVIMIENTO(id_detalle, id_movimiento[FK], id_lote[FK], cantidad, precio_unitario)
```

Esto es exactamente el modelo relacional que ya se había construido en la Fase 2 a partir del ER — la normalización formal confirma que no hace falta rediseñarlo, solo queda documentada la razón matemática (DF) de por qué está bien dividido.

## Verificación de las 5 tablas restantes (no necesitaban el ejemplo largo porque nunca tuvieron dependencia parcial ni transitiva)

| Tabla | Todo atributo no-clave depende de... | ¿Parcial? | ¿Transitiva? |
|---|---|---|---|
| `rol` | solo de `id_rol` | No (clave simple) | No — ningún atributo depende de otro atributo no-clave |
| `proveedor` | solo de `id_proveedor` | No (clave simple) | No |
| `examen_laboratorio` | solo de `id_examen` | No (clave simple) | No |
| `proveedor_producto` | `precio_compra` depende de la combinación completa `(id_proveedor, id_producto)` — el mismo producto tiene precios distintos según el proveedor | No — no hay atributo que dependa de solo una mitad | No — no hay atributos no-clave adicionales |
| `examen_producto` | `cantidad_requerida` depende de la combinación completa `(id_examen, id_producto)` | No | No |

**Regla que se aplicó en todo el diseño (S7 — sin redundancia):** ninguna tabla guarda un valor que pueda derivarse o copiarse de otra (por ejemplo, `lote` no guarda `nombre_producto` ni `nombre_categoria`, solo la FK `id_producto`) — eso es precisamente lo que 3FN prohíbe.
