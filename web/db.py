"""
db.py — Capa de acceso a datos (A1: separación de capas).

Toda la app pasa por aquí para hablar con PostgreSQL. Ninguna ruta abre su
propia conexión ni concatena SQL a mano: todas las consultas se ejecutan
parametrizadas (A4 — previene inyección SQL) a través de las funciones de
este módulo.

Driver: psycopg (v3), no psycopg2 — psycopg2-binary no tiene wheel
precompilado para Python 3.14 en Windows (pide Visual C++ Build Tools);
psycopg[binary] 3.x sí, y su API es muy similar.
"""
import psycopg
from psycopg.rows import dict_row
from flask import g, current_app


def get_db():
    """Devuelve la conexión de la petición actual, creándola si no existe.

    Se guarda en `flask.g` para reutilizar la misma conexión durante toda
    la petición HTTP en vez de abrir una nueva por cada consulta.
    `row_factory=dict_row` hace que cada fila se devuelva como dict.
    """
    if "db" not in g:
        g.db = psycopg.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            dbname=current_app.config["DB_NAME"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            row_factory=dict_row,
        )
    return g.db


def close_db(e=None):
    """Cierra la conexión al terminar la petición (registrado en app.py)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_all(sql, params=None):
    """SELECT que devuelve todas las filas como lista de dicts."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def query_one(sql, params=None):
    """SELECT que devuelve una sola fila (o None) como dict."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()


def execute(sql, params=None):
    """INSERT/UPDATE/DELETE. Hace commit si todo sale bien, rollback si falla.

    Relanza la excepción para que la ruta que llamó decida cómo mostrar el
    error al usuario (A2: no se exponen errores SQL crudos en la interfaz).
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
