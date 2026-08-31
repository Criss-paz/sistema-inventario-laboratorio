"""
config.py — Capa de configuración (A1: separación de capas).

Lee las variables de entorno desde el .env de la raíz del repositorio
(NUNCA se hardcodean credenciales aquí — R6/A1). Si no existe .env, usa los
valores de ejemplo de .env.example solo como referencia de nombres, no como
credenciales reales.
"""
import os
from dotenv import load_dotenv, find_dotenv

# find_dotenv() busca el .env subiendo desde este archivo hasta la raíz del
# repo, así que funciona sin importar desde dónde se ejecute `flask run`.
load_dotenv(find_dotenv())


class Config:
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "inventario_laboratorio")
    DB_USER = os.environ.get("DB_USER", "usuario_app")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

    SECRET_KEY = os.environ.get("APP_SECRET", "dev-only-change-me")
    APP_ENV = os.environ.get("APP_ENV", "development")
    APP_PORT = int(os.environ.get("APP_PORT", "8080"))
