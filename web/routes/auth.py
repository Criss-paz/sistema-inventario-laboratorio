"""
routes/auth.py — Login, logout y control básico de acceso.
RF-01 (iniciar sesión), RF-02 (cerrar sesión), RNF-03/04/05/06/17.

El control de acceso POR ROL (RF-05: qué puede hacer cada rol dentro de la
app) queda para la Entrega 3 — la propia rúbrica lo pondera aparte
("Control de acceso por rol en la app", 0.5 pts de Entrega 3). Aquí solo se
valida que exista sesión activa (login_required) para entrar a cualquier
módulo, y se guarda el rol en sesión para usarlo después.
"""
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

from db import query_one

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

    if row is None or not row["estado"]:
        flash(error_generico, "danger")
        return render_template("login.html"), 401

    if not check_password_hash(row["password_hash"], password_input):
        flash(error_generico, "danger")
        return render_template("login.html"), 401

    session.clear()
    session["id_usuario"] = row["id_usuario"]
    session["nombre_usuario"] = row["nombre"]
    session["nombre_rol"] = row["nombre_rol"]

    destino = request.args.get("next") or url_for("index")
    return redirect(destino)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))
