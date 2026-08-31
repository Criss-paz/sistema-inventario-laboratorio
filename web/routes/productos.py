"""
routes/productos.py — CRUD 2: Productos.
RF-06 (registrar), RF-07 (modificar), RF-08 (consultar), RF-09 (clasificar
por categoría).

Se eligió Productos como segundo CRUD (junto a Categorías) porque: (a) es
la entidad central del sistema y la más simple que ya tiene una FK real
para demostrar (id_categoria), a diferencia de Lote/Movimiento que dependen
de reglas de negocio con triggers (RN-01 a RN-04) que corresponden a la
Entrega 3, no a esta. (b) No tiene sentido ofrecer un CRUD de Lote sin
haber resuelto antes el de Producto, del que depende.

Mismo criterio de "eliminar" que Categorías: baja lógica vía `estado`
(ON DELETE RESTRICT en las FK que apuntan a producto).
"""
import psycopg

from flask import Blueprint, render_template, request, redirect, url_for, flash

from db import query_all, query_one, execute
from routes.auth import login_required

bp = Blueprint("productos", __name__, url_prefix="/productos")


def _categorias_activas():
    return query_all("SELECT id_categoria, nombre FROM categoria WHERE estado = TRUE ORDER BY nombre")


def _validar_formulario(form):
    """A3: validación de tipos, campos requeridos y formatos antes de la BD."""
    errores = []
    codigo = (form.get("codigo") or "").strip()
    nombre = (form.get("nombre") or "").strip()
    unidad_medida = (form.get("unidad_medida") or "").strip()
    id_categoria = (form.get("id_categoria") or "").strip()
    stock_minimo_raw = (form.get("stock_minimo") or "0").strip()

    if not codigo:
        errores.append("El código es obligatorio.")
    if not nombre:
        errores.append("El nombre es obligatorio.")
    if not unidad_medida:
        errores.append("La unidad de medida es obligatoria.")
    if not id_categoria.isdigit():
        errores.append("Debe seleccionar una categoría válida.")

    stock_minimo = None
    try:
        stock_minimo = float(stock_minimo_raw)
        if stock_minimo < 0:
            errores.append("El stock mínimo no puede ser negativo.")  # refuerza ck_producto_stock_minimo
    except ValueError:
        errores.append("El stock mínimo debe ser un número.")

    return errores, {
        "codigo": codigo,
        "nombre": nombre,
        "descripcion": (form.get("descripcion") or "").strip() or None,
        "unidad_medida": unidad_medida,
        "stock_minimo": stock_minimo,
        "id_categoria": int(id_categoria) if id_categoria.isdigit() else None,
        "requiere_vencimiento": form.get("requiere_vencimiento") == "on",
    }


@bp.route("/")
@login_required
def listar():
    productos = query_all(
        """
        SELECT p.id_producto, p.codigo, p.nombre, p.unidad_medida, p.stock_minimo,
               p.requiere_vencimiento, p.estado, c.nombre AS nombre_categoria
        FROM producto p
        JOIN categoria c ON c.id_categoria = p.id_categoria
        ORDER BY p.nombre
        """
    )
    return render_template("productos/list.html", productos=productos)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "GET":
        return render_template("productos/form.html", producto=None, categorias=_categorias_activas())

    errores, datos = _validar_formulario(request.form)
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("productos/form.html", producto=request.form, categorias=_categorias_activas()), 400

    try:
        execute(
            """
            INSERT INTO producto (id_categoria, codigo, nombre, descripcion, unidad_medida, stock_minimo, requiere_vencimiento)
            VALUES (%(id_categoria)s, %(codigo)s, %(nombre)s, %(descripcion)s, %(unidad_medida)s, %(stock_minimo)s, %(requiere_vencimiento)s)
            """,
            datos,
        )
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe un producto con el código "{datos["codigo"]}".', "danger")
        return render_template("productos/form.html", producto=request.form, categorias=_categorias_activas()), 409
    except psycopg.errors.ForeignKeyViolation:
        flash("La categoría seleccionada ya no existe.", "danger")
        return render_template("productos/form.html", producto=request.form, categorias=_categorias_activas()), 409
    except Exception:
        flash("No se pudo guardar el producto. Intente más tarde.", "danger")
        return render_template("productos/form.html", producto=request.form, categorias=_categorias_activas()), 500

    flash("Producto creado correctamente.", "success")
    return redirect(url_for("productos.listar"))


@bp.route("/<int:id_producto>/editar", methods=["GET", "POST"])
@login_required
def editar(id_producto):
    producto = query_one("SELECT * FROM producto WHERE id_producto = %s", (id_producto,))
    if producto is None:
        flash("El producto solicitado no existe.", "warning")
        return redirect(url_for("productos.listar"))

    if request.method == "GET":
        return render_template("productos/form.html", producto=producto, categorias=_categorias_activas())

    errores, datos = _validar_formulario(request.form)
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("productos/form.html", producto={**producto, **request.form}, categorias=_categorias_activas()), 400

    datos["id_producto"] = id_producto
    try:
        execute(
            """
            UPDATE producto
            SET id_categoria = %(id_categoria)s, codigo = %(codigo)s, nombre = %(nombre)s,
                descripcion = %(descripcion)s, unidad_medida = %(unidad_medida)s,
                stock_minimo = %(stock_minimo)s, requiere_vencimiento = %(requiere_vencimiento)s
            WHERE id_producto = %(id_producto)s
            """,
            datos,
        )
    except psycopg.errors.UniqueViolation:
        flash(f'Ya existe un producto con el código "{datos["codigo"]}".', "danger")
        return render_template("productos/form.html", producto={**producto, **request.form}, categorias=_categorias_activas()), 409
    except Exception:
        flash("No se pudo actualizar el producto. Intente más tarde.", "danger")
        return render_template("productos/form.html", producto={**producto, **request.form}, categorias=_categorias_activas()), 500

    flash("Producto actualizado correctamente.", "success")
    return redirect(url_for("productos.listar"))


@bp.route("/<int:id_producto>/alternar-estado", methods=["POST"])
@login_required
def alternar_estado(id_producto):
    producto = query_one("SELECT estado FROM producto WHERE id_producto = %s", (id_producto,))
    if producto is None:
        flash("El producto solicitado no existe.", "warning")
        return redirect(url_for("productos.listar"))

    nuevo_estado = not producto["estado"]
    execute("UPDATE producto SET estado = %s WHERE id_producto = %s", (nuevo_estado, id_producto))
    flash("Producto activado." if nuevo_estado else "Producto desactivado.", "success")
    return redirect(url_for("productos.listar"))
