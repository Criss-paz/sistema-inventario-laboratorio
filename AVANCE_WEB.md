# Avance de la aplicación web — Entrega 3

**Meta de la rúbrica para esta entrega:** 70% (módulos principales y control de acceso por rol).
**Avance declarado:** los 39 requerimientos funcionales de la Entrega 1 tienen pantalla o están cubiertos por la base de datos. Queda para la Entrega 4: despliegue en internet (S5), respaldos (RNF-11) y pulido final.
**Stack:** Python 3.14 + Flask 3 + PostgreSQL 18 (driver `psycopg` v3). Sin frameworks de interfaz: HTML, CSS y JavaScript propios.

## Módulos

| Módulo | Estado | Qué hace | Quién lo usa |
|---|---|---|---|
| Login / logout | ✅ | Sesión firmada, contraseña con hash, mensaje genérico ante error, redirección solo a rutas internas | Todos |
| Inicio | ✅ | Resumen del inventario: productos con existencia, inventario bajo, lotes vencidos y por vencer, últimos movimientos | Todos |
| Movimientos | ✅ | Pestañas Todos / Entradas / Salidas con filtros por fecha y búsqueda. Registrar entrada (crea o alimenta un lote) y salida (FEFO) llamando a los procedimientos almacenados | Consultar: todos. Registrar: administrador y encargado |
| Lotes | ✅ | Existencia por lote, vencidos, por vencer y la ficha de cada lote con sus movimientos. Corregir número, vencimiento o dar de baja (nunca la existencia) | Consultar: todos. Corregir: administrador |
| Productos | ✅ | CRUD con búsqueda, filtro por categoría, paginación y existencia en vivo | Consultar: todos. Editar: administrador |
| Exámenes | ✅ | CRUD, insumos que consume cada examen y para cuántas pruebas alcanza la existencia | Consultar: todos. Editar: administrador |
| Proveedores | ✅ | CRUD con baja lógica y productos que suministra con su precio | Consultar: todos. Editar: administrador |
| Categorías | ✅ | CRUD con baja lógica | Consultar: todos. Editar: administrador |
| Reportes | ✅ | Pantalla única: el usuario elige Inventario, Entradas, Salidas, Kardex, Proveedores, Pruebas, Catálogo de productos, Inventario bajo o Vencimientos. Todos en CSV e impresión | Todos |
| Usuarios y roles | ✅ | Crear usuarios, cambiar rol, restablecer contraseña, desactivar; tabla de permisos por rol | Administrador |

## Control de acceso por rol (RF-05)

Dos capas independientes:

1. **En la aplicación.** `routes/auth.py::rol_requerido()` protege cada ruta (responde 403 si el rol no corresponde) y las plantillas muestran solo los botones que el rol puede usar (`tiene_rol()`).
2. **En la base de datos.** Después del login, cada petición ejecuta `SET ROLE rol_administrador | rol_encargado | rol_consulta` (`web/db.py`). Aunque la interfaz tuviera un error, PostgreSQL niega lo que el rol no permite. Ningún rol puede leer `password_hash`, editar `cantidad_disponible` ni insertar movimientos sin pasar por los procedimientos.

| Rol | Puede |
|---|---|
| Administrador | Todo, incluidos catálogos, corrección de lotes y usuarios |
| Encargado de inventario | Consultar y registrar entradas y salidas |
| Usuario de consulta | Solo consultar y generar reportes |

## Reglas de negocio visibles en la interfaz

Los mensajes de los triggers y procedimientos (SQLSTATE P0001) llegan tal cual al usuario; cualquier otro error se reemplaza por un mensaje genérico (A2). Ejemplos:
- *"Existencia insuficiente de "CUVETTES FOR URISED": disponible 26.00 (sin contar lotes vencidos), solicitado 99999."*
- *"El producto "AIA-PACK CA19-9 CALIBRATOR SET" requiere fecha de vencimiento en sus lotes."*

## Reportes y método de valuación

El inventario se valoriza por **costo promedio ponderado móvil**, calculado en la base de datos (`fn_kardex_promedio`, `vw_valorizacion_inventario`):
- cada compra recalcula el costo promedio: (valor del saldo + valor de la compra) ÷ (cantidad del saldo + cantidad comprada);
- cada salida se valoriza al promedio vigente ese día;
- el reporte de inventario muestra código de producto, producto, presentación, existencia actual, precio unitario y precio total.

Comprobación contable con los datos reales (marzo a septiembre de 2026): compras Q3,811,436.54 − costo de lo consumido Q3,286,722.24 = Q524,714.30, frente a un inventario valorizado de Q524,714.36. La diferencia de Q0.06 viene del redondeo de cada salida.

## Datos

La base se carga con el inventario real del laboratorio (registros en papel transcritos a Excel): 806 productos, 1,188 lotes y 5,839 movimientos. Los errores que tenía el papel y cómo se trataron están en `docs/entrega-3/reporte-carga-datos.md`.

## Interfaz

Rediseñada como herramienta de trabajo: tipografía Atkinson Hyperlegible (distingue 0/O y 1/l/I al leer códigos y lotes), alojada en la app para funcionar sin internet; menú lateral por tarea; íconos SVG propios; un solo color de acento y colores de estado para vencido, por vencer y disponible. Verificada a 1440 px y a 390 px (celular), con foco visible para teclado.

## Validaciones

- Validación en el servidor antes de tocar la base (A3): campos obligatorios, números, fechas, formato de NIT, correo, usuario y contraseña (mínimo 8 caracteres y confirmación).
- Consultas 100% parametrizadas (A4); los filtros de tipo "lista fija" salen de diccionarios del código, nunca del texto del usuario.
- Duplicados (código, NIT, número de lote, usuario) se informan con un mensaje claro.

## Evidencia de pruebas

- **Casos de la Entrega 3:** `docs/casos-prueba/casos-prueba-entrega-3.md`. Los 8 verificados contra la base real en una transacción revertida; la ejecución manual con capturas está pendiente.
- **Pruebas automatizadas de la app (26/09/2026):** 142 verificaciones con los 3 usuarios (páginas, permisos por rol, formularios, mensajes de la base, reportes y CSV) y 19 del módulo de usuarios. 0 fallos. Las escrituras se revierten para no alterar el inventario.

## Cómo ejecutar

Ver `INSTALL.md`. En Windows, antes de ejecutar los scripts SQL: `$env:PGCLIENTENCODING = "UTF8"`.

```bash
cd web
.venv\Scripts\python.exe app.py      # http://localhost:8080
```

## Pendiente (Entrega 4)

- Despliegue en internet (estándar S5).
- Respaldo y restauración de la base (RNF-11).
- Pulido final a partir de la ejecución de los casos de prueba y la revisión del catedrático.
