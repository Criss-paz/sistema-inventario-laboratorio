# Bitácora de Utilización de IA

## Proyecto
Sistema Web de Gestión y Control de Inventario para el Laboratorio Privado Quetzaltenango

## Entrega
Entrega 1 — Análisis, propuesta y diseño conceptual

## PROMT INICIAL

Quiero que me ayudes a realizar la primera entrega de un proyecto para la universidad.

El proyecto consiste en desarrollar un **sistema web para controlar el inventario de un laboratorio**, en este caso para el Laboratorio Privado Quetzaltenango.

La idea principal es dejar de llevar el control del inventario de forma manual y crear un sistema donde podamos registrar y consultar los productos que tiene el laboratorio.

Necesito que me ayudes a desarrollar la propuesta del proyecto paso a paso, tratando de que todo tenga relación entre sí y que no se agreguen cosas que no sean necesarias para el sistema.

Para esta primera entrega necesito trabajar principalmente:

* Descripción del problema.
* Planteamiento del problema.
* Justificación.
* Objetivo general.
* Objetivos específicos.
* Alcance del sistema.
* Usuarios que utilizarán el sistema.
* Requerimientos funcionales.
* Requerimientos no funcionales.
* Reglas de negocio.
* Entidades y atributos.
* Relaciones entre las entidades.
* Modelo entidad-relación.
* Una propuesta inicial de la base de datos.
* Flujo de las principales operaciones del sistema.
* Una idea general de cómo estaría estructurado el sistema.

El sistema debe permitir controlar principalmente:

* Productos.
* Categorías.
* Proveedores.
* Lotes.
* Fechas de vencimiento.
* Existencias.
* Entradas de inventario.
* Salidas de inventario.
* Usuarios.
* Roles y permisos.
* Historial de movimientos.
* Stock mínimo.
* Reportes.

Por ejemplo, cuando ingrese un producto al inventario se debería poder registrar su producto, lote, proveedor, cantidad, fecha de ingreso y fecha de vencimiento.

Cuando se realice una salida, el sistema debe verificar que exista suficiente cantidad disponible y después actualizar el inventario.

También necesito que cada movimiento quede registrado para poder saber qué usuario realizó la operación y cuándo se realizó.

Para la base de datos quiero que primero se analice el modelo entidad-relación y después se pueda llevar a un modelo relacional que posteriormente pueda implementarse en **Oracle**.

Es importante que las entidades, atributos y relaciones tengan sentido con los requerimientos y que exista integridad entre los datos.

No quiero desarrollar todavía todo el sistema completo. En esta primera etapa necesito dejar bien definida la idea del proyecto, los requerimientos y el diseño inicial para posteriormente continuar con la base de datos y la programación.

Quiero que me vayas ayudando **sección por sección**, explicando de manera sencilla qué se está haciendo y por qué, para que como estudiante pueda entender y defender el proyecto si el ingeniero hace preguntas.

Al finalizar, revisar que todo lo realizado sea coherente entre el problema, objetivos, requerimientos, reglas de negocio y modelo de base de datos.

## Propósito
La inteligencia artificial se utilizó como herramienta de apoyo durante el análisis y la documentación del proyecto. La IA no sustituye las decisiones del equipo; toda propuesta fue revisada y validada antes de incorporarse.

## Registro detallado por actividad

### 1. Análisis del problema
**Actividad:** estructuración del problema y propuesta de solución.
**Uso de IA:** apoyo para organizar la situación actual, consecuencias y necesidad tecnológica.
**Validación:** el equipo contrastó el contenido con la realidad del laboratorio.

### 2. Requerimientos
**Actividad:** identificación y redacción de requerimientos funcionales, no funcionales y de datos.
**Uso de IA:** generación de una propuesta inicial y organización por categorías.
**Validación:** cada requerimiento fue revisado y se mantuvo únicamente si responde a una necesidad real.

### 3. Modelo conceptual
**Actividad:** identificación de entidades, atributos, relaciones y cardinalidades.
**Uso de IA:** apoyo para estructurar el modelo conceptual Chen.
**Resultado:** ROL, USUARIO, CATEGORIA, PRODUCTO, PROVEEDOR, LOTE, MOVIMIENTO, EXAMEN_LABORATORIO y DETALLE_MOVIMIENTO (9 entidades).
**Validación:** revisión de coherencia con reglas de negocio y requerimientos. Se resolvió la relación N:M MOVIMIENTO–LOTE mediante la entidad asociativa DETALLE_MOVIMIENTO.

### 4. Matriz de trazabilidad
**Actividad:** comprobar coherencia entre requerimientos y modelo ER.
**Uso de IA:** apoyo para construir una matriz de correspondencia.
**Validación:** el equipo revisó que cada relación y entidad tenga una justificación.

### 5. Redacción y ortografía
**Actividad:** mejorar organización, claridad y corrección lingüística.
**Uso de IA:** revisión de estilo y estructura técnica.
**Validación:** el equipo es responsable del contenido final.

## Declaración
La IA se utilizó como apoyo y no como sustituto del análisis del equipo. Toda propuesta fue revisada, validada y adaptada antes de incorporarse al proyecto.
