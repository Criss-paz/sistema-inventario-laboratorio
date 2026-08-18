# Sistema Web de Gestion y Control de Inventario — Laboratorio Privado Quetzaltenango

## Entrega 1 — Analisis, propuesta y diseño conceptual

### Descripcion
Proyecto orientado al diseño y posterior desarrollo de un sistema web para gestionar el inventario del Laboratorio Privado Quetzaltenango, con una base de datos relacional diseñada desde cero.

### Problema
El laboratorio carece de un sistema centralizado para administrar productos, existencias, lotes, vencimientos, proveedores, insumos por examen y movimientos de inventario.

### Objetivo
Diseñar y desarrollar una solucion web conectada a una base de datos relacional, con control de usuarios, productos, lotes, entradas, salidas, existencias y trazabilidad.

### Alcance inicial
- Usuarios y roles
- Categorias
- Productos
- Proveedores
- Examenes de laboratorio e insumos requeridos por examen
- Lotes y vencimientos
- Entradas y salidas
- Existencias
- Historial de movimientos
- Stock minimo
- Consultas y reportes
- Autenticacion y control de acceso

### Modelo conceptual
El modelo esta compuesto por **9 entidades principales**:

`ROL`, `USUARIO`, `CATEGORIA`, `PRODUCTO`, `PROVEEDOR`, `LOTE`, `MOVIMIENTO`, `EXAMEN_LABORATORIO` y `DETALLE_MOVIMIENTO`.

Se resuelven dos relaciones N:M explicitas —PROVEEDOR–PRODUCTO (`SUMINISTRA`) y EXAMEN_LABORATORIO–PRODUCTO (`REQUIERE`)— y la relacion conceptual N:M entre MOVIMIENTO y LOTE se resuelve mediante la entidad asociativa `DETALLE_MOVIMIENTO`.

### Estructura del repositorio
```text
sistema-inventario-laboratorio/
├── README.md
├── .gitignore
├── .gitattributes
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
└── web/            # Aplicacion web (desde Entrega 2)
```

### Documentacion de Entrega 1
- `docs/entrega-1/ENTREGA1_PROPUESTA.docx`
- `docs/diagramas/DIAGRAMA-ER-LAB.png`
- `docs/diagramas/DIAGRAMA-ER-LAB.drawio`
- `docs/diagramas/DIAGRAMA-ER-LAB.pdf`
- `docs/entrega-1/Gantt-Proyecto.xlsx`
- `docs/bitacora-ia/Bitacora-IA.md`
- `docs/certificaciones/CERTIFICACION_ENTREGA_1.md`

### SGBD
_(A definir por el equipo: MySQL, PostgreSQL o SQL Server.)_

### Integrantes
|     Nombre    |   Carné  |
|---------------|----------|
|CRISTOPHER PAZ_|2690245972|
|||

### Control de versiones
La entrega finaliza con un commit de cierre y el tag `entrega-1`.

### Estado
Entrega 1 — Analisis, propuesta y diseño conceptual.