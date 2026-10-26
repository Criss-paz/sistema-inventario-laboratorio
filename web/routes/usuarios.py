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

Roles y permisos (RN-28, RN-29): el administrador crea roles y marca qué
puede hacer cada uno (tablas permiso y rol_permiso). El rol Administrador
tiene siempre todos los permisos y no se renombra ni se elimina; un rol con
usuarios no se elimina. Cada cambio queda en la bitácora (RN-30).
"""
import re

import psycopg

from flask import Blueprint, g, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash

from db import get_db, query_all, query_one, execute, execute_many, mensaje_error
from routes.auth import permiso_requerido, ADMIN

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

USUARIO = re.compile(r"[a-z0-9._-]{3,50}")
LARGO_MINIMO_CLAVE = 8



def _mi_rol():
    """id_rol del usuario en sesión, leído de la base en esta petición."""
    get_db()
    return g.acceso["id_rol"]


def _roles():
    return query_all("SELECT id_rol, nombre, descripcion FROM rol ORDER BY id_rol")


def _permisos():
    return query_all("SELECT codigo, nombre, descripcion FROM permiso ORDER BY orden")


def _concedidos():
    """{id_rol: {códigos}} de todos los roles."""
    concedidos = {}
    for f in query_all("SELECT id_rol, codigo FROM rol_permiso"):
        concedidos.setdefault(f["id_rol"], set()).add(f["codigo"])
    return concedidos


def _sentencias_permisos(id_rol, antes, despues):
    """INSERT/DELETE para pasar el rol de `antes` a `despues` (solo lo que cambia)."""
    return ([("DELETE FROM rol_permiso WHERE id_rol = %s AND codigo = %s", (id_rol, c)) for c in sorted(antes - despues)]
            + [("INSERT INTO rol_permiso (id_rol, codigo) VALUES (%s, %s)", (id_rol, c)) for c in sorted(despues - antes)])


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
@permiso_requerido("USUARIOS")
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
    return render_template("usuarios/list.html", usuarios=usuarios, roles=roles,
                           permisos=_permisos(), concedidos=_concedidos())


@bp.route("/roles/permisos", methods=["POST"])
@permiso_requerido("USUARIOS")
def guardar_permisos():
    """Guarda la tabla de permisos completa (casillas p_<id_rol>_<código>)."""
    codigos = {p["codigo"] for p in _permisos()}
    concedidos = _concedidos()
    sentencias = []
    for rol in _roles():
        if rol["nombre"] == ADMIN:
            continue  # siempre tiene todo (RN-29)
        marcados = {c for c in codigos if request.form.get(f"p_{rol['id_rol']}_{c}")}
        if rol["id_rol"] == _mi_rol() and "USUARIOS" not in marcados:
            flash(f'No puede quitarle "Usuarios y roles" a su propio rol ({rol["nombre"]}): '
                  "se quedaría sin acceso a esta pantalla.", "danger")
            return redirect(url_for("usuarios.listar"))
        sentencias += _sentencias_permisos(rol["id_rol"], concedidos.get(rol["id_rol"], set()), marcados)
    if not sentencias:
        flash("No cambió ningún permiso.", "info")
        return redirect(url_for("usuarios.listar"))
    try:
        execute_many(sentencias)
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudieron guardar los permisos. Intente más tarde."), "danger")
        return redirect(url_for("usuarios.listar"))
    flash(f"Permisos guardados ({len(sentencias)} {'cambio' if len(sentencias) == 1 else 'cambios'}). "
          "Rigen desde la próxima página que abra cada usuario.", "success")
    return redirect(url_for("usuarios.listar"))


def _validar_rol(form):
    datos = {"nombre": (form.get("nombre") or "").strip(), "descripcion": (form.get("descripcion") or "").strip()}
    errores = []
    if not 3 <= len(datos["nombre"]) <= 50:
        errores.append("El nombre del rol debe tener de 3 a 50 caracteres.")
    if len(datos["descripcion"]) > 255:
        errores.append("La descripción admite hasta 255 caracteres.")
    codigos = {p["codigo"] for p in _permisos()}
    marcados = {c for c in codigos if form.get(f"p_{c}")}
    return errores, datos, marcados


@bp.route("/roles/nuevo", methods=["GET", "POST"])
@permiso_requerido("USUARIOS")
def rol_nuevo():
    contexto = {"rol": None, "permisos": _permisos(), "marcados": set(), "usuarios_rol": 0}
    if request.method == "GET":
        return render_template("usuarios/rol_form.html", **contexto)

    errores, datos, marcados = _validar_rol(request.form)
    contexto.update(rol=request.form, marcados=marcados)
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("usuarios/rol_form.html", **contexto), 400
    try:
        execute_many(
            [("INSERT INTO rol (nombre, descripcion) VALUES (%s, %s)", (datos["nombre"], datos["descripcion"] or None))]
            + [("INSERT INTO rol_permiso (id_rol, codigo) SELECT id_rol, %s FROM rol WHERE nombre = %s",
                (c, datos["nombre"])) for c in sorted(marcados)]
        )
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe un rol llamado "{datos["nombre"]}".', "danger")
        return render_template("usuarios/rol_form.html", **contexto), 409
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo crear el rol. Intente más tarde."), "danger")
        return render_template("usuarios/rol_form.html", **contexto), 500
    flash(f'Rol "{datos["nombre"]}" creado con {len(marcados)} '
          f'{"permiso" if len(marcados) == 1 else "permisos"}. Ya puede asignarlo a un usuario.', "success")
    return redirect(url_for("usuarios.listar"))


@bp.route("/roles/<int:id_rol>/editar", methods=["GET", "POST"])
@permiso_requerido("USUARIOS")
def rol_editar(id_rol):
    rol = query_one("SELECT id_rol, nombre, descripcion FROM rol WHERE id_rol = %s", (id_rol,))
    if rol is None:
        flash("El rol solicitado no existe.", "warning")
        return redirect(url_for("usuarios.listar"))
    es_admin = rol["nombre"] == ADMIN
    antes = _concedidos().get(id_rol, set())
    usuarios_rol = query_one("SELECT count(*) AS n FROM usuario WHERE id_rol = %s", (id_rol,))["n"]
    contexto = {"rol": rol, "permisos": _permisos(), "marcados": antes, "es_admin": es_admin,
                "usuarios_rol": usuarios_rol}
    if request.method == "GET":
        return render_template("usuarios/rol_form.html", **contexto)

    errores, datos, marcados = _validar_rol(request.form)
    if es_admin:
        # RN-29: el Administrador conserva su nombre y todos sus permisos.
        datos["nombre"], marcados = ADMIN, antes
    elif id_rol == _mi_rol() and "USUARIOS" not in marcados:
        errores.append('No puede quitarle "Usuarios y roles" a su propio rol: se quedaría sin acceso a esta pantalla.')
    contexto.update(rol={**rol, **request.form}, marcados=marcados)
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("usuarios/rol_form.html", **contexto), 400
    sentencias = []
    if (datos["nombre"], datos["descripcion"] or None) != (rol["nombre"], rol["descripcion"]):
        sentencias.append(("UPDATE rol SET nombre = %s, descripcion = %s WHERE id_rol = %s",
                           (datos["nombre"], datos["descripcion"] or None, id_rol)))
    sentencias += _sentencias_permisos(id_rol, antes, marcados)
    if not sentencias:
        flash("No hubo cambios.", "info")
        return redirect(url_for("usuarios.listar"))
    try:
        execute_many(sentencias)
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe un rol llamado "{datos["nombre"]}".', "danger")
        return render_template("usuarios/rol_form.html", **contexto), 409
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo guardar el rol. Intente más tarde."), "danger")
        return render_template("usuarios/rol_form.html", **contexto), 500
    flash(f'Rol "{datos["nombre"]}" actualizado.', "success")
    return redirect(url_for("usuarios.listar"))


@bp.route("/roles/<int:id_rol>/eliminar", methods=["POST"])
@permiso_requerido("USUARIOS")
def rol_eliminar(id_rol):
    rol = query_one(
        "SELECT r.nombre, (SELECT count(*) FROM usuario u WHERE u.id_rol = r.id_rol) AS usuarios "
        "FROM rol r WHERE r.id_rol = %s",
        (id_rol,),
    )
    if rol is None:
        flash("El rol solicitado no existe.", "warning")
    elif rol["nombre"] == ADMIN:
        flash("El rol Administrador no se puede eliminar.", "danger")
    elif rol["usuarios"]:
        flash(f'El rol "{rol["nombre"]}" tiene {rol["usuarios"]} '
              f'{"usuario" if rol["usuarios"] == 1 else "usuarios"} (activos o no). '
              "Asígneles otro rol antes de eliminarlo.", "danger")
    else:
        try:
            execute("DELETE FROM rol WHERE id_rol = %s", (id_rol,))
            flash(f'Rol "{rol["nombre"]}" eliminado.', "success")
        except Exception as exc:
            flash(mensaje_error(exc, "No se pudo eliminar el rol. Intente más tarde."), "danger")
    return redirect(url_for("usuarios.listar"))


@bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("USUARIOS")
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
@permiso_requerido("USUARIOS")
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
@permiso_requerido("USUARIOS")
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
