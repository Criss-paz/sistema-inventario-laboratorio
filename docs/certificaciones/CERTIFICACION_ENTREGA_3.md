# Certificación de Calidad — Entrega 3

**Proyecto:** Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango
**Entrega:** Entrega 3 — Implementación avanzada, seguridad y pruebas
**Fecha:** ___/09/2026

> **BORRADOR.** Esta certificación se firma cuando todas las casillas estén marcadas. Las que siguen vacías indican lo que falta antes del tag `entrega-3`.

Por medio de la presente, los integrantes del equipo hacemos constar que la documentación y el código de la **Entrega 3** fueron revisados antes de su presentación. Estado real de cada punto:

- [x] **Datos (DML):** más de 50 registros por tabla principal, con el inventario real del laboratorio (806 productos, 50 proveedores, 50 exámenes, 1,188 lotes, 5,839 movimientos). Excepción justificada: `categoria`, `rol` y `usuario` son catálogos de configuración. Los errores del registro en papel se documentan en `docs/entrega-3/reporte-carga-datos.md`.
- [x] **Vistas:** existencia, inventario bajo, lotes por vencer, historial y valorización a costo promedio ponderado (`sql/views/`).
- [x] **Triggers:** existencia por lote, historial inmutable y vencimiento obligatorio (`sql/triggers/001_triggers.sql`).
- [x] **Procedimientos:** `sp_registrar_entrada` y `sp_registrar_salida` con FEFO (`sql/procedures/001_procedures.sql`).
- [x] **Seguridad:** 3 roles de base de datos con privilegios diferenciados (`sql/security/001_roles.sql`), aplicados por la app con `SET ROLE`.
- [x] **Aplicación web al 70%:** módulos principales y control de acceso por rol (`AVANCE_WEB.md`).
- [x] **Matriz de trazabilidad** actualizada (`docs/entrega-3/matriz-trazabilidad.md`).
- [x] **Estándares** SQL y web revisados (`docs/entrega-3/estandares-cumplimiento.md`), con la única excepción declarada: S5, despliegue en internet, planificado para la Entrega 4.
- [x] **Bitácora de IA** actualizada (`docs/entrega-3/Bitacora-IA.md`).
- [ ] **Los 8 casos de prueba fueron ejecutados por el equipo** con capturas de evidencia (`docs/casos-prueba/casos-prueba-entrega-3.md`).
- [ ] **Participación visible de ambos integrantes** en los commits de esta entrega (R4).
- [x] No hay credenciales en el repositorio: `.env` no se versiona y los datos crudos del laboratorio (Excel) están excluidos por `.gitignore`. Los proveedores que son personas individuales se publican anonimizados.

---

## Firmas
Se dio el visto bueno para la entrega de este proyecto; ambos integrantes revisamos el contenido listado arriba.

| Nombre completo | Carné | Firma |
|---|---|---|
| Cristopher Alexis Castellanos Paz | 2690245972 | |
| José Eduardo Escobar | 2690245346 | |
