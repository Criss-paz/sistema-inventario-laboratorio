"""
config.py — Capa de configuración (A1: separación de capas).

Lee las variables de entorno desde el .env de la raíz del repositorio
(NUNCA se hardcodean credenciales aquí — R6/A1). Si no existe .env, usa los
valores de ejemplo de .env.example solo como referencia de nombres, no como
credenciales reales.

Dos formas de indicar la base de datos:
  - DATABASE_URL (producción: Neon la entrega así, con sslmode=require);
  - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD (instalación local).
"""
import os
from dotenv import load_dotenv, find_dotenv

# find_dotenv() busca el .env subiendo desde este archivo hasta la raíz del
# repo, así que funciona sin importar desde dónde se ejecute `flask run`.
load_dotenv(find_dotenv())


class Config:
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "inventario_laboratorio")
    DB_USER = os.environ.get("DB_USER", "usuario_app")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

    SECRET_KEY = os.environ.get("APP_SECRET", "dev-only-change-me")
    APP_ENV = os.environ.get("APP_ENV", "development")
    APP_PORT = int(os.environ.get("APP_PORT", "8080"))

    # Cookie de sesión: nunca accesible desde JavaScript; en producción, solo
    # por HTTPS (Render sirve la app con HTTPS).
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = APP_ENV == "production"


if Config.APP_ENV == "production" and Config.SECRET_KEY == "dev-only-change-me":
    # Sin una clave propia, cualquiera podría falsificar la sesión.
    raise RuntimeError("Defina APP_SECRET con una clave aleatoria antes de ejecutar en producción.")
