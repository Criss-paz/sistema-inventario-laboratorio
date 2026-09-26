"""
routes/auth.py — Login, logout y control de acceso por rol.
RF-01 (iniciar sesión), RF-02 (cerrar sesión), RF-05 (acceso según rol),
RNF-03/04/05/06/17.

El acceso por rol se controla en dos capas:
  1. Aquí, en la app: rol_requerido() bloquea la ruta y las plantillas
     ocultan lo que el rol no puede hacer.
  2. En la base: db.get_db() adopta el rol de BD con SET ROLE, así que
     PostgreSQL niega la operación aunque la capa 1 fallara.

Qué puede hacer cada rol (igual que sql/security/001_roles.sql):
  Administrador            todo: catálogos, lotes, movimientos, reportes
  Encargado de inventario  consultar + registrar entradas y salidas
  Usuario de consulta      solo consultar
"""
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash

from db import query_one, ROL_BD

ADMIN = "Administrador"
ENCARGADO = "Encargado de inventario"
CONSULTA = "Usuario de consulta"

bp = Blueprint("auth", __name__)


def login_required(view):
    """Decorador: exige sesión activa antes de entrar a una ruta protegida."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "id_usuario" not in session:
            flash("Debe iniciar sesión para continuar.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def rol_requerido(*roles):
    """Decorador: exige sesión activa y que el rol del usuario esté en `roles`."""
    def decorador(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("nombre_rol") not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorador


def tiene_rol(*roles):
    """Para las plantillas: ¿el usuario en sesión tiene alguno de `roles`?"""
    return session.get("nombre_rol") in roles


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

    if row is None or not row["estado"] or row["nombre_rol"] not in ROL_BD:
        flash(error_generico, "danger")
        return render_template("login.html"), 401

    if not check_password_hash(row["password_hash"], password_input):
        flash(error_generico, "danger")
        return render_template("login.html"), 401

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
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))
