"""
routes/categorias.py — CRUD 1: Categorías.
RF-09 (clasificar productos mediante categorías), RF-10 (administrar categorías).

"Eliminar" no borra la fila físicamente (política definida en
docs/entrega-2/modelo-relacional.md, "Decisiones cerradas #3"): se alterna
`estado` porque `producto.id_categoria` tiene ON DELETE RESTRICT y porque
una categoría usada por productos existentes no debe desaparecer del
historial.
"""
import psycopg

from flask import Blueprint, render_template, request, redirect, url_for, flash

from db import query_all, query_one, execute
from routes.auth import login_required

bp = Blueprint("categorias", __name__, url_prefix="/categorias")


@bp.route("/")
@login_required
def listar():
    categorias = query_all(
        "SELECT id_categoria, nombre, descripcion, estado FROM categoria ORDER BY nombre"
    )
    return render_template("categorias/list.html", categorias=categorias)


@bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    if request.method == "GET":
        return render_template("categorias/form.html", categoria=None)

    nombre = (request.form.get("nombre") or "").strip()
    descripcion = (request.form.get("descripcion") or "").strip() or None

    # A3: validación de campos requeridos antes de tocar la base de datos.
    if not nombre:
        flash("El nombre de la categoría es obligatorio.", "danger")
        return render_template("categorias/form.html", categoria=request.form), 400

    try:
        execute(
            "INSERT INTO categoria (nombre, descripcion) VALUES (%s, %s)",
            (nombre, descripcion),
        )
    except psycopg.errors.UniqueViolation:
        # uq_categoria_nombre — RN de negocio: nombre de categoría único.
        flash(f'Ya existe una categoría llamada "{nombre}".', "danger")
        return render_template("categorias/form.html", categoria=request.form), 409
    except Exception:
        flash("No se pudo guardar la categoría. Intente más tarde.", "danger")
        return render_template("categorias/form.html", categoria=request.form), 500

    flash("Categoría creada correctamente.", "success")
    return redirect(url_for("categorias.listar"))


@bp.route("/<int:id_categoria>/editar", methods=["GET", "POST"])
@login_required
def editar(id_categoria):
    categoria = query_one(
        "SELECT id_categoria, nombre, descripcion, estado FROM categoria WHERE id_categoria = %s",
        (id_categoria,),
    )
    if categoria is None:
        flash("La categoría solicitada no existe.", "warning")
        return redirect(url_for("categorias.listar"))

    if request.method == "GET":
        return render_template("categorias/form.html", categoria=categoria)

    nombre = (request.form.get("nombre") or "").strip()
    descripcion = (request.form.get("descripcion") or "").strip() or None

    if not nombre:
        flash("El nombre de la categoría es obligatorio.", "danger")
        return render_template("categorias/form.html", categoria={**categoria, **request.form}), 400

    try:
        execute(
            "UPDATE categoria SET nombre = %s, descripcion = %s WHERE id_categoria = %s",
            (nombre, descripcion, id_categoria),
        )
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe una categoría llamada "{nombre}".', "danger")
        return render_template("categorias/form.html", categoria={**categoria, **request.form}), 409
    except Exception:
        flash("No se pudo actualizar la categoría. Intente más tarde.", "danger")
        return render_template("categorias/form.html", categoria={**categoria, **request.form}), 500

    flash("Categoría actualizada correctamente.", "success")
    return redirect(url_for("categorias.listar"))


@bp.route("/<int:id_categoria>/alternar-estado", methods=["POST"])
@login_required
def alternar_estado(id_categoria):
    """Baja/alta lógica — no hay DELETE físico (ver docstring del módulo)."""
    categoria = query_one("SELECT estado FROM categoria WHERE id_categoria = %s", (id_categoria,))
    if categoria is None:
        flash("La categoría solicitada no existe.", "warning")
        return redirect(url_for("categorias.listar"))

    nuevo_estado = not categoria["estado"]
    try:
        execute("UPDATE categoria SET estado = %s WHERE id_categoria = %s", (nuevo_estado, id_categoria))
    except Exception:
        # A2: mismo criterio que el resto de rutas — mensaje claro, nunca el error SQL crudo.
        flash("No se pudo cambiar el estado de la categoría. Intente más tarde.", "danger")
        return redirect(url_for("categorias.listar"))

    flash("Categoría activada." if nuevo_estado else "Categoría desactivada.", "success")
    return redirect(url_for("categorias.listar"))
