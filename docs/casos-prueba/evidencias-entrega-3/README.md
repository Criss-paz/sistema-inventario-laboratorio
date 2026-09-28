# Evidencias — Entrega 3

Capturas de la ejecución de los casos de `../casos-prueba-entrega-3.md`, tomadas el 28/09/2026 por Cristopher Alexis Castellanos Paz sobre una instalación desde cero (PostgreSQL 18.6, Chromium 153, Windows 11).

| Archivo | Caso | Qué muestra |
|---|---|---|
| `CP3-00-precondicion.png` | Precondición | `admin.dev` creó el producto `PRUEBA-CP3` (existencia 0, activo) |
| `CP3-01a-entrada.png` | CP3-01 | Entrada n.º 5840: 10 unidades al lote `CP3-A`, responsable "Encargado de Prueba" |
| `CP3-01.png` | CP3-01 | Lotes `CP3-A` y `CP3-B` con 10 unidades cada uno |
| `CP3-02.png` | CP3-02 | Salida n.º 5842 repartida por FEFO: 10 de `CP3-B` y 5 de `CP3-A` |
| `CP3-03.png` | CP3-03 | Salida de 50 rechazada: existencia insuficiente (disponible 5.00) |
| `CP3-04.png` | CP3-04 | Entrada sin vencimiento rechazada por `trg_lote_vencimiento` |
| `CP3-05.png` / `.txt` | CP3-05 | `UPDATE` y `DELETE` sobre el historial rechazados por `fn_historial_inmutable` |
| `CP3-06a-consulta-movimientos.png` | CP3-06 | `consulta.dev`: Movimientos sin botones de registro ni sección Administración |
| `CP3-06b-consulta-403.png` | CP3-06 | `consulta.dev` en `/movimientos/entrada`: 403 |
| `CP3-06c-encargado-productos.png` | CP3-06 | `encargado.dev`: Productos sin "Nuevo producto" ni acciones de edición |
| `CP3-06d-encargado-403.png` | CP3-06 | `encargado.dev` en `/usuarios/`: 403 |
| `CP3-06e-admin-usuarios.png` | CP3-06 | `admin.dev`: Usuarios y roles con la tabla de permisos |
| `CP3-07.png` / `.txt` | CP3-07 | 4 instrucciones rechazadas con "permiso denegado" bajo `SET ROLE` |
| `CP3-08a-kardex.png` | CP3-08 | Kardex: promedio Q115, salida Q1,725, saldo 5 × Q115 = Q575 |
| `CP3-08b-inventario.png` | CP3-08 | Reporte de inventario: existencia 5, precio unitario 115.00, total Q575.00 |
| `CP3-99-cierre.png` | Cierre | `PRUEBA-CP3` desactivado por el administrador |

Los archivos `.txt` contienen la salida completa de `psql`, para poder copiar los mensajes.
