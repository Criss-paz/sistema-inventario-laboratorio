"""
routes/lotes.py — Lotes, vencimientos y existencia.
RF-14 a RF-19 (lotes, fecha de vencimiento, existencia por lote), RN-07.

Los lotes no se crean aquí: nacen con la primera entrada
(sp_registrar_entrada). El administrador puede corregir el número de lote,
el vencimiento o darlo de baja, pero NUNCA la existencia: su rol de base de
datos no tiene UPDATE sobre cantidad_disponible (sql/security/001_roles.sql);
la existencia solo cambia por movimientos.

Consultar: todos los roles. Corregir: Administrador.
"""
import datetime as dt

import psycopg

from flask import Blueprint, render_template, request, redirect, url_for, flash

from db import query_all, query_one, query_page, execute, mensaje_error
from routes.auth import login_required, rol_requerido, ADMIN

bp = Blueprint("lotes", __name__, url_prefix="/lotes")

FILTROS = {
    "existencia": "l.cantidad_disponible > 0",
    "vencidos": "l.cantidad_disponible > 0 AND l.fecha_vencimiento < CURRENT_DATE",
    "por_vencer": "l.cantidad_disponible > 0 AND l.fecha_vencimiento BETWEEN CURRENT_DATE AND CURRENT_DATE + 90",
    "todos": "TRUE",
}


@bp.route("/")
@login_required
def listar():
    filtro = request.args.get("filtro", "existencia")
    if filtro not in FILTROS:
        filtro = "existencia"
    q = (request.args.get("q") or "").strip()
    pagina = request.args.get("pagina", "1")
    pagina = int(pagina) if pagina.isdigit() else 1

    # El filtro sale de un diccionario fijo, nunca del texto del usuario (A4).
    condiciones, params = [FILTROS[filtro]], []
    if q:
        condiciones.append("(p.nombre ILIKE %s OR p.codigo ILIKE %s OR l.numero_lote ILIKE %s)")
        params += [f"%{q}%"] * 3

    lotes, total = query_page(
        f"""
        SELECT l.id_lote, l.numero_lote, l.fecha_ingreso, l.fecha_vencimiento, l.cantidad_disponible,
               l.estado, p.codigo, p.nombre AS producto, p.unidad_medida, pr.nombre AS proveedor,
               (l.fecha_vencimiento - CURRENT_DATE) AS dias_para_vencer
        FROM lote l
        JOIN producto p ON p.id_producto = l.id_producto
        JOIN proveedor pr ON pr.id_proveedor = l.id_proveedor
        WHERE {" AND ".join(condiciones)}
        ORDER BY l.fecha_vencimiento NULLS LAST, p.nombre, l.id_lote
        """,
        params, pagina,
    )
    return render_template("lotes/list.html", lotes=lotes, total=total, pagina=pagina, filtro=filtro, q=q)


@bp.route("/<int:id_lote>")
@login_required
def detalle(id_lote):
    lote = query_one(
        """
        SELECT l.*, p.codigo, p.nombre AS producto, p.unidad_medida, p.requiere_vencimiento,
               pr.nombre AS proveedor, (l.fecha_vencimiento - CURRENT_DATE) AS dias_para_vencer
        FROM lote l
        JOIN producto p ON p.id_producto = l.id_producto
        JOIN proveedor pr ON pr.id_proveedor = l.id_proveedor
        WHERE l.id_lote = %s
        """,
        (id_lote,),
    )
    if lote is None:
        flash("El lote solicitado no existe.", "warning")
        return redirect(url_for("lotes.listar"))
    movimientos = query_all(
        """
        SELECT id_movimiento, fecha_hora, tipo_movimiento, cantidad, nombre_usuario, observacion
        FROM vw_historial_movimientos
        WHERE id_lote = %s
        ORDER BY fecha_hora, id_movimiento
        """,
        (id_lote,),
    )
    return render_template("lotes/detalle.html", lote=lote, movimientos=movimientos)


@bp.route("/<int:id_lote>/editar", methods=["GET", "POST"])
@rol_requerido(ADMIN)
def editar(id_lote):
    lote = query_one(
        """
        SELECT l.*, p.nombre AS producto, p.requiere_vencimiento
        FROM lote l JOIN producto p ON p.id_producto = l.id_producto
        WHERE l.id_lote = %s
        """,
        (id_lote,),
    )
    if lote is None:
        flash("El lote solicitado no existe.", "warning")
        return redirect(url_for("lotes.listar"))

    if request.method == "GET":
        return render_template("lotes/form.html", lote=lote)

    errores = []
    numero_lote = (request.form.get("numero_lote") or "").strip()
    if not numero_lote:
        errores.append("El número de lote es obligatorio.")
    vence = None
    if request.form.get("fecha_vencimiento"):
        try:
            vence = dt.date.fromisoformat(request.form["fecha_vencimiento"])
        except ValueError:
            errores.append("La fecha de vencimiento no es válida.")
        else:
            if vence < lote["fecha_ingreso"]:
                errores.append("El vencimiento no puede ser anterior a la fecha de ingreso del lote.")
    estado = request.form.get("estado") == "on"
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("lotes/form.html", lote={**lote, **request.form}), 400

    try:
        execute(
            "UPDATE lote SET numero_lote = %s, fecha_vencimiento = %s, estado = %s WHERE id_lote = %s",
            (numero_lote, vence, estado, id_lote),
        )
    except psycopg.errors.UniqueViolation:
        flash(f'El producto ya tiene otro lote con el número "{numero_lote}".', "danger")
        return render_template("lotes/form.html", lote={**lote, **request.form}), 409
    except Exception as exc:
        # RN-07: "El producto ... requiere fecha de vencimiento" viene del trigger.
        flash(mensaje_error(exc, "No se pudo actualizar el lote. Intente más tarde."), "danger")
        return render_template("lotes/form.html", lote={**lote, **request.form}), 400

    flash("Lote actualizado correctamente.", "success")
    return redirect(url_for("lotes.detalle", id_lote=id_lote))
