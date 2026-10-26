# Manual técnico

**Sistema Web de Gestión y Control de Inventario — Laboratorio Privado Quetzaltenango**
Versión 1.1 · Entrega 4 · octubre de 2026 (número de documento, permisos por rol y bitácora)

Este manual es para quien instala, administra o modifica el sistema: el administrador del servidor, un desarrollador que continúe el proyecto o el catedrático que lo revisa. Describe la arquitectura, la base de datos, la aplicación web, la seguridad, la instalación, el despliegue, el respaldo y el mantenimiento. La guía de instalación paso a paso está en `INSTALL.md`; aquí se explica *por qué* está construido así y cómo operarlo.

---

## Contenido

1. [Arquitectura](#1-arquitectura)
2. [Estructura del repositorio](#2-estructura-del-repositorio)
3. [Base de datos](#3-base-de-datos)
4. [Aplicación web](#4-aplicación-web)
5. [Seguridad](#5-seguridad)
6. [Instalación y despliegue](#6-instalación-y-despliegue)
7. [Respaldo y restauración](#7-respaldo-y-restauración)
8. [Mantenimiento](#8-mantenimiento)
9. [Pruebas](#9-pruebas)
10. [Solución de problemas](#10-solución-de-problemas)
11. [Limitaciones conocidas y trabajo futuro](#11-limitaciones-conocidas-y-trabajo-futuro)

---

## 1. Arquitectura

```text
 Navegador ──HTTPS──▶  Flask (gunicorn)  ──psycopg 3──▶  PostgreSQL
 (HTML/CSS/JS)         web/                              tablas, triggers,
                       routes/  → db.py                  procedimientos, vistas,
                       templates/                        3 roles de BD, bitácora
```

| Capa | Tecnología | Responsabilidad |
|---|---|---|
| Presentación | Plantillas Jinja2, CSS y JavaScript propios, sin frameworks de interfaz; sistema visual de SIGAL | Mostrar datos y formularios; ocultar lo que el rol no puede usar |
| Aplicación | Python 3.12+ (probado con 3.12 en Render y 3.14 en desarrollo), Flask 3.0 | Sesión, validación de entrada, control de acceso por permiso, traducción de errores |
| Acceso a datos | `web/db.py` con psycopg 3 | Única puerta a PostgreSQL: conexión por petición, permisos del rol, `SET ROLE`, usuario para la bitácora, consultas parametrizadas |
| Datos y reglas de negocio | PostgreSQL 14+ (18 en desarrollo, 17 en Neon) | Integridad, existencias, FEFO, inmutabilidad del historial, numeración de documentos, valorización, permisos, auditoría |

**Decisión central: las reglas de negocio viven en la base de datos.** La existencia de un lote solo la cambia un trigger; las entradas, salidas y devoluciones solo se registran con procedimientos almacenados; el historial lo protege otro trigger; los permisos los aplica PostgreSQL. La aplicación valida antes para dar buenos mensajes, pero aunque tuviera un error, la base no permitiría un inventario incoherente.

**Producción:** la aplicación corre en Render (plan gratuito, `gunicorn app:app --workers 2`) y la base en Neon (PostgreSQL 17), las dos en US East (Ohio). Dirección: https://inventario-laboratorio-03s7.onrender.com

---

## 2. Estructura del repositorio

```text
├── README.md, INSTALL.md, AVANCE_WEB.md, .env.example, .gitignore, .gitattributes
├── docs/
│   ├── entrega-1/ … entrega-4/   documentos de cada entrega (prefijo ENTREGA<N>_)
│   ├── diagramas/                ER (Chen) y relacional: .drawio editable + PNG + PDF
│   ├── certificaciones/          CERTIFICACION_ENTREGA_<N>.md
│   ├── bitacora-ia/              bitácoras de uso de IA y la consolidada
│   └── casos-prueba/             casos de cada entrega y sus evidencias
├── sql/
│   ├── ddl/          001 esquema · 002 devolución · 003 baja lógica de exámenes · 004 corrección de entradas
│   │                 005 número de documento · 006 permisos por rol · 007 bitácora
│   ├── dml/          001–004 datos del papel (generar_carga.py) · 005 movimientos de SIGAL (generar_carga_sigal.py)
│   ├── triggers/     001 existencia, inmutabilidad, vencimiento · 002 tope de devolución · 003 corrección
│   │                 004 número de documento · 005 rol Administrador protegido · 006 bitácora
│   ├── procedures/   001 entrada y salida (FEFO) · 002 devolución · 003 corrección de entradas · 004 fn_rol_bd
│   ├── views/        001 consultas · 002 kardex y valorización · 003–004 devolución · 005 correcciones
│   │                 006 número en el historial · 007 bitácora
│   └── security/     001 roles · 002 devolución · 003 corrección · 004 permisos y bitácora
└── web/
    ├── app.py          arma la app: blueprints, filtros, manejadores de error, encabezados
    ├── config.py       variables de entorno
    ├── db.py           acceso a datos
    ├── respaldo.py     servicio de respaldo (también ejecutable por línea de comandos)
    ├── seed_usuarios.py  usuarios de desarrollo
    ├── routes/         un módulo por área (12)
    ├── templates/      43 plantillas
    └── static/         style.css (diseño de SIGAL, tema claro/oscuro), app.js (tema, menús, avisos,
                        búsqueda Ctrl K), fuentes Schibsted Grotesk y JetBrains Mono, favicon
```

Cada script SQL abre con un encabezado: archivo, propósito, autor, descripción, reglas de negocio, dependencias, SGBD y forma de ejecutarlo (estándar S3). Los scripts de esquema `002` a `007` son **migraciones aditivas**: se aplican sobre una base existente sin borrar datos. `005` además rellena el número de documento de los movimientos ya cargados (ver 3.1).

---

## 3. Base de datos

El diseño completo (modelo relacional, normalización 3FN y diccionario de datos) está en `docs/entrega-2/`. Esta sección resume lo que un administrador necesita saber.

### 3.1 Tablas

| Tabla | Contenido | Filas (datos iniciales) |
|---|---|---|
| `rol` | Roles de la aplicación; el administrador puede crear más | 3 |
| `permiso` | Acciones que se pueden conceder a un rol, con el nivel de PostgreSQL que necesita cada una | 11 |
| `rol_permiso` | Qué permisos tiene cada rol (N:M) | 14 |
| `usuario` | Usuarios, con contraseña en hash | 3 (desarrollo) |
| `categoria` | Clasificación de productos | 10 |
| `producto` | Catálogo de insumos y reactivos | 814 |
| `proveedor` | Proveedores | 51 |
| `lote` | Cada lote recibido, con su existencia | 1,296 |
| `movimiento` | Cabecera de cada entrada, salida o devolución, con su número de documento (E/S/D) | 6,560 |
| `detalle_movimiento` | Cuánto de cada lote movió cada movimiento (resuelve movimiento–lote N:M) | 6,646 |
| `examen_laboratorio` | Exámenes que ofrece el laboratorio | 50 |
| `proveedor_producto` | Qué productos suministra cada proveedor y a qué precio (N:M) | 425 |
| `examen_producto` | Qué insumos consume cada examen y cuánto (N:M) | 114 |
| `correccion_entrada` | Cada dato corregido de una entrada: valor anterior, nuevo, motivo, quién y cuándo (solo crece) | 0 |
| `bitacora` | Auditoría: quién creó, modificó o eliminó qué, inicios y cierres de sesión, descargas de respaldo (solo crece) | 0 |

Las 17 FK declaran `ON DELETE` y `ON UPDATE` con su justificación en el DDL (estándar S4): `RESTRICT` donde hay historial que proteger (lotes, movimientos, bitácora), `CASCADE` en las tablas puente.

**Número de documento (RN-27).** `movimiento.numero_documento` es `E`, `S` o `D` según el tipo, más 6 dígitos: `UNIQUE` y con un `CHECK` de formato y de prefijo. Los movimientos del papel y de la carga posterior conservan su número original; `ddl/005` lo tomó del texto de la observación (y limpió ese texto) desactivando el trigger de inmutabilidad solo dentro de su transacción. Los movimientos nuevos los numera `trg_movimiento_numero`. La numeración del papel tiene huecos (servicios y rechazos que no se cargaron); la de los nuevos no los tiene.

**Baja lógica.** Ningún catálogo se borra: `categoria`, `producto`, `proveedor`, `usuario`, `lote` y, desde la Entrega 4, `examen_laboratorio` tienen columna `estado`. Así el historial siempre puede mostrar a qué producto, proveedor o usuario se refiere cada movimiento.

**Único dato calculado que se almacena:** `lote.cantidad_disponible`. Lo mantiene exclusivamente el trigger de existencia, y se puede verificar contra el historial en cualquier momento con la consulta de coherencia de `sql/dml/README.md`, que debe devolver 0 (estándar S7).

### 3.2 Triggers

| Trigger | Tabla | Regla |
|---|---|---|
| `trg_detalle_movimiento_existencia` | `detalle_movimiento` | La entrada y la devolución suman a la existencia del lote; la salida resta, con bloqueo `FOR UPDATE`, y nunca la deja negativa (RN-01 a RN-04) |
| `trg_z_devolucion_tope` | `detalle_movimiento` | Una devolución no puede devolver más de lo que salió de ese lote, descontando lo ya devuelto (RN-22). El prefijo `z` hace que corra después del de existencia |
| `trg_movimiento_inmutable`, `trg_detalle_movimiento_inmutable` | `movimiento`, `detalle_movimiento` | Prohíben `UPDATE` y `DELETE`: el historial solo crece (RN-09). Única excepción: la cantidad y el precio de una entrada mientras corre `sp_corregir_entrada`, que deja la corrección registrada |
| `trg_lote_vencimiento` | `lote` | Si el producto requiere vencimiento, el lote debe tener fecha (RN-07) |
| `trg_z_correccion_existencia` | `detalle_movimiento` | Al corregir la cantidad de una entrada, ajusta el lote por la diferencia y no lo deja negativo (RN-01, RN-25) |
| `trg_correccion_inmutable` | `correccion_entrada` | Las correcciones no se modifican ni se borran |
| `trg_movimiento_numero` | `movimiento` | Asigna el siguiente número de su tipo (E/S/D), con un candado de transacción por tipo para que dos registros simultáneos no tomen el mismo, y en las devoluciones escribe la salida que corrigen por su número (RN-27) |
| `trg_rol_protegido` | `rol` | El rol Administrador no se renombra ni se elimina (RN-29) |
| `trg_bitacora_*` (12) | `categoria`, `producto`, `proveedor`, `examen_laboratorio`, `proveedor_producto`, `examen_producto`, `usuario`, `rol`, `rol_permiso`, `lote` (solo los datos que corrige una persona), `movimiento`, `correccion_entrada` | Escriben en la bitácora cada creación, modificación (solo los campos que cambiaron, con el valor anterior y el nuevo) y eliminación; nunca la contraseña (RN-30) |
| `trg_bitacora_inmutable` | `bitacora` | La bitácora no se modifica ni se borra |

En total, 22 triggers.

### 3.3 Procedimientos y funciones

| Objeto | Tipo | Qué hace |
|---|---|---|
| `sp_registrar_entrada` | Procedimiento, `SECURITY DEFINER` | Crea el lote si no existe (o suma al existente) y registra la entrada en una sola transacción |
| `sp_registrar_salida` | Procedimiento, `SECURITY DEFINER` | Reparte la cantidad entre los lotes no vencidos, primero el que vence antes (FEFO); falla completa si no alcanza |
| `sp_registrar_devolucion` | Procedimiento, `SECURITY DEFINER` | Registra el movimiento inverso de una salida, con motivo obligatorio, enlazado a ella (RN-19 a RN-21) |
| `sp_corregir_entrada` | Procedimiento, `SECURITY DEFINER`, solo Administrador | Corrige cantidad, precio, proveedor, número de lote o vencimiento de una entrada y registra cada cambio en `correccion_entrada` (RN-25, RN-26) |
| `fn_devolvible` | Función, `SECURITY DEFINER` | Saldo que aún se puede devolver de cada lote de una salida |
| `fn_kardex_promedio` | Función | Kardex de un producto a costo promedio ponderado móvil |
| `fn_validar_usuario_activo` | Función | Un movimiento solo lo registra un usuario activo (RN-08) |
| `fn_rol_bd` | Función | El rol de PostgreSQL más bajo que cubre los permisos de un rol de la aplicación: `rol_administrador` si es el Administrador o tiene algún permiso de ese nivel, `rol_encargado` si tiene alguno de nivel encargado, `rol_consulta` si no tiene ninguno (RN-28) |
| `fn_bitacora` | Función de trigger, `SECURITY DEFINER` | Escribe en la bitácora; el responsable sale de `current_setting('app.id_usuario')`, que la app fija en cada conexión |
| `fn_registrar_evento` | Función, `SECURITY DEFINER` | Registra un cierre de sesión o una descarga de respaldo a nombre del usuario de la conexión; ningún otro evento |
| `fn_*` restantes | Funciones de trigger | Implementan los triggers de 3.2 |

Los errores de negocio se lanzan con `RAISE EXCEPTION` sin código propio (SQLSTATE `P0001`) y con un texto escrito para el usuario. La aplicación muestra esos textos tal cual y oculta cualquier otro error (sección 4.3).

Los procedimientos son `SECURITY DEFINER` con `search_path` fijo (`public, pg_temp`). Así un rol sin `INSERT` sobre `movimiento` puede registrar movimientos, pero **solo** a través de ellos.

### 3.4 Vistas

| Vista | Uso |
|---|---|
| `vw_existencia_producto` | Existencia total y utilizable (sin lotes vencidos) por producto |
| `vw_inventario_bajo` | Productos en su stock mínimo o por debajo |
| `vw_lotes_por_vencer` | Lotes vencidos y por vencer (90 días) |
| `vw_historial_movimientos` | Historial legible: movimiento, lote, producto, proveedor y responsable, sin el hash de la contraseña |
| `vw_valorizacion_inventario` | Valor del inventario a costo promedio ponderado |
| `vw_devoluciones` | Auditoría de devoluciones con su salida de origen y motivo |
| `vw_correcciones_entrada` | Correcciones de entradas con el dato en palabras y quién las hizo |
| `vw_bitacora` | Bitácora con el nombre del responsable ("Sistema" si el cambio se hizo fuera de la app) |

`vw_historial_movimientos` incluye además el número de documento del movimiento y, en las devoluciones, el de la salida que corrigen.

### 3.5 Roles de base de datos

| Rol | Hereda de | Puede |
|---|---|---|
| `rol_consulta` | — | `SELECT` en catálogos, lotes y vistas; ejecutar `fn_kardex_promedio` y `fn_devolvible`. Sin acceso a `usuario`, `rol` ni a las tablas de movimientos |
| `rol_encargado` | `rol_consulta` | Además, ejecutar los tres procedimientos de registro |
| `rol_administrador` | `rol_encargado` | Además, ejecutar `sp_corregir_entrada`; `INSERT`/`UPDATE` en catálogos; `UPDATE` de `lote` solo en las columnas que corrige una persona (número, proveedor, fechas, estado; nunca `cantidad_disponible`); `DELETE` en las tablas puente; y administrar usuarios por columna, **sin poder leer `password_hash`** |

Ningún rol puede modificar `cantidad_disponible`, ni insertar, modificar o borrar movimientos directamente. Detalle y justificación en `sql/security/001_roles.sql`.

**Roles de la aplicación y roles de la base (RN-28).** Desde el 26/10/2026, los permisos de cada rol de la aplicación son datos (`permiso`, `rol_permiso`) que el administrador edita. Los 3 roles de PostgreSQL no cambian: son **niveles**. En cada petición, `fn_rol_bd` elige el nivel más bajo que cubre los permisos del rol y la app lo adopta con `SET ROLE`. Así se mantienen las dos capas: la app aplica el permiso exacto (por ejemplo, *Registrar salidas* sin *Registrar entradas*) y la base, el nivel. `rol_administrador` además puede crear, renombrar y eliminar roles y cambiar sus permisos, y leer la bitácora solo por `vw_bitacora`. Nadie tiene `INSERT` sobre `bitacora`.

### 3.6 Valorización

Costo promedio ponderado móvil, calculado en `fn_kardex_promedio`:

- **Compra:** promedio nuevo = (valor del saldo + valor de la compra) ÷ (cantidad del saldo + cantidad comprada).
- **Salida:** se valora al promedio vigente; no lo cambia.
- **Devolución:** reingresa al promedio vigente; tampoco lo cambia (RN-23).

Con los datos iniciales (papel y SIGAL, hasta el 21/10/2026), el inventario vale **Q600,338.34**. Esta cifra sirve para comprobar que una instalación quedó bien (CP4-14).

---

## 4. Aplicación web

### 4.1 Módulos

| Módulo (`web/routes/`) | Pantallas | Roles |
|---|---|---|
| `auth.py` | Login, logout, cambiar mi contraseña; `login_required`, `permiso_requerido`, `tiene_permiso`; inicio, intento fallido y cierre de sesión en la bitácora | Todos |
| `reportes.py` | Panel "Bodega hoy" (indicadores, calendario de vencimientos, reponer primero, actividad), inventario bajo, por vencer y `buscar` (JSON para la búsqueda `Ctrl K`: productos y movimientos por número) | Todos |
| `movimientos.py` | Historial (todos/entradas/salidas/devoluciones, búsqueda por número), detalle, entrada, salida, devolución, corrección de entradas | Consultar: todos · Registrar y corregir: permisos `REGISTRAR_ENTRADAS`, `REGISTRAR_SALIDAS`, `DEVOLVER_SALIDAS`, `CORREGIR_ENTRADAS` |
| `lotes.py` | Lista por estado, ficha, corrección de datos | Consultar: todos · Corregir: `EDITAR_LOTES` |
| `productos.py`, `categorias.py` | CRUD con baja lógica | Consultar: todos · Editar: `PRODUCTOS` |
| `proveedores.py` | CRUD con baja lógica y productos que suministra con su precio | Consultar: todos · Editar: `PROVEEDORES` |
| `examenes.py` | CRUD con baja lógica e insumos por examen | Consultar: todos · Editar: `EXAMENES` |
| `informes.py` | Pantalla única de reportes (9 tipos), CSV e impresión | Todos |
| `usuarios.py` | Usuarios; roles (crear, renombrar, eliminar) y tabla de permisos | `USUARIOS` |
| `bitacora.py` | Bitácora con filtros y CSV; traduce cada registro a una frase legible | `BITACORA` |
| `respaldo.py` | Descarga del respaldo (queda en la bitácora) | `RESPALDO` |

El rol Administrador tiene siempre todos los permisos; los demás, los que les asigne el administrador.

### 4.2 Flujo de una petición

1. Si hay sesión, `db.get_db()` abre la conexión de la petición y, como `usuario_app`, lee el rol del usuario, sus permisos y `fn_rol_bd`. Si el usuario ya no existe o está desactivado, la sesión se cierra (`SesionInvalida`) y se redirige al login. Después fija `app.id_usuario` (para la bitácora) y ejecuta `SET ROLE` con el nivel que corresponde, seguido de un `COMMIT` inmediato, para que un `ROLLBACK` posterior no lo deshaga.
2. `permiso_requerido("CÓDIGO")` verifica la sesión y el permiso. Si falta, responde 403; si no hay sesión, redirige al login. Como los permisos se leen en cada petición, un cambio del administrador rige desde la siguiente página.
3. La ruta valida la entrada (obligatorios, números con hasta 2 decimales, fechas, formatos) **antes** de tocar la base (A3).
4. Las consultas usan siempre parámetros (`%s` / `%(nombre)s`). Los pocos fragmentos de SQL armados con f-string solo combinan texto fijo del código, nunca texto del usuario (A4).
5. Al terminar la petición, `close_db` cierra la conexión.

### 4.3 Manejo de errores (A2)

`db.mensaje_error(exc, por_defecto)` muestra al usuario solo los mensajes de reglas de negocio (SQLSTATE `P0001`) y "Su rol no tiene permiso…" ante un `InsufficientPrivilege`. Cualquier otro error se reemplaza por un texto genérico. Las páginas 403, 404 y 500 son propias y nunca muestran trazas ni SQL.

### 4.4 Configuración (`.env`)

| Variable | Uso |
|---|---|
| `DATABASE_URL` | Producción (Neon). Si existe, se ignoran las `DB_*` |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Instalación local |
| `APP_SECRET` | Firma de la cookie de sesión. En producción es obligatoria: la app no arranca con el valor por defecto |
| `APP_ENV` | `production` activa la cookie solo por HTTPS, `ProxyFix` y HSTS |
| `APP_PORT` | Puerto en desarrollo (8080) |

`.env` nunca se versiona; `.env.example` documenta los nombres con valores ficticios (R6).

---

## 5. Seguridad

| Protección | Dónde | Qué evita |
|---|---|---|
| Contraseñas con hash (`werkzeug.security`, scrypt) | `auth.py`, `usuarios.py` | Leer contraseñas aunque se filtre la base |
| Ningún rol de la app puede leer `password_hash` | `security/001_roles.sql` | Que un error de la app exponga los hashes |
| Mensaje genérico de login | `auth.login` | Averiguar qué usuarios existen |
| Redirección tras login solo a rutas internas | `auth.login` | Redirecciones abiertas (`?next=https://otro-sitio`) |
| Control de acceso en dos capas: app (`permiso_requerido`, permiso exacto) y base (`SET ROLE`, nivel calculado con `fn_rol_bd`) | `auth.py`, `db.py` | Que un error en una capa dé acceso indebido |
| Sesión revalidada en cada petición | `db.get_db`, `app.sesion_vigente` | Que un usuario desactivado siga trabajando con la sesión abierta |
| Bitácora de auditoría inmutable, escrita por triggers `SECURITY DEFINER` | `triggers/006_bitacora.sql` | Cambios sin responsable; borrar el rastro de un cambio |
| Cookie de sesión `HttpOnly`, `SameSite=Lax` y, en producción, `Secure` | `config.py` | Robo de la sesión por JavaScript y envío desde otros sitios |
| Rechazo de POST con encabezado `Origin` ajeno | `app.mismo_origen` | Falsificación de peticiones entre sitios (CSRF), como segunda barrera |
| Encabezados `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options`, `Referrer-Policy`, HSTS | `app.encabezados_de_seguridad` | Contenido inyectado, páginas que "envuelven" al sistema, filtración de URL |
| Historial inmutable | Triggers | Alterar o borrar el rastro de una operación |
| Sin credenciales en el repositorio | `.gitignore`, `.env.example` | Exposición de contraseñas (R6) |

**La excepción documentada: `db.conexion_sin_rol()`.** Es la única conexión que no adopta un rol. La usan tres operaciones que necesitan `password_hash`:

- el login, antes de que exista sesión (también escribe el inicio o el intento fallido en la bitácora);
- el cambio de contraseña propio, siempre sobre el `id_usuario` de la sesión firmada y nunca sobre uno recibido del formulario (fija `app.id_usuario`, así el cambio queda en la bitácora a su nombre);
- el respaldo, restringido al Administrador y abierto en modo de solo lectura.

Cualquier otro uso nuevo de esa función debe justificarse igual.

**Recomendaciones de operación:**
- Cambiar las contraseñas iniciales en el primer ingreso (U-02).
- Activar la verificación en dos pasos en las cuentas de GitHub, Render y Neon: quien controla esas cuentas controla el sistema.
- Rotar la contraseña de Neon si alguna vez se expone (Neon → Connect → Reset password, y actualizar `DATABASE_URL` en Render).

---

## 6. Instalación y despliegue

### 6.1 Instalación local

`INSTALL.md`, pasos 1 a 7. En resumen:

1. Crear el usuario `usuario_app` y la base `inventario_laboratorio`.
2. Ejecutar los scripts SQL **en el orden del paso 3**. El orden importa:
   - los triggers van antes de los datos, para que validen también la carga inicial;
   - `security/` va después de que existan todos los objetos;
   - las migraciones (`002` a `007`) van al final; `ddl/005_numero_documento.sql`, después de las cargas de `dml/`, porque toma los números de su texto.
3. Copiar `.env.example` a `.env` y completarlo.
4. Instalar las dependencias (`pip install -r web/requirements.txt`) y ejecutar `python web/app.py`.

En Windows, antes de `psql`: `$env:PGCLIENTENCODING = "UTF8"`. Sin esto, las tildes se guardan corruptas sin ningún error.

La instalación completa desde cero toma unos 30 segundos de scripts. Se verificó el 26/10/2026 con los 33 pasos (CP4-14): 15 tablas, 814 productos, 6,560 movimientos numerados de E000001 a E001790, 0 lotes incoherentes y Q600,338.34.

### 6.2 Producción (Render + Neon)

`INSTALL.md`, paso 8. Dos detalles críticos:

- **La cadena de Neon debe ser la directa, sin `-pooler`.** La app cambia de rol con `SET ROLE` en cada conexión, y un pooler en modo transacción podría reutilizar una sesión con el rol de otro usuario.
- **Render no despliega solo.** El repositorio se conecta por URL pública: después de cada `push` hay que usar **Manual Deploy → Deploy latest commit**.

### 6.3 Actualizar una instalación existente

Cuando el repositorio trae una migración nueva (`sql/ddl/00N_*.sql` y compañía), se aplica sobre la base existente **sin** reinstalar. Para pasar una base de la Entrega 3 a la Entrega 4:

```bash
# Si la base todavía no tiene la devolución (Entrega 3, 29/09/2026):
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/ddl/002_devolucion.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/triggers/002_devolucion.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/procedures/002_devolucion.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/views/003_devolucion.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/views/004_kardex_devolucion.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/security/002_devolucion.sql
# Entrega 4 (reejecutable):
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/ddl/003_examen_estado.sql
# Corrección de entradas:
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/ddl/004_correccion_entrada.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/triggers/003_correccion_entrada.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/procedures/003_correccion_entrada.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/views/005_correccion_entrada.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/security/003_correccion_entrada.sql
# Movimientos de SIGAL (una sola vez; se niega a correr si ya se aplicó):
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/dml/005_carga_sigal.sql
# Número de documento (después de la carga anterior):
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/ddl/005_numero_documento.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/triggers/004_numero_documento.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/views/006_numero_documento.sql
# Permisos por rol y bitácora:
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/ddl/006_permisos.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/procedures/004_permisos.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/triggers/005_rol_protegido.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/ddl/007_bitacora.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/triggers/006_bitacora.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/views/007_bitacora.sql
psql "<cadena>" -v ON_ERROR_STOP=1 -f sql/security/004_permisos_bitacora.sql
```

**Orden con el despliegue:** primero la base y después el código. La versión de la app del 26/10/2026 lee `permiso` y `rol_permiso` en cada petición: si se despliega antes de las migraciones, ninguna página abre.

Para saber si una base ya tiene la devolución: `SELECT column_name FROM information_schema.columns WHERE table_name = 'movimiento' AND column_name = 'motivo';` (si devuelve una fila, ya está). Antes de aplicar cualquier migración en producción, **descargue un respaldo** (sección 7).

**Lo que pasó al aplicarlas en Neon (21/10/2026)**, por si hay que repetirlo en otra base:

- Sin `psql` a mano, los mismos scripts se pueden pegar en el **SQL Editor** de Neon: no usan comandos de `psql`. Si uno falla, el editor muestra «Failed transaction: ROLLBACK required»; el error está en la última pestaña de resultados, y hay que pulsar **ROLLBACK** antes de volver a intentar.
- En producción los usuarios se llaman `admin`, `encargado` y `consulta` (sin `.dev`). `005_carga_sigal.sql` acepta cualquiera de los dos nombres del encargado.
- Una **salida de prueba** hecha en producción (#5840, 1 unidad) había dejado en 0 el lote que SIGAL necesitaba, y la carga se detuvo con «Existencia insuficiente». No se borró, porque el historial es inmutable: se anuló con `sp_registrar_devolucion` y la carga se repitió. Resultado: 814 productos, 6,562 movimientos (incluyen la prueba y su devolución) y Q600,338.34, igual que la instalación desde cero.

El 26/10/2026 se aplicaron en Neon las migraciones del número de documento, los permisos y la bitácora en una sola ejecución del SQL Editor (68 instrucciones sin error): 0 movimientos sin número, última entrada E001790, última salida S004788 (la salida de prueba #5840 recibió el suyo) y 14 permisos asignados. Después, Manual Deploy en Render.

`security/002_devolucion.sql`, `003` y `004` solo contienen `ALTER FUNCTION`, `GRANT` y `REVOKE` sobre objetos propios, así que lo puede ejecutar el dueño de las tablas (`usuario_app` en local, `neondb_owner` en Neon) sin superusuario.

---

## 7. Respaldo y restauración

Cubre el requerimiento RNF-11.

### 7.1 Qué respalda

`web/respaldo.py` genera un archivo `.sql` con **los datos** de las 15 tablas, bitácora incluida. No incluye la estructura: tablas, triggers, procedimientos, vistas y roles ya están versionados en `sql/` y se reinstalan desde ahí. El archivo:

- usa bloques `COPY … FROM stdin`, el mismo formato que `pg_dump`, así que es SQL estándar y legible, y se restaura sin la aplicación;
- lee todas las tablas en **una sola foto** de la base (`REPEATABLE READ`, solo lectura), aunque alguien registre un movimiento mientras se genera;
- incluye un encabezado con la fecha, quién lo generó, la versión de PostgreSQL y el total de filas;
- se niega a generarse si la base tiene una tabla que el respaldo no conoce. Si se agrega una tabla, hay que sumarla a `TABLAS` en `respaldo.py`, en orden de dependencias.

**¿Por qué no `pg_dump`?** Render no lo incluye, y el que trae una imagen suele ser más viejo que el servidor de Neon (PostgreSQL 17), lo que `pg_dump` rechaza. Generar el mismo formato desde Python funciona igual en local y en producción.

### 7.2 Cómo obtenerlo

- **Desde la aplicación:** Administración → Respaldo → Descargar respaldo (U-12 del manual de usuario).
- **Desde la línea de comandos** (para una tarea programada en el servidor):

  ```bash
  cd web
  python respaldo.py /ruta/respaldos/respaldo_$(date +%Y%m%d).sql
  ```

  Ejemplo con el Programador de tareas de Windows o `cron`: una vez por semana, conservando las últimas 4 copias en un disco distinto del servidor.

### 7.3 Cómo restaurar

La restauración **reemplaza todos los datos** de la base de destino. Por eso no se ofrece desde la aplicación.

1. Tenga una base con el **esquema instalado**: `INSTALL.md`, paso 3, **sin** los scripts de `dml/` ni `seed_usuarios.py`. Si va a restaurar sobre la base actual, el esquema ya está.
2. Ejecute:

   ```bash
   # Windows: $env:PGCLIENTENCODING = "UTF8"
   psql -U usuario_app -d inventario_laboratorio -v ON_ERROR_STOP=1 -f respaldo_inventario_AAAAMMDD_HHMM.sql
   ```

   En Neon: `psql "<cadena de Neon>" -v ON_ERROR_STOP=1 -f respaldo_….sql`

3. Verifique con la consulta de coherencia de `sql/dml/README.md` (debe dar 0) y que Reportes → Inventario muestre el valor esperado.

Qué hace el archivo al restaurar, en **una sola transacción** (si algo falla, la base queda exactamente como estaba):

1. Apaga los triggers de usuario de las 15 tablas. La existencia de cada lote ya viene calculada, el trigger de historial inmutable impediría recargar los movimientos y los de la bitácora registrarían la restauración como si fueran cambios nuevos.
2. `TRUNCATE` de las 15 tablas.
3. `COPY` de cada tabla en orden de dependencias. Las FK **sí** se verifican, porque son triggers del sistema y no se apagan.
4. Ajusta cada secuencia de identidad al siguiente valor libre.
5. Vuelve a encender los triggers y hace `COMMIT`.

**Probado** (CP4-13, 20/10/2026): restaurado en una base vacía con tablas y triggers, las 11 tablas quedaron idénticas a la original (14,421 filas, hash md5 por tabla), los triggers activos y las identidades en el valor correcto.

---

## 8. Mantenimiento

### 8.1 Agregar una funcionalidad que toca la base

1. Escriba una **migración aditiva** numerada en la carpeta que corresponda (`sql/ddl/004_….sql`, `sql/views/005_….sql`…), con el encabezado estándar y, si se puede, reejecutable (`IF NOT EXISTS`).
2. Si crea objetos nuevos, otorgue los permisos en un script de `sql/security/` (un script, un propósito: S2).
3. Si crea una tabla, agréguela a `TABLAS` en `web/respaldo.py`.
4. Agregue la migración al orden de `INSTALL.md`, paso 3, y a la sección 6.3 de este manual.
5. Pruébela dentro de `BEGIN … ROLLBACK`, o en un esquema aparte (`CREATE SCHEMA prueba; SET search_path = prueba;`), antes del commit (S8).
6. Después del push: respaldo de producción, aplicar la migración en Neon y **Manual Deploy** en Render.

### 8.2 Agregar una pantalla

1. Cree o amplíe un módulo en `web/routes/`, con docstring que explique su responsabilidad y quién puede usarlo (A6).
2. Proteja cada ruta con `@login_required` o `@permiso_requerido("CÓDIGO")`. Si la acción es nueva, agregue su permiso a la tabla `permiso` con el nivel de base que necesita, en una migración.
3. Valide la entrada en el servidor, use `query_*`/`execute`/`call_procedure` de `db.py` con parámetros, y traduzca los errores con `mensaje_error`.
4. Si es un blueprint nuevo, regístrelo en `app.py` y agregue la entrada al menú en `templates/base.html`.

### 8.3 Tareas periódicas

| Tarea | Frecuencia |
|---|---|
| Descargar un respaldo y guardarlo fuera del servidor | Semanal y antes de cada cambio |
| Revisar Lotes → Vencidos con existencia y registrar su baja | Semanal |
| Revisar usuarios activos y desactivar a quien ya no trabaja en el laboratorio | Mensual |
| Revisar en la Bitácora los intentos fallidos de inicio de sesión y los cambios de permisos | Mensual |
| Actualizar dependencias de `web/requirements.txt` y volver a correr las pruebas | Trimestral |

---

## 9. Pruebas

| Conjunto | Dónde | Qué cubre |
|---|---|---|
| Casos de la Entrega 2 | `docs/casos-prueba/casos-prueba-entrega-2.md` | Login, CRUD de categorías y productos (18) |
| Casos de la Entrega 3 | `docs/casos-prueba/casos-prueba-entrega-3.md` | Triggers, FEFO, inmutabilidad, roles, valorización, devolución (14) |
| Casos de la Entrega 4 | `docs/casos-prueba/casos-prueba-entrega-4.md` | Flujos del manual de usuario, corrección de entradas, carga de SIGAL, número de documento, roles y permisos, bitácora, respaldo y restauración, instalación desde cero (19) |
| Regresión de la app | Descrita en los casos de la Entrega 4 | 43 pantallas × 3 roles y los módulos nuevos (239 verificaciones) |

Las pruebas de la app usan el cliente de pruebas de Flask (`app.test_client()`) contra una base real con los datos iniciales; cada una deshace lo que crea. Las del navegador usan Playwright con Edge.

---

## 10. Solución de problemas

Además de la tabla de `INSTALL.md`:

| Síntoma | Causa probable | Solución |
|---|---|---|
| "Acceso no permitido" en una pantalla que el rol sí debería ver | Falta un `GRANT` para un objeto nuevo: PostgreSQL negó la consulta y la app lo traduce a 403 | Revise el script de `security/` de ese objeto |
| La devolución falla con "columna motivo no existe" | La base no tiene las migraciones `002_devolucion` | Sección 6.3 |
| La lista de exámenes da error 500 tras actualizar el código | Falta `sql/ddl/003_examen_estado.sql` | Sección 6.3 |
| Ninguna página abre después de iniciar sesión (error 500) tras actualizar el código | Faltan las tablas `permiso` y `rol_permiso` (`ddl/006`) o `fn_rol_bd` | Sección 6.3: aplicar las migraciones antes del despliegue |
| Un usuario no ve un botón que su rol debería tener | Al rol le falta el permiso | Usuarios y roles → tabla de permisos (U-14). Rige desde la siguiente página |
| El respaldo dice "La lista de tablas del respaldo no coincide con la base" | Se agregó una tabla y no se sumó a `TABLAS` en `respaldo.py` | Agréguela en orden de dependencias |
| La restauración se detiene con un error y no cambia nada | Esquema distinto del respaldo (por ejemplo, falta una migración) | Instale las migraciones que faltan y repita: la restauración es atómica |
| Un formulario responde 403 sin motivo aparente en producción | El navegador envía un `Origin` distinto del dominio (proxy mal configurado) | Verifique `APP_ENV=production`, para que `ProxyFix` tome el host real |
| La primera carga en Render tarda casi un minuto | La instancia gratuita se suspende tras 15 minutos sin uso | Abrir la página un minuto antes de usarla |

---

## 11. Limitaciones conocidas y trabajo futuro

- **Sin bloqueo por intentos fallidos de login.** Las contraseñas tienen hash y el mensaje de error es genérico, pero no hay límite de intentos. Con 2 procesos de gunicorn, un contador en memoria no sería confiable; lo correcto es una tabla de intentos en la base.
- **El respaldo es manual o por tarea programada.** No se envía automáticamente fuera del servidor.
- **Restauración solo por `psql`.** Es intencional (reemplaza todo), pero exige acceso al servidor.
- **Plan gratuito de Render y Neon:** arranque lento tras inactividad y sin garantía de disponibilidad. Para uso real del laboratorio conviene un plan pagado o un servidor propio en la red local.
- **La bitácora crece sin límite.** No se archiva ni se depura (es inmutable a propósito). Con el volumen actual no es un problema; si creciera mucho, convendría particionarla por año.
- **Los permisos son por acción, no por dato.** Un rol con *Registrar salidas* puede sacar de cualquier producto; no hay permisos por área o por categoría.
