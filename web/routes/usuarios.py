"""
routes/usuarios.py — Usuarios y roles.
RF-03 (administrar usuarios), RF-04 (asignar roles), RF-05 (acceso por rol),
RN-15 (contraseñas siempre con hash), RNF-04/05.

Solo el Administrador entra aquí. Su rol de base de datos puede crear y
editar usuarios, pero no puede LEER password_hash (GRANT por columna,
sql/security/001_roles.sql): por eso ninguna consulta de este módulo pide
esa columna, y la contraseña solo se escribe ya convertida en hash con
werkzeug.security, la misma librería que la valida en el login.

"Eliminar" es baja lógica (estado): el usuario conserva su historial de
movimientos (RN-08, RN-09).
"""
import re

import psycopg

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash

from db import query_all, query_one, execute, mensaje_error
from routes.auth import rol_requerido, ADMIN

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

USUARIO = re.compile(r"[a-z0-9._-]{3,50}")
LARGO_MINIMO_CLAVE = 8

# Lo que cada rol puede hacer, para mostrarlo junto a la lista. Es el mismo
# reparto que aplican rol_requerido() en la app y los GRANT en la base.
PERMISOS = [
    ("Consultar inventario, lotes, historial y reportes", True, True, True),
    ("Registrar entradas y salidas", True, True, False),
    ("Crear y editar productos, categorías, proveedores y exámenes", True, False, False),
    ("Corregir datos de un lote (nunca su existencia)", True, False, False),
    ("Administrar usuarios y roles", True, False, False),
]


def _roles():
    return query_all("SELECT id_rol, nombre, descripcion FROM rol ORDER BY id_rol")


def _es_ultimo_admin_activo(id_usuario):
    """True si este usuario es el único administrador activo."""
    fila = query_one(
        """
        SELECT count(*) FILTER (WHERE u.id_usuario <> %s) AS otros
        FROM usuario u JOIN rol r ON r.id_rol = u.id_rol
        WHERE r.nombre = %s AND u.estado
        """,
        (id_usuario, ADMIN),
    )
    return fila["otros"] == 0


def _validar(form, nuevo):
    """A3: campos requeridos, formato del usuario y de la contraseña."""
    datos = {
        "nombre": (form.get("nombre") or "").strip(),
        "usuario": (form.get("usuario") or "").strip().lower(),
        "id_rol": (form.get("id_rol") or "").strip(),
    }
    clave = form.get("password") or ""
    confirmacion = form.get("password2") or ""
    errores = []
    if not datos["nombre"]:
        errores.append("El nombre es obligatorio.")
    if not USUARIO.fullmatch(datos["usuario"]):
        errores.append("El usuario debe tener de 3 a 50 caracteres: letras minúsculas, números, punto, guion o guion bajo.")
    if not datos["id_rol"].isdigit():
        errores.append("Seleccione un rol.")
    if nuevo or clave:
        if len(clave) < LARGO_MINIMO_CLAVE:
            errores.append(f"La contraseña debe tener al menos {LARGO_MINIMO_CLAVE} caracteres.")
        elif clave != confirmacion:
            errores.append("Las dos contraseñas no coinciden.")
    return errores, datos, clave


@bp.route("/")
@rol_requerido(ADMIN)
def listar():
    # Columnas explícitas: el rol de BD no puede leer password_hash.
    usuarios = query_all(
        """
        SELECT u.id_usuario, u.nombre, u.usuario, u.estado, u.fecha_creacion, r.nombre AS rol,
               (SELECT count(DISTINCT h.id_movimiento) FROM vw_historial_movimientos h
                 WHERE h.usuario = u.usuario) AS movimientos
        FROM usuario u
        JOIN rol r ON r.id_rol = u.id_rol
        ORDER BY u.estado DESC, r.id_rol, u.nombre
        """
    )
    roles = query_all(
        """
        SELECT r.id_rol, r.nombre, r.descripcion,
               count(u.id_usuario) FILTER (WHERE u.estado) AS activos
        FROM rol r LEFT JOIN usuario u ON u.id_rol = r.id_rol
        GROUP BY r.id_rol
        ORDER BY r.id_rol
        """
    )
    return render_template("usuarios/list.html", usuarios=usuarios, roles=roles, permisos=PERMISOS)


@bp.route("/nuevo", methods=["GET", "POST"])
@rol_requerido(ADMIN)
def nuevo():
    if request.method == "GET":
        return render_template("usuarios/form.html", usuario=None, roles=_roles())

    errores, datos, clave = _validar(request.form, nuevo=True)
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("usuarios/form.html", usuario=request.form, roles=_roles()), 400

    try:
        execute(
            "INSERT INTO usuario (id_rol, nombre, usuario, password_hash) VALUES (%s, %s, %s, %s)",
            (int(datos["id_rol"]), datos["nombre"], datos["usuario"], generate_password_hash(clave)),
        )
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe el usuario "{datos["usuario"]}".', "danger")
        return render_template("usuarios/form.html", usuario=request.form, roles=_roles()), 409
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo crear el usuario. Intente más tarde."), "danger")
        return render_template("usuarios/form.html", usuario=request.form, roles=_roles()), 500

    flash(f'Usuario "{datos["usuario"]}" creado. Ya puede iniciar sesión.', "success")
    return redirect(url_for("usuarios.listar"))


@bp.route("/<int:id_usuario>/editar", methods=["GET", "POST"])
@rol_requerido(ADMIN)
def editar(id_usuario):
    usuario = query_one(
        "SELECT id_usuario, id_rol, nombre, usuario, estado FROM usuario WHERE id_usuario = %s",
        (id_usuario,),
    )
    if usuario is None:
        flash("El usuario solicitado no existe.", "warning")
        return redirect(url_for("usuarios.listar"))
    es_propio = id_usuario == session.get("id_usuario")

    if request.method == "GET":
        return render_template("usuarios/form.html", usuario=usuario, roles=_roles(), es_propio=es_propio)

    errores, datos, clave = _validar(request.form, nuevo=False)
    # El administrador no puede cambiarse su propio rol: se quedaría sin
    # acceso a este módulo a mitad de la sesión.
    cambia_rol = datos["id_rol"] != str(usuario["id_rol"])
    if es_propio and cambia_rol:
        errores.append("No puede cambiar su propio rol. Pídaselo a otro administrador.")
    elif cambia_rol and usuario["estado"]:
        rol_actual = query_one("SELECT nombre FROM rol WHERE id_rol = %s", (usuario["id_rol"],))
        if rol_actual["nombre"] == ADMIN and _es_ultimo_admin_activo(id_usuario):
            errores.append("Es el único administrador activo: asigne otro administrador antes de cambiarle el rol.")
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("usuarios/form.html", usuario={**usuario, **request.form}, roles=_roles(),
                               es_propio=es_propio), 400

    try:
        if clave:
            execute(
                "UPDATE usuario SET nombre = %s, usuario = %s, id_rol = %s, password_hash = %s WHERE id_usuario = %s",
                (datos["nombre"], datos["usuario"], int(datos["id_rol"]), generate_password_hash(clave), id_usuario),
            )
        else:
            execute(
                "UPDATE usuario SET nombre = %s, usuario = %s, id_rol = %s WHERE id_usuario = %s",
                (datos["nombre"], datos["usuario"], int(datos["id_rol"]), id_usuario),
            )
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe el usuario "{datos["usuario"]}".', "danger")
        return render_template("usuarios/form.html", usuario={**usuario, **request.form}, roles=_roles(),
                               es_propio=es_propio), 409
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo actualizar el usuario. Intente más tarde."), "danger")
        return render_template("usuarios/form.html", usuario={**usuario, **request.form}, roles=_roles(),
                               es_propio=es_propio), 500

    if es_propio:
        session["nombre_usuario"] = datos["nombre"]
    flash("Usuario actualizado." + (" La nueva contraseña ya está activa." if clave else ""), "success")
    return redirect(url_for("usuarios.listar"))


@bp.route("/<int:id_usuario>/alternar-estado", methods=["POST"])
@rol_requerido(ADMIN)
def alternar_estado(id_usuario):
    usuario = query_one(
        """
        SELECT u.usuario, u.estado, r.nombre AS rol
        FROM usuario u JOIN rol r ON r.id_rol = u.id_rol
        WHERE u.id_usuario = %s
        """,
        (id_usuario,),
    )
    if usuario is None:
        flash("El usuario solicitado no existe.", "warning")
        return redirect(url_for("usuarios.listar"))

    if usuario["estado"]:
        if id_usuario == session.get("id_usuario"):
            flash("No puede desactivar su propio usuario.", "danger")
            return redirect(url_for("usuarios.listar"))
        if usuario["rol"] == ADMIN and _es_ultimo_admin_activo(id_usuario):
            flash("No puede desactivar al único administrador activo: nadie podría administrar el sistema.", "danger")
            return redirect(url_for("usuarios.listar"))

    try:
        execute("UPDATE usuario SET estado = %s WHERE id_usuario = %s", (not usuario["estado"], id_usuario))
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo cambiar el estado del usuario. Intente más tarde."), "danger")
        return redirect(url_for("usuarios.listar"))

    if usuario["estado"]:
        flash(f'Usuario "{usuario["usuario"]}" desactivado: ya no puede iniciar sesión. Su historial se conserva.', "success")
    else:
        flash(f'Usuario "{usuario["usuario"]}" activado.', "success")
    return redirect(url_for("usuarios.listar"))
