# Sistema Web de Gestión y Control de Inventario — Laboratorio Privado Quetzaltenango

## Entrega 1 — Análisis, propuesta y diseño conceptual

### Descripción
Proyecto orientado al diseño y posterior desarrollo de un sistema web para gestionar el inventario del Laboratorio Privado Quetzaltenango, con una base de datos relacional diseñada desde cero.

### Problema
El laboratorio carece de un sistema centralizado para administrar productos, existencias, lotes, vencimientos, proveedores, insumos por examen y movimientos de inventario.

### Objetivo
Diseñar y desarrollar una solución web conectada a una base de datos relacional, con control de usuarios, productos, lotes, entradas, salidas, existencias y trazabilidad.

### Alcance inicial
- Usuarios y roles
- Categorías
- Productos
- Proveedores
- Exámenes de laboratorio e insumos requeridos por examen
- Lotes y vencimientos
- Entradas y salidas
- Existencias
- Historial de movimientos
- Stock mínimo
- Consultas y reportes
- Autenticación y control de acceso

### Modelo conceptual
El modelo está compuesto por **9 entidades principales**:

`ROL`, `USUARIO`, `CATEGORIA`, `PRODUCTO`, `PROVEEDOR`, `LOTE`, `MOVIMIENTO`, `EXAMEN_LABORATORIO` y `DETALLE_MOVIMIENTO`.

Se resuelven dos relaciones N:M explícitas —PROVEEDOR–PRODUCTO (`SUMINISTRA`) y EXAMEN_LABORATORIO–PRODUCTO (`REQUIERE`)— y la relación conceptual N:M entre MOVIMIENTO y LOTE se resuelve mediante la entidad asociativa `DETALLE_MOVIMIENTO`.

### Estructura del repositorio
```text
sistema-inventario-laboratorio/
├── README.md
├── .gitignore
├── .env.example
├── INSTALL.md
├── docs/
│   ├── entrega-1/
│   ├── diagramas/
│   ├── certificaciones/
│   ├── bitacora-ia/
│   └── casos-prueba/
├── sql/
│   ├── ddl/
│   ├── dml/
│   ├── views/
│   ├── triggers/
│   ├── procedures/
│   └── security/
└── web/            # Aplicación web (desde Entrega 2)
```

### Documentación de Entrega 1
- `docs/entrega-1/ENTREGA1_PROPUESTA.docx`
- `docs/diagramas/ER-Chen-Laboratorio.png`
- `docs/diagramas/ER-Chen-Laboratorio.pdf`
- `docs/diagramas/ER-Chen-Laboratorio.drawio`
- `docs/entrega-1/Gantt-Proyecto.xlsx`
- `docs/bitacora-ia/Bitacora-IA.md`
- `docs/certificaciones/CERTIFICACION_ENTREGA_1.md`

### SGBD
_(A definir por el equipo: MySQL, PostgreSQL o SQL Server.)_

### Integrantes
| Nombre | Carné |
|--------|-------|
| _(Integrante 1)_ | _(carné)_ |
| _(Integrante 2)_ | _(carné)_ |

### Control de versiones
La entrega finaliza con un commit de cierre y el tag `entrega-1`.

### Estado
Entrega 1 — Análisis, propuesta y diseño conceptual.