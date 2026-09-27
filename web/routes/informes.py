"""
routes/informes.py — Reportes (RF-33 generar reportes, RF-34 información
histórica). Una sola entrada en el menú: el usuario elige el tipo de reporte
y sus filtros en /informes/ (TIPOS, abajo).

  Inventario     código, producto, presentación, existencia, precio unitario
                 y precio total de cada producto
  Entradas       compras de un período, por producto o proveedor
  Salidas        consumo de un período, valorizado a costo promedio
  Kardex         tarjeta de un producto, movimiento por movimiento
  Proveedores    datos de contacto y compras del período
  Pruebas        exámenes, sus insumos y cuántos alcanzan
  Productos      catálogo con presentación, mínimo y existencia
  (Inventario bajo y Vencimientos viven en routes/reportes.py)

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


# Tipos de reporte que se ofrecen en /informes/. Cada uno declara qué filtros
# usa, para que la pantalla muestre solo esos.
#   clave: (título, descripción, endpoint, filtros)
TIPOS = {
    "inventario": ("Inventario", "Existencias actuales con precio unitario (costo promedio ponderado) y precio total.",
                   "informes.inventario", ("categoria",)),
    "entradas": ("Entradas", "Compras recibidas en un período, por producto o por proveedor.",
                 "informes.entradas", ("periodo", "categoria", "agrupar_entradas")),
    "salidas": ("Salidas", "Consumo de un período, valorizado al costo promedio de cada día.",
                "informes.salidas", ("periodo", "categoria", "agrupar_salidas")),
    "kardex": ("Kardex de un producto", "Entradas, salidas y saldo de un producto, movimiento por movimiento.",
               "informes.kardex_buscar", ("producto", "periodo_opcional")),
    "proveedores": ("Proveedores", "Contacto de cada proveedor y cuánto se le compró en un período.",
                    "informes.proveedores", ("periodo",)),
    "pruebas": ("Pruebas de laboratorio", "Exámenes, insumos que consumen y cuántos alcanzan con la existencia actual.",
                "informes.pruebas", ()),
    "productos": ("Catálogo de productos", "Código, presentación, categoría, stock mínimo y existencia de cada producto.",
                  "informes.productos", ("categoria",)),
    "bajo": ("Inventario bajo", "Productos con existencia igual o menor a su stock mínimo.",
             "reportes.inventario_bajo", ("categoria",)),
    "vencimientos": ("Vencimientos", "Lotes vencidos o que vencen en los próximos 90 días.",
                     "reportes.por_vencer", ()),
}


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


@bp.route("/")
@login_required
def index():
    """Pantalla única de reportes: el usuario elige el tipo y sus filtros."""
    hoy = dt.date.today()
    productos = query_all(
        """
        SELECT p.codigo, p.nombre FROM producto p
        WHERE EXISTS (SELECT 1 FROM lote l WHERE l.id_producto = p.id_producto)
        ORDER BY p.nombre
        """
    )
    return render_template(
        "informes/index.html", tipos=TIPOS, categorias=_categorias(), productos=productos,
        desde=hoy.replace(day=1), hasta=hoy, tipo=request.args.get("tipo", "inventario"),
    )


@bp.route("/generar")
@login_required
def generar():
    """Recibe el formulario de /informes/ y abre el reporte elegido con sus filtros."""
    tipo = request.args.get("tipo", "")
    if tipo not in TIPOS:
        flash("Elija un tipo de reporte.", "warning")
        return redirect(url_for("informes.index"))
    _, _, endpoint, filtros = TIPOS[tipo]
    args = {}
    if "periodo" in filtros or "periodo_opcional" in filtros:
        for clave in ("desde", "hasta"):
            if request.args.get(clave):
                args[clave] = request.args[clave]
    if "categoria" in filtros and request.args.get("categoria", "").isdigit():
        args["categoria"] = request.args["categoria"]
    if "agrupar_entradas" in filtros:
        args["agrupar"] = request.args.get("agrupar_entradas", "producto")
    if "agrupar_salidas" in filtros:
        args["agrupar"] = request.args.get("agrupar_salidas", "producto")
    if "producto" in filtros:
        args["producto"] = request.args.get("producto", "")
    return redirect(url_for(endpoint, **args))


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
        SELECT v.id_producto, v.codigo, v.nombre, v.categoria, v.unidad_medida AS presentacion,
               v.existencia, v.existencia_vencida,
               v.costo_promedio AS precio_unitario, v.valor_inventario AS precio_total
        FROM vw_valorizacion_inventario v
        JOIN producto p ON p.id_producto = v.id_producto
        WHERE {where}
        ORDER BY v.nombre
        """,
        params,
    )
    if _quiere_csv():
        return _csv("inventario",
                    ["Código de producto", "Producto", "Presentación", "Existencia actual",
                     "Precio unitario (Q)", "Precio total (Q)"],
                    [[f["codigo"], f["nombre"], f["presentacion"], f["existencia"],
                      f["precio_unitario"], f["precio_total"]] for f in filas])

    # Totales por categoría, de las mismas filas del reporte.
    por_categoria = {}
    for f in filas:
        c = por_categoria.setdefault(f["categoria"], {"productos": 0, "valor": 0})
        c["productos"] += 1
        c["valor"] += f["precio_total"]
    total = sum(c["valor"] for c in por_categoria.values())
    valor_vencido = sum(f["existencia_vencida"] * f["precio_unitario"] for f in filas)
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
            fechas = {k: request.args[k] for k in ("desde", "hasta") if request.args.get(k)}
            return redirect(url_for("informes.kardex", id_producto=producto["id_producto"], **fechas))
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


@bp.route("/proveedores")
@login_required
def proveedores():
    desde, hasta = _periodo()
    todos = request.args.get("todos") == "1"
    filas = query_all(
        f"""
        SELECT pr.id_proveedor, pr.nombre, pr.nit, pr.telefono, pr.correo, pr.estado,
               (SELECT count(*) FROM proveedor_producto pp WHERE pp.id_proveedor = pr.id_proveedor) AS productos,
               count(DISTINCT h.id_movimiento) AS compras,
               COALESCE(sum(h.subtotal), 0) AS total,
               max(h.fecha_hora) AS ultima_compra
        FROM proveedor pr
        LEFT JOIN lote l ON l.id_proveedor = pr.id_proveedor
        LEFT JOIN vw_historial_movimientos h
               ON h.id_lote = l.id_lote AND h.tipo_movimiento = 'ENTRADA'
              AND h.fecha_hora >= %s AND h.fecha_hora < %s
        {"" if todos else "WHERE pr.estado"}
        GROUP BY pr.id_proveedor
        ORDER BY total DESC, pr.nombre
        """,
        (desde, hasta + dt.timedelta(days=1)),
    )
    if _quiere_csv():
        return _csv("proveedores",
                    ["Proveedor", "NIT", "Teléfono", "Correo", "Estado", "Productos que suministra",
                     "Compras en el período", "Total comprado (Q)", "Última compra"],
                    [[f["nombre"], f["nit"], f["telefono"] or "", f["correo"] or "",
                      "Activo" if f["estado"] else "Inactivo", f["productos"], f["compras"], f["total"],
                      f"{f['ultima_compra']:%d/%m/%Y}" if f["ultima_compra"] else ""] for f in filas])
    return render_template(
        "informes/proveedores.html", filas=filas, desde=desde, hasta=hasta, todos=todos,
        total=sum(f["total"] for f in filas),
    )


@bp.route("/pruebas")
@login_required
def pruebas():
    filas = query_all(
        """
        SELECT e.id_examen, e.codigo_interno, e.nombre_examen, e.descripcion,
               count(ep.id_producto) AS insumos,
               min(floor(v.existencia_utilizable / ep.cantidad_requerida)) AS alcanzan,
               (SELECT v2.nombre
                  FROM examen_producto ep2
                  JOIN vw_existencia_producto v2 ON v2.id_producto = ep2.id_producto
                 WHERE ep2.id_examen = e.id_examen
                 ORDER BY floor(v2.existencia_utilizable / ep2.cantidad_requerida), v2.nombre
                 LIMIT 1) AS insumo_limitante
        FROM examen_laboratorio e
        LEFT JOIN examen_producto ep ON ep.id_examen = e.id_examen
        LEFT JOIN vw_existencia_producto v ON v.id_producto = ep.id_producto
        GROUP BY e.id_examen
        ORDER BY e.nombre_examen
        """
    )
    if _quiere_csv():
        return _csv("pruebas-de-laboratorio",
                    ["Código", "Prueba", "Descripción", "Insumos", "Alcanza para (pruebas)", "Insumo que limita"],
                    [[f["codigo_interno"], f["nombre_examen"], f["descripcion"] or "", f["insumos"],
                      f["alcanzan"] if f["alcanzan"] is not None else "", f["insumo_limitante"] or ""] for f in filas])
    return render_template("informes/pruebas.html", filas=filas)


@bp.route("/productos")
@login_required
def productos():
    id_categoria = _categoria()
    condiciones, params = [], []
    if request.args.get("todos") != "1":
        condiciones.append("e.estado")
    if id_categoria:
        condiciones.append("p.id_categoria = %s")
        params.append(id_categoria)
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    filas = query_all(
        f"""
        SELECT e.codigo, e.nombre, e.unidad_medida AS presentacion, e.categoria, e.stock_minimo,
               e.existencia_utilizable, e.existencia_vencida, e.requiere_vencimiento, e.estado
        FROM vw_existencia_producto e
        JOIN producto p ON p.id_producto = e.id_producto
        {where}
        ORDER BY e.nombre
        """,
        params,
    )
    if _quiere_csv():
        return _csv("catalogo-de-productos",
                    ["Código de producto", "Producto", "Presentación", "Categoría", "Stock mínimo",
                     "Existencia utilizable", "Existencia vencida", "Requiere vencimiento", "Estado"],
                    [[f["codigo"], f["nombre"], f["presentacion"], f["categoria"], f["stock_minimo"],
                      f["existencia_utilizable"], f["existencia_vencida"],
                      "Sí" if f["requiere_vencimiento"] else "No", "Activo" if f["estado"] else "Inactivo"]
                     for f in filas])
    return render_template(
        "informes/productos.html", filas=filas, categorias=_categorias(), id_categoria=id_categoria,
        todos=request.args.get("todos") == "1",
    )
