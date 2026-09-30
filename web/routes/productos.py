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

from db import query_all, query_one, query_page, execute
from routes.auth import login_required, rol_requerido, ADMIN

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
        errores.append("La presentación es obligatoria.")
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
    # Filtros (A3: se validan antes de usarlos; van como parámetros, A4).
    q = (request.args.get("q") or "").strip()
    id_categoria = request.args.get("categoria", "")
    pagina = request.args.get("pagina", "1")
    pagina = int(pagina) if pagina.isdigit() else 1

    condiciones, params = [], []
    if q:
        condiciones.append("(e.nombre ILIKE %s OR e.codigo ILIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    if id_categoria.isdigit():
        condiciones.append("p.id_categoria = %s")
        params.append(int(id_categoria))
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    # La existencia sale de la vista (S7: calculada, no almacenada).
    productos, total = query_page(
        f"""
        SELECT e.id_producto, e.codigo, e.nombre, e.categoria AS nombre_categoria,
               e.unidad_medida, e.stock_minimo, e.requiere_vencimiento, e.estado,
               e.existencia_utilizable, e.existencia_vencida
        FROM vw_existencia_producto e
        JOIN producto p ON p.id_producto = e.id_producto
        {where}
        ORDER BY e.nombre
        """,
        params, pagina,
    )
    # El producto no guarda precio: el costo es el promedio ponderado móvil que
    # calcula el kardex (S7, dato calculable). Se pide solo para los productos
    # de esta página, no para los 806 del catálogo.
    valores = {}
    ids = [p["id_producto"] for p in productos]
    if ids:
        for fila in query_all(
            """
            SELECT id_producto, costo_promedio, valor_inventario
              FROM vw_valorizacion_inventario
             WHERE id_producto = ANY(%s)
            """,
            (ids,),
        ):
            valores[fila["id_producto"]] = fila

    resumen = query_one(
        """
        SELECT count(*) AS total,
               count(*) FILTER (WHERE estado) AS activos,
               count(*) FILTER (WHERE existencia_utilizable > 0) AS con_existencia,
               count(*) FILTER (WHERE requiere_vencimiento) AS con_vencimiento
        FROM vw_existencia_producto
        """
    )
    return render_template(
        "productos/list.html", productos=productos, total=total, pagina=pagina,
        resumen=resumen, categorias=_categorias_activas(), q=q, id_categoria=id_categoria,
        valores=valores,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@rol_requerido(ADMIN)
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
@rol_requerido(ADMIN)
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
@rol_requerido(ADMIN)
def alternar_estado(id_producto):
    producto = query_one("SELECT estado FROM producto WHERE id_producto = %s", (id_producto,))
    if producto is None:
        flash("El producto solicitado no existe.", "warning")
        return redirect(url_for("productos.listar"))

    nuevo_estado = not producto["estado"]
    try:
        execute("UPDATE producto SET estado = %s WHERE id_producto = %s", (nuevo_estado, id_producto))
    except Exception:
        # A2: mismo criterio que el resto de rutas — mensaje claro, nunca el error SQL crudo.
        flash("No se pudo cambiar el estado del producto. Intente más tarde.", "danger")
        return redirect(url_for("productos.listar"))

    flash("Producto activado." if nuevo_estado else "Producto desactivado.", "success")
    return redirect(url_for("productos.listar"))
