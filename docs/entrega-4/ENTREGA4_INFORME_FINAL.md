# Informe final

**Proyecto:** Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango
**Curso:** Base de Datos — Universidad Mariano Gálvez de Guatemala
**Integrantes:** José Eduardo Escobar (2690245346) · Cristopher Alexis Castellanos Paz (2690245972)
**SGBD:** PostgreSQL · **Aplicación:** Python + Flask
**Repositorio:** https://github.com/Criss-paz/sistema-inventario-laboratorio · **En línea:** https://inventario-laboratorio-03s7.onrender.com
**Fecha:** octubre de 2026

---

## 1. Resumen

El Laboratorio Privado Quetzaltenango llevaba el control de su bodega en papel. No había una forma confiable de saber cuánto quedaba de cada reactivo, qué lotes estaban por vencer ni quién había sacado qué. Este proyecto diseñó e implementó una base de datos relacional en PostgreSQL que resuelve ese problema, más una aplicación web que la consume.

El sistema final tiene:
- **11 tablas** en tercera forma normal;
- **5 triggers**, **3 procedimientos almacenados** y **6 vistas** con las reglas de negocio;
- **3 roles de base de datos** con privilegios diferenciados;
- una aplicación web con **11 módulos** y control de acceso en dos capas.

Funciona con el **inventario real del laboratorio**, transcrito de los registros en papel: 806 productos, 1,188 lotes y 5,839 movimientos de marzo a septiembre de 2026, valorizados en Q524,714.36. Está publicado en internet, y su instalación desde cero toma unos 12 segundos de scripts.

---

## 2. Problema y objetivos

### 2.1 Problema

Sin un sistema centralizado, el laboratorio no podía:
- conocer la existencia real de cada producto, ni por lote;
- detectar a tiempo los reactivos por vencer, o los vencidos que seguían en bodega;
- saber qué se estaba acabando;
- reconstruir quién registró cada movimiento;
- valorizar el inventario.

Además, los registros en papel tenían errores: códigos repetidos, cantidades ilegibles, vencimientos faltantes. Están documentados en `docs/entrega-3/ENTREGA3_REPORTE_CARGA_DATOS.md`.

### 2.2 Objetivo general

Diseñar, implementar y documentar un sistema de base de datos relacional que controle el inventario del laboratorio. Debía incluir el modelado, scripts SQL con estándares de calidad, seguridad, procedimientos almacenados y triggers, y una aplicación web que la consuma.

### 2.3 Cumplimiento de los objetivos específicos

| Objetivo de la consigna | Cómo se cumplió | Dónde |
|---|---|---|
| 1. Requerimientos de un caso real | 39 requerimientos funcionales, 18 no funcionales y 18 reglas de negocio iniciales, levantados con el laboratorio | `docs/entrega-1/ENTREGA1_PROPUESTA.pdf` |
| 2. Modelo ER (Chen) y relacional normalizado | ER con 9 entidades y 3 relaciones N:M; modelo relacional de 11 tablas en 3FN, con ejemplo de normalización paso a paso | `docs/diagramas/`, `docs/entrega-2/` |
| 3. Implementación en un SGBD | PostgreSQL 18 en desarrollo y 17 en producción (Neon) | `sql/` |
| 4. SQL y código con estándares | 8 de 8 estándares SQL y 6 de 6 de aplicación | `ENTREGA4_ESTANDARES_CUMPLIMIENTO.md` |
| 5. Integridad, seguridad, vistas, triggers y procedimientos | Ver sección 3 | `sql/` |
| 6. Validación con casos de prueba | 46 casos documentados y ejecutados en las entregas 2 a 4, todos aprobados, más regresión automatizada | `docs/casos-prueba/` |
| 7. Documentar el uso de IA y defender las decisiones | Bitácora por entrega y consolidada; guía de defensa | `docs/bitacora-ia/`, `ENTREGA4_GUIA_DEFENSA.md` |

---

## 3. Requisitos mínimos del sistema (consigna, sección 5)

| # | Requisito | Mínimo | Resultado | Evidencia |
|---|---|---|---|---|
| 1 | Entidades principales (sin asociativas N:M) | 8 | **9**: rol, usuario, categoria, producto, proveedor, lote, movimiento, detalle_movimiento, examen_laboratorio | Diagrama ER |
| 2 | Relaciones N:M resueltas | 2 | **3**: proveedor–producto (`proveedor_producto`), examen–producto (`examen_producto`) y movimiento–lote (`detalle_movimiento`) | Modelo relacional |
| 3 | Normalización hasta 3FN con ejemplo | Sí | Ejemplo completo de 0FN a 3FN | `docs/entrega-2/normalizacion-3fn.md` y `.xlsx` |
| 4 | Restricciones explícitas | 15 | **38** en el esquema inicial (PK, FK, UNIQUE, CHECK, NOT NULL), más las de las migraciones: `fk_movimiento_origen`, `ck_movimiento_devolucion` y `NOT NULL` de `examen_laboratorio.estado` | `docs/entrega-2/diccionario-datos.md`, `sql/ddl/` |
| 5 | Triggers y procedimientos con justificación | 2 y 2 | **5 triggers** y **3 procedimientos**, más 7 funciones, cada uno con su regla de negocio | `sql/triggers/`, `sql/procedures/` |
| 6 | Roles con privilegios diferenciados | 3 | **3**: `rol_consulta ⊂ rol_encargado ⊂ rol_administrador` | `sql/security/` |
| 7 | Registros por tabla principal | 50 | producto 806, lote 1,188, movimiento 5,839, detalle_movimiento 5,920, proveedor_producto 425, examen_producto 114, proveedor 50, examen_laboratorio 50. Excepciones justificadas: `rol`, `categoria` y `usuario` son catálogos de configuración | `sql/dml/` |

---

## 4. Solución construida

### 4.1 Decisiones de diseño principales

1. **El lote es la unidad de control.** La existencia se guarda por lote, no por producto: así se puede vencer, rastrear al proveedor y aplicar FEFO. La existencia por producto se calcula en una vista.
2. **El historial es inmutable.** Ningún movimiento se modifica ni se borra (RN-09). Lo garantizan dos triggers, y además ningún rol tiene `UPDATE` ni `DELETE` sobre esas tablas. Los errores se corrigen con un movimiento inverso, la devolución.
3. **Las reglas de negocio viven en la base de datos.** Existencias, FEFO, vencimiento obligatorio y tope de devolución se aplican aunque alguien use la base sin pasar por la aplicación.
4. **Seguridad en dos capas.** La aplicación protege cada ruta por rol y, además, adopta en PostgreSQL el rol del usuario (`SET ROLE`). Ni el administrador puede leer los hashes de contraseñas ni cambiar existencias a mano.
5. **Costo promedio ponderado móvil.** Cada compra recalcula el promedio y cada salida se valora al promedio vigente, calculado en la base con `fn_kardex_promedio`. El cuadre contable con los datos reales (compras − consumo = inventario) tiene una diferencia de Q0.06, que viene del redondeo de cada salida.
6. **Baja lógica en todos los catálogos.** Nada que tenga historial se borra.

### 4.2 Aplicación web (100%)

| Módulo | Funciones |
|---|---|
| Acceso | Login, logout, cambio de contraseña propio, menú y permisos por rol |
| Inicio | Indicadores del día: existencia, inventario bajo, vencidos, por vencer, actividad |
| Movimientos | Entradas, salidas por FEFO, devolución de salidas, historial con filtros |
| Lotes | Existencia por lote, vencidos, por vencer, ficha con historial, corrección de datos |
| Productos, Categorías, Proveedores, Exámenes | CRUD completo con baja lógica; productos y precios por proveedor; insumos por examen y "alcanza para N pruebas" |
| Reportes | 9 reportes (inventario valorizado, entradas, salidas, kardex, proveedores, pruebas, catálogo, inventario bajo, vencimientos) con CSV e impresión |
| Usuarios y roles | Alta, cambio de rol, contraseña nueva, desactivación |
| Respaldo | Descarga de un respaldo completo restaurable con `psql` |

El CRUD por tabla, con la justificación de las operaciones que no se ofrecen a propósito, está en `ENTREGA4_MATRIZ_TRAZABILIDAD.md`.

### 4.3 Evolución por entrega

| Entrega | Fecha | Producto principal |
|---|---|---|
| 1 | 18/08/2026 | Propuesta, requerimientos, ER en notación Chen, Gantt |
| 2 | 01/09/2026 | Modelo relacional, 3FN, diccionario, DDL; web al 30% (login, 2 CRUD) |
| 3 | 29/09/2026 | Datos reales, triggers, procedimientos, vistas, roles, 8 casos de prueba, despliegue; web al 70%; devolución de salidas |
| 4 | 03/11/2026 | Web al 100%: CRUD de proveedor–producto, baja de exámenes, respaldo, seguridad; manuales, informe y diagramas actualizados |

---

## 5. Pruebas

| Conjunto | Casos | Resultado |
|---|---|---|
| Entrega 2: login y CRUD | 18 | 18 aprobados |
| Entrega 3: triggers, FEFO, roles, valorización | 8 | 8 aprobados, sobre una instalación desde cero en un segundo equipo |
| Entrega 3: devolución de salidas | 6 | 6 aprobados |
| Entrega 4: flujos del manual de usuario, respaldo, instalación | 14 | 14 aprobados, con capturas |
| Regresión de la aplicación (Entrega 4) | 183 verificaciones | 0 fallas |

Las pruebas encontraron defectos reales, que se corrigieron antes de cada cierre:
- en la Entrega 3, el generador de la carga de datos y el kardex, que restaba las devoluciones;
- en la Entrega 4, tres plantillas que mostraban la devolución como salida y una etiqueta sin tilde.

---

## 6. Uso de inteligencia artificial

Se usó Claude Code como agente de apoyo en todas las entregas: análisis, SQL, aplicación, pruebas y documentación. El equipo revisó y probó cada resultado antes del commit (estándar S8), y la bitácora registra qué se pidió, qué se obtuvo, qué se validó y qué se corrigió o rechazó. El resumen de todas las entregas está en `docs/bitacora-ia/ENTREGA4_BITACORA_IA.md`.

La lección principal: la IA acelera mucho la escritura, pero **los errores que importaban los encontraron las pruebas contra la base real, no la revisión del código**. Por ejemplo:
- el trigger de existencia detectó un error del propio generador de la carga;
- los casos de la Entrega 4 detectaron que la interfaz mostraba la devolución como salida, aunque la base ya lo calculaba bien.

---

## 7. Dificultades y cómo se resolvieron

| Dificultad | Solución |
|---|---|
| Registros en papel con errores e inconsistencias | Carga con un generador (`sql/dml/generar_carga.py`) que documenta cada corrección; el trigger de existencia valida la carga |
| Corregir una salida mal registrada sin romper la inmutabilidad del historial | Devolución como movimiento inverso, enlazado a la salida y con motivo obligatorio |
| Mantener el control de acceso en la base con una sola conexión de aplicación | `SET ROLE` por petición, con `COMMIT` inmediato; pooler de Neon desactivado |
| Respaldo en un servidor sin `pg_dump` compatible | Respaldo generado en el mismo formato `COPY` desde Python, probado con una restauración real |
| Tildes corruptas al ejecutar `psql` en Windows | `PGCLIENTENCODING=UTF8`, documentado en `INSTALL.md` |
| Equipo de dos integrantes, no de tres (la consigna lo permite con autorización del catedrático) | Reparto por bloques, cada uno con commits propios |

---

## 8. Conclusiones

1. Un buen modelo de datos resuelve la mayor parte del problema. Elegir el **lote** como unidad de existencia y el **historial inmutable** como fuente de verdad hizo posibles el FEFO, los vencimientos, la trazabilidad y la valorización sin datos redundantes.
2. Poner las reglas de negocio en la base (triggers, procedimientos y roles) da garantías que la aplicación sola no puede dar. Aunque hubiera un error en la interfaz, PostgreSQL rechazaría una salida mayor a la existencia, una modificación del historial o una lectura de contraseñas.
3. Probar con **datos reales** fue decisivo: los errores del papel, la escala (5,839 movimientos) y los casos límite no habrían aparecido con datos inventados.
4. La documentación (manuales, matriz de trazabilidad, bitácora) no es un trámite: permite instalar el sistema desde cero en otro equipo y explicar cada decisión.

## 9. Recomendaciones

- Antes del uso diario, pasar a un plan pagado o a un servidor en la red del laboratorio: el plan gratuito tarda unos 50 segundos en despertar tras 15 minutos sin uso.
- Programar el respaldo semanal (`python web/respaldo.py`) y guardarlo fuera del servidor.
- Agregar en una versión futura: bloqueo por intentos fallidos de login, auditoría de cambios en catálogos y envío automático del respaldo fuera del servidor (manual técnico, sección 11).

---

## Anexos

| Documento | Ubicación |
|---|---|
| Declaración de integridad | `docs/entrega-4/ENTREGA4_DECLARACION_INTEGRIDAD.md` |
| Manual de usuario | `docs/entrega-4/ENTREGA4_MANUAL_USUARIO.md` |
| Manual técnico | `docs/entrega-4/ENTREGA4_MANUAL_TECNICO.md` |
| Matriz de trazabilidad v3 | `docs/entrega-4/ENTREGA4_MATRIZ_TRAZABILIDAD.md` |
| Cumplimiento de estándares | `docs/entrega-4/ENTREGA4_ESTANDARES_CUMPLIMIENTO.md` |
| Guía de defensa | `docs/entrega-4/ENTREGA4_GUIA_DEFENSA.md` |
| Casos de prueba de la Entrega 4 | `docs/casos-prueba/casos-prueba-entrega-4.md` |
| Bitácora de IA consolidada | `docs/bitacora-ia/ENTREGA4_BITACORA_IA.md` |
| Certificación | `docs/certificaciones/CERTIFICACION_ENTREGA_4.md` |
