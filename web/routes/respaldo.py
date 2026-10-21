"""
routes/respaldo.py — Respaldo de la base de datos (RNF-11).

Solo el Administrador. La pantalla explica qué incluye el respaldo y cómo se
restaura; el botón descarga un .sql generado por respaldo.py (capa de
servicio). La restauración NO se ofrece desde la app a propósito: reemplaza
todos los datos, así que se hace con psql siguiendo el manual técnico, por
alguien con acceso al servidor de base de datos.
"""
from flask import Blueprint, Response, render_template, flash, redirect, url_for, session

import respaldo
from db import query_all
from routes.auth import rol_requerido, ADMIN

bp = Blueprint("respaldo", __name__, url_prefix="/respaldo")


@bp.route("/")
@rol_requerido(ADMIN)
def inicio():
    # Conteos con el rol del Administrador (SET ROLE), solo para informar. El
    # historial se cuenta por la vista: ningún rol lee movimiento directamente.
    tablas = query_all(
        """
        SELECT 'Productos' AS tabla, count(*) AS filas FROM producto
        UNION ALL SELECT 'Lotes', count(*) FROM lote
        UNION ALL SELECT 'Movimientos', count(DISTINCT id_movimiento) FROM vw_historial_movimientos
        UNION ALL SELECT 'Líneas de movimientos (por lote)', count(*) FROM vw_historial_movimientos
        UNION ALL SELECT 'Proveedores', count(*) FROM proveedor
        UNION ALL SELECT 'Exámenes', count(*) FROM examen_laboratorio
        UNION ALL SELECT 'Usuarios', count(id_usuario) FROM usuario
        """
    )
    return render_template("respaldo/inicio.html", tablas=tablas, archivo=respaldo.nombre_archivo())


@bp.route("/descargar", methods=["POST"])
@rol_requerido(ADMIN)
def descargar():
    try:
        contenido, _ = respaldo.generar(generado_por=session.get("nombre_usuario", "Administrador"))
    except respaldo.RespaldoError as exc:
        # A2: el mensaje de RespaldoError está escrito para el usuario; el
        # error técnico original queda encadenado en el log del servidor.
        flash(str(exc), "danger")
        return redirect(url_for("respaldo.inicio"))
    return Response(
        contenido,
        mimetype="application/sql",
        headers={"Content-Disposition": f'attachment; filename="{respaldo.nombre_archivo()}"',
                 "Cache-Control": "no-store"},
    )
