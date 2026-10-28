"""
routes/bitacora.py — Bitácora de auditoría: quién hizo qué y cuándo (RN-30).

Solo lectura y solo con el permiso BITACORA. Lo que se muestra lo escriben
los triggers de sql/triggers/006_bitacora.sql (cada cambio de datos) y la
app en el inicio y cierre de sesión y en la descarga de respaldos; desde
aquí no se puede modificar ni borrar nada (trg_bitacora_inmutable).

La base guarda cada cambio de forma genérica (tabla, id, fila o campos
cambiados); esta ruta lo traduce a una frase para una persona:
"Modificó el producto «ABD PAD»: stock mínimo 5 → 10".
"""
import datetime as dt

from flask import Blueprint, render_template, request, url_for

from db import query_all, query_page
from routes.auth import permiso_requerido
from routes.informes import _csv

bp = Blueprint("bitacora", __name__, url_prefix="/bitacora")

ENTIDADES = {
    "movimiento": "Movimiento", "correccion_entrada": "Corrección de entrada", "lote": "Lote",
    "producto": "Producto", "categoria": "Categoría", "proveedor": "Proveedor",
    "proveedor_producto": "Precio de proveedor", "examen_laboratorio": "Examen",
    "examen_producto": "Insumo de examen", "usuario": "Usuario", "rol": "Rol",
    "rol_permiso": "Permiso de rol", "sesion": "Sesión", "respaldo": "Respaldo",
}
ACCIONES = {
    "CREAR": ("Creó", "kraft"), "MODIFICAR": ("Modificó", "amber"), "ELIMINAR": ("Eliminó", "red"),
    "INICIAR_SESION": ("Inició sesión", "green"), "SESION_FALLIDA": ("Intento fallido", "red"),
    "CERRAR_SESION": ("Cerró sesión", "none"), "DESCARGAR_RESPALDO": ("Descargó respaldo", "blue"),
}
TIPOS = {"ENTRADA": "entrada", "SALIDA": "salida", "DEVOLUCION": "devolución"}
# Campos que no aportan a una persona (ids internos ya representados en la frase).
OCULTOS = {"id_movimiento", "id_usuario", "id_detalle", "id_correccion", "fecha_creacion"}


# Nombres de columna con tilde o más claros para una persona.
CAMPOS = {
    "descripcion": "descripción", "codigo": "código", "numero_lote": "número de lote",
    "fecha_vencimiento": "vencimiento", "fecha_ingreso": "fecha de ingreso", "nit": "NIT",
    "unidad_medida": "presentación", "stock_minimo": "stock mínimo", "precio_unitario": "precio",
    "requiere_vencimiento": "requiere vencimiento", "codigo_interno": "código interno",
    "nombre_examen": "nombre", "telefono": "teléfono", "direccion": "dirección",
    "observacion": "observación", "id_rol": "rol", "id_categoria": "categoría", "id_proveedor": "proveedor",
}


def _campo(nombre):
    return CAMPOS.get(nombre) or nombre.removeprefix("id_").replace("_", " ")


def _valor(v):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "sí" if v else "no"
    return str(v)


def _filtros():
    """WHERE y parámetros a partir de los filtros de la pantalla."""
    condiciones, params = [], []
    usuario = request.args.get("usuario", "")
    if usuario.isdigit():
        condiciones.append("b.id_usuario = %s")
        params.append(int(usuario))
    elif usuario == "sistema":
        condiciones.append("b.id_usuario IS NULL")
    entidad = request.args.get("entidad", "")
    if entidad in ENTIDADES:
        condiciones.append("b.entidad = %s")
        params.append(entidad)
    accion = request.args.get("accion", "")
    if accion in ACCIONES:
        condiciones.append("b.accion = %s")
        params.append(accion)
    q = (request.args.get("q") or "").strip()[:100]
    if q:
        condiciones.append("(b.referencia ILIKE %s OR b.detalle::text ILIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    for nombre, operador in (("desde", ">="), ("hasta", "<")):
        try:
            fecha = dt.date.fromisoformat(request.args.get(nombre, ""))
        except ValueError:
            continue
        if operador == "<":
            fecha += dt.timedelta(days=1)  # "hasta" incluye todo ese día
        condiciones.append(f"b.fecha_hora {operador} %s")
        params.append(fecha)
    return ("WHERE " + " AND ".join(condiciones)) if condiciones else "", params


def _nombres(filas):
    """Nombres para las frases: roles, permisos, productos, proveedores,
    exámenes y números de movimiento que aparecen en esta página."""
    ids = {"producto": set(), "proveedor": set(), "examen": set(), "movimiento": set()}
    for f in filas:
        if f["entidad"] in ("proveedor_producto", "examen_producto") and f["referencia"]:
            ids["producto"].add(int(f["referencia"]))
            ids["proveedor" if f["entidad"] == "proveedor_producto" else "examen"].add(int(f["id_registro"]))
        if f["entidad"] == "correccion_entrada":
            ids["movimiento"].add(int(f["id_registro"]))

    def mapa(sql, valores):
        return {r["id"]: r["nombre"] for r in query_all(sql, (sorted(valores),))} if valores else {}

    # Un rol eliminado ya no está en la tabla rol: su nombre sale de la
    # propia bitácora (el último con que se registró).
    roles = {int(r["id_registro"]): r["referencia"] for r in query_all(
        "SELECT DISTINCT ON (id_registro) id_registro, referencia FROM vw_bitacora "
        "WHERE entidad = 'rol' ORDER BY id_registro, id_bitacora DESC")}
    roles.update({r["id_rol"]: r["nombre"] for r in query_all("SELECT id_rol, nombre FROM rol")})
    return {
        "rol": roles,
        "permiso": {r["codigo"]: r["nombre"] for r in query_all("SELECT codigo, nombre FROM permiso")},
        "producto": mapa("SELECT id_producto AS id, nombre FROM producto WHERE id_producto = ANY(%s)", ids["producto"]),
        "proveedor": mapa("SELECT id_proveedor AS id, nombre FROM proveedor WHERE id_proveedor = ANY(%s)", ids["proveedor"]),
        "examen": mapa("SELECT id_examen AS id, nombre_examen AS nombre FROM examen_laboratorio WHERE id_examen = ANY(%s)",
                       ids["examen"]),
        "movimiento": mapa("SELECT DISTINCT id_movimiento AS id, numero_documento AS nombre FROM vw_historial_movimientos "
                           "WHERE id_movimiento = ANY(%s)", ids["movimiento"]),
    }


def _describir(f, n):
    """Frase, enlace y lista de cambios de una fila de la bitácora."""
    accion, tono = ACCIONES[f["accion"]]
    entidad, ref, idr, det = f["entidad"], f["referencia"] or "", f["id_registro"], f["detalle"] or {}
    que, enlace, cambios = f"{ENTIDADES.get(entidad, entidad).lower()} «{ref}»", None, []

    if entidad == "sesion":
        que = ref if f["accion"] == "SESION_FALLIDA" else ""
    elif entidad == "respaldo":
        que = ref
    elif entidad == "movimiento" and f["accion"] == "ELIMINAR":
        # Solo por mantenimiento desde la base (manual técnico, 8.4): guarda
        # el movimiento, su detalle y el motivo.
        que = f"{TIPOS.get((det.get('movimiento') or {}).get('tipo_movimiento'), 'movimiento')} {ref}"
        if det.get("motivo"):
            cambios.append(("motivo", None, det["motivo"]))
    elif entidad == "movimiento":
        accion = "Registró"
        que = f"{TIPOS.get(det.get('tipo_movimiento'), 'movimiento')} {ref}"
        enlace = url_for("movimientos.detalle", id_movimiento=int(idr))
        if det.get("observacion"):
            cambios.append(("observación", None, det["observacion"]))
    elif entidad == "correccion_entrada":
        accion = "Corrigió"
        que = f"la entrada {n['movimiento'].get(int(idr), '#' + idr)}"
        enlace = url_for("movimientos.detalle", id_movimiento=int(idr))
        cambios.append((_campo(det.get("campo", ref)), det.get("valor_anterior"), det.get("valor_nuevo")))
        cambios.append(("motivo", None, det.get("motivo")))
    elif entidad == "rol_permiso":
        accion = "Concedió" if f["accion"] == "CREAR" else "Quitó"
        rol = n["rol"].get(int(idr), f"#{idr}")
        que = f"«{n['permiso'].get(ref, ref)}» {'al' if f['accion'] == 'CREAR' else 'del'} rol {rol}"
    elif entidad in ("proveedor_producto", "examen_producto"):
        producto = n["producto"].get(int(ref), f"#{ref}") if ref else "?"
        if entidad == "proveedor_producto":
            que = f"el precio de «{producto}» con {n['proveedor'].get(int(idr), '#' + idr)}"
        else:
            que = f"el insumo «{producto}» del examen {n['examen'].get(int(idr), '#' + idr)}"
    elif entidad == "lote" and idr:
        enlace = url_for("lotes.detalle", id_lote=int(idr))
    elif entidad == "producto" and idr:
        enlace = url_for("informes.kardex", id_producto=int(idr))

    if f["accion"] == "MODIFICAR":
        cambios += [(_campo(c), None if c == "contraseña" else _valor(v.get("antes")), _valor(v.get("despues")))
                    for c, v in det.items() if c not in OCULTOS]
    elif f["accion"] in ("CREAR", "ELIMINAR") and entidad in ("proveedor_producto", "examen_producto"):
        cambios += [(_campo(c), None, _valor(v)) for c, v in det.items()
                    if c in ("precio_compra", "cantidad_requerida")]
    return {"fecha": f["fecha_hora"], "usuario": f["nombre_usuario"], "accion": accion, "tono": tono,
            "que": que, "enlace": enlace, "cambios": cambios}


@bp.route("/")
@permiso_requerido("BITACORA")
def listar():
    where, params = _filtros()
    consulta = f"SELECT b.* FROM vw_bitacora b {where} ORDER BY b.fecha_hora DESC, b.id_bitacora DESC"

    if request.args.get("formato") == "csv":
        filas = query_all(consulta + " LIMIT 20000", params)
        n = _nombres(filas)
        registros = [_describir(f, n) for f in filas]
        return _csv("bitacora", ["Fecha", "Usuario", "Acción", "Sobre", "Detalle"], [
            [f"{r['fecha']:%d/%m/%Y %H:%M:%S}", r["usuario"], r["accion"], r["que"],
             "; ".join(f"{c}: {a} → {d}" if a is not None else f"{c}: {d}" for c, a, d in r["cambios"])]
            for r in registros])

    pagina = request.args.get("pagina", "1")
    pagina = int(pagina) if pagina.isdigit() else 1
    filas, total = query_page(consulta, params, pagina)
    n = _nombres(filas)
    usuarios = query_all("SELECT id_usuario, nombre FROM usuario ORDER BY nombre")
    return render_template(
        "bitacora/list.html", registros=[_describir(f, n) for f in filas], total=total, pagina=pagina,
        usuarios=usuarios, entidades=ENTIDADES, acciones={k: v[0] for k, v in ACCIONES.items()},
        filtro=request.args,
    )
