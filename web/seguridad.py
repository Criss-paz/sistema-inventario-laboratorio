"""
seguridad.py — Defensas contra falsificación y repetición de peticiones.

Responde a la observación del catedrático en la presentación del 27/10/2026:
que alguien podría conectarse e intentar "hacer o deshacer varios ingresos o
salidas". Se implementan tres barreras, ninguna de las cuales sustituye a las
de la base de datos (ningún rol tiene INSERT sobre `movimiento`; el historial
es inmutable), sino que las complementan en la capa web.

1. Token CSRF (`campo_csrf`). Impide que otro sitio provoque un POST con la
   sesión del usuario. La cookie ya es SameSite=Lax y `app.py` verifica el
   encabezado Origin, pero ese encabezado puede venir ausente: el token no
   depende del navegador.

2. Token de operación (`campo_operacion`). De un solo uso. Impide que el mismo
   registro se guarde dos veces, ya sea por recargar con F5, por doble clic o
   porque alguien reenvía una petición capturada. Es lo que responde
   literalmente a "hacer varios ingresos o salidas".

3. Límite de intentos de login (`intentos_recientes`). Cuenta los fallos de la
   bitácora, no una variable en memoria: así sigue valiendo aunque el servidor
   se reinicie o haya varios procesos de gunicorn, como en Render. El conteo
   es por usuario Y dirección de origen: si sólo mirara el usuario, cualquiera
   podría dejar fuera al administrador fallando cinco veces a propósito, que
   es cambiar una vulnerabilidad por otra.

Por qué no OAuth 2.0: es un protocolo de autorización delegada entre un
usuario, una aplicación de terceros y el servicio que guarda los datos. Este
sistema es una sola aplicación con sus propios usuarios y no delega nada en
nadie, así que OAuth no aporta defensa alguna contra el ataque descrito.
Tendría sentido si se expusiera una API a otros sistemas o si el login pasara
a la cuenta institucional; queda anotado como mejora futura en el informe.
"""
import secrets

from flask import session, request, abort
from markupsafe import Markup

from db import query_one

# Nombres de los campos ocultos que viajan en los formularios.
CAMPO_CSRF = "_csrf"
CAMPO_OPERACION = "_operacion"

# Cuántos tokens de operación se recuerdan a la vez. La sesión de Flask viaja
# en la cookie, así que la lista tiene que estar acotada: 24 cubre de sobra
# abrir varias pestañas, y al pasarse se descarta el más antiguo.
MAX_OPERACIONES_PENDIENTES = 24

# Umbral del bloqueo de login: 5 fallos del mismo usuario en 15 minutos.
MAX_INTENTOS = 5
VENTANA_MINUTOS = 15


# -----------------------------------------------------------------------------
# 1. CSRF
# -----------------------------------------------------------------------------
def token_csrf():
    """Token de la sesión actual; se crea la primera vez que se pide."""
    if CAMPO_CSRF not in session:
        session[CAMPO_CSRF] = secrets.token_urlsafe(32)
    return session[CAMPO_CSRF]


def campo_csrf():
    """Campo oculto para las plantillas: {{ campo_csrf() }}."""
    return Markup(f'<input type="hidden" name="{CAMPO_CSRF}" value="{token_csrf()}">')


def _csrf_valido():
    enviado = request.form.get(CAMPO_CSRF) or request.headers.get("X-CSRF-Token") or ""
    esperado = session.get(CAMPO_CSRF) or ""
    # compare_digest evita filtrar por tiempo cuántos caracteres coinciden.
    return bool(esperado) and secrets.compare_digest(enviado, esperado)


# -----------------------------------------------------------------------------
# 2. Token de operación (un solo uso)
# -----------------------------------------------------------------------------
def token_operacion():
    """Emite un token nuevo y lo deja pendiente de consumo."""
    pendientes = session.get("_ops", [])
    tok = secrets.token_urlsafe(16)
    pendientes.append(tok)
    # Acotar: la sesión viaja en la cookie.
    session["_ops"] = pendientes[-MAX_OPERACIONES_PENDIENTES:]
    return tok


def campo_operacion():
    """Campo oculto para los formularios que crean o deshacen movimientos."""
    return Markup(f'<input type="hidden" name="{CAMPO_OPERACION}" value="{token_operacion()}">')


def consumir_operacion():
    """Gasta el token del formulario. Devuelve False si ya se había usado.

    Que no esté en la lista significa una de dos cosas, y ambas deben
    rechazarse: o el formulario ya se envió (F5, doble clic, reenvío de una
    petición capturada), o el token nunca lo emitió este servidor.
    """
    tok = request.form.get(CAMPO_OPERACION) or ""
    pendientes = session.get("_ops", [])
    if not tok or tok not in pendientes:
        return False
    pendientes.remove(tok)
    session["_ops"] = pendientes
    return True


# -----------------------------------------------------------------------------
# 3. Límite de intentos de login
# -----------------------------------------------------------------------------
def origen_peticion():
    """IP del cliente. Detrás del proxy de Render, ProxyFix ya dejó la real."""
    return (request.remote_addr or "desconocida")[:45]


def intentos_recientes(usuario):
    """Fallos de login de ese usuario DESDE ESTA IP dentro de la ventana.

    Se lee de `bitacora`, que registra cada SESION_FALLIDA (RN-30), así que el
    conteo sobrevive a un reinicio y vale para los varios procesos de gunicorn
    de Render — una variable en memoria no haría ninguna de las dos cosas.

    El filtro por IP es deliberado: contar sólo por usuario permitiría que
    cualquiera bloqueara al administrador fallando cinco veces con su nombre.
    Un atacante que insista desde su propia dirección sí queda frenado.

    Un inicio de sesión correcto reinicia la cuenta: quien se equivocó cuatro
    veces y acertó a la quinta empieza de cero, y un bloqueo no se arrastra
    más allá de la siguiente entrada legítima.

    Los intentos hechos ya estando bloqueado quedan en la bitácora —interesa
    saber que alguien insistió— pero no se cuentan: si contaran, cada reintento
    reiniciaría la ventana y el bloqueo no caducaría nunca.

    Si la consulta fallara se devuelve 0: el bloqueo es una defensa añadida y
    no debe dejar fuera a nadie por un problema de la bitácora.
    """
    try:
        fila = query_one(
            """
            WITH ultimo_acierto AS (
                SELECT max(fecha_hora) AS cuando
                  FROM bitacora
                 WHERE accion = 'INICIAR_SESION'
                   AND entidad = 'sesion'
                   AND id_registro = %s
                   AND detalle ->> 'origen' = %s
            )
            SELECT count(*) AS n
              FROM bitacora, ultimo_acierto
             WHERE accion = 'SESION_FALLIDA'
               AND entidad = 'sesion'
               AND id_registro = %s
               AND detalle ->> 'origen' = %s
               AND fecha_hora > now() - make_interval(mins => %s)
               -- Los intentos que ya llegaron bloqueados no cuentan: si
               -- contaran, cada reintento reiniciaría la ventana y el bloqueo
               -- no caducaría jamás.
               AND coalesce((detalle ->> 'bloqueado')::boolean, false) = false
               -- Un acierto limpia la cuenta: sólo pesan los fallos
               -- posteriores a la última entrada correcta desde ese origen.
               AND fecha_hora > coalesce(ultimo_acierto.cuando, '-infinity'::timestamp)
            """,
            (usuario[:40], origen_peticion(), usuario[:40], origen_peticion(), VENTANA_MINUTOS),
        )
        return fila["n"] if fila else 0
    except Exception:
        return 0


def esta_bloqueado(usuario):
    return intentos_recientes(usuario) >= MAX_INTENTOS


# -----------------------------------------------------------------------------
# Registro en la aplicación
# -----------------------------------------------------------------------------
def registrar(app):
    """Activa la verificación CSRF global y publica los campos a las plantillas."""

    @app.before_request
    def _verificar_csrf():
        if request.method != "POST":
            return
        # El login no puede llevar token de sesión la primera vez (aún no hay
        # sesión), pero sí lo lleva: token_csrf() lo crea al pintar el
        # formulario y la cookie viaja con él.
        if not _csrf_valido():
            abort(403)

    @app.context_processor
    def _campos():
        return {"campo_csrf": campo_csrf, "campo_operacion": campo_operacion}
