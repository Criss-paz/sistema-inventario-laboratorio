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
from flask import Flask, redirect, url_for, render_template

from config import Config
from db import close_db
from routes.auth import bp as auth_bp, login_required
from routes.categorias import bp as categorias_bp
from routes.productos import bp as productos_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.teardown_appcontext(close_db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(productos_bp)

    @app.route("/")
    @login_required
    def index():
        return redirect(url_for("categorias.listar"))

    # A2: nunca se muestra un error crudo (traceback/SQL) al usuario final.
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
