"""
routes/proveedores.py — CRUD 3: Proveedores.
RF-11 (registrar), RF-12 (modificar), RF-13 (consultar), RN-16 (un
proveedor suministra varios productos: se muestran sus precios).

Consultar: todos los roles. Registrar/modificar/dar de baja: Administrador.
"Eliminar" es baja lógica vía `estado`, igual que Categorías y Productos
(lote.id_proveedor tiene ON DELETE RESTRICT).
"""
import re

import psycopg

from flask import Blueprint, render_template, request, redirect, url_for, flash

from db import query_all, query_one, query_page, execute, mensaje_error
from routes.auth import login_required, rol_requerido, ADMIN

bp = Blueprint("proveedores", __name__, url_prefix="/proveedores")

CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validar_formulario(form):
    """A3: validación de campos requeridos y formatos antes de la BD."""
    datos = {k: (form.get(k) or "").strip() for k in ("nombre", "nit", "telefono", "correo", "direccion")}
    errores = []
    if not datos["nombre"]:
        errores.append("El nombre es obligatorio.")
    if not datos["nit"]:
        errores.append("El NIT es obligatorio.")
    elif not re.fullmatch(r"[0-9A-Za-z-]{2,20}", datos["nit"]):
        errores.append("El NIT solo puede tener números, letras y guiones (máximo 20).")
    if datos["telefono"] and not re.fullmatch(r"[0-9 +-]{8,20}", datos["telefono"]):
        errores.append("El teléfono debe tener al menos 8 dígitos.")
    if datos["correo"] and not CORREO.match(datos["correo"]):
        errores.append("El correo no tiene un formato válido.")
    for campo in ("telefono", "correo", "direccion"):
        datos[campo] = datos[campo] or None
    return errores, datos


@bp.route("/")
@login_required
def listar():
    q = (request.args.get("q") or "").strip()
    pagina = request.args.get("pagina", "1")
    pagina = int(pagina) if pagina.isdigit() else 1
    where, params = "", []
    if q:
        where = "WHERE pr.nombre ILIKE %s OR pr.nit ILIKE %s"
        params = [f"%{q}%", f"%{q}%"]
    proveedores, total = query_page(
        f"""
        SELECT pr.id_proveedor, pr.nombre, pr.nit, pr.telefono, pr.correo, pr.estado,
               count(pp.id_producto) AS productos
        FROM proveedor pr
        LEFT JOIN proveedor_producto pp ON pp.id_proveedor = pr.id_proveedor
        {where}
        GROUP BY pr.id_proveedor
        ORDER BY pr.estado DESC, pr.nombre
        """,
        params, pagina,
    )
    return render_template("proveedores/list.html", proveedores=proveedores, total=total, pagina=pagina, q=q)


@bp.route("/<int:id_proveedor>")
@login_required
def detalle(id_proveedor):
    proveedor = query_one("SELECT * FROM proveedor WHERE id_proveedor = %s", (id_proveedor,))
    if proveedor is None:
        flash("El proveedor solicitado no existe.", "warning")
        return redirect(url_for("proveedores.listar"))
    productos = query_all(
        """
        SELECT p.codigo, p.nombre, p.unidad_medida, pp.precio_compra
        FROM proveedor_producto pp
        JOIN producto p ON p.id_producto = pp.id_producto
        WHERE pp.id_proveedor = %s
        ORDER BY p.nombre
        """,
        (id_proveedor,),
    )
    return render_template("proveedores/detalle.html", proveedor=proveedor, productos=productos)


@bp.route("/nuevo", methods=["GET", "POST"])
@rol_requerido(ADMIN)
def nuevo():
    if request.method == "GET":
        return render_template("proveedores/form.html", proveedor=None)

    errores, datos = _validar_formulario(request.form)
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("proveedores/form.html", proveedor=request.form), 400

    try:
        execute(
            """
            INSERT INTO proveedor (nombre, nit, telefono, correo, direccion)
            VALUES (%(nombre)s, %(nit)s, %(telefono)s, %(correo)s, %(direccion)s)
            """,
            datos,
        )
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe un proveedor con el NIT "{datos["nit"]}".', "danger")
        return render_template("proveedores/form.html", proveedor=request.form), 409
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo guardar el proveedor. Intente más tarde."), "danger")
        return render_template("proveedores/form.html", proveedor=request.form), 500

    flash("Proveedor creado correctamente.", "success")
    return redirect(url_for("proveedores.listar"))


@bp.route("/<int:id_proveedor>/editar", methods=["GET", "POST"])
@rol_requerido(ADMIN)
def editar(id_proveedor):
    proveedor = query_one("SELECT * FROM proveedor WHERE id_proveedor = %s", (id_proveedor,))
    if proveedor is None:
        flash("El proveedor solicitado no existe.", "warning")
        return redirect(url_for("proveedores.listar"))

    if request.method == "GET":
        return render_template("proveedores/form.html", proveedor=proveedor)

    errores, datos = _validar_formulario(request.form)
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("proveedores/form.html", proveedor={**proveedor, **request.form}), 400

    datos["id_proveedor"] = id_proveedor
    try:
        execute(
            """
            UPDATE proveedor
            SET nombre = %(nombre)s, nit = %(nit)s, telefono = %(telefono)s,
                correo = %(correo)s, direccion = %(direccion)s
            WHERE id_proveedor = %(id_proveedor)s
            """,
            datos,
        )
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe un proveedor con el NIT "{datos["nit"]}".', "danger")
        return render_template("proveedores/form.html", proveedor={**proveedor, **request.form}), 409
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo actualizar el proveedor. Intente más tarde."), "danger")
        return render_template("proveedores/form.html", proveedor={**proveedor, **request.form}), 500

    flash("Proveedor actualizado correctamente.", "success")
    return redirect(url_for("proveedores.listar"))


@bp.route("/<int:id_proveedor>/alternar-estado", methods=["POST"])
@rol_requerido(ADMIN)
def alternar_estado(id_proveedor):
    proveedor = query_one("SELECT estado FROM proveedor WHERE id_proveedor = %s", (id_proveedor,))
    if proveedor is None:
        flash("El proveedor solicitado no existe.", "warning")
        return redirect(url_for("proveedores.listar"))

    nuevo_estado = not proveedor["estado"]
    try:
        execute("UPDATE proveedor SET estado = %s WHERE id_proveedor = %s", (nuevo_estado, id_proveedor))
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo cambiar el estado del proveedor. Intente más tarde."), "danger")
        return redirect(url_for("proveedores.listar"))

    flash("Proveedor activado." if nuevo_estado else "Proveedor desactivado.", "success")
    return redirect(url_for("proveedores.listar"))
