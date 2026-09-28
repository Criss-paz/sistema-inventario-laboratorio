# sql/dml

Datos iniciales. Desde la Entrega 3 la base se carga con el **inventario real del laboratorio**: los registros en papel de marzo a septiembre de 2026, transcritos a Excel. Ninguna contraseña se escribe en SQL (RN-15): los usuarios los crea `web/seed_usuarios.py` con el mismo hash que valida el login.

**Estado:** Entrega 3.

| Script | Contenido |
|---|---|
| `001_seed.sql` | 3 roles, 5 categorías base y los 4 exámenes de la Entrega 2. |
| `002_carga_catalogo.sql` | **Generado.** 5 categorías más, 806 productos reales, 26 proveedores reales + 24 de prueba inactivos, 425 precios proveedor-producto. |
| `003_seed_examenes.sql` | 46 exámenes más y los insumos reales que consume cada uno (114 relaciones). |
| `004_carga_movimientos.sql` | **Generado.** 1,188 lotes y 5,839 movimientos (1,575 entradas y 4,264 salidas). Cada lote nace en 0 y su existencia la calculan los triggers. Requiere los usuarios de `seed_usuarios.py`. |
| `generar_carga.py` | Genera los dos scripts marcados y el reporte de hallazgos a partir del Excel. |

| Tabla | Registros |
|---|---|
| producto | 806 |
| proveedor | 50 (26 reales activos + 24 de prueba inactivos) |
| examen_laboratorio | 50 |
| lote | 1,188 |
| movimiento | 5,839 |
| detalle_movimiento | 5,920 |
| proveedor_producto / examen_producto | 425 / 114 |
| categoria / rol / usuario | 10 / 3 / 3 — catálogos de configuración; 50 serían relleno que no prueba nada |

## Datos reales: de dónde salen y qué se corrigió

El Excel **no está en el repositorio** (son datos internos del laboratorio; `.gitignore`). Los scripts generados sí, para que la base se pueda instalar sin él. Para regenerarlos:

```bash
pip install openpyxl
python sql/dml/generar_carga.py "ruta/al/inventario.xlsx"
```

Cada registro del papel pasó por las mismas reglas que aplica la base (CHECK, triggers, FEFO). Lo que no las cumplía y qué se hizo con cada caso está en [`docs/entrega-3/ENTREGA3_REPORTE_CARGA_DATOS.md`](../../docs/entrega-3/ENTREGA3_REPORTE_CARGA_DATOS.md): 65 salidas anotadas antes que su entrada, una salida que dejaba existencia negativa, una entrada que llegó ya vencida, entre otros.

Privacidad: los proveedores que son personas individuales se publican anonimizados, y los proveedores reales llevan un NIT provisional (`SIN-NIT-##`) porque el papel no lo registra.

**Verificación de coherencia** (debe dar 0): lotes cuya existencia no coincide con entradas − salidas del historial.
```sql
SELECT count(*) FROM lote l
 WHERE l.cantidad_disponible <> (
       SELECT COALESCE(sum(CASE m.tipo_movimiento WHEN 'ENTRADA' THEN d.cantidad ELSE -d.cantidad END), 0)
         FROM detalle_movimiento d JOIN movimiento m USING (id_movimiento)
        WHERE d.id_lote = l.id_lote);
```
