# Guía de defensa oral

Preparación para la defensa grupal (base de datos y aplicación web) y la individual. La consigna centra la calificación en que cada integrante **domine y justifique** las decisiones de diseño. Esta guía resume qué mostrar, en qué orden, y las preguntas más probables con su respuesta, que cada integrante debe poder dar con sus propias palabras.

---

## 1. Antes de la defensa

- [ ] Abrir https://inventario-laboratorio-03s7.onrender.com **un minuto antes**: el plan gratuito tarda unos 50 segundos en despertar.
- [ ] Tener a mano las credenciales de producción de los 3 roles (canal privado, no el repositorio).
- [ ] Tener `psql` conectado a la base local o a Neon, para mostrar triggers y roles en vivo.
- [ ] Abrir en pestañas: el diagrama ER, el diagrama relacional, `sql/triggers/001_triggers.sql`, `sql/procedures/001_procedures.sql` y `sql/security/001_roles.sql`.
- [ ] Repasar la sección 4 de esta guía: las preguntas individuales pueden ser sobre cualquier parte, no solo la que cada uno construyó.

---

## 2. Guion de la demostración grupal (unos 12 minutos)

| Min. | Qué se muestra | Qué se dice | Quién |
|---|---|---|---|
| 0–1 | Inicio como administrador | El problema: bodega en papel; ahora existencias, vencimientos y valor del inventario en un vistazo, con los datos reales | Cristopher |
| 1–3 | Diagrama ER y relacional | 9 entidades; el **lote** como unidad de existencia; 3 relaciones N:M resueltas; 3FN | José |
| 3–5 | Como encargado: registrar una entrada y luego una salida mayor a lo que hay en un solo lote | La salida se reparte por **FEFO**, lo hace el procedimiento `sp_registrar_salida`, no la aplicación | Cristopher |
| 5–6 | Intentar sacar más de lo que hay | El rechazo viene de la base de datos (trigger y procedimiento); la aplicación solo muestra el mensaje | Cristopher |
| 6–7 | Devolver la salida y abrir la ficha del lote | El historial no se edita (RN-09): la corrección es un movimiento inverso enlazado y con motivo | José |
| 7–8 | Kardex del producto | Costo promedio ponderado: la compra cambia el promedio y la salida y la devolución no | José |
| 8–10 | Como usuario de consulta: menú reducido; escribir `/usuarios/` a mano. Luego en `psql`: `SET ROLE rol_consulta; UPDATE producto …` | Control de acceso en **dos capas**: la app (403) y PostgreSQL (permiso denegado) | Cristopher |
| 10–11 | En `psql`: `UPDATE movimiento SET observacion='x' WHERE id_movimiento = 1;` | El trigger de inmutabilidad lo impide, incluso para el dueño de las tablas | José |
| 11–12 | Administración → Respaldo | RNF-11: respaldo completo, restaurable con `psql`, probado con una restauración real | José |

Comandos para `psql` (local: `psql -U usuario_app -d inventario_laboratorio`):

```sql
-- Capa de base de datos: el rol de consulta no puede escribir
SET ROLE rol_consulta;
UPDATE producto SET stock_minimo = 1 WHERE id_producto = 1;   -- permiso denegado
RESET ROLE;

-- Ni el administrador lee contraseñas ni cambia existencias a mano
SET ROLE rol_administrador;
SELECT password_hash FROM usuario;                            -- permiso denegado
UPDATE lote SET cantidad_disponible = 999 WHERE id_lote = 1;  -- permiso denegado
RESET ROLE;

-- El historial es inmutable
UPDATE movimiento SET observacion = 'x' WHERE id_movimiento = 1;  -- rechazado por el trigger

-- Coherencia de existencias contra el historial: debe dar 0
SELECT count(*) FROM lote l
WHERE l.cantidad_disponible <> coalesce((
  SELECT sum(CASE WHEN m.tipo_movimiento = 'SALIDA' THEN -d.cantidad ELSE d.cantidad END)
  FROM detalle_movimiento d JOIN movimiento m USING (id_movimiento)
  WHERE d.id_lote = l.id_lote), 0);
```

---

## 3. Cifras para tener presentes

| Dato | Valor |
|---|---|
| Tablas / entidades principales / relaciones N:M | 11 / 9 / 3 |
| Triggers / procedimientos / funciones / vistas / roles | 5 / 3 / 7 / 6 / 3 |
| Productos / lotes / movimientos (datos reales) | 806 / 1,188 / 5,839 |
| Valor del inventario con los datos iniciales | Q524,714.36 |
| Requerimientos | 39 RF, 18 RNF y 24 RN, todos implementados |
| Casos de prueba ejecutados (entregas 2 a 4) | 46, todos aprobados |

---

## 4. Preguntas probables y respuestas

### Modelo y normalización

**¿Por qué la existencia se guarda en `lote` y no en `producto`?**
Porque el vencimiento, el proveedor y el número de lote son de cada lote, no del producto. Con la existencia por lote se puede aplicar FEFO, saber qué hay vencido y rastrear de qué compra viene cada unidad. La existencia por producto es una suma, así que se calcula en `vw_existencia_producto` y no se guarda: guardarla sería redundancia (estándar S7) y podría desincronizarse.

**¿`cantidad_disponible` no es un dato calculado que viola la 3FN?**
Es la única cifra derivada que se almacena, y por una razón de rendimiento y de control: validar "no sacar más de lo que hay" en el mismo instante, con un bloqueo `FOR UPDATE` sobre la fila del lote. Solo la modifica el trigger, ningún rol puede escribirla, y se puede verificar contra el historial en cualquier momento (la consulta de la sección 2 debe dar 0).

**¿Qué relaciones N:M hay y cómo se resolvieron?**
Proveedor–producto (`proveedor_producto`, con el precio de compra), examen–producto (`examen_producto`, con la cantidad que consume cada examen) y movimiento–lote (`detalle_movimiento`): una salida FEFO puede tocar varios lotes, y un lote recibe muchos movimientos. Cada tabla puente tiene PK compuesta y su atributo propio.

**Dé un ejemplo de la normalización a 3FN.**
`docs/entrega-2/normalizacion-3fn.md` usa el registro de un movimiento, que es la parte más compleja del modelo.
- **1FN:** la hoja de cálculo guardaba todos los lotes de un movimiento en una sola celda. Se separa en una fila por cada par (movimiento, lote), con la cantidad en su propia columna.
- **2FN:** con la clave (id_movimiento, id_lote), la fecha, el tipo y el usuario dependían solo de id_movimiento, y el número de lote y el producto solo de id_lote. Eran dependencias parciales. Salen `MOVIMIENTO` y `LOTE`, y en `DETALLE_MOVIMIENTO` quedan solo cantidad y precio, que sí necesitan la clave completa.
- **3FN:** quedaban dependencias transitivas: `id_movimiento → id_usuario → nombre_usuario`, `id_lote → id_producto → nombre_producto` e `id_producto → id_categoria → nombre_categoria`. Esos datos pasan a `usuario`, `producto` y `categoria`, y en su lugar se guarda solo la FK.

**¿Por qué `ON DELETE RESTRICT` en unas FK y `CASCADE` en otras?**
`RESTRICT` donde hay historial que proteger: no se puede borrar un producto con lotes ni un lote con movimientos. `CASCADE` solo en las tablas puente: si desaparece un examen, sus insumos asignados ya no tienen sentido. En la práctica nada con historial se borra, porque se usa baja lógica.

### Reglas de negocio en la base

**¿Por qué poner reglas en triggers y procedimientos y no solo en Python?**
Porque así se cumplen aunque alguien use la base sin la aplicación, o aunque la aplicación tenga un error. La aplicación valida antes solo para dar mejores mensajes.

**¿Qué hace `sp_registrar_salida`?**
Recorre los lotes no vencidos del producto, ordenados por fecha de vencimiento (FEFO), y descuenta de cada uno hasta completar la cantidad. Todo ocurre en una transacción: si no alcanza, falla completa y no queda nada a medias. Es `SECURITY DEFINER`, así que el encargado puede registrar salidas sin tener `INSERT` sobre las tablas de movimientos.

**¿Por qué `SECURITY DEFINER` y qué riesgo tiene?**
El procedimiento corre con los permisos de su dueño. Así el rol del usuario no necesita permisos directos sobre las tablas y solo puede escribir **a través** del procedimiento, que valida todo. El riesgo es que alguien manipule el `search_path` para que el procedimiento llame a un objeto falso; por eso se fija con `SET search_path = public, pg_temp`.

**¿Cómo se corrige un movimiento mal registrado si el historial es inmutable?**
Con un movimiento inverso: la **devolución**. Queda enlazada a la salida que corrige (`id_movimiento_origen`) y con un motivo obligatorio, garantizado por un CHECK. Un trigger impide devolver más de lo que salió.

**¿Por qué el trigger del tope de devolución se llama `trg_z_…`?**
PostgreSQL dispara los triggers `BEFORE` de una misma tabla en orden alfabético, y este debe correr después del trigger de existencia.

**¿Cómo se valoriza el inventario?**
Por costo promedio ponderado móvil, calculado en `fn_kardex_promedio`. Cada compra recalcula el promedio como (valor del saldo + valor de la compra) ÷ (cantidad del saldo + cantidad comprada). Las salidas se valoran al promedio vigente y las devoluciones reingresan al mismo promedio, así que ninguna de las dos lo altera.

### Seguridad

**¿Cuáles son los 3 roles y en qué se diferencian?**
`rol_consulta` solo lee. `rol_encargado` hereda de consulta y además ejecuta los procedimientos de entrada, salida y devolución. `rol_administrador` hereda de encargado y además edita catálogos y usuarios. Ninguno puede leer `password_hash`, editar `cantidad_disponible` ni modificar movimientos.

**Si la aplicación se conecta con un solo usuario, ¿cómo aplica PostgreSQL los roles?**
Tras el login, cada petición ejecuta `SET ROLE` con el rol de base de datos del usuario. Desde ahí, PostgreSQL niega lo que ese rol no puede hacer, aunque la aplicación tuviera un error. Por eso el pooler de Neon está desactivado: un pooler en modo transacción podría reutilizar una sesión con el rol de otro usuario.

**¿Cómo se guardan las contraseñas?**
Con hash scrypt (`werkzeug.security`), nunca en texto. El mensaje de error del login es el mismo si el usuario no existe o si la contraseña está mal, para no revelar qué usuarios existen.

**¿Cómo se evita la inyección SQL?**
Todas las consultas pasan los datos del usuario como parámetros (`%s`) a psycopg. Los fragmentos que se arman en el código son texto fijo, y los identificadores dinámicos del respaldo se componen con `psycopg.sql.Identifier`.

**Si ningún rol lee `password_hash`, ¿cómo funciona el login?**
El login consulta con el usuario de conexión **antes** de adoptar un rol: es la excepción documentada `db.conexion_sin_rol()`. Solo la usan el login, el cambio de contraseña propio (siempre sobre el usuario de la sesión) y el respaldo (solo el administrador, en modo de solo lectura).

### Aplicación y operación

**¿Por qué algunas tablas no tienen "eliminar"?**
Los catálogos usan baja lógica, para que el historial siempre muestre a qué producto, proveedor o usuario se refiere. Los movimientos no se editan ni se borran por regla de negocio. La tabla completa de CRUD está en `ENTREGA4_MATRIZ_TRAZABILIDAD.md`.

**¿Cómo se respalda y se restaura?**
Administración → Respaldo descarga un `.sql` con los datos de las 11 tablas, leídos en una sola foto consistente (`REPEATABLE READ`). Se restaura con `psql` sobre el esquema instalado, en una sola transacción y con los triggers apagados solo durante la carga. Se probó restaurándolo: las 11 tablas quedaron idénticas a la original.

**¿Cómo se instala desde cero?**
Siguiendo `INSTALL.md`: crear la base, ejecutar los scripts en orden (estructura, triggers antes de los datos, seguridad al final), configurar `.env` y ejecutar la aplicación. Los scripts tardan unos 12 segundos.

**¿Cómo usaron la IA y cómo garantizan que entienden el resultado?**
Claude Code generó borradores de SQL, código y documentos. Cada resultado se probó contra la base real antes del commit, y la bitácora registra qué se corrigió o rechazó. Las pruebas encontraron errores que la IA no había visto: en el generador de la carga, en el kardex de devoluciones y en las plantillas. Cada decisión de esta guía la podemos explicar sin la herramienta.

**¿Qué mejorarían?**
Bloqueo de cuenta por intentos fallidos de login, auditoría de cambios en catálogos, envío automático del respaldo fuera del servidor y un servidor pagado o en la red del laboratorio (manual técnico, sección 11).
