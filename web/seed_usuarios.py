"""
seed_usuarios.py — Crea los usuarios de prueba (Entrega 2).

Va separado de sql/dml/001_seed.sql a propósito: las contraseñas se
hashean aquí con werkzeug.security.generate_password_hash, la MISMA
librería que routes/auth.py usa para verificarlas en el login. Escribir un
hash "a mano" dentro de un .sql arriesga usar un formato distinto al que
la app espera y que el login nunca funcione.

Uso:
    cd web
    pip install -r requirements.txt
    python seed_usuarios.py

Es idempotente: si el usuario ya existe, lo salta en vez de duplicarlo.

*** SOLO PARA DESARROLLO ***
Estas son credenciales de prueba, claramente identificadas como tales.
Nunca deben usarse en un ambiente real ni son las credenciales reales del
laboratorio (RN-15: las contraseñas siempre se guardan hasheadas, nunca en
texto plano — el texto plano de abajo es solo lo que se escribe en el
formulario de login durante las pruebas, no lo que queda en la BD).
"""
import psycopg
from werkzeug.security import generate_password_hash

from config import Config

# usuario, password (texto plano SOLO para pruebas locales), nombre, nombre_rol
USUARIOS_PRUEBA = [
    ("admin.dev", "Admin#Dev2026", "Administrador de Prueba", "Administrador"),
    ("encargado.dev", "Encargado#Dev2026", "Encargado de Prueba", "Encargado de inventario"),
    ("consulta.dev", "Consulta#Dev2026", "Usuario de Consulta de Prueba", "Usuario de consulta"),
]


def main():
    conn = psycopg.connect(
        host=Config.DB_HOST, port=Config.DB_PORT, dbname=Config.DB_NAME,
        user=Config.DB_USER, password=Config.DB_PASSWORD,
    )
    try:
        with conn.cursor() as cur:
            for usuario, password, nombre, nombre_rol in USUARIOS_PRUEBA:
                cur.execute("SELECT 1 FROM usuario WHERE usuario = %s", (usuario,))
                if cur.fetchone():
                    print(f"  - {usuario}: ya existe, se omite.")
                    continue

                cur.execute("SELECT id_rol FROM rol WHERE nombre = %s", (nombre_rol,))
                row = cur.fetchone()
                if row is None:
                    print(f"  ! Rol '{nombre_rol}' no existe. Ejecute primero sql/dml/001_seed.sql.")
                    continue
                id_rol = row[0]

                password_hash = generate_password_hash(password)
                cur.execute(
                    "INSERT INTO usuario (id_rol, nombre, usuario, password_hash) VALUES (%s, %s, %s, %s)",
                    (id_rol, nombre, usuario, password_hash),
                )
                print(f"  + {usuario} creado (rol: {nombre_rol}).")
        conn.commit()
    finally:
        conn.close()

    print("\nCredenciales de prueba (SOLO desarrollo):")
    for usuario, password, _, nombre_rol in USUARIOS_PRUEBA:
        print(f"  usuario={usuario}  password={password}  rol={nombre_rol}")


if __name__ == "__main__":
    main()
