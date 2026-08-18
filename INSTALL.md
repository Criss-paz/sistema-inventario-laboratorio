# Guia de instalacion — Sistema Web de Inventario

## Requisitos previos
- SGBD instalado (MySQL, PostgreSQL o SQL Server — a definir por el equipo).
- Cliente de base de datos (linea de comandos o interfaz grafica).
- _(A completar en Entrega 2: runtime del backend y navegador para el frontend.)_

## Pasos

### 1. Clonar el repositorio
```bash
git clone <URL-del-repositorio>
cd sistema-inventario-laboratorio
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con las credenciales reales de la base de datos.
```

### 3. Crear la base de datos
_(Desde Entrega 2, ejecutar los scripts en orden:)_
```bash
# Ejemplo (se detallara al tener los scripts DDL):
# 1. sql/ddl/     -> creacion de tablas y restricciones
# 2. sql/dml/     -> datos de prueba
# 3. sql/views/   -> vistas
# 4. sql/triggers/-> triggers
# 5. sql/procedures/ -> procedimientos almacenados
# 6. sql/security/-> roles y privilegios
```

### 4. Ejecutar la aplicacion web
_(A documentar desde Entrega 2.)_

## Estado
Entrega 1: solo documentacion y diseño conceptual. La instalacion funcional se documenta a partir de la Entrega 2.
