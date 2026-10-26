"""
app.py — Punto de entrada de la aplicación web (A1: separación de capas).

Solo arma la app: configuración (config.py), acceso a datos (db.py) y las
rutas (routes/*.py, cada una con su propia responsabilidad — A5). No hay
SQL ni lógica de negocio en este archivo.

Ejecutar:
    cd web
    pip install -r requirements.txt
    python app.py                 # desarrollo
    gunicorn app:app              # producción (Render)
"""
import datetime as dt

import psycopg
from urllib.parse import urlsplit

from flask import Flask, abort, flash, redirect, request, session, url_for, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from db import close_db, get_db, SesionInvalida
from routes.auth import bp as auth_bp, login_required, tiene_permiso, ADMIN
from routes.categorias import bp as categorias_bp
from routes.productos import bp as productos_bp
from routes.proveedores import bp as proveedores_bp
from routes.lotes import bp as lotes_bp
from routes.movimientos import bp as movimientos_bp
from routes.examenes import bp as examenes_bp
from routes.reportes import bp as reportes_bp
from routes.usuarios import bp as usuarios_bp
from routes.informes import bp as informes_bp
from routes.respaldo import bp as respaldo_bp
from routes.bitacora import bp as bitacora_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    if app.config["APP_ENV"] == "production":
        # Detrás del proxy de Render: toma el esquema (https) y el host reales
        # de los encabezados X-Forwarded-*, para que las URL salgan bien.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.teardown_appcontext(close_db)

    for bp in (auth_bp, categorias_bp, productos_bp, proveedores_bp, lotes_bp,
               movimientos_bp, examenes_bp, reportes_bp, usuarios_bp, informes_bp, respaldo_bp, bitacora_bp):
        app.register_blueprint(bp)

    # Formularios solo desde esta misma app. La cookie de sesión ya es
    # SameSite=Lax (config.py), que no viaja en un POST desde otro sitio; esta
    # verificación del encabezado Origin es una segunda barrera contra CSRF.
    @app.before_request
    def mismo_origen():
        if request.method == "POST":
            origen = request.headers.get("Origin")
            if origen and urlsplit(origen).netloc != request.host:
                abort(403)

    # Si el administrador desactivó al usuario (o lo borró), su sesión deja
    # de valer en la siguiente petición, no recién cuando la cierre.
    @app.before_request
    def sesion_vigente():
        if "id_usuario" in session and request.endpoint != "static":
            try:
                get_db()
            except SesionInvalida:
                session.clear()
                flash("Su usuario ya no está activo. Consulte con el administrador.", "warning")
                return redirect(url_for("auth.login"))

    # Encabezados de seguridad en todas las respuestas (RNF-17).
    # 'unsafe-inline' en script/style: las plantillas tienen scripts cortos y
    # confirmaciones onsubmit propios; no se carga nada de otros dominios.
    @app.after_request
    def encabezados_de_seguridad(respuesta):
        respuesta.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
        )
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "DENY"
        respuesta.headers["Referrer-Policy"] = "same-origin"
        if app.config["APP_ENV"] == "production":
            respuesta.headers["Strict-Transport-Security"] = "max-age=31536000"
        return respuesta

    # Las plantillas deciden qué botones mostrar con tiene_permiso('PRODUCTOS', ...).
    @app.context_processor
    def permisos():
        return {"tiene_permiso": tiene_permiso, "ADMIN": ADMIN, "ahora": dt.datetime.now()}

    # Montos en quetzales con separador de miles: 12,345.60
    @app.template_filter("q")
    def quetzales(valor):
        return "—" if valor is None else f"{valor:,.2f}"

    # Tipo de movimiento para mostrar, con tilde (la base guarda DEVOLUCION).
    @app.template_filter("tipo_mov")
    def tipo_movimiento(valor):
        return {"ENTRADA": "Entrada", "SALIDA": "Salida", "DEVOLUCION": "Devolución"}.get(valor, valor)

    @app.route("/")
    @login_required
    def index():
        return redirect(url_for("reportes.inicio"))

    # A2: nunca se muestra un error crudo (traceback/SQL) al usuario final.
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template(
            "error.html", code=403, title="Acceso no permitido",
            message="Su rol no tiene permiso para esta acción. Si lo necesita, pídale al administrador que se lo conceda en Usuarios y roles.",
        ), 403

    # Segunda capa: si la app dejara pasar algo, PostgreSQL lo niega (SET ROLE).
    @app.errorhandler(psycopg.errors.InsufficientPrivilege)
    def forbidden_db(_e):
        return forbidden(_e)

    @app.errorhandler(404)
    def not_found(_e):
        return render_template(
            "error.html", code=404, title="Página no encontrada",
            message="La dirección que buscas no existe o fue movida.",
        ), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template(
            "error.html", code=500, title="Error interno",
            message="Ocurrió un problema inesperado. Intenta de nuevo en unos minutos.",
        ), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["APP_PORT"], debug=(app.config["APP_ENV"] == "development"))
