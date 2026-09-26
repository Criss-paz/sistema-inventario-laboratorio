"""
routes/examenes.py — Exámenes de laboratorio y los insumos que requieren.
RF-36 a RF-39 (exámenes e insumos requeridos), RN-17 (un examen requiere
varios productos: tabla puente examen_producto).

Además de la lista de insumos, se calcula cuántos exámenes alcanzan con la
existencia utilizable actual: el insumo que menos rinde marca el límite.

Consultar: todos los roles. Registrar/modificar exámenes y sus insumos:
Administrador. examen_laboratorio no tiene columna estado; los insumos sí
se pueden quitar (DELETE solo en tablas puente, sql/security/001_roles.sql).
"""
import re
from decimal import Decimal, InvalidOperation

import psycopg

from flask import Blueprint, render_template, request, redirect, url_for, flash

from db import query_all, query_one, query_page, execute, mensaje_error
from routes.auth import login_required, rol_requerido, tiene_rol, ADMIN

bp = Blueprint("examenes", __name__, url_prefix="/examenes")


def _validar_formulario(form):
    """A3: campos requeridos y formato del código antes de la BD."""
    datos = {
        "nombre_examen": (form.get("nombre_examen") or "").strip(),
        "codigo_interno": (form.get("codigo_interno") or "").strip().upper(),
        "descripcion": (form.get("descripcion") or "").strip() or None,
    }
    errores = []
    if not datos["nombre_examen"]:
        errores.append("El nombre del examen es obligatorio.")
    if not re.fullmatch(r"[A-Z0-9-]{2,30}", datos["codigo_interno"]):
        errores.append("El código interno es obligatorio: letras, números y guiones (por ejemplo EX-GLU-01).")
    return errores, datos


@bp.route("/")
@login_required
def listar():
    q = (request.args.get("q") or "").strip()
    pagina = request.args.get("pagina", "1")
    pagina = int(pagina) if pagina.isdigit() else 1
    where, params = "", []
    if q:
        where = "WHERE e.nombre_examen ILIKE %s OR e.codigo_interno ILIKE %s"
        params = [f"%{q}%", f"%{q}%"]
    examenes, total = query_page(
        f"""
        SELECT e.id_examen, e.codigo_interno, e.nombre_examen, e.descripcion,
               count(ep.id_producto) AS insumos,
               min(floor(v.existencia_utilizable / ep.cantidad_requerida)) AS alcanzan
        FROM examen_laboratorio e
        LEFT JOIN examen_producto ep ON ep.id_examen = e.id_examen
        LEFT JOIN vw_existencia_producto v ON v.id_producto = ep.id_producto
        {where}
        GROUP BY e.id_examen
        ORDER BY e.nombre_examen
        """,
        params, pagina,
    )
    return render_template("examenes/list.html", examenes=examenes, total=total, pagina=pagina, q=q)


@bp.route("/<int:id_examen>")
@login_required
def detalle(id_examen):
    examen = query_one("SELECT * FROM examen_laboratorio WHERE id_examen = %s", (id_examen,))
    if examen is None:
        flash("El examen solicitado no existe.", "warning")
        return redirect(url_for("examenes.listar"))
    insumos = query_all(
        """
        SELECT ep.id_producto, v.codigo, v.nombre, v.unidad_medida, ep.cantidad_requerida,
               v.existencia_utilizable, floor(v.existencia_utilizable / ep.cantidad_requerida) AS alcanzan
        FROM examen_producto ep
        JOIN vw_existencia_producto v ON v.id_producto = ep.id_producto
        WHERE ep.id_examen = %s
        ORDER BY alcanzan, v.nombre
        """,
        (id_examen,),
    )
    # Solo el administrador ve el formulario para agregar insumos.
    productos = query_all("SELECT codigo, nombre FROM producto WHERE estado ORDER BY nombre") if tiene_rol(ADMIN) else []
    return render_template("examenes/detalle.html", examen=examen, insumos=insumos, productos=productos)


@bp.route("/nuevo", methods=["GET", "POST"])
@rol_requerido(ADMIN)
def nuevo():
    if request.method == "GET":
        return render_template("examenes/form.html", examen=None)

    errores, datos = _validar_formulario(request.form)
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("examenes/form.html", examen=request.form), 400
    try:
        execute(
            """
            INSERT INTO examen_laboratorio (nombre_examen, descripcion, codigo_interno)
            VALUES (%(nombre_examen)s, %(descripcion)s, %(codigo_interno)s)
            """,
            datos,
        )
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe un examen con el código "{datos["codigo_interno"]}".', "danger")
        return render_template("examenes/form.html", examen=request.form), 409
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo guardar el examen. Intente más tarde."), "danger")
        return render_template("examenes/form.html", examen=request.form), 500

    examen = query_one("SELECT id_examen FROM examen_laboratorio WHERE codigo_interno = %s", (datos["codigo_interno"],))
    flash("Examen creado. Agregue los insumos que requiere.", "success")
    return redirect(url_for("examenes.detalle", id_examen=examen["id_examen"]))


@bp.route("/<int:id_examen>/editar", methods=["GET", "POST"])
@rol_requerido(ADMIN)
def editar(id_examen):
    examen = query_one("SELECT * FROM examen_laboratorio WHERE id_examen = %s", (id_examen,))
    if examen is None:
        flash("El examen solicitado no existe.", "warning")
        return redirect(url_for("examenes.listar"))
    if request.method == "GET":
        return render_template("examenes/form.html", examen=examen)

    errores, datos = _validar_formulario(request.form)
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("examenes/form.html", examen={**examen, **request.form}), 400
    datos["id_examen"] = id_examen
    try:
        execute(
            """
            UPDATE examen_laboratorio
            SET nombre_examen = %(nombre_examen)s, descripcion = %(descripcion)s, codigo_interno = %(codigo_interno)s
            WHERE id_examen = %(id_examen)s
            """,
            datos,
        )
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe un examen con el código "{datos["codigo_interno"]}".', "danger")
        return render_template("examenes/form.html", examen={**examen, **request.form}), 409
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo actualizar el examen. Intente más tarde."), "danger")
        return render_template("examenes/form.html", examen={**examen, **request.form}), 500

    flash("Examen actualizado correctamente.", "success")
    return redirect(url_for("examenes.detalle", id_examen=id_examen))


@bp.route("/<int:id_examen>/insumos", methods=["POST"])
@rol_requerido(ADMIN)
def agregar_insumo(id_examen):
    codigo = (request.form.get("producto") or "").split(" — ")[0].strip()
    producto = query_one("SELECT id_producto FROM producto WHERE codigo = %s AND estado", (codigo,)) if codigo else None
    try:
        cantidad = Decimal((request.form.get("cantidad_requerida") or "").replace(",", "."))
    except InvalidOperation:
        cantidad = None
    if producto is None:
        flash("Seleccione un producto activo de la lista.", "danger")
    elif cantidad is None or cantidad <= 0 or cantidad.as_tuple().exponent < -2:
        flash("La cantidad requerida debe ser mayor que cero (hasta 2 decimales).", "danger")
    else:
        try:
            execute(
                "INSERT INTO examen_producto (id_examen, id_producto, cantidad_requerida) VALUES (%s, %s, %s)",
                (id_examen, producto["id_producto"], cantidad),
            )
            flash("Insumo agregado al examen.", "success")
        except psycopg.errors.UniqueViolation:
            flash("Ese insumo ya está en el examen. Quítelo y agréguelo con la nueva cantidad.", "warning")
        except Exception as exc:
            flash(mensaje_error(exc, "No se pudo agregar el insumo. Intente más tarde."), "danger")
    return redirect(url_for("examenes.detalle", id_examen=id_examen))


@bp.route("/<int:id_examen>/insumos/<int:id_producto>/quitar", methods=["POST"])
@rol_requerido(ADMIN)
def quitar_insumo(id_examen, id_producto):
    try:
        execute("DELETE FROM examen_producto WHERE id_examen = %s AND id_producto = %s", (id_examen, id_producto))
        flash("Insumo quitado del examen.", "success")
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo quitar el insumo. Intente más tarde."), "danger")
    return redirect(url_for("examenes.detalle", id_examen=id_examen))
