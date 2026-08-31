# Matriz de trazabilidad v1 — Entrega 2

Se fortalece en Entrega 3 (cuando existan vistas/triggers/procedimientos y más módulos web). Por ahora cubre lo que ya tiene soporte real: toda la base de datos (DDL) y los 2 módulos web construidos.

| Requerimiento | Tabla(s) | Campo(s) | Implementación | Evidencia |
|---|---|---|---|---|
| RF-01 Iniciar sesión | usuario, rol | usuario, password_hash, estado | `web/routes/auth.py::login` | CP-01, CP-02, CP-03 |
| RF-02 Cerrar sesión | — | sesión (no BD) | `web/routes/auth.py::logout` | CP-05 |
| RF-03 Administrar usuarios | usuario | todos | `sql/ddl/001_schema.sql` (tabla lista) + `web/seed_usuarios.py` (alta) | Módulo CRUD web de usuarios: pendiente, Entrega 3 |
| RF-04 Asignar roles | usuario.id_rol | id_rol | FK `fk_usuario_rol` en DDL | Diccionario de datos |
| RF-05 Control de acceso por rol | usuario, rol | id_rol | Sesión guarda `nombre_rol`; restricción de acciones por rol: pendiente, Entrega 3 | AVANCE_WEB.md, sección "Pendiente" |
| RF-06 a RF-08 Registrar/modificar/consultar productos | producto | todos | `web/routes/productos.py` (CRUD 2) | CP-11, CP-12, CP-14 |
| RF-09 Clasificar productos por categoría | producto.id_categoria | id_categoria | FK real + selector en `productos/form.html` | CP-11 |
| RF-10 Administrar categorías | categoria | todos | `web/routes/categorias.py` (CRUD 1) | CP-06 a CP-10 |
| RF-11 a RF-13 Proveedores | proveedor | todos | Tabla en DDL + datos de ejemplo en seed | Módulo CRUD web: pendiente, Entrega 3 |
| RF-14 a RF-19 Lotes/vencimientos/existencia | lote | todos | Tabla en DDL + datos de ejemplo en seed | Módulo web + triggers RN-01/RN-07: pendiente, Entrega 3 |
| RF-20 a RF-25 Entradas/salidas/validación de existencia | movimiento, detalle_movimiento, lote | tipo_movimiento, cantidad, cantidad_disponible | Tablas y CHECK en DDL; lógica de suma/resta (RN-02 a RN-04): pendiente como trigger, Entrega 3 | — |
| RF-26 a RF-28 Fecha/usuario/historial de movimientos | movimiento | fecha_hora, id_usuario | FK `fk_movimiento_usuario` (RN-08) en DDL | Diccionario de datos |
| RF-29 Inventario bajo | producto.stock_minimo, lote.cantidad_disponible | — | Campos ya existen; vista/consulta: pendiente, Entrega 3 | — |
| RF-30 Próximos a vencer | lote.fecha_vencimiento | — | Campo ya existe; consulta: pendiente, Entrega 3 | — |
| RF-36 a RF-39 Exámenes e insumos requeridos | examen_laboratorio, examen_producto, proveedor_producto | todos | Tablas puente en DDL + datos de ejemplo en seed | Módulo web: pendiente, Entrega 3 |
| RNF-04/05 Hash de contraseña | usuario.password_hash | password_hash | `werkzeug.security.generate_password_hash` en `seed_usuarios.py`, verificado con `check_password_hash` en login | CP-01, CP-02 |
| RNF-08 Restricciones de integridad | todas | — | 38 restricciones explícitas (PK/FK/UNIQUE/CHECK) — ver `diccionario-datos.md` | `sql/ddl/001_schema.sql` |
| A4 Consultas parametrizadas | — | — | `web/db.py` — toda consulta usa `%s`, ninguna concatena strings | Revisión de código |
