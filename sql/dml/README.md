# sql/dml

Datos iniciales y de prueba. Ninguna contraseña se escribe en SQL (RN-15): los usuarios los crea `web/seed_usuarios.py` con el mismo hash que valida el login.

**Estado:** ampliado en la Entrega 3 — supera los 50 registros en las tablas de operación.

| Script | Contenido |
|---|---|
| `001_seed.sql` | Catálogo real de la Entrega 2: 3 roles, 6 categorías, 12 productos, 3 proveedores, 4 exámenes y sus relaciones N:M. |
| `002_seed_catalogos.sql` | +45 productos y +46 exámenes reales de laboratorio clínico, +47 proveedores generados, +3 categorías, relaciones N:M. |
| `003_seed_movimientos.sql` | ~6 meses de historial: 117 lotes, 117 entradas y 586 salidas. Cada lote nace en 0 y su existencia la calculan los triggers. Requiere los usuarios de `seed_usuarios.py`. |

| Tabla | Registros |
|---|---|
| producto | 57 |
| proveedor | 50 |
| examen_laboratorio | 50 |
| lote | 117 |
| movimiento | 703 |
| detalle_movimiento | 703 |
| proveedor_producto / examen_producto | 108 / 67 |
| categoria / rol / usuario | 9 / 3 / 3 — catálogos de configuración; 50 serían relleno (ver justificación en `002_seed_catalogos.sql`) |

**Verificación de coherencia** (debe dar 0): lotes cuya existencia no coincide con entradas − salidas del historial.
```sql
SELECT count(*) FROM lote l
 WHERE l.cantidad_disponible <> (
       SELECT COALESCE(sum(CASE m.tipo_movimiento WHEN 'ENTRADA' THEN d.cantidad ELSE -d.cantidad END), 0)
         FROM detalle_movimiento d JOIN movimiento m USING (id_movimiento)
        WHERE d.id_lote = l.id_lote);
```
