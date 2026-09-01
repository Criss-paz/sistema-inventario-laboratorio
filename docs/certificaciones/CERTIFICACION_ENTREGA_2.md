# Certificación de Calidad — Entrega 2

**Proyecto:** Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango
**Entrega:** Entrega 2 — Diseño lógico, diccionario e implementación base
**Fecha:** 01/09/2026

Por medio de la presente, los integrantes del equipo hacemos constar que la documentación y el código correspondientes a la **Entrega 2** fueron revisados previamente a su presentación. Estado real de cada punto, sin inflar nada:

- [x] Cumplimos la estructura de carpetas obligatoria (Sección 7 de la consigna oficial).
- [x] Cumplimos los estándares del repositorio (Sección 6.1): R1 estructura, R2 README, R3 commits descriptivos, R4 participación visible de ambos integrantes, R5 tag `entrega-2`, R6 sin credenciales, R7 `.gitignore`, R8 acceso del catedrático.
- [x] Cumplimos los estándares SQL (Sección 6.2): snake_case, un script por propósito, encabezado con autor/descripción/dependencias en cada archivo, FK con ON DELETE/ON UPDATE documentadas, sin redundancia (normalización 3FN demostrada).
- [x] Cumplimos los estándares de aplicación web aplicables ya en esta entrega (Sección 6.3): separación de capas (config/db/rutas/plantillas), consultas parametrizadas, manejo de errores sin exponer SQL crudo, validación de entrada. (El checklist oficial marca el bloque completo de estándares de app para Entrega 4 — aquí se adelantó lo que ya corresponde a esta entrega.)
- [x] La bitácora de IA está actualizada (`docs/entrega-2/Bitacora-IA.md`).
- [x] **Los casos de prueba fueron ejecutados y documentados** — los 15 casos de `docs/casos-prueba/casos-prueba-entrega-2.md` se ejecutaron el 30/08/2026 contra PostgreSQL 18 + Python 3.14 reales (login, CRUD de categorías/productos, validaciones, duplicados, persistencia tras reinicio del servidor). 15/15 pasaron.
- [x] No hay credenciales expuestas en el repositorio: `.env` no se versiona (`.gitignore`, y se agregó `.venv/` que faltaba), `.env.example` solo tiene placeholders, y las credenciales de prueba en `seed_usuarios.py` están marcadas explícitamente como de desarrollo.

Antes de firmar se ejecutó una auditoría de cierre contra la consigna oficial (01/09/2026), registrada en `docs/entrega-2/Bitacora-IA.md`. Los hallazgos que afectaban esta certificación —la incoherencia del diagrama ER con el DDL y las rutas rotas en `README.md` y en el encabezado de `sql/dml/001_seed.sql`— quedaron corregidos antes de crear el tag `entrega-2`.

---

## Firmas
Se dio el visto bueno para la entrega de este proyecto; ambos integrantes revisamos el contenido listado arriba.

| Nombre completo | Carné | Firma |
|---|---|---|
| Cristopher Alexis Castellanos Paz | 2690245972 | X |
| José Eduardo Escobar | 2690245346 | X |


