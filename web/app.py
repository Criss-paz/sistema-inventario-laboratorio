"""
app.py — Punto de entrada de la aplicación web (A1: separación de capas).

Solo arma la app: configuración (config.py), acceso a datos (db.py) y las
rutas (routes/*.py, cada una con su propia responsabilidad — A5). No hay
SQL ni lógica de negocio en este archivo.

Ejecutar:
    cd web
    pip install -r requirements.txt
    python app.py
"""
import datetime as dt

import psycopg
from flask import Flask, redirect, url_for, render_template

from config import Config
from db import close_db
from routes.auth import bp as auth_bp, login_required, tiene_rol, ADMIN, ENCARGADO, CONSULTA
from routes.categorias import bp as categorias_bp
from routes.productos import bp as productos_bp
from routes.proveedores import bp as proveedores_bp
from routes.lotes import bp as lotes_bp
from routes.movimientos import bp as movimientos_bp
from routes.examenes import bp as examenes_bp
from routes.reportes import bp as reportes_bp
from routes.usuarios import bp as usuarios_bp
from routes.informes import bp as informes_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.teardown_appcontext(close_db)

    for bp in (auth_bp, categorias_bp, productos_bp, proveedores_bp, lotes_bp,
               movimientos_bp, examenes_bp, reportes_bp, usuarios_bp, informes_bp):
        app.register_blueprint(bp)

    # Las plantillas deciden qué botones mostrar con tiene_rol(ADMIN, ...).
    @app.context_processor
    def roles():
        return {"tiene_rol": tiene_rol, "ADMIN": ADMIN, "ENCARGADO": ENCARGADO, "CONSULTA": CONSULTA,
                "ahora": dt.datetime.now()}

    # Montos en quetzales con separador de miles: 12,345.60
    @app.template_filter("q")
    def quetzales(valor):
        return "—" if valor is None else f"{valor:,.2f}"

    @app.route("/")
    @login_required
    def index():
        return redirect(url_for("reportes.inicio"))

    # A2: nunca se muestra un error crudo (traceback/SQL) al usuario final.
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template(
            "error.html", code=403, title="Acceso no permitido",
            message="Su rol no tiene permiso para entrar a esta página.",
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
