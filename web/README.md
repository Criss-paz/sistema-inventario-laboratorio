# web

Aplicación web del sistema: Flask 3 + PostgreSQL 18 (driver `psycopg` v3).

**Estado:** implementada al 70% (Entrega 3). El detalle de módulos, roles y pruebas está en `AVANCE_WEB.md`, en la raíz del repositorio.

## Estructura

| Carpeta o archivo | Responsabilidad |
|---|---|
| `app.py` | Arma la aplicación: registra los módulos, los permisos para las plantillas y las páginas de error 403, 404 y 500 |
| `config.py` | Lee la configuración desde `.env` (nunca credenciales en el código) |
| `db.py` | Único acceso a PostgreSQL: adopta el rol de BD del usuario (`SET ROLE`), consultas parametrizadas, paginación, llamadas a procedimientos y mensajes de error para el usuario |
| `routes/` | Un módulo por área: `auth`, `movimientos`, `lotes`, `productos`, `examenes`, `proveedores`, `categorias`, `informes` (reportes), `reportes` (inicio y alertas), `usuarios` |
| `templates/` | Plantillas por módulo, más `base.html` (menú lateral), `_macros.html` y `_iconos.html` |
| `static/` | Estilos, fuentes Atkinson Hyperlegible (licencia OFL) y favicon |
| `seed_usuarios.py` | Crea los 3 usuarios de prueba con contraseña con hash |

## Ejecutar

```bash
cd web
pip install -r requirements.txt
python seed_usuarios.py   # solo la primera vez
python app.py             # http://localhost:8080
```

Instalación completa desde cero: `INSTALL.md`.
