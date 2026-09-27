# Casos de prueba — Entrega 3

Ocho casos que demuestran las piezas nuevas de esta entrega: triggers, procedimientos, vistas, roles de base de datos, control de acceso en la app y reportes a costo promedio ponderado.

## Cómo se prueban

**Verificación previa (26/09/2026).** Los 8 escenarios se ejecutaron contra la base real dentro de una transacción que se revirtió (`BEGIN … ROLLBACK`), así que no dejaron rastro en el inventario. La columna *Resultado obtenido* copia lo que respondió PostgreSQL en esa corrida. Además, la aplicación web pasó 142 verificaciones automatizadas con los 3 usuarios.

**Ejecución del equipo (pendiente).** Cada caso se vuelve a ejecutar a mano en la aplicación web, con una captura como evidencia en `docs/casos-prueba/evidencias-entrega-3/CP3-xx.png`. Al terminar, se marca el *Estado* y se sube con un commit propio.

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

**Usuarios:** `admin.dev` / `Admin#Dev2026`, `encargado.dev` / `Encargado#Dev2026`, `consulta.dev` / `Consulta#Dev2026` (solo desarrollo).

---

## Casos

| ID | Caso | Requerimientos | Precondición | Pasos | Resultado esperado | Resultado obtenido (verificación previa) | Estado |
|---|---|---|---|---|---|---|---|
| **CP3-01** | Una entrada crea el lote y suma su existencia | RF-14 a RF-18, RF-20, RF-22, RF-26, RF-27, RN-02, RN-06 | Producto `PRUEBA-CP3` creado por `admin.dev` | 1. Entrar como `encargado.dev`. 2. Movimientos → Registrar entrada: `PRUEBA-CP3`, proveedor SUMILAB, lote `CP3-A`, vence 31/01/2027, cantidad 10, precio Q100. 3. Repetir con lote `CP3-B`, vence 31/12/2026, cantidad 10, precio Q130. 4. Abrir Lotes y buscar `PRUEBA-CP3`. | Se crean 2 lotes con 10 unidades cada uno. Cada entrada aparece en Movimientos → Entradas con fecha, hora y "Encargado de Prueba" como responsable. | Lotes `CP3-A` (vence 2027-01-31) y `CP3-B` (vence 2026-12-31), **10.00** unidades cada uno. Se crearon 2 movimientos de entrada (en esa corrida, los n.º 5875 y 5876). | ⏳ Pendiente |
| **CP3-02** | Una salida descuenta primero del lote que vence antes (FEFO) | RF-21, RF-23, RF-35, RN-03, RN-05, RN-18 | CP3-01 ejecutado | 1. Como `encargado.dev`: Movimientos → Registrar salida: `PRUEBA-CP3`, cantidad 15, observación "Prueba CP3-02". 2. Abrir el detalle de la salida. | La salida se reparte en 2 lotes: 10 del lote `CP3-B` (vence antes) y 5 del lote `CP3-A`. Quedan `CP3-B` = 0 y `CP3-A` = 5. | Detalle de la salida: **CP3-B 10.00**, **CP3-A 5.00**. Existencias finales: `CP3-A` = 5.00, `CP3-B` = 0.00. | ⏳ Pendiente |
| **CP3-03** | No se permite sacar más de lo que hay | RF-24, RF-25, RN-01, RN-04 | CP3-02 ejecutado (quedan 5) | 1. Como `encargado.dev`: Registrar salida de `PRUEBA-CP3`, cantidad 50. | La salida no se registra y aparece el mensaje de la base de datos. La existencia sigue en 5. | Rechazada: *"Existencia insuficiente de "REACTIVO DE PRUEBA CP3": disponible 5.00 (sin contar lotes vencidos), solicitado 50."* | ⏳ Pendiente |
| **CP3-04** | Un reactivo no entra sin fecha de vencimiento | RF-18, RN-07 | Producto con "Requiere vencimiento" | 1. Como `encargado.dev`: Registrar entrada de `PRUEBA-CP3`, lote `CP3-C`, **sin** fecha de vencimiento, cantidad 5. | La entrada se rechaza con el mensaje del trigger `trg_lote_vencimiento`; no se crea el lote `CP3-C`. | Rechazada: *"El producto "REACTIVO DE PRUEBA CP3" requiere fecha de vencimiento en sus lotes."* | ⏳ Pendiente |
| **CP3-05** | El historial de movimientos no se puede modificar ni borrar | RF-28, RF-35, RN-09 | CP3-01 ejecutado | En `psql`, conectado como `usuario_app`: `UPDATE movimiento SET observacion = 'x' WHERE id_movimiento = <id de CP3-01>;` y luego `DELETE FROM detalle_movimiento WHERE id_movimiento = <id>;` | Ambas instrucciones fallan con el mensaje de `fn_historial_inmutable`; el movimiento queda intacto. La app tampoco ofrece editar ni borrar movimientos. | UPDATE y DELETE rechazados: *"Los movimientos de inventario no se pueden modificar ni eliminar (tabla movimiento / detalle_movimiento). Registre un movimiento inverso para corregir."* | ⏳ Pendiente |
| **CP3-06** | Cada rol ve y puede hacer solo lo suyo en la aplicación | RF-05, RNF-06, RNF-17 | Los 3 usuarios existen | 1. Entrar como `consulta.dev`: verificar que Movimientos no tiene "Registrar entrada/salida" y que no aparece "Administración". 2. Escribir en la barra de direcciones `/movimientos/entrada`. 3. Entrar como `encargado.dev`: sí puede registrar movimientos, pero Productos no tiene "Nuevo producto". 4. Escribir `/usuarios/`. | 2 → página "Acceso no permitido" (403). 4 → 403. `admin.dev` ve todo, incluido "Usuarios y roles". | Verificado con la prueba automatizada: `consulta.dev` recibe 403 en `/movimientos/entrada` y `/usuarios/`; `encargado.dev`, 403 en `/usuarios/` y `/productos/nuevo`; los botones aparecen solo para el rol que corresponde. | ⏳ Pendiente |
| **CP3-07** | La base de datos niega lo que el rol no permite, aunque la app fallara | RF-05, RNF-06, RN-15 | Roles creados con `sql/security/001_roles.sql` | En `psql` como `usuario_app`: 1. `SET ROLE rol_consulta;` → `UPDATE producto SET stock_minimo = 1 WHERE codigo = 'PRUEBA-CP3';` → `CALL sp_registrar_salida(...)`. 2. `SET ROLE rol_administrador;` → `SELECT password_hash FROM usuario;` → `UPDATE lote SET cantidad_disponible = 999 WHERE numero_lote = 'CP3-A';` | Las 4 instrucciones fallan con "permiso denegado". Ni siquiera el administrador puede leer contraseñas ni cambiar existencias a mano. | Las 4 rechazadas: *"permiso denegado a la tabla producto"*, *"… al procedimiento sp_registrar_salida"*, *"… a la tabla usuario"*, *"… a la tabla lote"*. | ⏳ Pendiente |
| **CP3-08** | El inventario se valoriza por costo promedio ponderado | RF-33, RF-34 | CP3-01 y CP3-02 ejecutados | 1. Reportes → Kardex de un producto → `PRUEBA-CP3`. 2. Reportes → Inventario, buscar `PRUEBA-CP3`. | Kardex: tras la segunda compra el costo promedio es (10×100 + 10×130) ÷ 20 = **Q115**. La salida de 15 se valoriza a Q115 = **Q1,725**. Saldo: 5 unidades × Q115 = **Q575**. El reporte de inventario muestra existencia 5, precio unitario 115.00 y precio total 575.00. | Kardex: promedio **115.0000** tras la 2.ª entrada; salida 15 × 115 = **1725.00**; saldo **5.00 / 115.0000 / 575.00**. `vw_valorizacion_inventario`: existencia 5.00, costo 115.0000, valor 575.00. | ⏳ Pendiente |

**Resultado de la verificación previa: 8 de 8 casos se comportaron como se esperaba.**

---

## Al terminar la ejecución del equipo

1. Guardar las 8 capturas en `docs/casos-prueba/evidencias-entrega-3/` con el nombre del caso (`CP3-01.png` …).
2. Cambiar cada *Estado* a ✅ Pasó (o ❌ Falló, con lo que ocurrió).
3. Anotar debajo la fecha, quién ejecutó los casos y en qué navegador.
4. Dar de baja el producto `PRUEBA-CP3`.
5. Hacer commit, por ejemplo: `test(casos): ejecuta los 8 casos de prueba de la Entrega 3`.

**Ejecutado por:** _______________  **Fecha:** ___/___/2026  **Navegador:** _______________
