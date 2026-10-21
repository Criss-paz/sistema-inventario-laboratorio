"""
respaldo.py — Respaldo de los datos de la base (RNF-11). Capa de servicio:
no conoce Flask ni plantillas; la ruta routes/respaldo.py solo lo llama.

Genera un archivo .sql que se restaura con psql sobre una base que ya tiene
el esquema instalado (INSTALL.md, paso 3, sin los scripts de dml/):

    psql -v ON_ERROR_STOP=1 -d inventario_laboratorio -f respaldo_inventario_AAAAMMDD_HHMM.sql

Por qué así y no con pg_dump:
  - Render no trae pg_dump, y el que trae una imagen suele ser más viejo que
    el servidor de Neon (PostgreSQL 17), lo que pg_dump rechaza.
  - El archivo usa el mismo formato que pg_dump (bloques COPY ... FROM stdin),
    así que sigue siendo SQL estándar, legible y restaurable sin la app.
  - Solo respalda DATOS. Tablas, triggers, procedimientos, vistas y roles ya
    están versionados en sql/ y se reinstalan desde ahí.

Al restaurar, los triggers se desactivan mientras se cargan las filas: la
existencia de cada lote ya viene calculada en el respaldo, y el trigger de
historial inmutable (RN-09) no debe impedir recargar el historial completo.
Todo ocurre en una sola transacción: si algo falla, la base queda como estaba.

Uso desde la línea de comandos (por ejemplo, una tarea programada):
    cd web
    python respaldo.py ruta/del/archivo.sql
"""
import datetime as dt
import io
import sys

import psycopg
from psycopg import sql as pgsql

from db import conexion_sin_rol

# Orden de carga: cada tabla después de las que referencia con FK.
# Si el esquema gana una tabla nueva, generar() se niega a respaldar hasta
# que se agregue aquí (un respaldo incompleto es peor que ninguno).
TABLAS = (
    "rol", "usuario", "categoria", "producto", "proveedor", "lote",
    "movimiento", "detalle_movimiento", "examen_laboratorio",
    "proveedor_producto", "examen_producto",
)

# Guatemala no usa horario de verano: UTC-6 todo el año.
ZONA_GT = dt.timezone(dt.timedelta(hours=-6), "America/Guatemala")


class RespaldoError(RuntimeError):
    """El respaldo no se pudo generar. El mensaje se puede mostrar al usuario."""


def nombre_archivo(momento=None):
    momento = momento or dt.datetime.now(ZONA_GT)
    return f"respaldo_inventario_{momento:%Y%m%d_%H%M}.sql"


def _columnas(cur, tabla):
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND is_generated = 'NEVER'
        ORDER BY ordinal_position
        """,
        (tabla,),
    )
    return [fila["column_name"] for fila in cur.fetchall()]


def _columna_identidad(cur, tabla):
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND is_identity = 'YES'
        """,
        (tabla,),
    )
    fila = cur.fetchone()
    return fila["column_name"] if fila else None


def _verificar_tablas(cur):
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    en_base = {fila["tablename"] for fila in cur.fetchall()}
    faltan = en_base - set(TABLAS)
    sobran = set(TABLAS) - en_base
    if faltan or sobran:
        raise RespaldoError(
            "La lista de tablas del respaldo no coincide con la base "
            f"(sin respaldar: {', '.join(sorted(faltan)) or 'ninguna'}; "
            f"inexistentes: {', '.join(sorted(sobran)) or 'ninguna'}). Actualice web/respaldo.py."
        )


def generar(generado_por="línea de comandos"):
    """Devuelve (contenido en bytes, {tabla: filas}) con el respaldo completo.

    REPEATABLE READ + READ ONLY: todas las tablas se leen en la misma foto de
    la base, aunque alguien registre un movimiento mientras se genera.
    """
    salida = io.BytesIO()
    conteo = {}
    escribir = lambda texto: salida.write(texto.encode("utf-8"))
    try:
        # Sin SET ROLE (ver db.conexion_sin_rol): un respaldo sin las
        # contraseñas no serviría para restaurar el sistema.
        with conexion_sin_rol() as conn:
            conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
            conn.read_only = True
            with conn.cursor() as cur:
                _verificar_tablas(cur)
                cur.execute("SELECT current_database() AS base, version() AS version")
                fila = cur.fetchone()
                base, version = fila["base"], fila["version"]
                ident = {t: pgsql.Identifier(t) for t in TABLAS}

                cuerpo = io.BytesIO()
                for tabla in TABLAS:
                    columnas = _columnas(cur, tabla)
                    lista = pgsql.SQL(", ").join(map(pgsql.Identifier, columnas))
                    cur.execute(pgsql.SQL("SELECT count(*) AS filas FROM {}").format(ident[tabla]))
                    conteo[tabla] = cur.fetchone()["filas"]

                    cuerpo.write(f"\n-- {tabla}: {conteo[tabla]} filas\n".encode())
                    cuerpo.write(pgsql.SQL("COPY {} ({}) FROM stdin;\n").format(ident[tabla], lista)
                                 .as_string(conn).encode())
                    consulta = pgsql.SQL("COPY (SELECT {} FROM {} ORDER BY 1) TO STDOUT").format(lista, ident[tabla])
                    with cur.copy(consulta) as copia:
                        for bloque in copia:
                            cuerpo.write(bytes(bloque))
                    cuerpo.write(b"\\.\n")

                    identidad = _columna_identidad(cur, tabla)
                    if identidad:
                        # Que el siguiente id generado no choque con los restaurados.
                        cuerpo.write(
                            f"SELECT setval(pg_get_serial_sequence('{tabla}', '{identidad}'), "
                            f"coalesce(max({identidad}), 0) + 1, false) FROM {tabla};\n".encode()
                        )
    except RespaldoError:
        raise
    except psycopg.Error as exc:
        raise RespaldoError("No se pudo leer la base de datos para generar el respaldo.") from exc

    momento = dt.datetime.now(ZONA_GT)
    lista_tablas = ", ".join(TABLAS)
    escribir(
        "-- =============================================================================\n"
        "-- Respaldo de datos — Sistema de Inventario, Laboratorio Privado Quetzaltenango\n"
        f"-- Generado:   {momento:%d/%m/%Y %H:%M} (hora de Guatemala) por {generado_por}\n"
        f"-- Base:       {base} — {version.split(',')[0]}\n"
        f"-- Contenido:  {sum(conteo.values()):,} filas en {len(TABLAS)} tablas (solo datos)\n"
        "--\n"
        "-- RESTAURAR (reemplaza TODOS los datos actuales de la base de destino):\n"
        "--   1. La base debe tener el esquema instalado: INSTALL.md, paso 3, sin dml/.\n"
        "--   2. psql -v ON_ERROR_STOP=1 -d inventario_laboratorio -f <este archivo>\n"
        "--   En Windows, antes: $env:PGCLIENTENCODING = \"UTF8\"\n"
        "-- Corre en una sola transacción: si algo falla, la base queda como estaba.\n"
        "-- =============================================================================\n\n"
        "\\set ON_ERROR_STOP on\n"
        "SET client_encoding = 'UTF8';\n"
        "BEGIN;\n\n"
        "-- Los triggers recalcularían existencias ya calculadas y el de historial\n"
        "-- inmutable (RN-09) impediría recargar movimientos: se apagan solo durante la carga.\n"
    )
    for tabla in TABLAS:
        escribir(f"ALTER TABLE {tabla} DISABLE TRIGGER USER;\n")
    escribir(f"\nTRUNCATE {lista_tablas} RESTART IDENTITY;\n")
    salida.write(cuerpo.getvalue())
    escribir("\n")
    for tabla in TABLAS:
        escribir(f"ALTER TABLE {tabla} ENABLE TRIGGER USER;\n")
    escribir("\nCOMMIT;\n\n-- Fin del respaldo\n")
    return salida.getvalue(), conteo


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python respaldo.py ruta/del/archivo.sql")
    try:
        contenido, filas = generar()
    except RespaldoError as exc:
        sys.exit(f"Error: {exc}")
    with open(sys.argv[1], "wb") as archivo:
        archivo.write(contenido)
    print(f"Respaldo guardado en {sys.argv[1]}: {sum(filas.values()):,} filas en {len(filas)} tablas.")
