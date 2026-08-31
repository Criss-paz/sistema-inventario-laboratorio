# Casos de prueba — Entrega 2

**Ejecutados el 30/08/2026** contra una instancia real: PostgreSQL 18 + Python 3.14 + Flask, en la máquina de desarrollo del equipo. No se ejecutaron a mano en un navegador: se automatizaron con `Invoke-WebRequest` (PowerShell) contra el servidor Flask real (`python app.py`), verificando además el estado final directamente en la base de datos con `psql` cuando aplicaba. Detalle de la sesión: `docs/entrega-2/Bitacora-IA.md`.

| ID | Caso | Precondición | Datos | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|---|---|
| CP-01 | Login correcto | `seed_usuarios.py` ejecutado | usuario=`admin.dev`, password=`Admin#Dev2026` | Redirige a `/categorias/`, muestra nombre y rol en el header | Status 200, URI final `/categorias/`, contenido incluye "Administrador de Prueba" y "Administrador" | ✅ Pasó |
| CP-02 | Login incorrecto — contraseña errónea | Igual que CP-01 | usuario=`admin.dev`, password=`incorrecta` | Mensaje "Usuario o contraseña incorrectos", permanece en `/login`, código 401 | Status 401, cuerpo contiene "incorrectos" | ✅ Pasó |
| CP-03 | Login incorrecto — usuario inexistente | — | usuario=`no.existe`, password=`x` | Mismo mensaje genérico que CP-02 | Status 401, mismo mensaje genérico confirmado | ✅ Pasó |
| CP-04 | Acceso sin sesión bloqueado | Sesión cerrada | GET `/productos/` sin cookie de sesión | Redirige a `/login?next=...` | Status 200 final, URI `http://127.0.0.1:8080/login?next=/productos/`, formulario de login presente | ✅ Pasó |
| CP-05 | Logout | Sesión iniciada | POST `/logout` | Sesión termina, `/productos/` vuelve a bloquear con la misma cookie | Logout status 200; solicitud posterior a `/productos/` con la misma sesión redirige de nuevo a `/login` | ✅ Pasó |
| CP-06 | Creación de categoría válida | Sesión iniciada | nombre="Anticoagulantes", descripción="Insumos anticoagulantes" | Aparece en el listado; fila nueva en `categoria` | Aparece en el listado (id_categoria=6 verificado en BD) | ✅ Pasó |
| CP-07 | Creación de categoría duplicada | CP-06 ejecutado | nombre="Anticoagulantes" (repetido) | Mensaje de duplicado, código 409, no se inserta fila | Status 409, mensaje "Ya existe una categoría..." confirmado | ✅ Pasó |
| CP-08 | Validación de campo obligatorio — categoría sin nombre | Sesión iniciada | nombre="" | Mensaje "El nombre de la categoría es obligatorio.", no llega a la BD | Status 400, mensaje "obligatorio" confirmado | ✅ Pasó |
| CP-09 | Modificación de categoría | CP-06 ejecutado | Editar descripción de "Anticoagulantes" | El listado y la BD reflejan el nuevo texto | Verificado directo en BD: `descripcion = 'Descripcion editada por prueba CP-09'` | ✅ Pasó |
| CP-10 | Baja lógica de categoría | CP-06 ejecutado | POST alternar-estado | Estado cambia a inactiva, la fila NO desaparece de `categoria` | Verificado en BD: `SELECT * FROM categoria WHERE id_categoria=6` → fila presente, `estado=f` | ✅ Pasó |
| CP-11 | Creación de producto válido con FK | Categoría "Reactivos" (id=1) existe | código="REA-999", categoría=Reactivos, unidad="ml", stock_minimo=10 | Aparece en el listado con el nombre de categoría correcto | Aparece en listado junto a "Reactivos"; `id_producto=11` con `id_categoria=1` en BD | ✅ Pasó |
| CP-12 | Creación de producto con código duplicado | CP-11 ejecutado | código="REA-999" (repetido) | Mensaje de duplicado, código 409, no se inserta fila | Status 409, mensaje "Ya existe un producto..." confirmado | ✅ Pasó |
| CP-13 | Validación de stock mínimo negativo | Sesión iniciada | stock_minimo=-5 | Mensaje de validación, no llega a la BD | Status 400, mensaje "no puede ser negativo" confirmado | ✅ Pasó |
| CP-14 | Modificación de producto (cambio de FK) | CP-11 ejecutado | Cambiar categoría del producto a "Material de laboratorio" (id=2) | El listado y la BD reflejan la nueva categoría | Verificado en BD con JOIN: `REA-999 → Material de laboratorio` | ✅ Pasó |
| CP-15 | Persistencia real tras reinicio del servidor | CP-06/CP-11 ejecutados | Detener el proceso `python app.py` (`TaskStop`) y levantarlo de nuevo desde cero | Los registros creados/editados siguen apareciendo | Servidor reiniciado como proceso nuevo; "Anticoagulantes" y "REA-999" (con su categoría editada) siguen presentes | ✅ Pasó |

**Resultado: 15 de 15 casos pasaron.** Ningún resultado fue inventado — cada fila cita cómo se verificó (respuesta HTTP y/o consulta directa a PostgreSQL con `psql`).

## Pruebas manuales adicionales (equipo, en navegador)
Después de las pruebas automatizadas, el equipo abrió la aplicación en el navegador y probó a mano:

| ID | Caso | Datos | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|---|
| CP-16 | Login manual con los 3 roles de prueba | `admin.dev`, `encargado.dev`, `consulta.dev` | Los 3 inician sesión y ven el layout con su nombre y rol correctos | Confirmado por el equipo en navegador | ✅ Pasó |
| CP-17 | Creación manual de un producto desde el formulario web | Producto código `101010001`, nombre `H13` | El producto aparece en el listado y persiste en la BD | Verificado directamente en PostgreSQL: `id_producto=13, codigo='101010001', nombre='H13', estado=activo` | ✅ Pasó |
| CP-18 | Curación manual del catálogo completo con datos reales | Sesión iniciada como `admin.dev` | El equipo editó, una por una desde el formulario web, las 5 categorías y los 10 productos del seed inicial, reemplazando los nombres/descripciones genéricos por el catálogo real del laboratorio (códigos, nombres y unidades reales) | Cada edición persiste; el listado refleja el catálogo real | Verificado en PostgreSQL: las 5 categorías (`REACTIVOS`, `MATERIAL PARA EL LABORATORIO`, `EQUIPO DE PROTECCION PERSONAL`, `INSUMOS DE TOMA DE MUESTRA`, `CALIBRADORES`) y los 10 productos (p. ej. `1707801 MF GLUCOSA - GLU`, `HCFW HbA1c CASSETTE FINECARE, WONDFO`, `TV4MLEPET TUBO AL VACÍO DE 4 ML. EDTA PET - AROSA`) quedaron actualizados con los valores reales — confirmado por consulta directa a `categoria`/`producto` | ✅ Pasó |

Con esto, la interacción manual real en navegador (que en la primera ronda de pruebas quedó pendiente porque esa ronda fue HTTP automatizada) también quedó cubierta — y de paso el catálogo de demostración dejó de ser genérico: es el catálogo real del laboratorio. `sql/dml/001_seed.sql` se actualizó para reflejarlo (ver `docs/entrega-2/Bitacora-IA.md`).

## Qué sigue sin probarse (fuera del alcance de esta entrega)
- Control de acceso diferenciado por rol dentro de la app (que `encargado.dev` no pueda hacer lo mismo que `admin.dev`) — es explícitamente de Entrega 3; por ahora los 3 roles pueden usar los mismos 2 módulos.
- Carga con 50+ registros por tabla (el seed tiene un set reducido de demostración).
