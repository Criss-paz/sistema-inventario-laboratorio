# Defensas contra peticiones falsificadas o repetidas

**Añadido el 27/10/2026**, a raíz de la observación del catedrático durante la presentación: que alguien podría conectarse al sistema e intentar **hacer o deshacer varios ingresos o salidas**, y que convendría implementar *tokens*, mencionando OAuth 2.0.

Este documento explica qué se implementó, por qué, y por qué **OAuth 2.0 no era la respuesta** a esa observación concreta.

---

## 1. Por qué OAuth 2.0 no aplica a este sistema

OAuth 2.0 es un protocolo de **autorización delegada**. Resuelve un problema con tres participantes:

> ¿Cómo autorizo a la aplicación X para que lea mis datos del servicio Y, sin entregarle mi contraseña de Y?

Es lo que ocurre al entrar a un sitio con «Iniciar sesión con Google»: Google emite un token de alcance y duración limitados, y el sitio nunca ve la contraseña.

**Este sistema no tiene esa forma.** Es una sola aplicación Flask, con su propia tabla `usuario` y su propia base de datos. No hay terceros ni nada que delegar. Implementar OAuth 2.0 aquí significaría levantar un servidor de autorización que emite tokens para la misma aplicación que los valida: más complejidad, más superficie de ataque y **ninguna defensa adicional** contra el ataque descrito.

**Dónde sí tendría sentido**, y queda anotado como mejora futura:

- Si se expusiera una **API** para otro sistema del laboratorio o una aplicación móvil.
- Si el inicio de sesión pasara a la **cuenta institucional** de la universidad mediante OAuth 2.0 / OpenID Connect. El sistema dejaría de almacenar contraseñas, que es una ganancia real de seguridad — pero tampoco resuelve el problema de la repetición.

---

## 2. Qué protegía el sistema antes de este cambio

Conviene decirlo, porque el punto de partida no era débil:

| Ataque | Ya estaba cubierto por |
|---|---|
| Robar la cookie de sesión con JavaScript | `HttpOnly`, `Secure` en producción y una política de contenido (CSP) |
| Insertar movimientos saltándose la aplicación | Ningún rol tiene `INSERT` sobre `movimiento`; la única vía son los procedimientos |
| Modificar o borrar el historial | El trigger `fn_historial_inmutable` |
| Dejar existencia negativa | El trigger de existencia por lote |
| Usar la sesión de un usuario ya desactivado | Se revalida en cada petición |

La capa de base de datos es la defensa más fuerte y no la toca ninguno de los cambios siguientes: **aunque alguien falsificara una petición HTTP perfecta, seguiría sin poder insertar un movimiento directamente.**

---

## 3. El hueco real que sí existía

**No había protección contra la repetición.** Si alguien capturaba una petición válida de «registrar salida» y la reenviaba —o si el usuario simplemente recargaba con **F5** después de guardar— el sistema registraba el movimiento **otra vez**. Nada decía «esta operación ya se hizo».

Eso es, literalmente, *hacer varios ingresos o salidas*. Era el hallazgo que justificaba el cambio.

Había dos huecos menores más:

- La verificación del encabezado `Origin` **pasaba cuando el encabezado no venía**. La cookie `SameSite=Lax` cubría el caso en la práctica, pero dependía del navegador.
- **No había límite de intentos de inicio de sesión**: se podían probar contraseñas sin freno.

---

## 4. Lo implementado

Todo vive en [`web/seguridad.py`](../../web/seguridad.py), que se registra desde `app.py`.

### 4.1 Token CSRF en los 27 formularios

Cada sesión recibe un token aleatorio. Toda petición `POST` debe traerlo, o el servidor responde **403** antes de ejecutar nada.

- Se compara con `secrets.compare_digest`, que no filtra por tiempo cuántos caracteres coinciden.
- Se inyecta en las plantillas con `{{ campo_csrf() }}`.
- Cubre también el inicio de sesión, lo que impide el *login CSRF* (forzar a alguien a entrar con una cuenta ajena).

A diferencia de la verificación de `Origin`, **no depende de que el navegador envíe nada**.

### 4.2 Token de un solo uso en cada movimiento

Las cinco operaciones que mueven inventario —entrada, salida, devolución, corrección y eliminación— emiten un token **al pintar el formulario** y lo **gastan al guardarlo**.

Si llega un segundo envío con el mismo token, el sistema no registra nada y avisa: *«Esta operación ya se registró.»*

Esto bloquea las tres variantes del mismo problema:

1. Recargar con **F5** después de guardar.
2. Doble clic en el botón.
3. Reenviar una petición capturada.

La lista de tokens pendientes está acotada a 24 porque la sesión de Flask viaja en la cookie.

### 4.3 Bloqueo tras cinco intentos fallidos

Cinco fallos en quince minutos bloquean el acceso con un **429**. Tres decisiones de diseño que vale la pena defender:

**Se cuenta desde la bitácora, no desde una variable en memoria.** Así el conteo sobrevive a un reinicio del servidor y vale para los varios procesos de gunicorn que corren en Render. Una variable en memoria no haría ninguna de las dos cosas.

**Se cuenta por usuario Y dirección de origen.** Contar sólo por usuario tendría un efecto perverso: cualquiera podría dejar fuera al administrador fallando cinco veces a propósito con su nombre. Sería cambiar una vulnerabilidad por otra. Con el filtro por origen, quien insiste desde su propia dirección se frena solo.

**Un inicio de sesión correcto reinicia la cuenta.** Quien se equivocó cuatro veces y acertó a la quinta empieza de cero.

---

## 5. Pruebas ejecutadas

| Prueba | Resultado |
|---|---|
| `POST` de login sin token CSRF | **403**, rechazado |
| `POST` de login con token válido | Aceptado |
| Primer envío del formulario de salida | Registra el movimiento |
| Segundo envío con el **mismo** token | **No registra nada**; el total de salidas no cambia |
| Cinco fallos de contraseña | El sexto intento responde **429** |
| Contraseña correcta estando bloqueado | **429**: el bloqueo no se salta acertando |
| Otro usuario con su contraseña correcta | **200**: el bloqueo no lo afecta |
| Cuatro fallos, un acierto, cuatro fallos más | Sigue permitiendo: el acierto reinició el contador |

Detalle en `docs/casos-prueba/casos-prueba-entrega-4.md`, casos **CP4-21** a **CP4-24**.

---

## 6. Limitación conocida

**Un usuario bloqueado no se puede desbloquear desde la aplicación.** El conteo se lee de la bitácora, que es inmutable por diseño (RN-30), así que no hay forma de borrar los intentos fallidos. Las únicas salidas son **esperar los quince minutos** o entrar correctamente desde otra dirección.

Se asume a propósito: una pantalla para desbloquear usuarios sería, ella misma, un objetivo de ataque. Quince minutos es una espera tolerable y el bloqueo se cura solo.

---

**Verificado el 27/10/2026** sobre la instalación local reconstruida desde `INSTALL.md`, con los tres roles.
