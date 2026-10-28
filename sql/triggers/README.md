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

## Entrega 3 y 4 (migraciones)

| Script | Triggers | Regla |
|---|---|---|
| `002_devolucion.sql` | `trg_z_devolucion_tope` | RN-22: no se devuelve más de lo que salió |
| `003_correccion_entrada.sql` | Excepción controlada en la inmutabilidad, `trg_z_correccion_existencia`, `trg_correccion_inmutable` | RN-25: la corrección ajusta el lote y no se borra |
| `004_numero_documento.sql` | `trg_movimiento_numero` | RN-27: número correlativo por tipo, sin huecos |
| `005_rol_protegido.sql` | `trg_rol_protegido` | RN-29: el rol Administrador no se renombra ni se elimina |
| `006_bitacora.sql` | `trg_bitacora_*` en 12 tablas y `trg_bitacora_inmutable` | RN-30: cada cambio queda en la bitácora, que no se modifica |
| `007_eliminar_entrada.sql` | Excepción controlada en `fn_historial_inmutable` | RN-31: solo el borrado de una entrada por su procedimiento |

Total: 22 triggers.
