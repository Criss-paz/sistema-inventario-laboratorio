# sql/views

Vistas de consulta del inventario. Todo lo que muestran es **calculado** a partir de las tablas (estándar S7): ninguna tabla guarda existencias por producto, faltantes ni días para vencer.

**Estado:** implementado — Entrega 3.

| Vista | Qué muestra | Requerimientos |
|---|---|---|
| `vw_existencia_producto` | Existencia por producto, separada en utilizable (sin vencer) y vencida. Los productos sin lotes aparecen con 0. | RF-08, RF-19, RF-32 |
| `vw_inventario_bajo` | Productos activos cuya existencia **utilizable** es igual o inferior al stock mínimo, con el faltante para reponer. | RF-29, RN-10, RN-11 |
| `vw_lotes_por_vencer` | Lotes con existencia que ya vencieron o vencen en los próximos **90 días**, con los días restantes. | RF-30, RN-07 |
| `vw_historial_movimientos` | Cada movimiento con su usuario, lote, producto, cantidad y subtotal. | RF-26 a RF-28, RF-34, RF-35 |
| `fn_kardex_promedio(id)` *(002)* | Kardex por **costo promedio ponderado móvil**: cada entrada recalcula el promedio, cada salida se valoriza al promedio vigente. Una fila por movimiento con saldo y promedio. | RF-33, RF-34 |
| `vw_valorizacion_inventario` *(002)* | Existencia, costo promedio y valor del inventario por producto (última fila del kardex). | RF-33 |

**Decisiones a defender:**
- RN-11 dice "igual o inferior", por eso la comparación es `<=`. Un producto con mínimo 0 y existencia 0 sí aparece como inventario bajo, porque está agotado.
- El inventario bajo usa la existencia utilizable: un reactivo vencido no sirve para trabajar, así que no debe ocultar que hay que reponer.
- La Entrega 1 no fija el horizonte de "próximo a vencer". Se eligieron 90 días (tiempo típico de pedido a proveedor); se cambia en un solo `INTERVAL`.

**Orden de ejecución:** `001_views.sql` después de `sql/ddl/001_schema.sql`; `002_valorizacion_promedio.sql` después de `001` (usa sus vistas).

**Verificación del promedio** (colesterol HDL, 14/04/2026): saldo de 7 unidades a Q900 (Q6,300) + compra de 5 a Q600 (Q3,000) = 12 unidades por Q9,300 → promedio **Q775**. Las salidas siguientes se valorizan a Q775.
