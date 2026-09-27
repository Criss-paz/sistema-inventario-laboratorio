"""
routes/reportes.py — Inicio y reportes del inventario.
RF-29 (inventario bajo), RF-30 (próximos a vencer), RF-31 a RF-35 (reportes
y consultas), RN-10, RN-11.

Todo sale de las vistas de sql/views/001_views.sql: la app no recalcula
existencias ni faltantes (S7). Todos los roles pueden consultar; por eso
aquí no se lee la tabla movimiento (rol_consulta solo ve la vista).
"""
import datetime as dt

from flask import Blueprint, render_template, request

from db import query_all, query_one, query_page
from routes.auth import login_required
from routes.informes import _csv

bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _categorias():
    return query_all("SELECT id_categoria, nombre FROM categoria WHERE estado ORDER BY nombre")


def _pagina():
    pagina = request.args.get("pagina", "1")
    return int(pagina) if pagina.isdigit() else 1


@bp.route("/inicio")
@login_required
def inicio():
    resumen = query_one(
        """
        SELECT
          (SELECT count(*) FROM producto WHERE estado) AS productos_activos,
          (SELECT count(*) FROM vw_existencia_producto WHERE existencia_utilizable > 0) AS con_existencia,
          (SELECT count(*) FROM vw_inventario_bajo b
            WHERE EXISTS (SELECT 1 FROM lote l WHERE l.id_producto = b.id_producto)) AS bajo_con_historial,
          (SELECT count(*) FROM vw_lotes_por_vencer WHERE situacion = 'VENCIDO') AS lotes_vencidos,
          (SELECT count(*) FROM vw_lotes_por_vencer WHERE situacion = 'POR VENCER') AS lotes_por_vencer,
          (SELECT count(DISTINCT id_movimiento) FROM vw_historial_movimientos
            WHERE fecha_hora >= CURRENT_DATE - 30) AS movimientos_30_dias
        """
    )
    por_vencer = query_all(
        "SELECT * FROM vw_lotes_por_vencer ORDER BY fecha_vencimiento, producto LIMIT 8"
    )
    ultimos = query_all(
        """
        SELECT id_movimiento, fecha_hora, tipo_movimiento, producto, cantidad, unidad_medida, nombre_usuario
        FROM vw_historial_movimientos
        ORDER BY fecha_hora DESC, id_movimiento DESC
        LIMIT 8
        """
    )
    return render_template(
        "reportes/inicio.html", resumen=resumen, por_vencer=por_vencer, ultimos=ultimos, hoy=dt.date.today(),
    )


@bp.route("/inventario-bajo")
@login_required
def inventario_bajo():
    id_categoria = request.args.get("categoria", "")
    q = (request.args.get("q") or "").strip()
    # Por defecto se ocultan los productos que nunca tuvieron un lote: son
    # parte del catálogo pero no se compraron en el periodo registrado.
    todos = request.args.get("todos") == "1"

    condiciones, params = [], []
    if not todos:
        condiciones.append("EXISTS (SELECT 1 FROM lote l WHERE l.id_producto = b.id_producto)")
    if id_categoria.isdigit():
        condiciones.append("p.id_categoria = %s")
        params.append(int(id_categoria))
    if q:
        condiciones.append("(b.nombre ILIKE %s OR b.codigo ILIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    consulta = f"""
        SELECT b.*
        FROM vw_inventario_bajo b
        JOIN producto p ON p.id_producto = b.id_producto
        {where}
        ORDER BY b.faltante DESC, b.nombre
    """
    if request.args.get("formato") == "csv":
        return _csv("inventario-bajo",
                    ["Código de producto", "Producto", "Categoría", "Presentación", "Existencia utilizable",
                     "Existencia vencida", "Stock mínimo", "Faltante"],
                    [[f["codigo"], f["nombre"], f["categoria"], f["unidad_medida"], f["existencia_utilizable"],
                      f["existencia_vencida"], f["stock_minimo"], f["faltante"]] for f in query_all(consulta, params)])
    filas, total = query_page(consulta, params, _pagina())
    return render_template(
        "reportes/inventario_bajo.html", filas=filas, total=total, pagina=_pagina(),
        categorias=_categorias(), id_categoria=id_categoria, q=q, todos=todos,
    )


@bp.route("/por-vencer")
@login_required
def por_vencer():
    situacion = request.args.get("situacion", "")
    q = (request.args.get("q") or "").strip()
    condiciones, params = [], []
    if situacion in ("VENCIDO", "POR VENCER"):
        condiciones.append("situacion = %s")
        params.append(situacion)
    if q:
        condiciones.append("(producto ILIKE %s OR codigo ILIKE %s OR numero_lote ILIKE %s)")
        params += [f"%{q}%"] * 3
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    consulta = f"SELECT * FROM vw_lotes_por_vencer {where} ORDER BY fecha_vencimiento, producto"
    if request.args.get("formato") == "csv":
        return _csv("vencimientos",
                    ["Lote", "Código de producto", "Producto", "Proveedor", "Vence", "Días", "Situación",
                     "Existencia", "Presentación"],
                    [[f["numero_lote"], f["codigo"], f["producto"], f["proveedor"],
                      f"{f['fecha_vencimiento']:%d/%m/%Y}", f["dias_para_vencer"], f["situacion"],
                      f["cantidad_disponible"], f["unidad_medida"]] for f in query_all(consulta, params)])
    filas, total = query_page(consulta, params, _pagina())
    return render_template(
        "reportes/por_vencer.html", filas=filas, total=total, pagina=_pagina(), situacion=situacion, q=q,
    )
