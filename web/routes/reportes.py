"""
routes/reportes.py — Inicio y reportes del inventario.
RF-29 (inventario bajo), RF-30 (próximos a vencer), RF-31 a RF-35 (reportes
y consultas), RN-10, RN-11.

Todo sale de las vistas de sql/views/001_views.sql: la app no recalcula
existencias ni faltantes (S7). Todos los roles pueden consultar; por eso
aquí no se lee la tabla movimiento (rol_consulta solo ve la vista).
"""
import datetime as dt
import re

from flask import Blueprint, jsonify, render_template, request, url_for

from db import query_all, query_one, query_page
from routes.auth import login_required
from routes.informes import _csv

bp = Blueprint("reportes", __name__, url_prefix="/reportes")

TIPOS = {"ENTRADA": "Entrada", "SALIDA": "Salida", "DEVOLUCION": "Devolución"}


def _categorias():
    return query_all("SELECT id_categoria, nombre FROM categoria WHERE estado ORDER BY nombre")


def _pagina():
    pagina = request.args.get("pagina", "1")
    return int(pagina) if pagina.isdigit() else 1


MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre")


def _calendario(lotes, hoy):
    """Agrupa los lotes con existencia por mes de vencimiento (presentación):
    una columna de vencidos, los 12 meses desde el actual y "Después"."""
    columnas = [{"clave": "vencidos", "titulo": "Vencidos", "anio": "", "hoy": False, "lotes": []}]
    for n in range(12):
        mes = (hoy.month - 1 + n) % 12 + 1
        anio = hoy.year + (hoy.month - 1 + n) // 12
        columnas.append({"clave": (anio, mes), "titulo": MESES[mes - 1][:3],
                         "anio": str(anio)[2:] if n == 0 or mes == 1 else "", "hoy": n == 0, "lotes": []})
    columnas.append({"clave": "despues", "titulo": "Después", "anio": "", "hoy": False, "lotes": []})
    por_clave = {c["clave"]: c for c in columnas}
    for l in lotes:
        if l["dias"] < 0:
            por_clave["vencidos"]["lotes"].append(l)
        else:
            por_clave.get((l["fecha_vencimiento"].year, l["fecha_vencimiento"].month), columnas[-1])["lotes"].append(l)
    return columnas


@bp.route("/inicio")
@login_required
def inicio():
    """Panel "Bodega hoy" (diseño de SIGAL). Todas las cifras salen de las
    vistas y tablas que el rol del usuario puede leer (S7: nada se recalcula
    ni se guarda en la app)."""
    hoy = dt.date.today()
    resumen = query_one(
        """
        SELECT
          (SELECT count(*) FROM producto WHERE estado) AS productos_activos,
          (SELECT count(*) FROM vw_existencia_producto WHERE estado AND existencia_utilizable > 0) AS con_existencia,
          (SELECT coalesce(sum(valor_inventario), 0) FROM vw_valorizacion_inventario) AS valor_bodega,
          (SELECT count(*) FROM vw_lotes_por_vencer WHERE situacion = 'POR VENCER') AS lotes_por_vencer,
          (SELECT count(*) FROM vw_lotes_por_vencer WHERE situacion = 'VENCIDO') AS lotes_vencidos,
          (SELECT count(*) FROM vw_inventario_bajo b
            WHERE b.existencia_utilizable > 0
              AND EXISTS (SELECT 1 FROM lote l WHERE l.id_producto = b.id_producto)) AS bajo_minimo,
          (SELECT count(*) FROM vw_existencia_producto e
            WHERE e.estado AND e.existencia_utilizable <= 0
              AND EXISTS (SELECT 1 FROM lote l WHERE l.id_producto = e.id_producto)) AS agotados
        """
    )
    lotes = query_all(
        """
        SELECT l.id_lote, l.numero_lote, p.nombre AS producto, p.unidad_medida, l.fecha_vencimiento,
               l.cantidad_disponible, l.fecha_vencimiento - CURRENT_DATE AS dias
        FROM lote l
        JOIN producto p ON p.id_producto = l.id_producto
        WHERE l.estado AND l.cantidad_disponible > 0 AND l.fecha_vencimiento IS NOT NULL
        ORDER BY l.fecha_vencimiento, p.nombre
        """
    )
    sin_fecha = query_one(
        "SELECT count(*) AS n FROM lote WHERE estado AND cantidad_disponible > 0 AND fecha_vencimiento IS NULL"
    )["n"]
    # Reponer primero: bajo el mínimo, primero los agotados y después los que
    # más se consumen (salidas de los últimos 60 días).
    reponer = query_all(
        """
        SELECT b.id_producto, b.codigo, b.nombre, b.unidad_medida, b.stock_minimo, b.existencia_utilizable,
               coalesce(c.consumo, 0) AS consumo_60
        FROM vw_inventario_bajo b
        LEFT JOIN (SELECT id_producto, sum(cantidad) AS consumo
                     FROM vw_historial_movimientos
                    WHERE tipo_movimiento = 'SALIDA' AND fecha_hora >= CURRENT_DATE - 60
                    GROUP BY id_producto) c ON c.id_producto = b.id_producto
        WHERE EXISTS (SELECT 1 FROM lote l WHERE l.id_producto = b.id_producto)
        ORDER BY (b.existencia_utilizable > 0), coalesce(c.consumo, 0) DESC, b.nombre
        LIMIT 7
        """
    )
    actividad = query_all(
        """
        SELECT id_movimiento, numero_documento, tipo_movimiento, codigo, producto, unidad_medida,
               max(fecha_hora) AS fecha_hora, sum(cantidad) AS cantidad
        FROM vw_historial_movimientos
        WHERE fecha_hora >= CURRENT_DATE - 14
        GROUP BY id_movimiento, numero_documento, tipo_movimiento, codigo, producto, unidad_medida
        ORDER BY max(fecha_hora) DESC, id_movimiento DESC
        LIMIT 9
        """
    )
    return render_template(
        "reportes/inicio.html", resumen=resumen, calendario=_calendario(lotes, hoy), sin_fecha=sin_fecha,
        reponer=reponer, actividad=actividad, hoy=hoy, mes=MESES[hoy.month - 1],
    )


@bp.route("/buscar")
@login_required
def buscar():
    """Búsqueda rápida de la barra superior (Ctrl K): un movimiento por su
    número de documento (E1790 o E001790) y productos activos por nombre o
    código, con su existencia utilizable. Responde JSON."""
    q = (request.args.get("q") or "").strip()[:60]
    if len(q) < 2:
        return jsonify([])
    movimientos = []
    numero = re.fullmatch(r"([EeSsDd])0*(\d{1,6})", q)
    if numero:
        documento = numero.group(1).upper() + numero.group(2).zfill(6)
        movimientos = [
            {"grupo": "Movimientos", "codigo": f"{f['fecha_hora']:%d/%m/%Y}",
             "nombre": f"{TIPOS[f['tipo_movimiento']]} {f['numero_documento']}",
             "existencia": f["producto"] + (f" y {f['otros']} más" if f["otros"] else ""),
             "url": url_for("movimientos.detalle", id_movimiento=f["id_movimiento"])}
            for f in query_all(
                """
                SELECT id_movimiento, numero_documento, tipo_movimiento, min(fecha_hora) AS fecha_hora,
                       min(producto) AS producto, count(*) - 1 AS otros
                FROM vw_historial_movimientos
                WHERE numero_documento = %s
                GROUP BY id_movimiento, numero_documento, tipo_movimiento
                """,
                (documento,),
            )
        ]
    filas = query_all(
        """
        SELECT id_producto, codigo, nombre, unidad_medida, existencia_utilizable
        FROM vw_existencia_producto
        WHERE estado AND (nombre ILIKE %s OR codigo ILIKE %s)
        ORDER BY (codigo ILIKE %s) DESC, nombre
        LIMIT 12
        """,
        (f"%{q}%", f"%{q}%", f"{q}%"),
    )
    def _existencia(valor, unidad):
        """Igual que la macro con_unidad: "1 unidad", "3 unidades", "2 cajas"."""
        u = (unidad or "").lower()
        if valor != 1 and u:
            u += "s" if u[-1] in "aeiou" else "es"
        return f"{valor:,.2f}".rstrip("0").rstrip(".") + f" {u}"

    return jsonify(movimientos + [
        {"codigo": f["codigo"], "nombre": f["nombre"],
         "existencia": _existencia(f["existencia_utilizable"], f["unidad_medida"]),
         "url": url_for("informes.kardex", id_producto=f["id_producto"])}
        for f in filas
    ])


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
