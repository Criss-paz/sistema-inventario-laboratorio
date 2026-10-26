"""
db.py — Capa de acceso a datos (A1: separación de capas).

Toda la app pasa por aquí para hablar con PostgreSQL. Ninguna ruta abre su
propia conexión ni concatena SQL a mano: todas las consultas se ejecutan
parametrizadas (A4 — previene inyección SQL) a través de las funciones de
este módulo.

Control de acceso en la base: la app se conecta como usuario_app y, cuando
hay sesión, lee los permisos del rol del usuario (tablas permiso y
rol_permiso, RN-28) y adopta con SET ROLE el rol de PostgreSQL que los cubre
(fn_rol_bd, sql/procedures/004_permisos.sql). Así PostgreSQL aplica el nivel
de permisos aunque la interfaz tuviera un error (defensa en profundidad).
También informa en la conexión quién es el usuario (app.id_usuario), para
que los triggers de la bitácora registren al responsable (RN-30).

Driver: psycopg (v3), no psycopg2 — psycopg2-binary no tiene wheel
precompilado para Python 3.14 en Windows (pide Visual C++ Build Tools);
psycopg[binary] 3.x sí, y su API es muy similar.
"""
import psycopg
from psycopg import sql as pgsql
from psycopg.rows import dict_row
from flask import g, current_app, session

from config import Config

# Los únicos roles de PostgreSQL que la app puede adoptar.
ROLES_BD = {"rol_administrador", "rol_encargado", "rol_consulta"}


class SesionInvalida(Exception):
    """El usuario de la sesión ya no existe o fue desactivado."""


def _acceso(conn, id_usuario):
    """Rol, permisos y rol de BD del usuario, leídos como usuario_app (antes
    de SET ROLE). El Administrador tiene siempre todos los permisos (RN-29)."""
    return conn.execute(
        """
        SELECT r.id_rol, r.nombre AS rol, fn_rol_bd(r.id_rol) AS rol_bd,
               CASE WHEN r.nombre = 'Administrador' THEN ARRAY(SELECT codigo FROM permiso)
                    ELSE ARRAY(SELECT codigo FROM rol_permiso WHERE id_rol = r.id_rol) END AS permisos
        FROM usuario u JOIN rol r ON r.id_rol = u.id_rol
        WHERE u.id_usuario = %s AND u.estado
        """,
        (id_usuario,),
    ).fetchone()


def get_db():
    """Devuelve la conexión de la petición actual, creándola si no existe.

    Se guarda en `flask.g` para reutilizar la misma conexión durante toda
    la petición HTTP en vez de abrir una nueva por cada consulta.
    `row_factory=dict_row` hace que cada fila se devuelva como dict.
    """
    if "db" not in g:
        if current_app.config["DATABASE_URL"]:
            # Producción (Neon): la URL ya trae usuario, servidor y sslmode.
            conn = psycopg.connect(current_app.config["DATABASE_URL"], row_factory=dict_row)
        else:
            conn = psycopg.connect(
                host=current_app.config["DB_HOST"],
                port=current_app.config["DB_PORT"],
                dbname=current_app.config["DB_NAME"],
                user=current_app.config["DB_USER"],
                password=current_app.config["DB_PASSWORD"],
                row_factory=dict_row,
            )
        if "id_usuario" in session:
            acceso = _acceso(conn, session["id_usuario"])
            if acceso is None or acceso["rol_bd"] not in ROLES_BD:
                conn.close()
                # Nunca seguir con los privilegios completos de usuario_app.
                raise SesionInvalida()
            g.acceso = {"id_rol": acceso["id_rol"], "rol": acceso["rol"], "permisos": frozenset(acceso["permisos"])}
            conn.execute("SELECT set_config('app.id_usuario', %s, false)", (str(session["id_usuario"]),))
            conn.execute(pgsql.SQL("SET ROLE {}").format(pgsql.Identifier(acceso["rol_bd"])))
            # commit inmediato: un SET dentro de una transacción que después
            # se revierte (rollback por error) se pierde junto con ella.
            conn.commit()
        g.db = conn
    return g.db


def permisos_actuales():
    """Permisos del usuario en sesión (vacío sin sesión)."""
    if "id_usuario" not in session:
        return frozenset()
    get_db()
    return g.acceso["permisos"]


def conexion_sin_rol():
    """Conexión nueva con el usuario dueño de las tablas, SIN `SET ROLE`.

    Es la excepción documentada al control de acceso en la base: ningún rol
    de la app puede leer usuario.password_hash (sql/security/001_roles.sql),
    así que lo que necesita ese dato usa esta conexión. Solo la usan:
      - el login (antes de que exista sesión, vía get_db);
      - cambiar_contrasena (routes/auth.py), siempre sobre el usuario de la
        propia sesión, que está firmada por la app (informa app.id_usuario
        para que la bitácora registre el cambio a su nombre);
      - el respaldo (respaldo.py), restringido al Administrador y de solo
        lectura.
    Lee Config y no current_app para que respaldo.py funcione también desde
    la línea de comandos. Quien la abre la cierra (usar con `with`).
    """
    if Config.DATABASE_URL:
        return psycopg.connect(Config.DATABASE_URL, row_factory=dict_row)
    return psycopg.connect(host=Config.DB_HOST, port=Config.DB_PORT, dbname=Config.DB_NAME,
                           user=Config.DB_USER, password=Config.DB_PASSWORD, row_factory=dict_row)


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


def execute_many(sentencias):
    """Varias sentencias [(sql, params), ...] en UNA transacción: o se
    aplican todas o ninguna (por ejemplo, los permisos de un rol)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for sql, params in sentencias:
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
