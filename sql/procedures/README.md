# sql/procedures

Procedimientos almacenados que registran una entrada o una salida de inventario como **una sola operación atómica**: encabezado (`movimiento`) + detalle (`detalle_movimiento`) + lote, todo o nada.

**Estado:** implementado — Entrega 3.

| Procedimiento | Qué hace | Reglas |
|---|---|---|
| `sp_registrar_entrada` | Registra una entrada de producto. Si el lote (producto + número) ya existe le suma; si no, lo crea en 0 y la entrada lo carga, así ningún lote tiene existencia sin un movimiento que la respalde. | RF-20, RF-22, RN-02, RN-05, RN-06, RN-07, RN-08 |
| `sp_registrar_salida` | Registra una salida de producto eligiendo los lotes por **FEFO** (vence primero, sale primero), sin tocar lotes vencidos y repartiendo en varios lotes si uno no alcanza. Valida la existencia total antes de mover nada. | RF-21, RF-23, RF-25, RN-03, RN-04, RN-08, RN-18 |
| `fn_validar_usuario_activo` | Función auxiliar de ambos: el responsable del movimiento debe estar activo. | RN-08 |

La existencia del lote **no** la modifican estos procedimientos: la actualiza el trigger `trg_detalle_movimiento_existencia` (ver `sql/triggers/`), para que haya una sola fuente de verdad.

```sql
-- el último argumento (NULL) es INOUT y devuelve el id_movimiento generado
CALL sp_registrar_entrada(1, 1, 1, 'L-2026-010', '2027-12-31', 100, 85.50, 'Compra', NULL);
CALL sp_registrar_salida(2, 1, 25, 'Consumo área química', NULL);
```

**Orden de ejecución:** `ddl/001_schema.sql` → `triggers/001_triggers.sql` → `procedures/001_procedures.sql`.
