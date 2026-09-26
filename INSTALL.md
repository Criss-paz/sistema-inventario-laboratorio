# Guía de instalación — Sistema Web de Inventario

Estado: actualizado en la Entrega 3 (BD con triggers, procedimientos, vistas y 3 roles de motor + app web Flask).

## Requisitos previos
- PostgreSQL 14 o superior.
- Python 3.10 o superior con `pip`.
- Cliente de base de datos (`psql` o una GUI como pgAdmin/DBeaver) — opcional pero recomendado para verificar.

## 1. Clonar el repositorio
```bash
git clone <URL-del-repositorio>
cd sistema-inventario-laboratorio
```

## 2. Crear la base de datos
```bash
psql -U postgres -c "CREATE DATABASE inventario_laboratorio;"
psql -U postgres -c "CREATE USER usuario_app WITH PASSWORD 'elija-una-contrasena-local';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE inventario_laboratorio TO usuario_app;"
psql -U postgres -d inventario_laboratorio -c "GRANT ALL ON SCHEMA public TO usuario_app;"
```
El último comando es necesario en **PostgreSQL 15 o superior**: desde esa versión, el schema `public` ya no da permiso de `CREATE` a un usuario que no sea el dueño de la base — sin ese `GRANT`, el DDL del siguiente paso falla con `permission denied for schema public`.

`usuario_app` es el único usuario con el que se conecta la app. Los 3 roles de motor con privilegios diferenciados se crean en el paso 3 (`sql/security/`) y la app los adopta con `SET ROLE` después del login.

## 3. Ejecutar los scripts SQL en orden
```bash
psql -U usuario_app -d inventario_laboratorio -f sql/ddl/001_schema.sql
psql -U usuario_app -d inventario_laboratorio -f sql/triggers/001_triggers.sql
psql -U usuario_app -d inventario_laboratorio -f sql/procedures/001_procedures.sql
psql -U usuario_app -d inventario_laboratorio -f sql/views/001_views.sql
psql -U usuario_app -d inventario_laboratorio -f sql/dml/001_seed.sql
psql -U usuario_app -d inventario_laboratorio -f sql/dml/002_carga_catalogo.sql
psql -U usuario_app -d inventario_laboratorio -f sql/dml/003_seed_examenes.sql
python web/seed_usuarios.py          # requiere el paso 4 (.env) y las dependencias del paso 5
psql -U usuario_app -d inventario_laboratorio -f sql/dml/004_carga_movimientos.sql
psql -U postgres    -d inventario_laboratorio -f sql/security/001_roles.sql
```
Por qué este orden:
1. `ddl/` — tablas y restricciones.
2. `triggers/` — **antes** del seed, para que las reglas de negocio (RN-07, existencias) se apliquen también a los datos de prueba.
3. `procedures/` — dependen de las tablas y de los triggers.
4. `views/` — solo dependen de las tablas.
5. `dml/001` a `003` — catálogos: 806 productos y 26 proveedores reales del laboratorio (+24 de prueba inactivos), 50 exámenes.
6. `seed_usuarios.py` — usuarios con contraseña hasheada por la app; los movimientos necesitan un responsable (RN-08).
7. `dml/004` — el inventario real de marzo a septiembre de 2026: 1,188 lotes y 5,839 movimientos, con la existencia calculada por los triggers (tarda unos segundos).
8. `security/` — **como `postgres`**: crear roles requiere superusuario. Va al final porque otorga permisos sobre tablas, vistas y procedimientos que ya deben existir.

En Windows, si `psql` no está en el PATH, use la ruta completa: `& "C:\Program Files\PostgreSQL\18\bin\psql.exe" ...`

## 4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env: DB_HOST, DB_PORT (5432 para PostgreSQL), DB_NAME, DB_USER, DB_PASSWORD,
# y APP_SECRET (una cadena aleatoria — la usa Flask para firmar la sesión de login).
```

## 5. Instalar dependencias e inicializar usuarios de prueba
```bash
cd web
pip install -r requirements.txt
python seed_usuarios.py
```
Esto crea 3 usuarios de desarrollo (uno por rol) con contraseña hasheada correctamente. El script imprime las credenciales de prueba al final — **son solo para desarrollo, nunca credenciales reales**.

## 6. Ejecutar la aplicación web
```bash
# desde la carpeta web/, con el entorno virtual activo
python app.py
```
Abrir `http://localhost:8080` (o el valor de `APP_PORT` en `.env`) e iniciar sesión con uno de los usuarios impresos en el paso 5.

## 7. Verificación rápida
- [ ] `psql` conecta a `inventario_laboratorio` sin error.
- [ ] `\dt` en `psql` muestra las 11 tablas.
- [ ] El login funciona con `admin.dev` y rechaza una contraseña incorrecta.
- [ ] El módulo Categorías lista, crea, edita y desactiva un registro.
- [ ] El módulo Productos lista, crea, edita y desactiva un registro, y su categoría viene de la tabla `categoria` (no texto libre).
- [ ] Cerrar sesión redirige al login y bloquea el acceso directo a `/productos` sin sesión.

## Solución de errores frecuentes
| Síntoma | Causa probable | Solución |
|---|---|---|
| `psycopg.OperationalError: connection refused` | PostgreSQL no está corriendo o el puerto en `.env` no es 5432 | Verificar el servicio de PostgreSQL y el valor de `DB_PORT` |
| `permission denied for schema public` al correr `001_schema.sql` | Falta el `GRANT ALL ON SCHEMA public` del paso 2 (PostgreSQL 15+ ya no lo da por defecto) | Repetir el último comando del paso 2 |
| Falla instalando `psycopg2-binary` pidiendo "Microsoft Visual C++ 14.0" | No hay wheel precompilado de psycopg2 para tu versión de Python (pasa con Python muy nuevo, p. ej. 3.14) | Ya migrado: el proyecto usa `psycopg[binary]` (psycopg 3), que sí trae wheel — asegúrate de tener la versión actual de `requirements.txt` |
| `role "rol_consulta" does not exist` o `permiso denegado` al usar la app | No se ejecutó `sql/security/001_roles.sql` como `postgres` | Repetir el último comando del paso 3 con `-U postgres` |
| `relation "categoria" does not exist` | No se ejecutó `001_schema.sql` | Repetir el paso 3 |
| Login siempre dice "Usuario o contraseña incorrectos" | No se ejecutó `seed_usuarios.py`, o se insertó un usuario a mano con un hash inválido | Ejecutar `python seed_usuarios.py`; nunca escribir `password_hash` a mano |
| `ModuleNotFoundError: No module named 'flask'` | No se instalaron dependencias en el entorno activo | `pip install -r web/requirements.txt` dentro del entorno correcto |
