"""
routes/movimientos.py — Entradas, salidas e historial de inventario.
RF-20 a RF-25 (entradas, salidas con FEFO y validación de existencia),
RF-26 a RF-28 (historial con responsable y fecha), RN-01, RN-04, RN-08.
Devolución de una salida equivocada: RN-19 a RN-22 (vínculo con la salida
corregida, motivo obligatorio, reposición de existencia y tope devolvible).
Corrección de una entrada mal digitada: RN-25 y RN-26 (la entrada no se
borra; cada campo corregido queda registrado con su motivo). Eliminación de
una entrada registrada por error: RN-31 (solo el Administrador, si ninguna
de sus unidades salió; el lote se ajusta y queda en la bitácora).

Las entradas y salidas NO se insertan desde aquí: se llama a los
procedimientos sp_registrar_entrada / sp_registrar_salida, que validan las
reglas de negocio. Ningún rol de base de datos tiene INSERT sobre
movimiento, así que no hay otro camino (sql/security/001_roles.sql).
Si una regla se viola, el procedimiento o el trigger lanza un mensaje
(SQLSTATE P0001) que se muestra tal cual al usuario (db.mensaje_error).

Consultar historial: todos los roles. Registrar entradas, salidas y
devoluciones y corregir entradas: según los permisos del rol (RN-28).
"""
import datetime as dt
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from db import query_all, query_one, query_page, call_procedure, mensaje_error
from routes.auth import login_required, permiso_requerido, solo_administrador

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


def _numero(id_movimiento):
    """Número de documento (E000001, S000001, D000001) de un movimiento: RN-27."""
    fila = query_one("SELECT numero_documento FROM vw_historial_movimientos WHERE id_movimiento = %s LIMIT 1",
                     (id_movimiento,))
    return fila["numero_documento"] if fila else f"#{id_movimiento}"


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
    if tipo not in ("ENTRADA", "SALIDA", "DEVOLUCION"):
        tipo = ""
    if tipo:
        condiciones.append("h.tipo_movimiento = %s")
        params.append(tipo)
    if q:
        condiciones.append("(h.numero_documento ILIKE %s OR h.producto ILIKE %s OR h.codigo ILIKE %s "
                           "OR h.numero_lote ILIKE %s OR pr.nombre ILIKE %s)")
        params += [f"%{q}%"] * 5
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
        SELECT h.id_movimiento, h.numero_documento, h.fecha_hora, h.tipo_movimiento, h.nombre_usuario, h.numero_lote,
               h.id_lote, h.id_producto, h.codigo, h.producto, h.cantidad, h.unidad_medida, h.precio_unitario,
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

    # Salidas y devoluciones no guardan precio (sería calculable, S7): se
    # valorizan al costo promedio móvil del kardex. Se resuelve solo para los
    # movimientos de esta página — medido en 44 ms para 50 filas — y se indexa
    # por (movimiento, producto), que es lo que identifica a cada línea.
    costos = {}
    ids = sorted({f["id_movimiento"] for f in filas
                  if f["tipo_movimiento"] != "ENTRADA"})
    if ids:
        for fila in query_all(
            """
            SELECT k.id_movimiento, k.id_producto,
                   coalesce(k.costo_unitario_salida, k.costo_unitario_entrada) AS costo
              FROM (SELECT DISTINCT id_producto
                      FROM vw_historial_movimientos
                     WHERE id_movimiento = ANY(%s)) p
              CROSS JOIN LATERAL fn_kardex_promedio(p.id_producto) k
             WHERE k.id_movimiento = ANY(%s)
            """,
            (ids, ids),
        ):
            costos[(fila["id_movimiento"], fila["id_producto"])] = fila["costo"]

    return render_template(
        "movimientos/historial.html", filas=filas, total=total, pagina=pagina,
        tipo=tipo, q=q, desde=desde, hasta=hasta, conteo=conteo, costos=costos,
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

    # Solo las ENTRADAS guardan precio: es el de la factura del proveedor.
    # Las salidas y devoluciones no lo guardan (sería un dato calculable, S7):
    # se valorizan al costo promedio ponderado móvil vigente ese día, que
    # calcula fn_kardex_promedio. Sin esto la pantalla mostraba "0.00".
    costos = {}
    if detalles[0]["tipo_movimiento"] != "ENTRADA":
        for fila in query_all(
            """
            SELECT k.id_producto,
                   coalesce(k.costo_unitario_salida, k.costo_unitario_entrada) AS costo
              FROM (SELECT DISTINCT id_producto
                      FROM vw_historial_movimientos
                     WHERE id_movimiento = %s) p
              CROSS JOIN LATERAL fn_kardex_promedio(p.id_producto) k
             WHERE k.id_movimiento = %s
            """,
            (id_movimiento, id_movimiento),
        ):
            costos[fila["id_producto"]] = fila["costo"]

    correcciones = query_all(
        "SELECT * FROM vw_correcciones_entrada WHERE id_movimiento = %s ORDER BY fecha_hora, id_correccion",
        (id_movimiento,),
    )
    return render_template("movimientos/detalle.html", mov=detalles[0],
                           detalles=detalles, costos=costos, correcciones=correcciones)


@bp.route("/entrada", methods=["GET", "POST"])
@permiso_requerido("REGISTRAR_ENTRADAS")
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

    flash(f"Entrada {_numero(fila['p_id_movimiento'])} registrada: {cantidad.normalize():f} de "
          f"{producto['nombre']} en el lote {numero_lote}.", "success")
    return redirect(url_for("movimientos.detalle", id_movimiento=fila["p_id_movimiento"]))


@bp.route("/salida", methods=["GET", "POST"])
@permiso_requerido("REGISTRAR_SALIDAS")
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

    flash(f"Salida {_numero(fila['p_id_movimiento'])} registrada: {cantidad.normalize():f} de {producto['nombre']}. "
          "Los lotes se eligieron por FEFO (primero el que vence antes).", "success")
    return redirect(url_for("movimientos.detalle", id_movimiento=fila["p_id_movimiento"]))


@bp.route("/<int:id_movimiento>/devolucion", methods=["GET", "POST"])
@permiso_requerido("DEVOLVER_SALIDAS")
def devolucion(id_movimiento):
    """Devuelve al inventario lo que sacó una salida equivocada (RN-19 a RN-22).

    No inserta nada por su cuenta: llama a sp_registrar_devolucion, que es
    quien valida el tope por lote y deja el vínculo con la salida corregida.
    Igual que entrada() y salida(), ningún rol tiene INSERT sobre movimiento.
    """
    mov = query_one(
        "SELECT id_movimiento, numero_documento, tipo_movimiento, fecha_hora, nombre_usuario, observacion "
        "FROM vw_historial_movimientos WHERE id_movimiento = %s LIMIT 1",
        (id_movimiento,),
    )
    if mov is None:
        flash("El movimiento solicitado no existe.", "warning")
        return redirect(url_for("movimientos.historial"))

    if mov["tipo_movimiento"] != "SALIDA":
        flash(f"Solo se puede devolver una salida. El movimiento {mov['numero_documento']} "
              f"es de tipo {mov['tipo_movimiento'].lower()}.", "warning")
        return redirect(url_for("movimientos.detalle", id_movimiento=id_movimiento))

    pendientes = query_all("SELECT * FROM fn_devolvible(%s)", (id_movimiento,))
    if not pendientes:
        flash(f"La salida {mov['numero_documento']} ya fue devuelta por completo.", "info")
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
    flash(f"Devolución {_numero(fila['p_id_movimiento'])} registrada: {total.normalize():f} devuelto a "
          f"{len(id_lotes)} lote(s). La salida {mov['numero_documento']} queda corregida "
          "y ambos movimientos permanecen en el historial.", "success")
    return redirect(url_for("movimientos.detalle", id_movimiento=fila["p_id_movimiento"]))


@bp.route("/<int:id_movimiento>/corregir", methods=["GET", "POST"])
@permiso_requerido("CORREGIR_ENTRADAS")
def corregir(id_movimiento):
    """Corrige una entrada mal digitada sin borrarla (RN-25, RN-26).

    Solo valida el formulario y llama a sp_corregir_entrada, que registra
    cada campo corregido en correccion_entrada y ajusta la existencia del
    lote. Los campos que no cambian se envían como NULL (no se tocan).
    """
    entrada = query_one(
        """
        SELECT h.id_movimiento, h.numero_documento, h.tipo_movimiento, h.fecha_hora, h.nombre_usuario,
               h.observacion, h.codigo, h.producto, h.unidad_medida, h.cantidad, h.precio_unitario,
               l.id_lote, l.numero_lote, l.id_proveedor, l.fecha_ingreso, l.fecha_vencimiento,
               l.cantidad_disponible, p.requiere_vencimiento,
               (SELECT count(*) FROM vw_historial_movimientos o
                 WHERE o.id_lote = l.id_lote AND o.tipo_movimiento = 'ENTRADA') AS entradas_del_lote
        FROM vw_historial_movimientos h
        JOIN lote l ON l.id_lote = h.id_lote
        JOIN producto p ON p.id_producto = h.id_producto
        WHERE h.id_movimiento = %s
        """,
        (id_movimiento,),
    )
    if entrada is None:
        flash("El movimiento solicitado no existe.", "warning")
        return redirect(url_for("movimientos.historial"))
    if entrada["tipo_movimiento"] != "ENTRADA":
        flash("Solo se pueden corregir entradas. Una salida equivocada se corrige con una devolución.", "warning")
        return redirect(url_for("movimientos.detalle", id_movimiento=id_movimiento))

    proveedores = query_all(
        "SELECT id_proveedor, nombre FROM proveedor WHERE estado OR id_proveedor = %s ORDER BY nombre",
        (entrada["id_proveedor"],),
    )
    contexto = {"e": entrada, "proveedores": proveedores, "form": request.form}
    if request.method == "GET":
        return render_template("movimientos/corregir.html", **contexto)

    # A3: validación en el servidor antes de tocar la base.
    errores = []
    motivo = (request.form.get("motivo") or "").strip()[:255]
    if len(motivo) < 10:
        errores.append("Explique el motivo de la corrección (al menos 10 caracteres).")
    cantidad = _decimal(request.form.get("cantidad"), "La cantidad", errores, minimo_exclusivo=0)
    precio = _decimal(request.form.get("precio_unitario"), "El precio unitario", errores, minimo=0)
    numero_lote = (request.form.get("numero_lote") or "").strip()
    if not numero_lote or len(numero_lote) > 50:
        errores.append("El número de lote es obligatorio (máximo 50 caracteres).")
    id_proveedor = request.form.get("id_proveedor", "")
    if not id_proveedor.isdigit():
        errores.append("Seleccione el proveedor.")
    vence_txt = (request.form.get("fecha_vencimiento") or "").strip()
    vence = None
    if vence_txt:
        try:
            vence = dt.date.fromisoformat(vence_txt)
        except ValueError:
            errores.append("La fecha de vencimiento no es válida.")
    elif entrada["fecha_vencimiento"] is not None:
        errores.append("La fecha de vencimiento no se puede dejar vacía; corríjala o déjela como está.")
    if errores:
        for e in errores:
            flash(e, "danger")
        return render_template("movimientos/corregir.html", **contexto), 400

    # Solo se envía lo que cambió; el procedimiento ignora los NULL.
    def cambio(nuevo, actual):
        return None if nuevo == actual else nuevo

    try:
        fila = call_procedure(
            "CALL sp_corregir_entrada(%s, %s, %s, %s, %s, %s, %s, %s, NULL)",
            (session["id_usuario"], id_movimiento, motivo,
             cambio(cantidad, entrada["cantidad"]), cambio(precio, entrada["precio_unitario"]),
             cambio(int(id_proveedor), entrada["id_proveedor"]), cambio(numero_lote, entrada["numero_lote"]),
             cambio(vence, entrada["fecha_vencimiento"])),
        )
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo corregir la entrada. Intente más tarde."), "danger")
        return render_template("movimientos/corregir.html", **contexto), 400

    n = fila["p_cambios"]
    flash(f"Entrada {entrada['numero_documento']} corregida: {n} {'dato' if n == 1 else 'datos'}. "
          "El registro original y la corrección quedan en el historial.", "success")
    return redirect(url_for("movimientos.detalle", id_movimiento=id_movimiento))


@bp.route("/<int:id_movimiento>/eliminar", methods=["GET", "POST"])
@solo_administrador
def eliminar(id_movimiento):
    """Elimina una entrada registrada por error (RN-31).

    Solo muestra lo que pasará y pide el motivo: sp_eliminar_entrada vuelve
    a validar todo (rol, tipo, correcciones, unidades ya consumidas), deja la
    constancia en la bitácora y ajusta el lote en una sola transacción.
    """
    lineas = query_all(
        """
        SELECT h.id_movimiento, h.numero_documento, h.tipo_movimiento, h.fecha_hora, h.nombre_usuario,
               h.codigo, h.producto, h.unidad_medida, h.cantidad, h.id_lote, h.numero_lote,
               l.cantidad_disponible,
               (SELECT count(*) FROM vw_historial_movimientos o WHERE o.id_lote = h.id_lote) AS movimientos_del_lote,
               (SELECT count(*) FROM vw_correcciones_entrada c WHERE c.id_movimiento = h.id_movimiento) AS correcciones
        FROM vw_historial_movimientos h
        JOIN lote l ON l.id_lote = h.id_lote
        WHERE h.id_movimiento = %s
        ORDER BY h.id_detalle
        """,
        (id_movimiento,),
    )
    if not lineas:
        flash("El movimiento solicitado no existe.", "warning")
        return redirect(url_for("movimientos.historial"))
    e = lineas[0]
    if e["tipo_movimiento"] != "ENTRADA":
        flash("Solo se eliminan entradas. Una salida equivocada se corrige con una devolución.", "warning")
        return redirect(url_for("movimientos.detalle", id_movimiento=id_movimiento))

    # Lo mismo que valida el procedimiento, para avisar antes de intentarlo.
    bloqueos = []
    if e["correcciones"]:
        bloqueos.append("Tiene correcciones registradas. Si sobra cantidad, corríjala en lugar de eliminarla.")
    for ln in lineas:
        if ln["cantidad_disponible"] < ln["cantidad"]:
            bloqueos.append(f"Del lote {ln['numero_lote']} ya salieron "
                            f"{(ln['cantidad'] - ln['cantidad_disponible']).normalize():f} de las "
                            f"{ln['cantidad'].normalize():f} que sumó esta entrada.")
    contexto = {"e": e, "lineas": lineas, "bloqueos": bloqueos, "form": request.form}
    if request.method == "GET":
        return render_template("movimientos/eliminar.html", **contexto)

    motivo = (request.form.get("motivo") or "").strip()[:255]
    if len(motivo) < 10:
        flash("Explique el motivo de la eliminación (al menos 10 caracteres).", "danger")
        return render_template("movimientos/eliminar.html", **contexto), 400
    if bloqueos:
        for b in bloqueos:
            flash(b, "danger")
        return render_template("movimientos/eliminar.html", **contexto), 400

    try:
        fila = call_procedure("CALL sp_eliminar_entrada(%s, %s, %s, NULL)",
                              (session["id_usuario"], id_movimiento, motivo))
    except Exception as exc:
        flash(mensaje_error(exc, "No se pudo eliminar la entrada. Intente más tarde."), "danger")
        return render_template("movimientos/eliminar.html", **contexto), 400

    ajustes = "; ".join(
        f"el lote {ln['numero_lote']} " + ("se eliminó (no tenía otros movimientos)"
                                           if ln["movimientos_del_lote"] == 1 else
                                           f"bajó a {(ln['cantidad_disponible'] - ln['cantidad']).normalize():f}")
        for ln in lineas)
    flash(f"Entrada {e['numero_documento']} eliminada: {ajustes}. Queda registrada en la bitácora.", "success")
    return redirect(url_for("movimientos.historial", tipo="ENTRADA"))


@bp.route("/existencia")
@permiso_requerido("REGISTRAR_SALIDAS")
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
