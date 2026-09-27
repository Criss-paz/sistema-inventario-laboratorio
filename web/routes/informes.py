"""
routes/informes.py — Reportes de inventario valorizados (RF-33, RF-34).

  Inventario valorizado  existencia, costo promedio y valor por producto
  Entradas               compras de un período, por producto o proveedor
  Salidas                consumo de un período, valorizado a costo promedio
  Kardex                 tarjeta de un producto, movimiento por movimiento

Método de valuación: COSTO PROMEDIO PONDERADO MÓVIL. El cálculo lo hace la
base de datos (fn_kardex_promedio y vw_valorizacion_inventario, en
sql/views/002_valorizacion_promedio.sql); aquí solo se filtra y se muestra.

Todos los roles pueden consultar. Cada reporte se descarga en CSV (para
Excel) agregando ?formato=csv, y se imprime con el botón del navegador.
"""
import csv
import datetime as dt
import io

from flask import Blueprint, Response, render_template, request, redirect, url_for, flash

from db import query_all, query_one
from routes.auth import login_required

bp = Blueprint("informes", __name__, url_prefix="/informes")


def _categorias():
    return query_all("SELECT id_categoria, nombre FROM categoria WHERE estado ORDER BY nombre")


def _periodo():
    """Período del reporte: por defecto, del primer día del mes a hoy."""
    hoy = dt.date.today()
    try:
        desde = dt.date.fromisoformat(request.args.get("desde", ""))
    except ValueError:
        desde = hoy.replace(day=1)
    try:
        hasta = dt.date.fromisoformat(request.args.get("hasta", ""))
    except ValueError:
        hasta = hoy
    if hasta < desde:
        desde, hasta = hasta, desde
    return desde, hasta


def _categoria():
    valor = request.args.get("categoria", "")
    return int(valor) if valor.isdigit() else None


def _quiere_csv():
    return request.args.get("formato") == "csv"


def _csv(nombre, encabezados, filas):
    """CSV para Excel: UTF-8 con BOM (para que Excel lea las tildes)."""
    salida = io.StringIO()
    salida.write("﻿")
    escritor = csv.writer(salida)
    escritor.writerow(encabezados)
    escritor.writerows(filas)
    return Response(
        salida.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre}-{dt.date.today():%Y%m%d}.csv"'},
    )


@bp.route("/inventario")
@login_required
def inventario():
    id_categoria = _categoria()
    q = (request.args.get("q") or "").strip()
    todos = request.args.get("todos") == "1"

    condiciones, params = ["v.estado"], []
    if not todos:
        condiciones.append("v.existencia > 0")
    if id_categoria:
        condiciones.append("p.id_categoria = %s")
        params.append(id_categoria)
    if q:
        condiciones.append("(v.nombre ILIKE %s OR v.codigo ILIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    where = " AND ".join(condiciones)

    filas = query_all(
        f"""
        SELECT v.id_producto, v.codigo, v.nombre, v.categoria, v.unidad_medida, v.existencia,
               v.existencia_vencida, v.costo_promedio, v.valor_inventario
        FROM vw_valorizacion_inventario v
        JOIN producto p ON p.id_producto = v.id_producto
        WHERE {where}
        ORDER BY v.categoria, v.nombre
        """,
        params,
    )
    if _quiere_csv():
        return _csv("inventario-valorizado",
                    ["Código", "Producto", "Categoría", "Unidad", "Existencia", "Existencia vencida",
                     "Costo promedio (Q)", "Valor (Q)"],
                    [[f["codigo"], f["nombre"], f["categoria"], f["unidad_medida"], f["existencia"],
                      f["existencia_vencida"], f["costo_promedio"], f["valor_inventario"]] for f in filas])

    # Totales por categoría, de las mismas filas del reporte.
    por_categoria = {}
    for f in filas:
        c = por_categoria.setdefault(f["categoria"], {"productos": 0, "valor": 0})
        c["productos"] += 1
        c["valor"] += f["valor_inventario"]
    total = sum(c["valor"] for c in por_categoria.values())
    valor_vencido = sum(f["existencia_vencida"] * f["costo_promedio"] for f in filas)
    return render_template(
        "informes/inventario.html", filas=filas, por_categoria=sorted(por_categoria.items()),
        total=total, valor_vencido=valor_vencido, categorias=_categorias(),
        id_categoria=id_categoria, q=q, todos=todos, hoy=dt.date.today(),
    )


@bp.route("/entradas")
@login_required
def entradas():
    desde, hasta = _periodo()
    agrupar = request.args.get("agrupar", "producto")
    if agrupar not in ("producto", "proveedor"):
        agrupar = "producto"
    id_categoria = _categoria()

    condiciones = ["h.tipo_movimiento = 'ENTRADA'", "h.fecha_hora >= %s", "h.fecha_hora < %s"]
    params = [desde, hasta + dt.timedelta(days=1)]
    if id_categoria:
        condiciones.append("p.id_categoria = %s")
        params.append(id_categoria)
    where = " AND ".join(condiciones)
    base = f"""
        FROM vw_historial_movimientos h
        JOIN lote l ON l.id_lote = h.id_lote
        JOIN proveedor pr ON pr.id_proveedor = l.id_proveedor
        JOIN producto p ON p.id_producto = h.id_producto
        WHERE {where}
    """
    if agrupar == "producto":
        filas = query_all(
            f"""
            SELECT h.id_producto, h.codigo, h.producto AS nombre, h.unidad_medida,
                   count(DISTINCT h.id_movimiento) AS compras, sum(h.cantidad) AS cantidad,
                   sum(h.subtotal) AS total,
                   round(sum(h.subtotal) / nullif(sum(h.cantidad), 0), 2) AS precio_promedio
            {base}
            GROUP BY h.id_producto, h.codigo, h.producto, h.unidad_medida
            ORDER BY total DESC, nombre
            """,
            params,
        )
    else:
        filas = query_all(
            f"""
            SELECT pr.nombre, count(DISTINCT h.id_movimiento) AS compras,
                   count(DISTINCT h.id_producto) AS productos, sum(h.subtotal) AS total
            {base}
            GROUP BY pr.nombre
            ORDER BY total DESC, pr.nombre
            """,
            params,
        )
    if _quiere_csv():
        if agrupar == "producto":
            return _csv("entradas-por-producto",
                        ["Código", "Producto", "Unidad", "Compras", "Cantidad", "Precio promedio (Q)", "Total (Q)"],
                        [[f["codigo"], f["nombre"], f["unidad_medida"], f["compras"], f["cantidad"],
                          f["precio_promedio"], f["total"]] for f in filas])
        return _csv("entradas-por-proveedor", ["Proveedor", "Compras", "Productos distintos", "Total (Q)"],
                    [[f["nombre"], f["compras"], f["productos"], f["total"]] for f in filas])

    return render_template(
        "informes/entradas.html", filas=filas, agrupar=agrupar, desde=desde, hasta=hasta,
        total=sum(f["total"] for f in filas), compras=sum(f["compras"] for f in filas),
        categorias=_categorias(), id_categoria=id_categoria,
    )


@bp.route("/salidas")
@login_required
def salidas():
    desde, hasta = _periodo()
    agrupar = request.args.get("agrupar", "producto")
    if agrupar not in ("producto", "categoria"):
        agrupar = "producto"
    id_categoria = _categoria()

    # Las salidas se valorizan con el kardex: cada una al costo promedio
    # vigente el día que ocurrió, no al promedio de hoy.
    condiciones = ["k.tipo_movimiento = 'SALIDA'", "k.fecha_hora >= %s", "k.fecha_hora < %s"]
    params = [desde, hasta + dt.timedelta(days=1)]
    if id_categoria:
        condiciones.append("p.id_categoria = %s")
        params.append(id_categoria)
    where = " AND ".join(condiciones)
    base = f"""
        FROM fn_kardex_promedio() k
        JOIN producto p ON p.id_producto = k.id_producto
        JOIN categoria c ON c.id_categoria = p.id_categoria
        WHERE {where}
    """
    if agrupar == "producto":
        filas = query_all(
            f"""
            SELECT p.id_producto, p.codigo, p.nombre, p.unidad_medida, c.nombre AS categoria,
                   count(*) AS salidas, sum(k.cantidad_salida) AS cantidad,
                   round(sum(k.total_salida) / nullif(sum(k.cantidad_salida), 0), 2) AS costo_promedio,
                   sum(k.total_salida) AS total
            {base}
            GROUP BY p.id_producto, c.nombre
            ORDER BY total DESC, p.nombre
            """,
            params,
        )
    else:
        filas = query_all(
            f"""
            SELECT c.nombre, count(*) AS salidas, count(DISTINCT p.id_producto) AS productos,
                   sum(k.total_salida) AS total
            {base}
            GROUP BY c.nombre
            ORDER BY total DESC, c.nombre
            """,
            params,
        )
    if _quiere_csv():
        if agrupar == "producto":
            return _csv("salidas-por-producto",
                        ["Código", "Producto", "Categoría", "Unidad", "Salidas", "Cantidad",
                         "Costo promedio (Q)", "Costo total (Q)"],
                        [[f["codigo"], f["nombre"], f["categoria"], f["unidad_medida"], f["salidas"],
                          f["cantidad"], f["costo_promedio"], f["total"]] for f in filas])
        return _csv("salidas-por-categoria", ["Categoría", "Salidas", "Productos distintos", "Costo total (Q)"],
                    [[f["nombre"], f["salidas"], f["productos"], f["total"]] for f in filas])

    return render_template(
        "informes/salidas.html", filas=filas, agrupar=agrupar, desde=desde, hasta=hasta,
        total=sum(f["total"] for f in filas), n_salidas=sum(f["salidas"] for f in filas),
        categorias=_categorias(), id_categoria=id_categoria,
    )


@bp.route("/kardex")
@login_required
def kardex_buscar():
    """Formulario para elegir el producto; envía a su kardex."""
    texto = request.args.get("producto")
    if texto:
        codigo = texto.split(" — ")[0].strip()
        producto = query_one("SELECT id_producto FROM producto WHERE codigo = %s", (codigo,))
        if producto:
            return redirect(url_for("informes.kardex", id_producto=producto["id_producto"]))
        flash("Seleccione un producto de la lista.", "warning")
    productos = query_all(
        """
        SELECT p.codigo, p.nombre FROM producto p
        WHERE EXISTS (SELECT 1 FROM lote l WHERE l.id_producto = p.id_producto)
        ORDER BY p.nombre
        """
    )
    return render_template("informes/kardex_buscar.html", productos=productos)


@bp.route("/kardex/<int:id_producto>")
@login_required
def kardex(id_producto):
    producto = query_one(
        """
        SELECT p.id_producto, p.codigo, p.nombre, p.unidad_medida, c.nombre AS categoria
        FROM producto p JOIN categoria c ON c.id_categoria = p.id_categoria
        WHERE p.id_producto = %s
        """,
        (id_producto,),
    )
    if producto is None:
        flash("El producto solicitado no existe.", "warning")
        return redirect(url_for("informes.kardex_buscar"))

    filas = query_all("SELECT * FROM fn_kardex_promedio(%s)", (id_producto,))
    # Con período: el saldo inicial es el último saldo antes de "desde".
    saldo_inicial = None
    if request.args.get("desde") or request.args.get("hasta"):
        desde, hasta = _periodo()
        anteriores = [f for f in filas if f["fecha_hora"].date() < desde]
        saldo_inicial = anteriores[-1] if anteriores else None
        filas = [f for f in filas if desde <= f["fecha_hora"].date() <= hasta]
    else:
        desde = hasta = None

    if _quiere_csv():
        return _csv(f"kardex-{producto['codigo']}",
                    ["Fecha", "Movimiento", "Detalle", "Entrada cantidad", "Entrada costo unitario (Q)",
                     "Entrada total (Q)", "Salida cantidad", "Salida costo unitario (Q)", "Salida total (Q)",
                     "Saldo cantidad", "Costo promedio (Q)", "Saldo valor (Q)"],
                    [[f"{f['fecha_hora']:%d/%m/%Y %H:%M}", f["tipo_movimiento"], f["observacion"] or "",
                      f["cantidad_entrada"], f["costo_unitario_entrada"], f["total_entrada"],
                      f["cantidad_salida"], f["costo_unitario_salida"], f["total_salida"],
                      f["saldo_cantidad"], f["costo_promedio"], f["saldo_valor"]] for f in filas])

    return render_template(
        "informes/kardex.html", producto=producto, filas=filas, saldo_inicial=saldo_inicial,
        desde=desde, hasta=hasta,
        total_entradas=sum(f["total_entrada"] or 0 for f in filas),
        total_salidas=sum(f["total_salida"] or 0 for f in filas),
    )
