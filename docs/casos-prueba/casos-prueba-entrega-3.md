# Casos de prueba — Entrega 3

Ocho casos que demuestran las piezas nuevas de esta entrega: triggers, procedimientos, vistas, roles de base de datos, control de acceso en la app y reportes a costo promedio ponderado.

## Cómo se prueban

**Verificación previa (26/09/2026, José Eduardo Escobar).** Los 8 escenarios se ejecutaron contra la base real dentro de una transacción que se revirtió (`BEGIN … ROLLBACK`), así que no dejaron rastro en el inventario. Además, la aplicación web pasó 142 verificaciones automatizadas con los 3 usuarios.

**Ejecución del equipo (28/09/2026, Cristopher Alexis Castellanos Paz).** Los 8 casos se ejecutaron sobre una **instalación desde cero** en otro equipo, siguiendo `INSTALL.md` al pie de la letra (PostgreSQL 18.6 + Python 3.13, Windows 11): los 11 scripts SQL corrieron sin errores y la base quedó con los mismos números que la de desarrollo (806 productos, 1,188 lotes, 5,839 movimientos, 0 lotes incoherentes con el historial, inventario valorizado en Q524,714.36). Los casos de la aplicación se ejecutaron en el navegador Chromium, conducido paso a paso con Playwright para que cada captura muestre exactamente la pantalla que produjo la acción; los casos CP3-05 y CP3-07 se ejecutaron en `psql`. La columna *Resultado obtenido* copia lo que respondió el sistema en esa corrida y la columna *Evidencia* enlaza su captura.

**Producto de prueba.** Para no alterar el inventario real, todos los casos usan un producto creado solo para esto:

| Campo | Valor |
|---|---|
| Código | `PRUEBA-CP3` |
| Nombre | `REACTIVO DE PRUEBA CP3` |
| Categoría | REACTIVOS |
| Presentación | UNIDAD |
| Stock mínimo | 5 |
| Requiere vencimiento | Sí |

Los movimientos de prueba quedan en el historial, porque el historial no se puede borrar (RN-09), pero todos llevan "Prueba CP3" en la observación. Al terminar, el administrador da de baja el producto (Productos → Desactivar).

**Usuarios:** `admin.dev` / `Admin#Dev2026`, `encargado.dev` / `Encargado#Dev2026`, `consulta.dev` / `Consulta#Dev2026` (solo desarrollo; en producción no funcionan).

---

## Casos

| ID | Caso | Requerimientos | Precondición | Pasos | Resultado esperado | Resultado obtenido (28/09/2026) | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| **CP3-01** | Una entrada crea el lote y suma su existencia | RF-14 a RF-18, RF-20, RF-22, RF-26, RF-27, RN-02, RN-06 | Producto `PRUEBA-CP3` creado por `admin.dev` ([precondición](evidencias-entrega-3/CP3-00-precondicion.png)) | 1. Entrar como `encargado.dev`. 2. Movimientos → Registrar entrada: `PRUEBA-CP3`, proveedor SUMILAB, lote `CP3-A`, vence 31/01/2027, cantidad 10, precio Q100. 3. Repetir con lote `CP3-B`, vence 31/12/2026, cantidad 10, precio Q130. 4. Abrir Lotes y buscar `PRUEBA-CP3`. | Se crean 2 lotes con 10 unidades cada uno. Cada entrada aparece en Movimientos → Entradas con fecha, hora y "Encargado de Prueba" como responsable. | Lotes `CP3-A` (vence 31/01/2027) y `CP3-B` (vence 31/12/2026), **10 unidades** cada uno, proveedor SUMILAB. Movimientos de entrada n.º 5840 y 5841, responsable "Encargado de Prueba". | [CP3-01](evidencias-entrega-3/CP3-01.png), [entrada](evidencias-entrega-3/CP3-01a-entrada.png) | ✅ Pasó |
| **CP3-02** | Una salida descuenta primero del lote que vence antes (FEFO) | RF-21, RF-23, RF-35, RN-03, RN-05, RN-18 | CP3-01 ejecutado | 1. Como `encargado.dev`: Movimientos → Registrar salida: `PRUEBA-CP3`, cantidad 15, observación "Prueba CP3-02". 2. Abrir el detalle de la salida. | La salida se reparte en 2 lotes: 10 del lote `CP3-B` (vence antes) y 5 del lote `CP3-A`. Quedan `CP3-B` = 0 y `CP3-A` = 5. | Salida n.º 5842: **CP3-B 10 unidades**, **CP3-A 5 unidades**; la app indica "La salida se repartió en 2 lotes: primero el que vence antes (FEFO)". Existencias finales: `CP3-A` = 5.00, `CP3-B` = 0.00. | [CP3-02](evidencias-entrega-3/CP3-02.png) | ✅ Pasó |
| **CP3-03** | No se permite sacar más de lo que hay | RF-24, RF-25, RN-01, RN-04 | CP3-02 ejecutado (quedan 5) | 1. Como `encargado.dev`: Registrar salida de `PRUEBA-CP3`, cantidad 50. | La salida no se registra y aparece el mensaje de la base de datos. La existencia sigue en 5. | Rechazada: *"Existencia insuficiente de "REACTIVO DE PRUEBA CP3": disponible 5.00 (sin contar lotes vencidos), solicitado 50."* No se creó movimiento. | [CP3-03](evidencias-entrega-3/CP3-03.png) | ✅ Pasó |
| **CP3-04** | Un reactivo no entra sin fecha de vencimiento | RF-18, RN-07 | Producto con "Requiere vencimiento" | 1. Como `encargado.dev`: Registrar entrada de `PRUEBA-CP3`, lote `CP3-C`, **sin** fecha de vencimiento, cantidad 5. | La entrada se rechaza con el mensaje del trigger `trg_lote_vencimiento`; no se crea el lote `CP3-C`. | Rechazada: *"El producto "REACTIVO DE PRUEBA CP3" requiere fecha de vencimiento en sus lotes."* El lote `CP3-C` no existe (ver consulta final de CP3-07). | [CP3-04](evidencias-entrega-3/CP3-04.png) | ✅ Pasó |
| **CP3-05** | El historial de movimientos no se puede modificar ni borrar | RF-28, RF-35, RN-09 | CP3-01 ejecutado | En `psql`, conectado como `usuario_app`: `UPDATE movimiento SET observacion = 'x' WHERE id_movimiento = 5840;` y luego `DELETE FROM detalle_movimiento WHERE id_movimiento = 5840;` | Ambas instrucciones fallan con el mensaje de `fn_historial_inmutable`; el movimiento queda intacto. La app tampoco ofrece editar ni borrar movimientos. | UPDATE y DELETE rechazados: *"Los movimientos de inventario no se pueden modificar ni eliminar (tabla movimiento / detalle_movimiento). Registre un movimiento inverso para corregir."* El movimiento 5840 conserva su observación "Prueba CP3-01". | [CP3-05](evidencias-entrega-3/CP3-05.png) ([texto](evidencias-entrega-3/CP3-05.txt)) | ✅ Pasó |
| **CP3-06** | Cada rol ve y puede hacer solo lo suyo en la aplicación | RF-05, RNF-06, RNF-17 | Los 3 usuarios existen | 1. Entrar como `consulta.dev`: verificar que Movimientos no tiene "Registrar entrada/salida" y que no aparece "Administración". 2. Escribir en la barra de direcciones `/movimientos/entrada`. 3. Entrar como `encargado.dev`: sí puede registrar movimientos, pero Productos no tiene "Nuevo producto". 4. Escribir `/usuarios/`. | 2 → página "Acceso no permitido" (403). 4 → 403. `admin.dev` ve todo, incluido "Usuarios y roles". | 1 → `consulta.dev` no ve botones de registro ni la sección Administración. 2 → **403 "Acceso no permitido"**. 3 → `encargado.dev` no ve "Nuevo producto" ni acciones de edición. 4 → **403**. `admin.dev` ve "Usuarios y roles" con la tabla de permisos por rol. | [a](evidencias-entrega-3/CP3-06a-consulta-movimientos.png), [b](evidencias-entrega-3/CP3-06b-consulta-403.png), [c](evidencias-entrega-3/CP3-06c-encargado-productos.png), [d](evidencias-entrega-3/CP3-06d-encargado-403.png), [e](evidencias-entrega-3/CP3-06e-admin-usuarios.png) | ✅ Pasó |
| **CP3-07** | La base de datos niega lo que el rol no permite, aunque la app fallara | RF-05, RNF-06, RN-15 | Roles creados con `sql/security/001_roles.sql` | En `psql` como `usuario_app`: 1. `SET ROLE rol_consulta;` → `UPDATE producto SET stock_minimo = 1 WHERE codigo = 'PRUEBA-CP3';` → `CALL sp_registrar_salida(...)`. 2. `SET ROLE rol_administrador;` → `SELECT password_hash FROM usuario;` → `UPDATE lote SET cantidad_disponible = 999 WHERE numero_lote = 'CP3-A';` | Las 4 instrucciones fallan con "permiso denegado". Ni siquiera el administrador puede leer contraseñas ni cambiar existencias a mano. | Las 4 rechazadas: *"permiso denegado a la tabla producto"*, *"permiso denegado al procedimiento sp_registrar_salida"*, *"permiso denegado a la tabla usuario"*, *"permiso denegado a la tabla lote"*. Existencias sin cambio: `CP3-A` = 5.00, `CP3-B` = 0.00. | [CP3-07](evidencias-entrega-3/CP3-07.png) ([texto](evidencias-entrega-3/CP3-07.txt)) | ✅ Pasó |
| **CP3-08** | El inventario se valoriza por costo promedio ponderado | RF-33, RF-34 | CP3-01 y CP3-02 ejecutados | 1. Reportes → Kardex de un producto → `PRUEBA-CP3`. 2. Reportes → Inventario, buscar `PRUEBA-CP3`. | Kardex: tras la segunda compra el costo promedio es (10×100 + 10×130) ÷ 20 = **Q115**. La salida de 15 se valoriza a Q115 = **Q1,725**. Saldo: 5 unidades × Q115 = **Q575**. El reporte de inventario muestra existencia 5, precio unitario 115.00 y precio total 575.00. | Kardex (como `consulta.dev`): promedio **115.00** tras la 2.ª entrada; salida 15 × 115.00 = **1,725.00**; saldo **5 / 115.00 / 575.00**. Reporte de inventario: existencia 5, precio unitario 115.00, precio total **Q575.00**. | [a](evidencias-entrega-3/CP3-08a-kardex.png), [b](evidencias-entrega-3/CP3-08b-inventario.png) | ✅ Pasó |

**Resultado de la ejecución del equipo: 8 de 8 casos pasaron.** Al terminar, `admin.dev` desactivó el producto `PRUEBA-CP3` ([cierre](evidencias-entrega-3/CP3-99-cierre.png)).

**Hallazgos de la ejecución** (no afectan el resultado de los casos; corregidos el mismo día):
- En Registrar salida, la ayuda de existencia decía "5 unidad" en vez de "5 unidades". Ahora usa la misma regla de plural que el resto de la app.
- El botón "Activar" de los listados se mostraba en rojo, como si fuera una acción peligrosa. Ahora solo "Desactivar" va en rojo.

---

**Ejecutado por:** Cristopher Alexis Castellanos Paz  **Fecha:** 28/09/2026  **Navegador:** Chromium 153 (Playwright 1.63), Windows 11

---

## Casos añadidos el 29/09/2026 — devolución de salidas

La devolución no estaba en los 39 requerimientos: el equipo la propuso al notar que una salida mal registrada no se podía corregir, porque el historial es inmutable (RN-09). Se implementó como el *movimiento inverso* que el propio trigger `fn_historial_inmutable` indica en su mensaje de error.

**Cómo se probaron.** En `psql` como `usuario_app`, sobre la instalación local reconstruida desde cero siguiendo `INSTALL.md` (PostgreSQL 18.4, 29/09/2026): los 13 scripts corrieron sin errores y la base quedó con los mismos números de la corrida del 28/09 (806 productos, 1,188 lotes, 5,839 movimientos, inventario valorizado en **Q524,714.36**). No hay capturas de pantalla: la evidencia es la transcripción literal de la sesión, igual que en CP3-05 y CP3-07.

**Producto de prueba:** `PRUEBA-CP3D` — *REACTIVO DE PRUEBA DEVOLUCION*, categoría REACTIVOS, presentación UNIDAD. Se le registró una entrada de **20 unidades a Q100** y una salida de **12**. Al terminar se dio de baja.

| ID | Caso | Requerimientos | Pasos | Resultado esperado | Resultado obtenido (29/09/2026) | Estado |
|---|---|---|---|---|---|---|
| **CP3-09** | Una devolución repone la existencia del lote y deja constancia de por qué | RN-19, RN-20, RN-21 | Tras la salida de 12 (existencia 8), llamar a `sp_registrar_devolucion` con el motivo escrito | La existencia sube, el movimiento queda de tipo `DEVOLUCION` con su motivo y el vínculo a la salida corregida. La salida original no se altera. | Existencia tras la salida: **8.00**. Registrada la devolución, el movimiento queda con `tipo_movimiento = DEVOLUCION`, `id_movimiento_origen = 5841` y el motivo guardado. La salida #5841 permanece intacta en el historial. | ✅ Pasó |
| **CP3-10** | No se puede devolver más de lo que esa salida sacó | RN-22 | Intentar devolver 99 unidades de una salida que retiró 12 | El trigger `fn_devolucion_tope` rechaza la operación completa y la existencia no cambia | Rechazado: *"No se puede devolver 99.00 del lote CP3D-A: la salida #5841 retiró 12.00 y ya se habían devuelto 0.00. **Máximo devolvible: 12.00**."* | ✅ Pasó |
| **CP3-10b** | Una devolución sin motivo se rechaza | RN-20 | Llamar al procedimiento con el motivo en blanco | Se rechaza antes de tocar el inventario | Rechazado: *"Debe indicar el motivo de la devolución."* El `CHECK ck_movimiento_devolucion` lo impide también si alguien insertara a mano. | ✅ Pasó |
| **CP3-11** | Devolución parcial: se devuelve una parte y queda saldo pendiente | RN-19, RN-22 | Devolver 5 de las 12 que salieron y consultar `fn_devolvible` | La existencia sube solo 5 y el saldo devolvible baja a 7 | Existencia: 8.00 → **13.00**. `fn_devolvible` informa: sacado **12.00**, devuelto **5.00**, devolvible **7.00**. | ✅ Pasó |
| **CP3-12** | El kardex valoriza la devolución al costo promedio vigente | RN-23, RF-33, RF-34 | Consultar `fn_kardex_promedio` del producto de prueba | La devolución entra como reingreso al promedio vigente, sin alterarlo | Las tres líneas del kardex: ENTRADA 20 @ Q100 → saldo 20 / **Q2,000**; SALIDA 12 @ Q100 → saldo 8 / **Q800**; DEVOLUCION 5 @ Q100 → saldo 13 / **Q1,300**. El costo promedio se mantiene en **Q100.0000**. | ✅ Pasó |
| **CP3-12b** | El rol de solo consulta no puede devolver | RF-05, RNF-06 | `SET ROLE rol_consulta` y llamar al procedimiento | PostgreSQL lo niega aunque la aplicación fallara | Rechazado: *"permiso denegado a la tabla movimiento"*. En la aplicación, `consulta.dev` recibe **403** al abrir la pantalla de devolución. | ✅ Pasó |

**Resultado: 6 de 6 casos pasaron.** Transcripción completa en [CP3-09-a-12.txt](evidencias-entrega-3/CP3-09-a-12.txt). Al terminar, el producto `PRUEBA-CP3D` quedó dado de baja.

**Hallazgo corregido durante estas pruebas.** Al añadir el tipo `DEVOLUCION`, `fn_kardex_promedio` lo trataba como salida, porque decidía con `IF tipo = 'ENTRADA' … ELSE` y ese `ELSE` capturaba cualquier tipo nuevo: **restaba** la devolución en vez de sumarla. Se detectó comparando el saldo del kardex (2.00) con la existencia real (4.00) del producto 393. Corregido en `sql/views/004_kardex_devolucion.sql`; verificado después que los **425 productos con movimiento** cuadran con su existencia real y que el inventario sigue valorizado en Q524,714.36.

---

**Ejecutado por:** Cristopher Alexis Castellanos Paz  **Fecha:** 29/09/2026  **Entorno:** PostgreSQL 18.4 + Python 3.14, Windows 11
