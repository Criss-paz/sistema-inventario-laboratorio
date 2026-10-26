"""
routes/auth.py — Login, logout y control de acceso por rol.
RF-01 (iniciar sesión), RF-02 (cerrar sesión), RF-05 (acceso según rol),
RNF-03/04/05/06/17. Además, cada usuario puede cambiar su propia contraseña.

El acceso se controla en dos capas:
  1. Aquí, en la app: permiso_requerido() bloquea la ruta y las plantillas
     ocultan lo que el rol no tiene permitido (tiene_permiso).
  2. En la base: db.get_db() adopta con SET ROLE el rol de PostgreSQL que
     cubre los permisos del rol, así que PostgreSQL niega la operación
     aunque la capa 1 fallara.

Los permisos de cada rol son datos (tablas permiso y rol_permiso, RN-28)
que el Administrador define en Usuarios y roles. Consultar inventario,
lotes, historial y reportes lo pueden todos. El rol Administrador tiene
siempre todos los permisos (RN-29).

Los inicios de sesión (correctos y fallidos) y los cierres quedan en la
bitácora (RN-30).
"""
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash, generate_password_hash

from db import query_one, execute, conexion_sin_rol, permisos_actuales

# El único rol con nombre fijo: tiene siempre todos los permisos (RN-29).
ADMIN = "Administrador"

bp = Blueprint("auth", __name__)

LARGO_MINIMO_CLAVE = 8


def login_required(view):
    """Decorador: exige sesión activa antes de entrar a una ruta protegida."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "id_usuario" not in session:
            flash("Debe iniciar sesión para continuar.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def permiso_requerido(codigo):
    """Decorador: exige sesión activa y que el rol del usuario tenga `codigo`
    (tabla permiso: REGISTRAR_ENTRADAS, PRODUCTOS, USUARIOS, ...)."""
    def decorador(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if codigo not in permisos_actuales():
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorador


def tiene_permiso(*codigos):
    """Para las plantillas: ¿el rol del usuario tiene alguno de `codigos`?"""
    return bool(permisos_actuales() & set(codigos))


def _bitacora_sesion(accion, id_usuario, referencia):
    """Inicio de sesión correcto o fallido (RN-30). Se escribe con la
    conexión de usuario_app de esta petición: todavía no hay rol adoptado."""
    try:
        execute(
            "INSERT INTO bitacora (id_usuario, accion, entidad, referencia) VALUES (%s, %s, 'sesion', %s)",
            (id_usuario, accion, referencia[:150]),
        )
    except Exception:
        pass  # la bitácora no debe impedir entrar


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    usuario_input = (request.form.get("usuario") or "").strip()
    password_input = request.form.get("password") or ""

    # A3: validación de entrada antes de tocar la base de datos.
    if not usuario_input or not password_input:
        flash("Usuario y contraseña son obligatorios.", "danger")
        return render_template("login.html"), 400

    # Se descarta la sesión anterior ANTES de consultar: la verificación del
    # password la hace usuario_app, sin adoptar el rol de otro usuario.
    session.clear()
    try:
        row = query_one(
            """
            SELECT u.id_usuario, u.nombre, u.password_hash, u.estado, r.nombre AS nombre_rol
            FROM usuario u
            JOIN rol r ON r.id_rol = u.id_rol
            WHERE u.usuario = %s
            """,
            (usuario_input,),
        )
    except Exception:
        # A2: nunca se muestra el error SQL crudo al usuario.
        flash("No se pudo conectar con la base de datos. Intente más tarde.", "danger")
        return render_template("login.html"), 500

    # Mensaje genérico a propósito: no se revela si el usuario existe o no
    # (RNF-17: evitar accesos no autorizados / fuga de información de login).
    error_generico = "Usuario o contraseña incorrectos."

    if row is None or not row["estado"] or not check_password_hash(row["password_hash"], password_input):
        _bitacora_sesion("SESION_FALLIDA", row["id_usuario"] if row else None,
                         f'Intento con el usuario "{usuario_input[:60]}"')
        flash(error_generico, "danger")
        return render_template("login.html"), 401

    _bitacora_sesion("INICIAR_SESION", row["id_usuario"], usuario_input)

    session["id_usuario"] = row["id_usuario"]
    session["nombre_usuario"] = row["nombre"]
    session["nombre_rol"] = row["nombre_rol"]

    # Solo rutas internas: evita que ?next=https://otro-sitio redirija fuera.
    destino = request.args.get("next") or ""
    if not destino.startswith("/") or destino.startswith("//"):
        destino = url_for("index")
    return redirect(destino)


@bp.route("/logout", methods=["POST"])
def logout():
    if "id_usuario" in session:
        try:
            execute("SELECT fn_registrar_evento('CERRAR_SESION')")
        except Exception:
            pass  # la bitácora no debe impedir salir
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/mi-cuenta/contrasena", methods=["GET", "POST"])
@login_required
def cambiar_contrasena():
    """Cualquier usuario cambia SU contraseña confirmando la actual (RN-15).

    Los roles de encargado y de consulta no tienen acceso a la tabla usuario,
    y ninguno puede leer password_hash; por eso la verificación y el UPDATE
    usan db.conexion_sin_rol(), igual que el login, y siempre sobre el
    id_usuario de la sesión (firmada por la app), nunca uno recibido del
    formulario.
    """
    if request.method == "GET":
        return render_template("cambiar_contrasena.html")

    actual = request.form.get("actual") or ""
    nueva = request.form.get("nueva") or ""
    confirmacion = request.form.get("confirmacion") or ""

    # A3: validación antes de tocar la base de datos.
    errores = []
    if not actual:
        errores.append("Escriba su contraseña actual.")
    if len(nueva) < LARGO_MINIMO_CLAVE:
        errores.append(f"La nueva contraseña debe tener al menos {LARGO_MINIMO_CLAVE} caracteres.")
    elif nueva != confirmacion:
        errores.append("La confirmación no coincide con la nueva contraseña.")
    elif nueva == actual:
        errores.append("La nueva contraseña debe ser distinta de la actual.")
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("cambiar_contrasena.html"), 400

    try:
        with conexion_sin_rol() as conn:
            conn.execute("SELECT set_config('app.id_usuario', %s, false)", (str(session["id_usuario"]),))
            fila = conn.execute(
                "SELECT password_hash FROM usuario WHERE id_usuario = %s AND estado",
                (session["id_usuario"],),
            ).fetchone()
            if fila is None or not check_password_hash(fila["password_hash"], actual):
                flash("La contraseña actual no es correcta.", "danger")
                return render_template("cambiar_contrasena.html"), 400
            conn.execute(
                "UPDATE usuario SET password_hash = %s WHERE id_usuario = %s",
                (generate_password_hash(nueva), session["id_usuario"]),
            )
    except Exception:
        # A2: nunca se muestra el error SQL crudo al usuario.
        flash("No se pudo cambiar la contraseña. Intente más tarde.", "danger")
        return render_template("cambiar_contrasena.html"), 500

    flash("Contraseña cambiada. Úsela la próxima vez que inicie sesión.", "success")
    return redirect(url_for("index"))
