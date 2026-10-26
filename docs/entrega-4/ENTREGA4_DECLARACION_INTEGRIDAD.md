# Declaración de integridad académica

**Proyecto:** Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango
**Curso:** Base de Datos — Universidad Mariano Gálvez de Guatemala
**Entrega:** Entrega 4 — Integración, documentación y defensa oral

Los integrantes del equipo declaramos que:

1. **El trabajo es nuestro.** El análisis, el modelo de datos, la base de datos, la aplicación y la documentación de este repositorio los produjo este equipo para este curso. No copiamos el trabajo de otro grupo ni lo compartimos con otro grupo.

2. **Usamos inteligencia artificial y lo documentamos.** Como permite la consigna, usamos Claude Code (Anthropic) como agente de apoyo para escribir SQL, código, pruebas y documentación. Cada uso está registrado en `docs/bitacora-ia/`: qué se pidió, qué produjo la herramienta, qué revisamos, qué corregimos o rechazamos y quién lo validó. Ningún resultado de la IA se incorporó sin revisarse y probarse contra la base de datos real (estándar S8).

3. **Entendemos y podemos defender lo entregado.** Cada integrante conoce el modelo de datos, las reglas de negocio y su implementación (triggers, procedimientos, vistas, roles), y las decisiones de diseño registradas en los documentos de cada entrega. Estamos preparados para explicarlas en la defensa grupal e individual.

4. **Los datos son reales y se usan con autorización.** El inventario cargado es el del Laboratorio Privado Quetzaltenango y se usa con fines académicos. De marzo a septiembre de 2026 proviene de los registros en papel, que el equipo pasó a Excel para la entrega del inventario trimestral; del 24/09 al 21/10/2026, del respaldo de la base de datos de SIGAL, donde el laboratorio siguió registrando con la misma numeración. Ni los Excel ni ese respaldo se publican (están excluidos por `.gitignore`), los proveedores que son personas individuales aparecen anonimizados y de los movimientos de octubre solo se conservó el área que pidió cada insumo, no el nombre de quien lo pidió.

5. **Los resultados reportados son los obtenidos.** Los casos de prueba registran lo que el sistema respondió al ejecutarse, con capturas o transcripciones. Los defectos encontrados se documentan junto con su corrección. Lo que no se cumple, o depende de una acción pendiente, se declara como tal.

6. **No publicamos credenciales.** El repositorio no contiene contraseñas reales ni el archivo `.env`, y las credenciales de producción se entregan por un canal privado.

7. **Las fuentes externas se reconocen.** Las librerías usadas (Flask, psycopg, python-dotenv, gunicorn y Werkzeug) son de código abierto y figuran en `web/requirements.txt`. Las tipografías Schibsted Grotesk y JetBrains Mono tienen licencia SIL Open Font License (`web/static/fonts/OFL.txt`).

**SIGAL** (Sistema de Gestión y Almacenaje de Laboratorio) es un proyecto del mismo integrante José Eduardo Escobar que nació de este sistema. De él se tomó:
- **El diseño de la interfaz:** colores, tipografías, estructura de pantallas, Panel, búsqueda rápida y tema oscuro. Se adaptó a las plantillas de esta aplicación.
- **Las ideas** del respaldo descargable, de las protecciones de seguridad y de guardar los permisos de cada rol como datos que el administrador edita. Aquí se implementaron de otra forma: con las tablas `permiso` y `rol_permiso` y conservando los roles de PostgreSQL como segunda capa.

Concretamente, `web/static/style.css` adapta la hoja de estilos de SIGAL (variables de color, componentes y tema oscuro) y algunos íconos de `_iconos.html` (menú, sol, luna, ojo) vienen de su juego de íconos. La lógica, las rutas, la base de datos y sus reglas de negocio son las de este proyecto. SIGAL usa otra arquitectura (FastAPI, SQLAlchemy y una página única en JavaScript), así que su código de aplicación no se reutilizó: `web/static/app.js` se escribió para estas plantillas.

---

## Firmas

| Nombre completo | Carné | Firma | Fecha |
|---|---|---|---|
| José Eduardo Escobar | 2690245346 | José Eduardo Escobar | 26/10/2026 |
| Cristopher Alexis Castellanos Paz | 2690245972 | | |
