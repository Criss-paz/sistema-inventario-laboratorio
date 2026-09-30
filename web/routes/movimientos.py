"""
routes/movimientos.py — Entradas, salidas e historial de inventario.
RF-20 a RF-25 (entradas, salidas con FEFO y validación de existencia),
RF-26 a RF-28 (historial con responsable y fecha), RN-01, RN-04, RN-08.
Devolución de una salida equivocada: RN-19 a RN-22 (vínculo con la salida
corregida, motivo obligatorio, reposición de existencia y tope devolvible).

Las entradas y salidas NO se insertan desde aquí: se llama a los
procedimientos sp_registrar_entrada / sp_registrar_salida, que validan las
reglas de negocio. Ningún rol de base de datos tiene INSERT sobre
movimiento, así que no hay otro camino (sql/security/001_roles.sql).
Si una regla se viola, el procedimiento o el trigger lanza un mensaje
(SQLSTATE P0001) que se muestra tal cual al usuario (db.mensaje_error).

Consultar historial: todos los roles. Registrar: Administrador y Encargado.
"""
import datetime as dt
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from db import query_all, query_one, query_page, call_procedure, mensaje_error
from routes.auth import login_required, rol_requerido, ADMIN, ENCARGADO

bp = Blueprint("movimientos", __name__, url_prefix="/movimientos")


def _productos_activos():
    """Para el buscador del formulario (datalist): código y nombre."""
    return query_all("SELECT codigo, nombre, unidad_medida FROM producto WHERE estado ORDER BY nombre")


def _producto_por_texto(texto):
    """El buscador envía "CÓDIGO — NOMBRE"; se toma el código."""
    codigo = (texto or "").split(" — ")[0].strip()
    if not codigo:
        return None
    return query_one(
        "SELECT id_producto, codigo, nombre, requiere_vencimiento FROM producto WHERE codigo = %s AND estado",
        (codigo,),
    )


def _decimal(valor, campo, errores, minimo_exclusivo=None, minimo=None):
    try:
        numero = Decimal((valor or "").strip().replace(",", "."))
    except InvalidOperation:
        errores.append(f"{campo} debe ser un número.")
        return None
    if minimo_exclusivo is not None and numero <= minimo_exclusivo:
        errores.append(f"{campo} debe ser mayor que {minimo_exclusivo}.")
    if minimo is not None and numero < minimo:
        errores.append(f"{campo} no puede ser negativo.")
    if numero.as_tuple().exponent < -2 or abs(numero) >= Decimal("100000000"):
        errores.append(f"{campo} admite hasta 8 enteros y 2 decimales.")
    return numero


@bp.route("/")
@login_required
def historial():
    tipo = request.args.get("tipo", "")
    q = (request.args.get("q") or "").strip()
    desde = request.args.get("desde", "")
    hasta = request.args.get("hasta", "")
    pagina = request.args.get("pagina", "1")
    pagina = int(pagina) if pagina.isdigit() else 1

    condiciones, params = [], []
    if tipo not in ("ENTRADA", "SALIDA"):
        tipo = ""
    if tipo:
        condiciones.append("h.tipo_movimiento = %s")
        params.append(tipo)
    if q:
        condiciones.append("(h.producto ILIKE %s OR h.codigo ILIKE %s OR h.numero_lote ILIKE %s OR pr.nombre ILIKE %s)")
        params += [f"%{q}%"] * 4
    for valor, operador in ((desde, ">="), (hasta, "<")):
        try:
            fecha = dt.date.fromisoformat(valor)
        except ValueError:
            continue
        if operador == "<":
            fecha += dt.timedelta(days=1)  # "hasta" incluye todo ese día
        condiciones.append(f"h.fecha_hora {operador} %s")
        params.append(fecha)
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    filas, total = query_page(
        f"""
        SELECT h.id_movimiento, h.fecha_hora, h.tipo_movimiento, h.nombre_usuario, h.numero_lote,
               h.id_lote, h.codigo, h.producto, h.cantidad, h.unidad_medida, h.precio_unitario,
               h.subtotal, h.observacion, pr.nombre AS proveedor
        FROM vw_historial_movimientos h
        JOIN lote l ON l.id_lote = h.id_lote
        JOIN proveedor pr ON pr.id_proveedor = l.id_proveedor
        {where}
        ORDER BY h.fecha_hora DESC, h.id_movimiento DESC, h.id_detalle
        """,
        params, pagina,
    )
    # Conteo de movimientos por tipo para las pestañas (no de líneas de detalle).
    conteo = {f["tipo_movimiento"]: f["n"] for f in query_all(
        "SELECT tipo_movimiento, count(DISTINCT id_movimiento) AS n FROM vw_historial_movimientos GROUP BY 1"
    )}
    return render_template(
        "movimientos/historial.html", filas=filas, total=total, pagina=pagina,
        tipo=tipo, q=q, desde=desde, hasta=hasta, conteo=conteo,
    )


@bp.route("/<int:id_movimiento>")
@login_required
def detalle(id_movimiento):
    detalles = query_all(
        "SELECT * FROM vw_historial_movimientos WHERE id_movimiento = %s ORDER BY id_detalle",
        (id_movimiento,),
    )
    if not detalles:
        flash("El movimiento solicitado no existe.", "warning")
        return redirect(url_for("movimientos.historial"))
    return render_template("movimientos/detalle.html", mov=detalles[0], detalles=detalles)


@bp.route("/entrada", methods=["GET", "POST"])
@rol_requerido(ADMIN, ENCARGADO)
def entrada():
    proveedores = query_all("SELECT id_proveedor, nombre FROM proveedor WHERE estado ORDER BY nombre")
    contexto = {"productos": _productos_activos(), "proveedores": proveedores, "form": request.form}
    if request.method == "GET":
        return render_template("movimientos/entrada.html", **contexto)

    errores = []
    producto = _producto_por_texto(request.form.get("producto"))
    if producto is None:
        errores.append("Seleccione un producto activo de la lista.")
    id_proveedor = request.form.get("id_proveedor", "")
    if not id_proveedor.isdigit():
        errores.append("Seleccione un proveedor.")
    numero_lote = (request.form.get("numero_lote") or "").strip()
    if not numero_lote:
        errores.append("El número de lote es obligatorio.")
    elif len(numero_lote) > 50:
        errores.append("El número de lote admite hasta 50 caracteres.")
    vence = None
    if request.form.get("fecha_vencimiento"):
        try:
            vence = dt.date.fromisoformat(request.form["fecha_vencimiento"])
        except ValueError:
            errores.append("La fecha de vencimiento no es válida.")
    cantidad = _decimal(request.form.get("cantidad"), "La cantidad", errores, minimo_exclusivo=0)
    precio = _decimal(request.form.get("precio_unitario") or "0", "El precio unitario", errores, minimo=0)
    observacion = (request.form.get("observacion") or "").strip()[:255] or None

    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("movimientos/entrada.html", **contexto), 400

    try:
        fila = call_procedure(
            "CALL sp_registrar_entrada(%s, %s, %s, %s, %s::date, %s::numeric, %s::numeric, %s, NULL)",
            (session["id_usuario"], producto["id_producto"], int(id_proveedor), numero_lote,
             vence, cantidad, precio, observacion),
        )
    except Exception as exc:
        # Aquí llegan, por ejemplo, "requiere fecha de vencimiento" (RN-07)
        # o "el lote está dado de baja", con el texto del trigger.
        flash(mensaje_error(exc, "No se pudo registrar la entrada. Intente más tarde."), "danger")
        return render_template("movimientos/entrada.html", **contexto), 400

    flash(f"Entrada registrada: {cantidad.normalize():f} de {producto['nombre']} en el lote {numero_lote}.", "success")
    return redirect(url_for("movimientos.detalle", id_movimiento=fila["p_id_movimiento"]))


@bp.route("/salida", methods=["GET", "POST"])
@rol_requerido(ADMIN, ENCARGADO)
def salida():
    contexto = {"productos": _productos_activos(), "form": request.form}
    if request.method == "GET":
        return render_template("movimientos/salida.html", **contexto)

    errores = []
    producto = _producto_por_texto(request.form.get("producto"))
    if producto is None:
        errores.append("Seleccione un producto activo de la lista.")
    cantidad = _decimal(request.form.get("cantidad"), "La cantidad", errores, minimo_exclusivo=0)
    observacion = (request.form.get("observacion") or "").strip()[:255] or None

    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("movimientos/salida.html", **contexto), 400

    try:
        fila = call_procedure(
            "CALL sp_registrar_salida(%s, %s, %s::numeric, %s, NULL)",
            (session["id_usuario"], producto["id_producto"], cantidad, observacion),
        )
    except Exception as exc:
        # RN-04: "Existencia insuficiente de ..." viene del procedimiento.
        flash(mensaje_error(exc, "No se pudo registrar la salida. Intente más tarde."), "danger")
        return render_template("movimientos/salida.html", **contexto), 400

    flash(f"Salida registrada: {cantidad.normalize():f} de {producto['nombre']}. "
          "Los lotes se eligieron por FEFO (primero el que vence antes).", "success")
    return redirect(url_for("movimientos.detalle", id_movimiento=fila["p_id_movimiento"]))


@bp.route("/<int:id_movimiento>/devolucion", methods=["GET", "POST"])
@rol_requerido(ADMIN, ENCARGADO)
def devolucion(id_movimiento):
    """Devuelve al inventario lo que sacó una salida equivocada (RN-19 a RN-22).

    No inserta nada por su cuenta: llama a sp_registrar_devolucion, que es
    quien valida el tope por lote y deja el vínculo con la salida corregida.
    Igual que entrada() y salida(), ningún rol tiene INSERT sobre movimiento.
    """
    mov = query_one(
        "SELECT id_movimiento, tipo_movimiento, fecha_hora, nombre_usuario, observacion "
        "FROM vw_historial_movimientos WHERE id_movimiento = %s LIMIT 1",
        (id_movimiento,),
    )
    if mov is None:
        flash("El movimiento solicitado no existe.", "warning")
        return redirect(url_for("movimientos.historial"))

    if mov["tipo_movimiento"] != "SALIDA":
        flash(f"Solo se puede devolver una salida. El movimiento #{id_movimiento} "
              f"es de tipo {mov['tipo_movimiento'].lower()}.", "warning")
        return redirect(url_for("movimientos.detalle", id_movimiento=id_movimiento))

    pendientes = query_all("SELECT * FROM fn_devolvible(%s)", (id_movimiento,))
    if not pendientes:
        flash(f"La salida #{id_movimiento} ya fue devuelta por completo.", "info")
        return redirect(url_for("movimientos.detalle", id_movimiento=id_movimiento))

    contexto = {"mov": mov, "pendientes": pendientes, "form": request.form}
    if request.method == "GET":
        return render_template("movimientos/devolucion.html", **contexto)

    # A3: validación en el servidor antes de tocar la base.
    errores = []
    motivo = (request.form.get("motivo") or "").strip()
    if len(motivo) < 10:
        errores.append("Explique el motivo de la devolución (al menos 10 caracteres).")
    motivo = motivo[:255]

    id_lotes, cantidades = [], []
    for fila in pendientes:
        bruto = (request.form.get(f"cantidad_{fila['id_lote']}") or "").strip()
        if not bruto:
            continue
        # Nombre en masculino a propósito: _decimal redacta "... no puede ser
        # negativo", que con "La cantidad" quedaría mal concordado.
        cantidad = _decimal(bruto, f"El total a devolver del lote {fila['numero_lote']}",
                            errores, minimo=0)
        if cantidad is None or cantidad == 0:
            continue
        if cantidad > fila["devolvible"]:
            errores.append(
                f"Del lote {fila['numero_lote']} solo quedan "
                f"{fila['devolvible'].normalize():f} por devolver.")
            continue
        id_lotes.append(fila["id_lote"])
        cantidades.append(cantidad)

    if not id_lotes and not errores:
        errores.append("Indique cuánto devolver de al menos un lote.")

    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("movimientos/devolucion.html", **contexto), 400

    try:
        fila = call_procedure(
            "CALL sp_registrar_devolucion(%s, %s, %s, %s::integer[], %s::numeric[], NULL)",
            (session["id_usuario"], id_movimiento, motivo, id_lotes, cantidades),
        )
    except Exception as exc:
        # El tope por lote (RN-22) y el resto de reglas vienen del trigger
        # o del procedimiento con su mensaje ya redactado.
        flash(mensaje_error(exc, "No se pudo registrar la devolución. Intente más tarde."), "danger")
        return render_template("movimientos/devolucion.html", **contexto), 400

    total = sum(cantidades)
    flash(f"Devolución registrada: {total.normalize():f} devuelto a "
          f"{len(id_lotes)} lote(s). La salida #{id_movimiento} queda corregida "
          "y ambos movimientos permanecen en el historial.", "success")
    return redirect(url_for("movimientos.detalle", id_movimiento=fila["p_id_movimiento"]))


@bp.route("/existencia")
@rol_requerido(ADMIN, ENCARGADO)
def existencia():
    """Ayuda del formulario de salida: existencia utilizable del producto."""
    producto = _producto_por_texto(request.args.get("producto"))
    if producto is None:
        return {"ok": False}
    fila = query_one(
        "SELECT existencia_utilizable, unidad_medida FROM vw_existencia_producto WHERE id_producto = %s",
        (producto["id_producto"],),
    )
    return {"ok": True, "existencia": float(fila["existencia_utilizable"]), "unidad": fila["unidad_medida"]}
