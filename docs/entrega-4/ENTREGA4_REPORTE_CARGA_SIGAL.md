# Reporte de la carga de SIGAL — Entrega 4

Movimientos que el laboratorio registró en **SIGAL** después del registro en papel, cargados con `sql/dml/005_carga_sigal.sql` (generado por `sql/dml/generar_carga_sigal.py` a partir del respaldo de SIGAL del 21/10/2026, que no se publica). Mismo método y decisiones que la carga del papel (`docs/entrega-3/ENTREGA3_REPORTE_CARGA_DATOS.md`).

## Resumen

| Dato | Cargado |
|---|---|
| Período | 24/09/2026 a 21/10/2026 |
| Entradas | 205 |
| Salidas | 516 |
| Lotes nuevos | 108 |
| Productos nuevos | 8 |
| Proveedores nuevos | 1 |
| Precios proveedor–producto actualizados | 158 |

**Cómo se evita duplicar:** SIGAL conservó la numeración del papel (E######, S######). Se cargan solo los registros posteriores al 23/09/2026 cuyo código no estaba ya en la base. Hasta esa fecha los dos sistemas coinciden.

## Productos nuevos (8)

Categoría asignada por palabras clave del nombre (mismas reglas que la carga del papel).

| Código | Producto | Categoría | Presentación | Mínimo | Requiere vencimiento |
|---|---|---|---|---|---|
| 423485 | SPOTFIRE R/ST PANEL | REACTIVOS | UNIDAD | 10.00 | Sí |
| 30455-02 | VIDAS D DIMER EXCLUSION II | REACTIVOS | CAJA | 10.00 | Sí |
| SCF | SANGRE DE CARNERO (FRASCO) | MICROBIOLOGIA | FRASCO | 1.00 | No |
| 105-000822-A0 | ALBUMIN KIT (BROMOCRESOL GREEN METHOD) | REACTIVOS | KIT | 1.00 | Sí |
| 30450 | VIDAS B.R.A.H.M.S. PCT | REACTIVOS | CAJA | 2.00 | Sí |
| STAIAPHGH | ST AIA-PACK HGH | REACTIVOS | TRAY DE 20 U. | 2.00 | Sí |
| PRM15P | PRUEBA RAPIDA MULTIDROGAS 15 PARAMETROS | REACTIVOS | UNIDAD | 5.00 | Sí |
| STAIAPCA15-3C | ST AIA-PACK CA 15-3 CALIBRATOR | CALIBRADORES | UNIDAD | 1.00 | Sí |

## Proveedores nuevos (1)

NIT provisional; se corrige desde la aplicación.

| Proveedor | NIT |
|---|---|
| SUMILAB TOSOH | SIN-NIT-27 |

## Entradas sin número de lote (22)

Se les asignó el lote `SL-<entrada>` (decisión 3).

| Entrada | Producto | Lote asignado |
|---|---|---|
| E001622 | PHA1CHPLC | SL-E001622 |
| E001623 | PHA1CHPLC | SL-E001623 |
| E001625 | SCF | SL-E001625 |
| E001640 | NIP021 | SL-E001640 |
| E001641 | VIA059 | SL-E001641 |
| E001642 | NIP038 | SL-E001642 |
| E001643 | NIP004 | SL-E001643 |
| E001644 | NIP006 | SL-E001644 |
| E001645 | AMB021 | SL-E001645 |
| E001678 | 2815 | SL-E001678 |
| E001679 | 110428 | SL-E001679 |
| E001681 | 10293 | SL-E001681 |
| E001732 | HCGU1ULS/OC | SL-E001732 |
| E001733 | BRO120MLE | SL-E001733 |
| E001734 | GNCTS-A | SL-E001734 |
| E001735 | AE1U-B2U | SL-E001735 |
| E001755 | ALCCK | SL-E001755 |
| E001756 | GCVS1ML | SL-E001756 |
| E001757 | GSSC1ML | SL-E001757 |
| E001758 | GSL1ML | SL-E001758 |
| E001759 | GSD1ML | SL-E001759 |
| E001760 | KFRCC1P | SL-E001760 |

## Entradas a un lote existente con otro vencimiento (4)

Se sumaron al lote existente, que conserva su vencimiento (decisión 4, igual que `sp_registrar_entrada`). Revisar cuál fecha es la correcta y, si hace falta, usar *Corregir entrada*.

| Entrada | Producto | Lote | Vencimiento del lote | Vencimiento en SIGAL |
|---|---|---|---|---|
| E001606 | 8102204 | 13535262626 | 01/08/2027 | 01/08/2028 |
| E001706 | 83609 | 137 | 31/07/2027 | 31/12/2028 |
| E001725 | HPAGHCCTK | F0610X7F02 | 09/08/2028 | 09/06/2028 |
| E001726 | FOBSOHCTK | F0731W3E00D | 31/07/2027 | 31/08/2027 |

## Entradas rechazadas (1)

La base no las admite.

| Entrada | Producto | Motivo |
|---|---|---|
| E001732 | HCGU1ULS/OC | Vencimiento anterior al ingreso. |

## Verificación después de cargar (21/10/2026)

Hecha sobre la base de desarrollo, después de aplicar `005_carga_sigal.sql`:

- **0 lotes incoherentes** con su historial y ningún lote con existencia negativa.
- **Existencia final por producto contra la de SIGAL:** de 813 productos comparados, **804 coinciden exactamente**. Las 9 diferencias tienen causa conocida:

| Producto | Aquí | SIGAL | Causa |
|---|---|---|---|
| 8478034 | 2 | 4 | La entrada E000312 se rechazó en la carga del papel: su vencimiento era anterior al ingreso (`ENTREGA3_REPORTE_CARGA_DATOS.md`, sección 3) |
| HCGU1ULS/OC | 1 | 3 | La entrada E001732 se rechaza en esta carga por el mismo motivo (tabla de arriba) |
| 231010101001, CFU6PB, CL882001F, CUBREOBJ22X22, FOBSOHCTK, N1723, PRM15P | 8, 30, 6, 32, 2, 2, 12 | 7, 28, 5, 31, 1, 1, 9 | **El contador de existencias de SIGAL no coincide con sus propios movimientos.** Las entradas menos las salidas registradas en SIGAL dan exactamente lo que muestra este sistema |

La última fila muestra por qué este sistema no guarda la existencia por producto (estándar S7). SIGAL la guarda como un número aparte (`productos.existencias`) que se actualiza con cada operación y que, después de ediciones y borrados, quedó desfasado de su propio historial. Aquí la existencia es siempre la suma del historial: lo que mantiene el trigger por lote y lo que verifica la consulta de coherencia.

## Decisiones

| Tema | Decisión |
|---|---|
| Qué se carga | Registros de SIGAL posteriores al 23/09/2026 cuyo código no está en la base |
| Responsable | `encargado.dev`, igual que la carga del papel; en SIGAL los usuarios son personas con nombre y el repositorio es público. La observación de cada salida conserva el área solicitante |
| Fechas | SIGAL las guarda en UTC; se convierten a hora de Guatemala |
| Salidas | Repartidas por FEFO sin lotes vencidos, como `sp_registrar_salida` |
| Datos de SIGAL que no tienen lugar en este modelo | Requisiciones, pedidos, avisos, descuentos y retenciones de las facturas: no se cargan |
