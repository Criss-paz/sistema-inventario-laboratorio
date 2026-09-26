# sql/triggers

Disparadores para reglas de integridad que no pueden expresarse solo con CHECK/FK, porque cruzan tablas o dependen del tipo de operación.

**Estado:** implementado — Entrega 3.

| Trigger | Tabla / evento | Regla de negocio |
|---|---|---|
| `trg_detalle_movimiento_existencia` | `detalle_movimiento` BEFORE INSERT | RN-02 (entrada suma), RN-03 (salida resta), RN-04 (no sacar más de lo disponible), RN-01 (nunca negativo). Rechaza también movimientos sobre lotes dados de baja. |
| `trg_movimiento_inmutable`, `trg_detalle_movimiento_inmutable` | `movimiento` / `detalle_movimiento` BEFORE UPDATE OR DELETE | RN-09: el historial es de solo inserción; un error se corrige con un movimiento inverso. |
| `trg_lote_vencimiento` | `lote` BEFORE INSERT OR UPDATE | RN-07: fecha de vencimiento obligatoria si `producto.requiere_vencimiento = TRUE`. |

La justificación de negocio de cada uno está comentada en `001_triggers.sql` (estándar S6).

**Orden de ejecución:** `sql/ddl/001_schema.sql` → `sql/triggers/001_triggers.sql` → resto de scripts.
