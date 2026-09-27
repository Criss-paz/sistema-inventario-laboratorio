# docs/entrega-3

**Entrega 3 — Implementación avanzada, seguridad y pruebas.**
**Estado:** implementada (26/09/2026). Base de datos, aplicación web y documentación completas.
**Cierre formal pendiente** (antes del 29/09): ejecución manual de los 8 casos de prueba con capturas, firma de Cristopher Alexis Castellanos Paz en la certificación (José Eduardo Escobar ya firmó) y tag `entrega-3`.

## Qué se entrega

### Base de datos

| Pieza | Archivo | Resumen |
|---|---|---|
| Datos (DML) | `sql/dml/` | Inventario real del laboratorio: 806 productos, 50 proveedores, 50 exámenes, 1,188 lotes, 5,839 movimientos |
| Triggers | `sql/triggers/001_triggers.sql` | Existencia por lote (RN-01 a RN-04), historial inmutable (RN-09), vencimiento obligatorio (RN-07) |
| Procedimientos | `sql/procedures/001_procedures.sql` | `sp_registrar_entrada`, `sp_registrar_salida` (FEFO) |
| Vistas | `sql/views/001_views.sql`, `002_valorizacion_promedio.sql` | Existencia, inventario bajo, lotes por vencer, historial, kardex y valorización a costo promedio ponderado |
| Seguridad | `sql/security/001_roles.sql` | 3 roles con privilegios diferenciados; procedimientos `SECURITY DEFINER` |

### Aplicación web

Módulos principales con control de acceso por rol: detalle en `AVANCE_WEB.md`.

### Documentos de esta carpeta

| Archivo | Contenido |
|---|---|
| `matriz-trazabilidad.md` | Versión 2: cada RF, RN y RNF con su objeto en la base, su módulo web y la prueba que lo demuestra |
| `reporte-carga-datos.md` | Errores encontrados en los registros en papel y cómo se trató cada uno |
| `Bitacora-IA.md` | Uso de IA en esta entrega |

### Pruebas

`docs/casos-prueba/casos-prueba-entrega-3.md`: 8 casos (FEFO, reglas de existencia, historial inmutable, roles en la app y en la base, costo promedio ponderado).

### Certificación

`docs/certificaciones/CERTIFICACION_ENTREGA_3.md`.
