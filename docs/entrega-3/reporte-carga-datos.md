# Reporte de carga del inventario real

Generado por `sql/dml/generar_carga.py`. Fuente: inventario del laboratorio de marzo a septiembre de 2026, llevado **en papel** y transcrito a Excel. El Excel no se publica en el repositorio.

Cada registro del papel pasó por las mismas reglas que aplica la base de datos (CHECK, triggers y el criterio FEFO de `sp_registrar_salida`). Este reporte lista lo que **no** cumplía esas reglas y qué se hizo con cada caso. Es evidencia de por qué el laboratorio necesita el sistema: en papel, nada de esto se detectó.

## Resumen

| Dato | En el papel | Cargado |
|---|---|---|
| Productos | 815 | 806 (9 servicios excluidos) |
| Proveedores | 26 | 26 reales + 24 de prueba inactivos = 50 |
| Entradas | 1581 | 1575 |
| Salidas | 4270 | 4264 |
| Lotes | — | 1188 |
| Precios proveedor-producto | — | 425 |

## Problemas de calidad encontrados

### 1. Salidas anotadas antes que su entrada (65)

El papel registra el consumo de un insumo días antes que la entrada que lo trajo. Lo más probable es que el insumo llegó y se usó antes de anotar la factura. La base de datos rechaza estas salidas porque dejarían existencia negativa (RN-01). **Decisión del equipo:** mover cada una a la fecha de la entrada que la cubre. La observación del movimiento conserva la fecha original.

| Salida | Producto | Cantidad | Fecha en papel | Fecha cargada |
|---|---|---|---|---|
| S000666 | HPATH | 10 | 08/04/2026 | 09/04/2026 |
| S001648 | 410851 | 2 | 26/05/2026 | 05/06/2026 |
| S001844 | 410851 | 4 | 02/06/2026 | 05/06/2026 |
| S002323 | 423643 | 1 | 23/06/2026 | 25/06/2026 |
| S002994 | CO2P1U | 1 | 24/07/2026 | 29/07/2026 |
| S003044 | CO2P1U | 1 | 28/07/2026 | 29/07/2026 |
| S003033 | 423643 | 2 | 28/07/2026 | 31/07/2026 |
| S003927 | RFIT-ASY-0116 | 3 | 04/09/2026 | 21/09/2026 |
| S003950 | 503 | 1 | 04/09/2026 | 21/09/2026 |
| S003970 | AIAPCEACS | 1 | 08/09/2026 | 21/09/2026 |
| S003971 | AIAPFT3CS | 1 | 08/09/2026 | 21/09/2026 |
| S003977 | 974010 | 1 | 08/09/2026 | 21/09/2026 |
| S003987 | BOLS093 | 6 | 08/09/2026 | 21/09/2026 |
| S004029 | BRO120MLE | 200 | 11/09/2026 | 21/09/2026 |
| S004039 | CFU6PB | 4 | 11/09/2026 | 21/09/2026 |
| S004170 | CFU6PB | 3 | 11/09/2026 | 21/09/2026 |
| S004098 | CFU6PB | 2 | 18/09/2026 | 21/09/2026 |
| S004040 | HPAGHCCTK | 1 | 11/09/2026 | 21/09/2026 |
| S004044 | STAIAPACTH | 2 | 11/09/2026 | 21/09/2026 |
| S004053 | AIAPDSTC | 1 | 11/09/2026 | 21/09/2026 |
| S004176 | AIAPDSTC | 1 | 14/09/2026 | 21/09/2026 |
| S004054 | STAIAPCEA | 1 | 11/09/2026 | 21/09/2026 |
| S004164 | BAPPA | 1 | 11/09/2026 | 21/09/2026 |
| S004175 | AIAPSSETII | 1 | 11/09/2026 | 21/09/2026 |
| S004089 | AIAPSSETII | 1 | 14/09/2026 | 21/09/2026 |
| S004063 | 156 | 1 | 14/09/2026 | 21/09/2026 |
| S004081 | STAIAPTSH | 4 | 14/09/2026 | 21/09/2026 |
| S004141 | 424733 | 1 | 18/09/2026 | 21/09/2026 |
| S004143 | Z62 | 1 | 18/09/2026 | 21/09/2026 |
| S004144 | 21343 | 5 | 18/09/2026 | 21/09/2026 |
| S004145 | 420739 | 5 | 18/09/2026 | 21/09/2026 |
| S004185 | 6802584 | 2 | 18/09/2026 | 21/09/2026 |
| S004197 | PCRLCCS | 1 | 18/09/2026 | 21/09/2026 |
| S004010 | 410851 | 4 | 11/09/2026 | 22/09/2026 |
| S003953 | 105-012288-00 | 1 | 04/09/2026 | 22/09/2026 |
| S003989 | 105-012288-00 | 1 | 08/09/2026 | 22/09/2026 |
| S003954 | 105-012290-00 | 1 | 04/09/2026 | 22/09/2026 |
| S004153 | 231010101001 | 2 | 04/09/2026 | 22/09/2026 |
| S004038 | 231010101001 | 3 | 11/09/2026 | 22/09/2026 |
| S004097 | 231010101001 | 1 | 18/09/2026 | 22/09/2026 |
| S003959 | 6844288 | 1 | 08/09/2026 | 22/09/2026 |
| S004004 | 6844288 | 1 | 11/09/2026 | 22/09/2026 |
| S004168 | 6844288 | 1 | 11/09/2026 | 22/09/2026 |
| S003988 | 105-012298-A0 | 1 | 08/09/2026 | 22/09/2026 |
| S004102 | 105-012298-A0 | 1 | 18/09/2026 | 22/09/2026 |
| S003991 | 105-000405-00 | 1 | 08/09/2026 | 22/09/2026 |
| S004101 | 105-000405-00 | 1 | 18/09/2026 | 22/09/2026 |
| S004011 | 21341 | 2 | 11/09/2026 | 22/09/2026 |
| S004140 | 21341 | 1 | 18/09/2026 | 22/09/2026 |
| S004014 | 423719 | 1 | 11/09/2026 | 22/09/2026 |
| S004018 | 7D2343 | 10 | 11/09/2026 | 22/09/2026 |
| S004125 | 7D2343 | 5 | 18/09/2026 | 22/09/2026 |
| S004034 | 105-012294-A0 | 1 | 11/09/2026 | 22/09/2026 |
| S004045 | 424106 | 1 | 11/09/2026 | 22/09/2026 |
| S004169 | 6801895 | 1 | 11/09/2026 | 22/09/2026 |
| S004074 | 6801895 | 1 | 14/09/2026 | 22/09/2026 |
| S004172 | 10446445 | 1 | 11/09/2026 | 22/09/2026 |
| S004182 | 410853 | 1 | 11/09/2026 | 22/09/2026 |
| S004079 | 105-012283-00 | 1 | 14/09/2026 | 22/09/2026 |
| S004108 | 8379034 | 1 | 18/09/2026 | 22/09/2026 |
| S004134 | 30463 | 1 | 18/09/2026 | 22/09/2026 |
| S004137 | 30307 | 1 | 18/09/2026 | 22/09/2026 |
| S004142 | 423646 | 1 | 18/09/2026 | 22/09/2026 |
| S004188 | 1988211 | 1 | 18/09/2026 | 22/09/2026 |
| S004189 | 8102204 | 1 | 18/09/2026 | 22/09/2026 |

### 2. Salidas rechazadas (1)

No existe ninguna entrada posterior que las cubra: en el papel, la existencia quedó negativa.

| Salida | Producto | Fecha | Cantidad | Existencia al final |
|---|---|---|---|---|
| S003684 | CO2P1U | 21/08/2026 | 2 | 0 |

### 3. Entradas rechazadas (1)

| Entrada | Producto | Ingreso | Vence | Motivo |
|---|---|---|---|---|
| E000312 | 8478034 | 10/03/2026 | 11/01/2026 | Vencimiento anterior a la fecha de ingreso (ck_lote_fecha_vencimiento). |

### 4. Correcciones con evidencia (2)

| Entrada | Producto | En papel | Cargado | Motivo |
|---|---|---|---|---|
| E000134 | CFU6PB | 1200 a Q9.50 | 24 a Q475.00 | Anotada en unidades sueltas; convertida a cajas de 50 (1200 u = 24 cajas). |
| E000399 | CFU6PB | 600 a Q9.50 | 12 a Q475.00 | Anotada en unidades sueltas; convertida a cajas de 50 (600 u = 12 cajas). |

Evidencia: con la conversión, entradas − salidas de este producto da exactamente la existencia que reporta el inventario (26 cajas), y el precio por caja coincide con las demás compras (Q475–Q487.50).

### 5. Números de lote

- 641 entradas no traen número de lote. Se creó uno por entrada con el formato `SL-<entrada>` (por ejemplo `SL-E000001`), para que cada compra siga siendo rastreable.
- Lotes que en realidad eran un número decimal generado por Excel al transcribir (1); se trataron como "sin lote": E000595 (`0.9999600159936025`).
- 15 entradas repiten un número de lote del mismo producto con **otra** fecha de vencimiento. En la base, un número de lote es único por producto, así que se les agregó un sufijo:

| Entrada | Producto | Lote en papel | Lote cargado |
|---|---|---|---|
| E000470 | CFU6PB | 25091 | 25091-2 |
| E000612 | CFU6PB | 25091 | 25091-2 |
| E000625 | 1669829 | 80334083357 | 80334083357-2 |
| E000850 | 83606 | 502 | 502-2 |
| E000956 | 30463 | 1011812370 | 1011812370-2 |
| E001015 | 105-012298-A0 | 2026010851 | 2026010851-2 |
| E001148 | 420739 | 2883492403 | 2883492403-2 |
| E001179 | PCTCFW | F2101B20BA7D | F2101B20BA7D-2 |
| E001206 | 1988211 | 94734383037 | 94734383037-2 |
| E001314 | N1723 | CP13.32 | CP13.32-2 |
| E001365 | ICFW | FW041910BA0 | FW041910BA0-2 |
| E001426 | HPAGHCCTK | F0610X7F02 | F0610X7F02-2 |
| E001462 | 21343 | 2433443403 | 2433443403-2 |
| E001498 | AIAPSSETII | G160057 | G160057-2 |
| E001524 | HPAGHCCTK | F0610X7F02 | F0610X7F02-2 |

### 6. Salidas cubiertas con un lote ya vencido (12)

Al repartir por FEFO, estas salidas solo tenían existencia en lotes vencidos a esa fecha. Se cargaron porque el consumo sí ocurrió. En la operación normal, `sp_registrar_salida` no permite usar lotes vencidos. Revisar si el vencimiento se transcribió mal o si se usó reactivo vencido.

| Salida | Producto | Fecha |
|---|---|---|
| S001668 | CFU6PB | 26/05/2026 |
| S001728 | AIAPCA199CS | 26/05/2026 |
| S001759 | CFU6PB | 01/06/2026 |
| S001840 | CFU6PB | 02/06/2026 |
| S001853 | SC5 | 02/06/2026 |
| S002028 | 8001133 | 09/06/2026 |
| S002120 | SC5 | 12/06/2026 |
| S002240 | AIAPWC | 19/06/2026 |
| S002324 | 410853 | 23/06/2026 |
| S003364 | 8001133 | 07/08/2026 |
| S003849 | SC5 | 01/09/2026 |
| S004015 | SC5 | 11/09/2026 |

### 7. Existencia final distinta a la del Excel (1)

La columna "Existencias" del Excel se calculó como entradas − salidas, sin validar. Las diferencias vienen de los rechazos y correcciones anteriores.

| Código | Producto | Excel | Base de datos |
|---|---|---|---|
| 8478034 | CK (18P) - VITROS | 5 | 3 |

### 8. Otros

- **Servicios excluidos** (no son artículos de inventario): CARGOS POR FLETE (PAGO POR ENVIO DE REACTIVO), CÓD. QR ALMACENADOS PARA VERIF. DE AUTENTICIDAD DE RESULTADOS, MANTENIMIENTO CORRECTIVO A EQUIPO DE BIOQUÍMICA, MANTENIMIENTO GENERAL A MICROSOPIO, MANTENIMIENTO PREVENTIVO A OBJETIVO OCULAR DE MICROSCOPIO 100X, RENTA DE IMPRESORA ZEBRA ZD210d, REPARACIONES VARIAS/CAMBIO DE PIEZAS, REPARACIÓN DE SISTEMA ELÉCTRICO DE MICROSCOPIO, SERVICIO DE MANTENIMIENTO PREVENTIVO.
- **Productos desactivados** (el código traía el prefijo `/DESACT/`): se cargan con su historial y se dan de baja lógica al final: RQ9140D (CONTROLES DE TERCERA OPINION OCTUBRE 2025).
- **Nombre repetido con distinto código** (posible duplicado a revisar): AIAPBHCS, AIAPBHCGCS — AIA-PACK B HCG CALIBRATOR SET.
- **Productos sin stock mínimo**: 1, se cargaron con 0.
- **Proveedor-producto sin precio**: 377 productos tienen proveedor pero nunca se compraron ni tienen costo registrado; no se cargó esa relación porque `precio_compra` es obligatorio.

## Decisiones de la carga

| Tema | Decisión |
|---|---|
| NIT de proveedores | El papel no lo registra. NIT provisional `SIN-NIT-01`… (obligatorio y único en el modelo); se corrige desde la aplicación. |
| Proveedores personas | 2 proveedores son personas individuales: se publican como `PROVEEDOR INDIVIDUAL ##` (el repositorio es público). |
| 50 proveedores | Solo hay 26 reales. Se agregan 24 **de prueba**, inactivos, para cumplir el mínimo de la consigna sin mezclarlos con los reales. |
| Categorías | El papel no las trae. Se asignaron por palabras clave del nombre (reglas en `generar_carga.py`). |
| Requiere vencimiento | Si el producto tiene entradas: sí, cuando todas traen vencimiento. Si no tiene: según su categoría. |
| Responsable | El papel no registra quién hizo el movimiento: se asignan a `encargado.dev`. |
| Horas | El papel solo trae la fecha. Cada día se numeran desde las 07:00, un minuto por registro: primero las entradas, luego las salidas ajustadas y al final las salidas, en el orden del papel. |

## Productos por categoría

| Categoría | Productos |
|---|---|
| BANCO DE SANGRE | 8 |
| CALIBRADORES | 75 |
| EQUIPO DE PROTECCION PERSONAL | 17 |
| EQUIPO Y REPUESTOS | 23 |
| INSUMOS DE TOMA DE MUESTRA | 60 |
| LIMPIEZA Y DESINFECCION | 10 |
| MATERIAL PARA EL LABORATORIO | 51 |
| MICROBIOLOGIA | 169 |
| PAPELERIA Y ETIQUETADO | 8 |
| REACTIVOS | 385 |
