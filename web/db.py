"""
db.py — Capa de acceso a datos (A1: separación de capas).

Toda la app pasa por aquí para hablar con PostgreSQL. Ninguna ruta abre su
propia conexión ni concatena SQL a mano: todas las consultas se ejecutan
parametrizadas (A4 — previene inyección SQL) a través de las funciones de
este módulo.

Control de acceso en la base (Entrega 3): la app se conecta como
usuario_app y, cuando hay sesión, adopta con SET ROLE el rol de base de
datos del usuario (sql/security/001_roles.sql). Así PostgreSQL aplica los
permisos aunque la interfaz tuviera un error (defensa en profundidad).

Driver: psycopg (v3), no psycopg2 — psycopg2-binary no tiene wheel
precompilado para Python 3.14 en Windows (pide Visual C++ Build Tools);
psycopg[binary] 3.x sí, y su API es muy similar.
"""
import psycopg
from psycopg import sql as pgsql
from psycopg.rows import dict_row
from flask import g, current_app, session

# Rol de la aplicación (tabla `rol`) → rol de base de datos.
ROL_BD = {
    "Administrador": "rol_administrador",
    "Encargado de inventario": "rol_encargado",
    "Usuario de consulta": "rol_consulta",
}


def get_db():
    """Devuelve la conexión de la petición actual, creándola si no existe.

    Se guarda en `flask.g` para reutilizar la misma conexión durante toda
    la petición HTTP en vez de abrir una nueva por cada consulta.
    `row_factory=dict_row` hace que cada fila se devuelva como dict.
    """
    if "db" not in g:
        conn = psycopg.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            dbname=current_app.config["DB_NAME"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            row_factory=dict_row,
        )
        if "id_usuario" in session:
            rol_bd = ROL_BD.get(session.get("nombre_rol"))
            if rol_bd is None:
                conn.close()
                # Nunca seguir con los privilegios completos de usuario_app.
                raise PermissionError("El rol de la sesión no tiene rol de base de datos.")
            conn.execute(pgsql.SQL("SET ROLE {}").format(pgsql.Identifier(rol_bd)))
            # commit inmediato: un SET dentro de una transacción que después
            # se revierte (rollback por error) se pierde junto con ella.
            conn.commit()
        g.db = conn
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


def query_page(sql, params, pagina, por_pagina=50):
    """SELECT paginado. Devuelve (filas, total) para tablas grandes
    (806 productos, ~5,800 movimientos) sin traer todo a la página."""
    pagina = max(pagina, 1)
    filas = query_all(
        f"SELECT t.*, count(*) OVER () AS total_filas FROM ({sql}) AS t LIMIT %s OFFSET %s",
        tuple(params or ()) + (por_pagina, (pagina - 1) * por_pagina),
    )
    total = filas[0]["total_filas"] if filas else 0
    return filas, total


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


def call_procedure(sql, params=None):
    """CALL a un procedimiento almacenado. Devuelve la fila de parámetros
    INOUT (por ejemplo el id del movimiento creado). Mismo manejo de
    transacción que execute()."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            fila = cur.fetchone()
        conn.commit()
        return fila
    except Exception:
        conn.rollback()
        raise


def mensaje_error(exc, por_defecto):
    """Texto que se le puede mostrar al usuario para un error de la base (A2).

    Solo se muestran los mensajes de reglas de negocio, que triggers y
    procedimientos lanzan con RAISE EXCEPTION (SQLSTATE P0001) y que están
    escritos para el usuario. Cualquier otro error se reemplaza por
    `por_defecto`: nunca se muestra SQL ni detalles técnicos.
    """
    if isinstance(exc, psycopg.errors.RaiseException):
        return exc.diag.message_primary
    if isinstance(exc, psycopg.errors.InsufficientPrivilege):
        return "Su rol no tiene permiso para realizar esta operación."
    return por_defecto
