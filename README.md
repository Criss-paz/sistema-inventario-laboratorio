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
│   ├── entrega-2/
│   ├── entrega-3/
│   ├── entrega-4/
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
- `docs/diagramas/DIAGRAMA-ER-LAB.drawio` — diagrama ER editable (fuente)
- `docs/diagramas/DIAGRAMA-ER-LAB.drawio.png`
- `docs/diagramas/DIAGRAMA-ER-LAB.drawio.pdf`
- `docs/entrega-1/Gantt-Proyecto.xlsx`
- `docs/bitacora-ia/Bitacora-IA.md`
- `docs/certificaciones/CERTIFICACION_ENTREGA_1.md`

### Documentacion de Entrega 2
- `docs/entrega-2/modelo-relacional.md` — modelo relacional (11 tablas)
- `docs/entrega-2/normalizacion-3fn.md` — normalización 3FN con ejemplo completo
- `docs/entrega-2/diccionario-datos.md` — diccionario de datos + matriz de 38 restricciones
- `docs/entrega-2/matriz-trazabilidad.md` — trazabilidad RF → tabla/módulo
- `sql/ddl/001_schema.sql` — DDL ejecutable
- `sql/dml/001_seed.sql` + `web/seed_usuarios.py` — datos de prueba
- `web/` — aplicación Flask: login, layout, CRUD de Categorías y Productos
- `AVANCE_WEB.md` — estado de la app web
- `docs/casos-prueba/casos-prueba-entrega-2.md` — 15 casos automatizados + 3 manuales, ejecutados (18/18)
- `docs/certificaciones/CERTIFICACION_ENTREGA_2.md` — firmada por ambos integrantes
- `docs/entrega-2/Bitacora-IA.md` — bitácora de IA de esta entrega

### SGBD
**PostgreSQL** — decidido en la Entrega 2. La Entrega 1 dejó este punto abierto ("a definir") y la bitácora de IA de la Entrega 1 mencionaba Oracle como intención inicial; el equipo confirmó PostgreSQL por su soporte completo de CHECK/FK/triggers/funciones, instalación simple y facilidad de defensa académica. Justificación completa en `docs/entrega-2/Bitacora-IA.md`.

### Integrantes
|     Nombre    |   Carné  |
|---------------|----------|
|CRISTOPHER ALEXIS CASTELLANOS PAZ|2690245972|
|JOSE EDUARDO ESCOBAR|2690245346|

### Control de versiones
Cada entrega finaliza con un commit de cierre y su tag: `entrega-1`, `entrega-2`.

### Estado
- Entrega 1 — Análisis, propuesta y diseño conceptual: **cerrada** (tag `entrega-1`).
- Entrega 2 — Diseño lógico, diccionario e implementación base: **cerrada** (tag `entrega-2`, 01/09/2026). Contenido verificado por ejecución real (PostgreSQL 18 + Python 3.14, 30/08/2026 — 15/15 casos automatizados y 3 manuales en navegador). Incluye: SGBD (PostgreSQL), stack web (Flask + psycopg 3), modelo relacional, normalización 3FN, diccionario de datos, DDL, datos de prueba, login + 2 CRUD (Categorías, Productos), `AVANCE_WEB.md`, matriz de trazabilidad, casos de prueba ejecutados, diagrama ER corregido y re-exportado, y certificación firmada por ambos integrantes.
- Entrega 3 — Implementación avanzada, seguridad y pruebas: **en curso**. Pendiente: vistas, triggers, procedimientos, 3 roles de PostgreSQL, control de acceso por rol en la app, ampliación del seed a 50+ registros por tabla principal y app web al 70%.

> **Nota sobre la integración:** el proyecto lo desarrollan 2 estudiantes. La consigna indica grupos de 3 "puede variar con autorización del catedrático".