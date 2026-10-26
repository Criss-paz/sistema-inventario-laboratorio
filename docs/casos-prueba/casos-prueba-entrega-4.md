# Casos de prueba — Entrega 4

La Entrega 4 se revisa con tres pruebas funcionales: **la aplicación completa operativa**, **la instalación desde cero** y **los flujos del manual de usuario**. Estos casos cubren las tres:

- **CP4-01 a CP4-12** recorren, en el navegador, cada flujo del manual de usuario (`docs/entrega-4/ENTREGA4_MANUAL_USUARIO.md`, flujos U-01 a U-12), con los tres roles. Juntos tocan los 11 módulos y el CRUD de todas las tablas principales.
- **CP4-13** prueba el respaldo y la restauración (RNF-11).
- **CP4-14** instala la base desde cero siguiendo `INSTALL.md`.
- **CP4-15 a CP4-19** prueban lo que se agregó después: corrección de entradas, carga de SIGAL, número de documento, roles con permisos editables y bitácora.

Los casos de las entregas 2 y 3 siguen vigentes (`casos-prueba-entrega-2.md`, `casos-prueba-entrega-3.md`). La regresión de esta entrega confirma que no se rompió nada de lo anterior (ver el final del documento).

## Cómo se ejecutaron

**Fecha:** 20/10/2026. **Entorno:** Windows 11, PostgreSQL 18.6, Python 3.14, Flask 3.0.3, en el equipo de José Eduardo Escobar, sobre la base con el inventario real del laboratorio.

**Navegador:** Microsoft Edge, conducido paso a paso con Playwright 1.64, para que cada captura muestre exactamente la pantalla que produjo la acción. El texto de la columna *Resultado obtenido* es lo que respondió el sistema en esa corrida, copiado de `evidencias-entrega-4/CP4-resultados.json`.

**Datos de prueba.** Para no alterar el inventario real, los casos crean sus propios registros, todos con "CP4" en el nombre:

| Registro | Valor |
|---|---|
| Producto | `PRUEBA-CP4` — REACTIVO DE PRUEBA CP4 (REACTIVOS, UNIDAD, stock mínimo 5, requiere vencimiento) |
| Proveedor | PROVEEDOR DE PRUEBA CP4, NIT `CP4-0001` |
| Lote | `CP4-A`, vence 30/04/2027 |
| Examen | EXAMEN DE PRUEBA CP4, código `EX-CP4` |
| Usuario | `prueba.cp4`, rol Usuario de consulta |

Los movimientos de prueba quedan en el historial, porque el historial no se puede borrar (RN-09), y llevan "Prueba CP4" en la observación. Al final, CP4-11 da de baja el producto y el proveedor de prueba. El examen y el usuario de prueba ya quedan dados de baja en CP4-07 y CP4-09.

**Usuarios:** `admin.dev`, `encargado.dev` y `consulta.dev` (contraseñas de desarrollo en `web/seed_usuarios.py`; en producción no funcionan).

---

## Casos

| ID | Flujo del manual | Requerimientos | Pasos | Resultado esperado | Resultado obtenido (20/10/2026) | Evidencia | Estado |
|---|---|---|---|---|---|---|---|
| **CP4-01** | U-01 Iniciar y cerrar sesión; menú por rol | RF-01, RF-02, RF-05, RNF-17 | 1. Entrar como `admin.dev` con una contraseña incorrecta. 2. Entrar con la correcta. 3. Salir. 4. Entrar como `consulta.dev` y escribir `/usuarios/` en la barra de direcciones. | 1 → mensaje genérico. 2 → Inicio con las secciones Operación, Catálogos y Administración. 3 → "Sesión cerrada". 4 → sin sección Administración; `/usuarios/` responde "Acceso no permitido". | 1 → *"Usuario o contraseña incorrectos."* 2 → menú: Inicio, Movimientos, Lotes, Reportes / Productos, Exámenes, Proveedores, Categorías / **Usuarios y roles, Respaldo**. 3 → *"Sesión cerrada."* 4 → menú sin Administración; `/usuarios/` → **"Acceso no permitido"**. | [a](evidencias-entrega-4/CP4-01a-login.png), [b](evidencias-entrega-4/CP4-01b-login-incorrecto.png), [c](evidencias-entrega-4/CP4-01c-inicio-admin.png), [d](evidencias-entrega-4/CP4-01d-inicio-consulta.png), [e](evidencias-entrega-4/CP4-01e-consulta-403.png) | ✅ Pasó |
| **CP4-02** | U-02 Cambiar mi contraseña | RN-15, RNF-04, RNF-17 | Como `consulta.dev`: 1. Botón de la llave; nueva contraseña con confirmación distinta. 2. Repetir bien. 3. Salir y entrar con la contraseña vieja, luego con la nueva. 4. Volver a la original. | 1 → rechazo. 2 → cambio confirmado. 3 → la vieja ya no sirve y la nueva sí. | 1 → *"La confirmación no coincide con la nueva contraseña."* 2 → *"Contraseña cambiada. Úsela la próxima vez que inicie sesión."* 3 → vieja: *"Usuario o contraseña incorrectos."*; nueva: entra a Inicio. 4 → restaurada. | [a](evidencias-entrega-4/CP4-02a-formulario.png), [b](evidencias-entrega-4/CP4-02b-cambiada.png) | ✅ Pasó |
| **CP4-03** | U-08 Crear un producto | RF-06 a RF-09, RN-13 | Como `admin.dev`: 1. Productos → Nuevo producto `PRUEBA-CP4`. 2. Buscarlo en la lista. 3. Intentar crear otro con el mismo código. | 1 y 2 → producto activo con existencia 0. 3 → rechazo por código duplicado. | 1 → *"Producto creado correctamente."* 2 → `PRUEBA-CP4 \| REACTIVO DE PRUEBA CP4 \| REACTIVOS \| UNIDAD \| 0 \| 5 \| … \| Sí \| Activo`. 3 → *"Ya existe un producto con el código "PRUEBA-CP4"."* | [a](evidencias-entrega-4/CP4-03a-nuevo-producto.png), [b](evidencias-entrega-4/CP4-03b-producto-creado.png) | ✅ Pasó |
| **CP4-04** | U-09 Proveedor y productos que suministra | RF-11 a RF-13, RF-39, RN-16 | Como `admin.dev`: 1. Nuevo proveedor (NIT `CP4-0001`). 2. En su ficha, asignar `PRUEBA-CP4` a Q48.00. 3. Asignarlo de nuevo a Q50.00. | 1 → proveedor creado. 2 → producto en la ficha. 3 → el precio se reemplaza, sin duplicar la fila. | 1 → *"Proveedor creado correctamente."* 2 y 3 → *"Producto y precio guardados para este proveedor."* Ficha: una sola fila `PRUEBA-CP4 \| REACTIVO DE PRUEBA CP4 \| UNIDAD \| 50.00 \| Quitar`. | [CP4-04](evidencias-entrega-4/CP4-04-proveedor-producto.png) | ✅ Pasó |
| **CP4-05** | U-03 Registrar una entrada | RF-14 a RF-18, RF-20, RF-22, RF-26, RF-27 | Como `encargado.dev`: Registrar entrada de `PRUEBA-CP4`, proveedor de prueba, lote `CP4-A`, vence 30/04/2027, 20 unidades a Q50. Abrir Lotes. | Lote creado con 20 unidades, responsable "Encargado de Prueba". | *"Entrada registrada: 20 de REACTIVO DE PRUEBA CP4 en el lote CP4-A."* Movimiento n.º 5880. Lote: `CP4-A \| PROVEEDOR DE PRUEBA CP4 \| 20/10/2026 \| 30/04/2027 \| 20 unidades \| Activo`. | [a](evidencias-entrega-4/CP4-05a-entrada.png), [b](evidencias-entrega-4/CP4-05b-entrada-registrada.png), [c](evidencias-entrega-4/CP4-05c-lote.png) | ✅ Pasó |
| **CP4-06** | U-04 Salida y U-05 Devolución; U-06 ficha del lote | RF-21, RF-23, RF-28, RF-35, RN-03, RN-09, RN-19 a RN-22 | Como `encargado.dev`: 1. Registrar salida: el formulario muestra la existencia; sacar 8. 2. "Devolver esta salida" con motivo de menos de 10 caracteres. 3. Devolver 3 con motivo válido. 4. Abrir la ficha del lote. | 1 → existencia 20 visible; salida por FEFO. 2 → no se registra. 3 → devolución enlazada a la salida. 4 → +20, −8, +3; existencia 15. | 1 → *"Existencia utilizable: 20 unidades"*; *"Salida registrada: 8 de REACTIVO DE PRUEBA CP4. Los lotes se eligieron por FEFO…"* (n.º 5881). 2 → el navegador no envía el formulario (`minlength=10`; el servidor también lo valida). 3 → *"Devolución registrada: 3 devuelto a 1 lote(s). La salida #5881 queda corregida…"* 4 → ficha: Entrada +20, Salida −8, Devolución +3; **existencia 15**. | [a](evidencias-entrega-4/CP4-06a-salida.png), [b](evidencias-entrega-4/CP4-06b-salida-registrada.png), [c](evidencias-entrega-4/CP4-06c-devolucion.png), [d](evidencias-entrega-4/CP4-06d-devolucion-registrada.png), [e](evidencias-entrega-4/CP4-06e-ficha-lote.png) | ✅ Pasó |
| **CP4-07** | U-10 Examen, insumos y baja lógica | RF-36 a RF-38, RN-17, RN-24 | Como `admin.dev`: 1. Nuevo examen `EX-CP4`. 2. Agregar insumo `PRUEBA-CP4`, 0.5 por examen. 3. Ver el reporte Pruebas. 4. Dar de baja el examen y ver el reporte de nuevo. | 2 → con 15 unidades alcanza para 30 exámenes. 3 → el examen aparece. 4 → deja de aparecer, pero conserva su ficha. | 1 → *"Examen creado. Agregue los insumos que requiere."* 2 → *"Con la existencia actual alcanza para 30 exámenes. El insumo que limita es REACTIVO DE PRUEBA CP4."* 3 → aparece. 4 → *"Examen dado de baja. Ya no aparece en el informe de pruebas."*; en el reporte: **no aparece**. | [a](evidencias-entrega-4/CP4-07a-examen-insumos.png), [b](evidencias-entrega-4/CP4-07b-examen-de-baja.png) | ✅ Pasó |
| **CP4-08** | U-07 Reportes y exportación | RF-29 a RF-34 | Como `consulta.dev`: 1. Reportes → Kardex de `PRUEBA-CP4`. 2. Descargar CSV. 3. Inventario, Inventario bajo y Vencimientos. | Kardex: entrada 20 × Q50 = Q1,000; salida 8 × Q50 = Q400; devolución 3 × Q50 = Q150 **como entrada**; saldo 15 × Q50 = **Q750**. CSV descargable. | Kardex: saldo inicial 0 → 20 / Q1,000.00 → 12 / Q600.00 → **15 / 50.00 / Q750.00**, con la devolución en la columna de Entradas (3 × 50.00 = 150.00). CSV `kardex-PRUEBA-CP4-20261020.csv` con 4 líneas. Inventario, Inventario bajo y Vencimientos cargan; `PRUEBA-CP4` figura en el inventario. | [a](evidencias-entrega-4/CP4-08a-reportes.png), [b](evidencias-entrega-4/CP4-08b-kardex.png), [csv](evidencias-entrega-4/CP4-08-kardex.csv), [c](evidencias-entrega-4/CP4-08c-inventario-bajo.png), [d](evidencias-entrega-4/CP4-08d-vencimientos.png), [e](evidencias-entrega-4/CP4-08e-inventario.png) | ✅ Pasó |
| **CP4-09** | U-11 Crear, usar y desactivar un usuario | RF-03, RF-04, RN-14, RN-15 | Como `admin.dev`: 1. Nuevo usuario `prueba.cp4`, rol Usuario de consulta. 2. Entrar con él. 3. Desactivarlo. 4. Intentar entrar de nuevo. | 2 → entra con el rol asignado. 4 → no puede entrar; su historial se conserva. | 1 → *"Usuario "prueba.cp4" creado. Ya puede iniciar sesión."* 2 → entra como **Usuario de consulta**. 3 → *"Usuario "prueba.cp4" desactivado: ya no puede iniciar sesión. Su historial se conserva."* 4 → *"Usuario o contraseña incorrectos."* | [a](evidencias-entrega-4/CP4-09a-nuevo-usuario.png), [b](evidencias-entrega-4/CP4-09b-usuarios.png) | ✅ Pasó |
| **CP4-10** | U-12 Descargar un respaldo | RNF-11, RF-05 | 1. Como `admin.dev`: Administración → Respaldo → Descargar. 2. Como `encargado.dev`: abrir `/respaldo/`. | 1 → archivo `.sql` con fecha y hora, firmado por el usuario, con las 11 tablas. 2 → "Acceso no permitido". | 1 → `respaldo_inventario_20261020_1918.sql`; encabezado *"Generado: 20/10/2026 19:18 (hora de Guatemala) por Administrador de Prueba … 14,421 filas en 11 tablas"*; **11 bloques COPY**. 2 → **"Acceso no permitido"**. | [CP4-10](evidencias-entrega-4/CP4-10a-respaldo.png) | ✅ Pasó |
| **CP4-11** | U-08 y U-09 Dar de baja | RF-10, RF-13 | Como `admin.dev`: desactivar `PRUEBA-CP4` y el proveedor de prueba. | Ambos quedan inactivos y conservan su historial. | *"Producto desactivado."*, *"Proveedor desactivado."* | [CP4-11](evidencias-entrega-4/CP4-11-cierre.png) | ✅ Pasó |
| **CP4-12** | Uso en celular (sección 15 del manual) | RNF-18 | Como `encargado.dev`, abrir Inicio con pantalla de 390 × 844 px. | Menú arriba, indicadores legibles, botones de registro visibles, sin desplazamiento horizontal de la página. | Menú arriba, indicadores y botones visibles. Ancho del documento = ancho de la pantalla (390 px) en Inicio, Movimientos, Registrar salida, Lotes, Reportes y Productos: la página no se desborda; las tablas anchas se desplazan dentro de su recuadro. | [CP4-12](evidencias-entrega-4/CP4-12-celular.png) | ✅ Pasó |
| **CP4-13** | Manual técnico, sección 7: restaurar un respaldo | RNF-11 | 1. Generar el respaldo. 2. Crear un esquema vacío con tablas y triggers. 3. Restaurar con `psql`. 4. Comparar cada tabla con la original. | Las 11 tablas idénticas; triggers encendidos otra vez; identidades que continúan después del último id. | Restauración sin errores en menos de 1 s. **11 de 11 tablas idénticas** (14,421 filas, hash md5 por tabla). 0 triggers apagados. Siguiente `id_movimiento` = 5883 (máximo original 5882). | [texto](evidencias-entrega-4/CP4-13-respaldo-restauracion.txt) | ✅ Pasó |
| **CP4-14** | `INSTALL.md`, paso 3: instalación desde cero | S5, RNF-02 | Ejecutar en un esquema vacío los 16 pasos de `INSTALL.md` en orden (15 scripts SQL y `seed_usuarios.py`). | Todo corre sin errores y la base queda con los números de la entrega. | **16 de 16 pasos OK** en 12 s. 11 tablas; 806 productos, 50 proveedores, 50 exámenes, 1,188 lotes, 5,839 movimientos; **0 lotes incoherentes** con su historial; inventario valorizado en **Q524,714.36**, igual que en la Entrega 3. | [texto](evidencias-entrega-4/CP4-14-instalacion.txt) | ✅ Pasó |

**Resultado: 14 de 14 casos pasaron.**

Sobre CP4-14: los dos scripts de `sql/security/` no se incluyeron, porque crean roles de PostgreSQL (requiere superusuario) y esos roles ya existen en este servidor. Su ejecución desde cero está probada en la Entrega 3 (instalación en un segundo equipo, 28/09/2026) y en producción (Neon).

---

## Segunda ejecución con la interfaz nueva (21/10/2026)

El 21/10/2026 la interfaz adoptó el diseño de SIGAL: menú oscuro, barra superior con búsqueda `Ctrl K` y menú de usuario, Panel "Bodega hoy" y tema claro u oscuro. La lógica, las rutas y la base no cambiaron. Para que los flujos del manual queden verificados sobre la interfaz que se entrega, **se volvieron a ejecutar CP4-01 a CP4-12** en Edge, con datos de prueba nuevos ("CP4B": producto `PRUEBA-CP4B`, proveedor NIT `CP4-0002`, lote `CP4B-A`, examen `EX-CP4B`, usuario `prueba.cp4b`), porque los de la primera corrida ya existen.

| Caso | Resultado obtenido (21/10/2026) | Estado |
|---|---|---|
| CP4-01 | Mensaje genérico ante contraseña incorrecta; menú del administrador con Panel … Respaldo; *"Sesión cerrada."* (ahora desde el menú de usuario); `consulta.dev` en `/usuarios/` → **"Acceso no permitido"** | ✅ |
| CP4-02 | Confirmación distinta rechazada; contraseña cambiada desde el menú de usuario; la vieja ya no entra y la nueva sí; se restauró la original | ✅ |
| CP4-03 | *"Producto creado correctamente."*; la lista lo muestra con su categoría y su medidor de existencia en 0 (Agotado); código duplicado rechazado | ✅ |
| CP4-04 | Producto asignado al proveedor y precio cambiado a 50.00, una sola fila | ✅ |
| CP4-05 | *"Entrada registrada: 20 de REACTIVO DE PRUEBA CP4B en el lote CP4B-A."* (movimiento n.º 5883) | ✅ |
| CP4-06 | Existencia mostrada 20; salida de 8 por FEFO (n.º 5884); motivo corto bloqueado; devolución de 3; la ficha del lote termina en **15** | ✅ |
| CP4-07 | Examen con insumo "alcanza para 30 exámenes"; dado de baja, deja de aparecer en el reporte de pruebas | ✅ |
| CP4-08 | Kardex: 20 / Q1,000.00 → 12 / Q600.00 → **15 / Q750.00**, con la devolución en Entradas; CSV de 4 líneas | ✅ |
| CP4-09 | Usuario `prueba.cp4b` creado, entra como Usuario de consulta; desactivado, ya no entra | ✅ |
| CP4-10 | Respaldo de 14,434 filas en 11 tablas con 11 bloques COPY; el encargado recibe 403 | ✅ |
| CP4-11 | Producto y proveedor de prueba desactivados | ✅ |
| CP4-12 | Panel en 390 px con el menú plegado y los indicadores en dos columnas | ✅ |
| Interfaz | `Ctrl K` encuentra el producto y `Enter` abre su kardex; el tema oscuro se recuerda al recargar; el menú de usuario se cierra al hacer clic fuera; los puntos del calendario muestran su ficha | ✅ |

| **CP4-15** | U-13 Corregir una entrada: entrada CP4B de 20 unidades a Q50 → 22 a Q55, motivo escrito. *"Entrada #5883 corregida: 2 datos…"*; la ficha muestra 2 correcciones (antes/después/motivo/quién); el lote pasa de 15 a **17**; el kardex recalcula: saldo 17 × Q55 = **Q935**. Antes, en `psql` (`BEGIN … ROLLBACK`): bajar la entrada por debajo de lo ya salido se rechaza con el mínimo posible; corregir una salida, sin cambios, motivo corto o vencimiento anterior al ingreso se rechazan; `rol_encargado` no puede ejecutar el procedimiento; ni el dueño de las tablas puede modificar o borrar un detalle o una corrección fuera del procedimiento | ✅ |
| **CP4-16** | Carga de SIGAL (`dml/005`): 205 entradas y 516 salidas del 24/09 al 21/10/2026, 0 lotes incoherentes, ninguno negativo; **804 de 813** productos con la misma existencia que SIGAL y las 9 diferencias explicadas (`ENTREGA4_REPORTE_CARGA_SIGAL.md`). La instalación desde cero con los 21 pasos (CP4-14, actualizado) da 814 productos, 6,560 movimientos y Q600,338.34 | ✅ |

**12 de 12 casos aprobados también con la interfaz nueva, más CP4-15 y CP4-16.** Capturas en `evidencias-entrega-4/interfaz-sigal/` (son las que ilustran el manual de usuario) y respuestas del sistema en `interfaz-sigal/CP4-resultados.json`. La regresión automatizada se repitió después del cambio: 183 verificaciones, 0 fallas.

## Tercera ronda: número de documento, roles y bitácora (26/10/2026)

El 26/10/2026 se agregaron tres funciones a pedido del laboratorio: cada movimiento con su número (E/S/D), permisos que el administrador edita por rol y una bitácora de auditoría. Se probaron con el cliente de pruebas de Flask (40 verificaciones) y en Edge.

| ID | Flujo del manual | Requerimientos | Resultado obtenido (26/10/2026) | Evidencia | Estado |
|---|---|---|---|---|---|
| **CP4-17** | U-03, U-04 y búsqueda: número de documento | RN-27 | Los movimientos cargados conservan el número del papel y de SIGAL: el historial muestra la columna N.º (`S004789`, `S004788`…) y en las salidas solo el área, sin "(SIGAL)" ni "(registro en papel)". `Ctrl K` con "e1790" encuentra **Entrada E001790** y `Enter` abre su ficha, titulada así. El kardex y su CSV muestran "Salida S004439". Una entrada y una salida nuevas, dentro de `BEGIN … ROLLBACK`, reciben **E001793** y **S004790**: el siguiente del correlativo. | [a](evidencias-entrega-4/numeracion-roles-bitacora/CP4-17a-historial-con-numero.png), [b](evidencias-entrega-4/numeracion-roles-bitacora/CP4-17b-busqueda-por-numero.png), [c](evidencias-entrega-4/numeracion-roles-bitacora/CP4-17c-ficha-entrada-E001790.png), [resultados](evidencias-entrega-4/numeracion-roles-bitacora/CP4-17-a-19-resultados.txt) | ✅ Pasó |
| **CP4-18** | U-14 Roles y permisos | RN-28, RN-29, RF-04, RF-05 | La tabla de Usuarios y roles muestra casillas por rol; el Administrador, fijo con todo. Al darle "Productos y categorías" al Usuario de consulta, **la sesión ya abierta** de `consulta.dev` entra a Nuevo producto y su rol de BD sube a `rol_administrador`; al quitárselo vuelve a 403 y a `rol_consulta`. Rol nuevo con 1 permiso → nivel `rol_encargado`; renombrado y con Bitácora → `rol_administrador`; eliminado (sin usuarios). No se elimina un rol con usuarios; el Administrador no se renombra ni se elimina. Un usuario desactivado pierde la sesión en la siguiente página. El usuario de consulta recibe 403 en Registrar entrada, con el mensaje que indica pedirle el permiso al administrador. | [a](evidencias-entrega-4/numeracion-roles-bitacora/CP4-18a-tabla-de-permisos.png), [b](evidencias-entrega-4/numeracion-roles-bitacora/CP4-18b-formulario-rol-nuevo.png), [c](evidencias-entrega-4/numeracion-roles-bitacora/CP4-18c-consulta-sin-permiso.png) | ✅ Pasó |
| **CP4-19** | U-15 Bitácora | RN-30 | Quedan registrados los 3 inicios de sesión, el intento fallido (usuario inexistente), el cierre de sesión con su responsable, conceder y quitar un permiso ("Concedió «Productos y categorías» al rol Usuario de consulta"), crear, renombrar y eliminar un rol, desactivar y reactivar un usuario (estado sí → no → sí). El CSV se descarga. Ningún registro guarda el hash de la contraseña (solo "contraseña: (cambiada)"). Un `UPDATE` directo a la bitácora se rechaza: *"La bitácora no se puede modificar ni borrar."* | [a](evidencias-entrega-4/numeracion-roles-bitacora/CP4-19a-bitacora.png), [b](evidencias-entrega-4/numeracion-roles-bitacora/CP4-19b-bitacora-modificaciones.png), [c](evidencias-entrega-4/numeracion-roles-bitacora/CP4-19c-bitacora-permisos.png) | ✅ Pasó |

**3 de 3 casos aprobados.** La instalación desde cero se repitió con los 33 scripts (CP4-14, actualizado): mismos totales, Q600,338.34, numeración de E000001 a E001790 y ninguna observación con el origen de la carga. En producción (Neon) se aplicaron las migraciones el 26/10/2026: 0 movimientos sin número, última entrada E001790, última salida S004788 (la salida de prueba #5840 recibió el suyo) y 14 permisos asignados.

## Defectos encontrados al ejecutar los casos

Las pruebas encontraron tres defectos, que se corrigieron antes de cerrar estos resultados:

| Encontrado en | Defecto | Corrección |
|---|---|---|
| CP4-08 | El kardex mostraba la devolución en las columnas de **Salidas** con "—", aunque el total de entradas sí la sumaba. Lo causaba el mismo patrón `if ENTRADA … else` que `sql/views/004_kardex_devolucion.sql` ya había corregido en la base, ahora en la plantilla. | `informes/kardex.html`: la devolución va en Entradas. Commit "fix(web): muestra la devolución como reingreso en kardex, lote e inicio". |
| CP4-06 | La ficha del lote mostraba la devolución con signo **"−"** y el color de las salidas, aunque suma existencia. En Inicio tenía el mismo color. | `lotes/detalle.html` y `reportes/inicio.html`: solo SALIDA resta. Mismo commit. |
| CP4-06 | La etiqueta decía "Devolucion", sin tilde (D1). | Filtro `tipo_mov` en `app.py`. Commit "fix(web): escribe «Devolución» con tilde en las etiquetas de movimiento". |

Las capturas CP4-06e y CP4-08b se tomaron después de esas correcciones.

## Regresión

Después de todos los cambios de la Entrega 4 se volvió a recorrer la aplicación con el cliente de pruebas de Flask, contra la base real:

| Prueba | Verificaciones | Resultado |
|---|---|---|
| Las 43 pantallas de la app con los 3 roles: cada una responde 200 o 403 según el rol, ninguna da error | 129 | 0 fallas |
| CRUD de proveedor–producto: asignar, cambiar precio, quitar, validaciones y permisos | 12 | 0 fallas |
| Baja lógica de exámenes: informe, CSV, permisos, reactivación | 14 | 0 fallas |
| Respaldo: pantalla, descarga, contenido, permisos | 12 | 0 fallas |
| Seguridad: cambio de contraseña, encabezados HTTP, POST desde otro origen | 16 | 0 fallas |
| Corrección de entradas: botón y formulario solo para el Administrador, validaciones de la app y mensajes de la base, 403 para los otros roles, sin dejar correcciones | 16 | 0 fallas |
| Número de documento: ficha, historial, búsqueda por número, lote, kardex y su CSV, devolución, Panel | 9 | 0 fallas |
| Roles, permisos y bitácora (CP4-18 y CP4-19) | 31 | 0 fallas |
| **Total** | **239** | **0 fallas** |

Cada prueba deshace lo que crea (quita el producto asignado, reactiva el examen, devuelve la contraseña original, devuelve los permisos y elimina el rol de prueba) y su última verificación comprueba que la base quedó como estaba. Lo único que permanece es lo que debe permanecer: las filas que esas acciones dejan en la bitácora (RN-30).

**Nota sobre la base de desarrollo.** Una primera versión de la prueba automatizada de la corrección suponía que la entrada CP4B seguía en 20 unidades a Q50. Después de CP4-15 ya no era así, de modo que su verificación "sin cambios" registró 2 correcciones reales: la entrada volvió a 20 a Q50, con el motivo "Sin cambiar ningún dato". Como exige RN-25, esas correcciones no se pueden borrar y quedan en la base de desarrollo, sobre datos de prueba. La prueba se corrigió para leer los valores actuales y ya no escribe nada.
