# Guía de instalación — Sistema Web de Inventario

Estado: instrucciones reales desde la Entrega 2 (BD PostgreSQL + app web Flask con login y 2 CRUD). Triggers, procedimientos y roles a nivel de motor se agregan en la Entrega 3.

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

(Los roles diferenciados a nivel de motor — mínimo 3 con privilegios distintos — se agregan en `sql/security/` en la Entrega 3. Por ahora `usuario_app` es el único rol de conexión.)

## 3. Ejecutar los scripts SQL en orden
```bash
psql -U usuario_app -d inventario_laboratorio -f sql/ddl/001_schema.sql
psql -U usuario_app -d inventario_laboratorio -f sql/dml/001_seed.sql
```
Orden general para el resto del proyecto (aún no existen todos):
1. `sql/ddl/` — creación de tablas y restricciones (✅ ya existe: `001_schema.sql`)
2. `sql/dml/` — datos de prueba (✅ ya existe: `001_seed.sql`, sin usuarios — ver paso 5)
3. `sql/views/` — vistas (Entrega 3)
4. `sql/triggers/` — triggers (Entrega 3)
5. `sql/procedures/` — procedimientos (Entrega 3)
6. `sql/security/` — roles y privilegios del motor (Entrega 3)

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
| `relation "categoria" does not exist` | No se ejecutó `001_schema.sql` | Repetir el paso 3 |
| Login siempre dice "Usuario o contraseña incorrectos" | No se ejecutó `seed_usuarios.py`, o se insertó un usuario a mano con un hash inválido | Ejecutar `python seed_usuarios.py`; nunca escribir `password_hash` a mano |
| `ModuleNotFoundError: No module named 'flask'` | No se instalaron dependencias en el entorno activo | `pip install -r web/requirements.txt` dentro del entorno correcto |
