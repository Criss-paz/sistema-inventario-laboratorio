"""
Archivo:      generar_carga.py
Propósito:    Convertir el inventario real del laboratorio (registros en papel
              transcritos a Excel) en los scripts de carga de la base de datos.
Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
              Privado Quetzaltenango
Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
              — generado con apoyo de IA (Claude Code); ver
              docs/bitacora-ia/Bitacora-IA.md para el registro de uso.

Genera:
  sql/dml/002_carga_catalogo.sql       categorías, productos, proveedores y
                                        proveedor_producto
  sql/dml/004_carga_movimientos.sql    lotes, entradas y salidas
  docs/entrega-3/reporte-carga-datos.md hallazgos de calidad de datos

Uso (el Excel NO está en el repositorio: son datos internos del laboratorio):
  pip install openpyxl
  python sql/dml/generar_carga.py "ruta/al/inventario.xlsx"

Decisiones (acordadas con el equipo, detalladas en el reporte):
  1. Servicios (mantenimientos, reparaciones, fletes, rentas) no son
     inventario: se excluyen con sus entradas.
  2. Entradas sin número de lote: se crea un lote "SL-<entrada>".
  3. Salidas registradas antes que la entrada que las cubre: se mueven a la
     fecha de esa entrada y quedan anotadas. Si ninguna entrada posterior las
     cubre, se rechazan.
  4. Las salidas se asignan a lotes por FEFO (primero el que vence antes),
     igual que sp_registrar_salida.
  5. Proveedores que son personas individuales se anonimizan (el repositorio
     es público). Se identifican por hash para no escribir el nombre aquí.
  6. Proveedores reales sin NIT: NIT provisional "SIN-NIT-##".
"""

import collections
import datetime as dt
import hashlib
import itertools
import re
import sys
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parents[2]
SALIDA_CATALOGO = RAIZ / "sql" / "dml" / "002_carga_catalogo.sql"
SALIDA_MOVIMIENTOS = RAIZ / "sql" / "dml" / "004_carga_movimientos.sql"
SALIDA_REPORTE = RAIZ / "docs" / "entrega-3" / "reporte-carga-datos.md"

# sha256 del nombre en mayúsculas de los proveedores que son personas.
PERSONAS = {
    "64f1fe6813e5eb3666df785dde98fb2cb0672287bf7fde7318f42712927bd252",
    "5b04b6667b0f8071a9967f6b525dc8786c94c222fe0cf2d44e05a2cc5c2265bf",
}

# Correcciones con evidencia (ver reporte). CFU6PB: las dos primeras entradas
# se anotaron en unidades sueltas (Q9.50 c/u) y las demás en cajas de 50
# (Q475). Convertidas a cajas, entradas − salidas = 26, la existencia
# que reporta el propio inventario.
CORRECCIONES = {
    "E000134": {"factor": 50, "motivo": "Anotada en unidades sueltas; convertida a cajas de 50 (1200 u = 24 cajas)."},
    "E000399": {"factor": 50, "motivo": "Anotada en unidades sueltas; convertida a cajas de 50 (600 u = 12 cajas)."},
}

SERVICIO = re.compile(r"MANTENIMIENTO|REPARACI|FLETE|RENTA DE|SERVICIO DE|C[ÓO]D\. QR")

# Clasificación por palabras clave, en orden: gana la primera regla.
REGLAS_CATEGORIA = [
    ("EQUIPO Y REPUESTOS", r"CENTRIFUGA|MICROSCOPIO|SWITCH|AGITADOR|VORTEX|BUSCADOR DE VENAS|TERM[ÓO]METRO|\bTIMER\b|C[ÁA]MARA DE NEUBAUER|REPUESTO|L[ÁA]MPARA|OBJETIVO OCULAR|ELECTRODO|PCB ASSY|FAN ASSY|MEMBRANE ASSEMBLY|TUBING KIT|TRANSPORDER"),
    ("CALIBRADORES", r"CALIBRAT|CALIBRADOR|CONTROLES DE TERCERA|CONTROL DE CALIDAD|CONTROL TYDAL|MAC CONTROLS|MULTI ANALYTE CONTROL|ASSYED|MULTISERA|STANDARD FS|STANDARD 3ML|DENSICHECK|BC-6D|CBC-5D"),
    ("EQUIPO DE PROTECCION PERSONAL", r"GUANTE|MASCARILLA|\bBATA\b|COFIA|GORRO"),
    ("BANCO DE SANGRE", r"BOLSA (DE )?SANGRE|BOLSA DOBLE|BOLSA SIMPLE|BOLSA TRANSFER|TRANSFUSI"),
    ("INSUMOS DE TOMA DE MUESTRA", r"AGUJA|JERINGA|TUBO AL VAC|\bBAND\.|BANDEJA DE TUBO|\bLIGA|LANCETA|CURITA|ALGOD|PAD ALCOHOL|TOALLA C/|BOTE DE RECOLECC|RECOLECTOR|CONTENEDORES|FRASCO DE HECES|BOLSA DE ORINA|CAMISA|ESP[ÉE]CULO|MICROPORE|TUBO CON GEL|BAJA LENGUA|HISOPO|PERICRANEALES|BISTUR"),
    ("MICROBIOLOGIA", r"AGAR|DISCOS|TAXO|BLISTER|MAGAZINE|MEGAZINE|GRAM |ZIEHL|\bASAS?\b|LOOP|INOCULA|CAJA PETRI|MEDIO DE TRANSPORTE|TRANSYSTEM|VITEK|BACT / ALERT|SANGRE DE CARNERO|INDOL|CATALASA|COLIFORMES|IDEXX|BATER[IÍ]AS BIOQU|LACTOFENOL|KOH|BROTH|HEMOCULTIVOS"),
    ("LIMPIEZA Y DESINFECCION", r"ALCOHOL|DAYKIN|EXTRAN|CLEANING|SANITIZING|CLEANSER|TIMEROSAL|ACETONA"),
    ("PAPELERIA Y ETIQUETADO", r"PAPEL/IMPRESORA|PRINTER PAPER|PAPEL PARA (CHORUS|EQUIPO)|ETIQUETA"),
    ("MATERIAL PARA EL LABORATORIO", r"TUBO|MICROTUBO|PUNTA|TIPS|PIPET|PORTA ?OBJETOS|CUBRE|LAMINILLA|CUBETA|CUVETTE|SAMPLE CUPS|APLICADORES|PARAFILM|CINTA|ERLENMEYER|PAPEL|BLOCK|COPA |TEST CUP|TREATMENT CUP|FRASCOS|ACEITE DE INMERSI|IMMERSION OIL"),
]
# Por defecto: REACTIVOS.

CATEGORIAS_NUEVAS = {
    "MICROBIOLOGIA": "Medios de cultivo, discos de sensibilidad, tinciones y asas",
    "LIMPIEZA Y DESINFECCION": "Desinfectantes, alcoholes y soluciones de limpieza de equipos",
    "PAPELERIA Y ETIQUETADO": "Papel térmico para equipos y etiquetas de código de barras",
    "EQUIPO Y REPUESTOS": "Equipo menor y repuestos (no vencen)",
    "BANCO DE SANGRE": "Bolsas de recolección y equipos de transfusión",
}
# Categorías que vencen, para productos que aún no tienen entradas.
CATEGORIAS_CON_VENCIMIENTO = {"REACTIVOS", "CALIBRADORES", "MICROBIOLOGIA", "BANCO DE SANGRE"}

LOTE_INVALIDO = re.compile(r"^0\.\d{6,}$")  # número decimal que Excel puso en la columna de lote


def sql(v):
    """Literal SQL de un valor de Python."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return repr(round(v, 2)) if isinstance(v, float) else str(v)
    if isinstance(v, dt.datetime):
        return f"'{v:%Y-%m-%d %H:%M}'"
    if isinstance(v, dt.date):
        return f"'{v:%Y-%m-%d}'"
    return "'" + str(v).replace("'", "''") + "'"


def fila_sql(valores):
    return "(" + ", ".join(sql(v) for v in valores) + ")"


def leer_hoja(libro, nombre):
    filas = list(libro[nombre].iter_rows(values_only=True))
    encabezado = filas[0]
    return [dict(zip(encabezado, f)) for f in filas[1:] if any(v is not None for v in f)]


def texto(v):
    return None if v is None else str(v).strip()


def categoria_de(nombre, proveedor):
    if proveedor and proveedor.startswith("LABTRONIC"):
        return "MICROBIOLOGIA"  # discos de antibiograma
    for cat, patron in REGLAS_CATEGORIA:
        if re.search(patron, nombre):
            return cat
    return "REACTIVOS"


def main(ruta_excel):
    libro = openpyxl.load_workbook(ruta_excel, read_only=True, data_only=True)
    productos_x = leer_hoja(libro, "Productos")
    entradas_x = leer_hoja(libro, "Entradas")
    salidas_x = leer_hoja(libro, "Salidas")
    proveedores_x = leer_hoja(libro, "Proveedores")

    rep = collections.defaultdict(list)  # hallazgos para el reporte

    # ------------------------------------------------------------------ proveedores
    alias = {}
    n_persona = 0
    for p in proveedores_x:
        nombre = texto(p["Proveedor"])
        if hashlib.sha256(nombre.upper().encode()).hexdigest() in PERSONAS:
            n_persona += 1
            alias[nombre] = f"PROVEEDOR INDIVIDUAL {n_persona:02d}"
        else:
            alias[nombre] = nombre
    rep["anonimizados"] = n_persona
    proveedores = [alias[texto(p["Proveedor"])] for p in proveedores_x]

    def prov(nombre):
        return alias.get(texto(nombre)) if nombre else None

    # ------------------------------------------------------------------ productos
    productos = {}
    excluidos = set()
    for p in productos_x:
        codigo, nombre = texto(p["Código"]), texto(p["Nombre"])
        if SERVICIO.search(nombre.upper()):
            excluidos.add(codigo)
            rep["servicios"].append((codigo, nombre))
            continue
        activo = True
        if codigo.startswith("/DESACT/"):
            codigo_limpio = codigo[len("/DESACT/"):]
            rep["desactivados"].append((codigo, codigo_limpio, nombre))
            activo = False
        else:
            codigo_limpio = codigo
        assert len(codigo_limpio) <= 30 and len(nombre) <= 150, codigo
        productos[codigo] = {
            "codigo": codigo_limpio,
            "nombre": nombre,
            "categoria": categoria_de(nombre.upper(), texto(p["Proveedor"])),
            "unidad": (texto(p["Presentación"]) or "UNIDAD").upper(),
            "minimo": p["Mínimo"] or 0,
            "proveedor": prov(p["Proveedor"]),
            "costo": p["Costo promedio (Q)"],
            "activo": activo,
            "existencia_papel": p["Existencias"] or 0,
        }
        if p["Mínimo"] is None:
            rep["sin_minimo"].append(codigo)
    assert len({p["codigo"] for p in productos.values()}) == len(productos), "códigos repetidos"

    nombres = collections.Counter(p["nombre"].upper() for p in productos.values())
    rep["nombre_repetido"] = [(p["codigo"], p["nombre"]) for p in productos.values() if nombres[p["nombre"].upper()] > 1]

    # ------------------------------------------------------------------ entradas → lotes
    entradas = []
    for e in entradas_x:
        codigo = texto(e["Código producto"])
        if codigo in excluidos:
            continue
        cantidad, precio = e["Cantidad"], float(e["Precio unitario (Q)"])
        ref = e["Entrada"]
        if ref in CORRECCIONES:
            f = CORRECCIONES[ref]["factor"]
            rep["correcciones"].append((ref, codigo, f"{cantidad} a Q{precio:.2f}", f"{cantidad // f} a Q{precio * f:.2f}", CORRECCIONES[ref]["motivo"]))
            cantidad, precio = cantidad // f, precio * f
        fecha = e["Fecha"].date()
        vence = e["Vence"].date() if e["Vence"] else None
        lote = texto(e["Lote"])
        if lote and LOTE_INVALIDO.match(lote):
            rep["lote_invalido"].append((ref, lote))
            lote = None
        if vence and vence < fecha:
            rep["entrada_rechazada"].append((ref, codigo, fecha, vence, "Vencimiento anterior a la fecha de ingreso (ck_lote_fecha_vencimiento)."))
            continue
        entradas.append({"ref": ref, "codigo": codigo, "fecha": fecha, "vence": vence, "lote": lote,
                         "cantidad": cantidad, "precio": precio,
                         "proveedor": prov(e["Proveedor"]) or productos[codigo]["proveedor"] or "DESCONOCIDO"})

    # requiere_vencimiento: si tiene entradas, lo dicen los datos (todas traen
    # vencimiento); si no, la categoría.
    por_producto = collections.defaultdict(list)
    for e in entradas:
        por_producto[e["codigo"]].append(e)
    for codigo, p in productos.items():
        es = por_producto.get(codigo)
        p["vence"] = all(e["vence"] for e in es) if es else p["categoria"] in CATEGORIAS_CON_VENCIMIENTO

    # Un lote = producto + número. Mismo número con otro vencimiento → sufijo.
    lotes = {}   # (codigo, numero) → dict
    for e in sorted(entradas, key=lambda e: (e["fecha"], e["ref"])):
        numero = e["lote"] or f"SL-{e['ref']}"
        clave = (e["codigo"], numero)
        k = 2
        while clave in lotes and lotes[clave]["vence"] != e["vence"]:
            clave = (e["codigo"], f"{numero}-{k}")
            k += 1
        if clave[1] != numero:
            rep["lote_sufijo"].append((e["ref"], e["codigo"], numero, clave[1]))
        if clave not in lotes:
            lotes[clave] = {"id": len(lotes) + 1, "codigo": e["codigo"], "numero": clave[1],
                            "proveedor": e["proveedor"], "ingreso": e["fecha"], "vence": e["vence"]}
        e["id_lote"] = lotes[clave]["id"]
    rep["entradas_sin_lote"] = sum(1 for e in entradas if not e["lote"])

    # ------------------------------------------------------------------ simulación en orden
    salidas_por_dia = collections.defaultdict(list)
    for s in salidas_x:
        codigo = texto(s["Código producto"])
        if codigo in excluidos:
            continue
        salidas_por_dia[s["Fecha"].date()].append({"ref": s["Salida"], "codigo": codigo,
                                                   "fecha": s["Fecha"].date(), "cantidad": s["Cantidad"]})
    entradas_por_dia = collections.defaultdict(list)
    for e in entradas:
        entradas_por_dia[e["fecha"]].append(e)

    existencia = collections.defaultdict(float)          # id_lote → cantidad
    lotes_de = collections.defaultdict(list)             # codigo → [lote]
    for l in lotes.values():
        lotes_de[l["codigo"]].append(l)
    eventos = []    # (fecha_hora, tipo, observacion, usuario, [(id_lote, cantidad, precio)])
    pendientes = collections.defaultdict(list)          # codigo → [salida]

    def disponible(codigo):
        return sum(existencia[l["id"]] for l in lotes_de[codigo])

    def fefo(salida, dia):
        """Reparte la salida entre lotes: primero los no vencidos a esa fecha,
        del que vence antes al que vence después (igual que sp_registrar_salida)."""
        orden = sorted((l for l in lotes_de[salida["codigo"]] if existencia[l["id"]] > 0),
                       key=lambda l: (l["vence"] is not None and l["vence"] < dia,
                                      l["vence"] or dt.date.max, l["ingreso"], l["id"]))
        restante, detalle, uso_vencido = salida["cantidad"], [], False
        for l in orden:
            if restante <= 0:
                break
            q = min(restante, existencia[l["id"]])
            existencia[l["id"]] -= q
            restante -= q
            detalle.append((l["id"], q, 0))
            uso_vencido |= l["vence"] is not None and l["vence"] < dia
        if uso_vencido:
            rep["salida_lote_vencido"].append((salida["ref"], salida["codigo"], dia))
        return detalle

    for dia in sorted(set(salidas_por_dia) | set(entradas_por_dia)):
        # Horas consecutivas (07:00, 07:01, ...) en el orden en que se procesan:
        # entradas, salidas ajustadas y salidas. Así el orden por fecha_hora es
        # exactamente el de esta simulación.
        minuto = itertools.count()
        inicio = dt.datetime.combine(dia, dt.time(7))

        def hora():
            return inicio + dt.timedelta(minutes=next(minuto))

        for e in sorted(entradas_por_dia[dia], key=lambda e: e["ref"]):
            existencia[e["id_lote"]] += e["cantidad"]
            eventos.append((hora(), "ENTRADA",
                            f"Entrada {e['ref']} (registro en papel)", [(e["id_lote"], e["cantidad"], e["precio"])]))
        for codigo in list(pendientes):
            siguen = []
            for s in pendientes[codigo]:
                if disponible(codigo) >= s["cantidad"]:
                    rep["salida_ajustada"].append((s["ref"], codigo, s["cantidad"], s["fecha"], dia))
                    eventos.append((hora(), "SALIDA",
                                    f"Salida {s['ref']} (registro en papel; fecha ajustada del {s['fecha']:%d/%m/%Y}, se anotó antes que su entrada)",
                                    fefo(s, dia)))
                else:
                    siguen.append(s)
            pendientes[codigo] = siguen
        for s in sorted(salidas_por_dia[dia], key=lambda s: s["ref"]):
            if disponible(s["codigo"]) >= s["cantidad"]:
                eventos.append((hora(), "SALIDA",
                                f"Salida {s['ref']} (registro en papel)", fefo(s, dia)))
            else:
                pendientes[s["codigo"]].append(s)
    for codigo, lista in pendientes.items():
        for s in lista:
            rep["salida_rechazada"].append((s["ref"], codigo, s["fecha"], s["cantidad"], disponible(codigo)))

    # Existencia final vs. la que reporta el Excel.
    for codigo, p in productos.items():
        if abs(disponible(codigo) - p["existencia_papel"]) > 0.001:
            rep["existencia_distinta"].append((p["codigo"], p["nombre"], p["existencia_papel"], disponible(codigo)))

    # ------------------------------------------------------------------ proveedor_producto
    precio_par = {}
    for e in sorted(entradas, key=lambda e: (e["fecha"], e["ref"])):
        precio_par[(e["proveedor"], e["codigo"])] = e["precio"]          # el último precio pagado
    for codigo, p in productos.items():
        if p["proveedor"] and (p["proveedor"], codigo) not in precio_par and p["costo"] is not None:
            precio_par[(p["proveedor"], codigo)] = float(p["costo"])
    rep["par_sin_precio"] = sum(1 for c, p in productos.items()
                                if p["proveedor"] and (p["proveedor"], c) not in precio_par)

    escribir_catalogo(productos, proveedores, precio_par)
    escribir_movimientos(productos, lotes, eventos)
    escribir_reporte(rep, productos, proveedores, lotes, eventos, precio_par, len(entradas_x), len(salidas_x))
    print(f"productos {len(productos)}, proveedores {len(proveedores)}, lotes {len(lotes)}, "
          f"movimientos {len(eventos)}, detalles {sum(len(d) for *_, d in eventos)}")


ENCABEZADO = """-- =============================================================================
-- Archivo:      {archivo}
-- Propósito:    {proposito}
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (Cristopher Alexis Castellanos Paz, José Eduardo Escobar)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/Bitacora-IA.md para el registro de uso.
-- ARCHIVO GENERADO por sql/dml/generar_carga.py a partir del inventario real
-- del laboratorio (registros en papel, marzo a septiembre de 2026, transcritos
-- a Excel). No editar a mano: corregir el generador y volver a ejecutarlo.
-- Hallazgos y decisiones de la carga: docs/entrega-3/reporte-carga-datos.md
-- Descripción:  {descripcion}
-- Dependencias: {dependencias}
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f {archivo}
-- =============================================================================
"""


def escribir_catalogo(productos, proveedores, precio_par):
    o = [ENCABEZADO.format(
        archivo="002_carga_catalogo.sql",
        proposito="Cargar el catálogo real: categorías, productos, proveedores\n--               y precios por proveedor (proveedor_producto).",
        descripcion=f"{len(productos)} productos, {len(proveedores)} proveedores reales + 24 de\n"
                    "--               prueba inactivos (consigna: 50 por tabla principal).\n"
                    "--               Las FK se resuelven por nombre/código, nunca por id.",
        dependencias="001_schema.sql, 001_triggers.sql, 001_seed.sql")]
    o.append("BEGIN;\n")
    o.append("-- Categorías que el inventario real necesita además de las de 001_seed.sql.")
    o.append("INSERT INTO categoria (nombre, descripcion) VALUES")
    o.append(",\n".join("    " + fila_sql(c) for c in CATEGORIAS_NUEVAS.items()) + ";\n")

    o.append("-- Proveedores reales. El inventario en papel no registra NIT (obligatorio y")
    o.append("-- único en el modelo): se asigna uno provisional que el administrador corrige")
    o.append("-- desde la aplicación. Proveedores que son personas: anonimizados.")
    o.append("INSERT INTO proveedor (nombre, nit) VALUES")
    o.append(",\n".join("    " + fila_sql((n, f"SIN-NIT-{i:02d}")) for i, n in enumerate(proveedores, 1)) + ";\n")

    o.append("-- 24 proveedores DE PRUEBA (no existen) para llegar a 50, inactivos para que")
    o.append("-- no aparezcan al registrar entradas. Nombres generados de forma determinista.")
    o.append("""INSERT INTO proveedor (nombre, nit, telefono, correo, direccion, estado)
SELECT format('%s %s %s, S.A.',
              (ARRAY['Distribuidora', 'Comercial', 'Importadora', 'Suministros', 'Droguería', 'Grupo'])[1 + i % 6],
              (ARRAY['Médica', 'Clínica', 'Diagnóstica', 'de Laboratorio', 'Hospitalaria', 'Biomédica', 'Científica', 'Analítica'])[1 + (i / 6) % 8],
              (ARRAY['del Altiplano', 'de Occidente', 'Xela', 'Centroamericana', 'Guatemalteca', 'del Pacífico', 'Maya'])[1 + i % 7]),
       format('%s-%s', 5000000 + i * 1373, i % 10),
       format('7%s', lpad((7760000 + i * 211)::TEXT, 7, '0')),
       format('ventas%s@proveedor%s.com.gt', i, i),
       format('%s calle %s-%s zona %s, Quetzaltenango', 1 + i % 20, 1 + i % 15, 10 + i % 80, 1 + i % 12),
       FALSE
  FROM generate_series(1, 24) AS g(i);
""")

    o.append("-- Productos. Columnas: categoría (por nombre), código, nombre, unidad,")
    o.append("-- stock mínimo, requiere vencimiento (RN-07), estado.")
    o.append("INSERT INTO producto (id_categoria, codigo, nombre, unidad_medida, stock_minimo, requiere_vencimiento, estado)")
    o.append("SELECT c.id_categoria, v.codigo, v.nombre, v.unidad, v.minimo, v.vence, v.estado")
    o.append("  FROM (VALUES")
    filas = [fila_sql((p["categoria"], p["codigo"], p["nombre"], p["unidad"], p["minimo"], p["vence"], True))
             for p in sorted(productos.values(), key=lambda p: p["nombre"])]
    o.append(",\n".join("    " + f for f in filas))
    o.append("  ) AS v(categoria, codigo, nombre, unidad, minimo, vence, estado)")
    o.append("  JOIN categoria c ON c.nombre = v.categoria;\n")
    o.append("-- Los productos desactivados se dan de baja en 004, después de cargar su historial.\n")

    o.append("-- PROVEEDOR-PRODUCTO (RN-16): último precio pagado a cada proveedor según las")
    o.append("-- entradas; si nunca hubo entrada, el costo promedio del inventario.")
    o.append("INSERT INTO proveedor_producto (id_proveedor, id_producto, precio_compra)")
    o.append("SELECT pr.id_proveedor, p.id_producto, v.precio")
    o.append("  FROM (VALUES")
    o.append(",\n".join("    " + fila_sql((prov, productos[c]["codigo"], float(precio)))
                        for (prov, c), precio in sorted(precio_par.items())))
    o.append("  ) AS v(proveedor, codigo, precio)")
    o.append("  JOIN proveedor pr ON pr.nombre = v.proveedor")
    o.append("  JOIN producto  p  ON p.codigo  = v.codigo;\n")
    o.append("COMMIT;\n\n-- Fin de 002_carga_catalogo.sql")
    SALIDA_CATALOGO.write_text("\n".join(o) + "\n", encoding="utf-8")


def escribir_movimientos(productos, lotes, eventos):
    # Se conserva el orden de la simulación; las horas ya son crecientes.
    assert all(a[0] < b[0] for a, b in zip(eventos, eventos[1:])), "horas fuera de orden"
    o = [ENCABEZADO.format(
        archivo="004_carga_movimientos.sql",
        proposito="Cargar el historial real de inventario: lotes, entradas y\n--               salidas, con la existencia calculada por los triggers.",
        descripcion=f"{len(lotes)} lotes y {len(eventos)} movimientos "
                    f"({sum(1 for e in eventos if e[1] == 'ENTRADA')} entradas, "
                    f"{sum(1 for e in eventos if e[1] == 'SALIDA')} salidas).\n"
                    "--               Cómo se garantiza la coherencia:\n"
                    "--               1. Todo lote se inserta con cantidad_disponible = 0.\n"
                    "--               2. Los movimientos se insertan EN ORDEN DE FECHA y el\n"
                    "--                  trigger trg_detalle_movimiento_existencia suma o resta\n"
                    "--                  cada detalle. Si una salida excediera la existencia,\n"
                    "--                  el trigger abortaría toda la carga (RN-01/RN-04).\n"
                    "--               3. Las salidas ya vienen repartidas por lote con FEFO\n"
                    "--                  (mismo criterio que sp_registrar_salida).\n"
                    "--               INSERT directo y no CALL: los procedimientos registran\n"
                    "--               con fecha now(); una carga histórica necesita fechas\n"
                    "--               pasadas. Las reglas de existencia viven en el trigger.\n"
                    "--               Responsable: el papel no registra quién hizo cada\n"
                    "--               movimiento; se asignan al usuario encargado.dev (RN-08).",
        dependencias="002_carga_catalogo.sql y web/seed_usuarios.py\n"
                     "--               (los movimientos necesitan un usuario responsable)")]
    o.append("BEGIN;\n")
    o.append("CREATE TEMP TABLE carga_lote (ref INTEGER, codigo VARCHAR(30), numero_lote VARCHAR(50),")
    o.append("                              proveedor VARCHAR(150), fecha_ingreso DATE, fecha_vencimiento DATE);")
    o.append("CREATE TEMP TABLE carga_movimiento (orden INTEGER, tipo VARCHAR(10), fecha_hora TIMESTAMP, observacion VARCHAR(255));")
    o.append("CREATE TEMP TABLE carga_detalle (orden INTEGER, ref_lote INTEGER, cantidad NUMERIC(10,2), precio NUMERIC(10,2));\n")
    o.append("INSERT INTO carga_lote VALUES")
    o.append(",\n".join("    " + fila_sql((l["id"], productos[l["codigo"]]["codigo"], l["numero"], l["proveedor"], l["ingreso"], l["vence"]))
                        for l in sorted(lotes.values(), key=lambda l: l["id"])) + ";\n")
    o.append("INSERT INTO carga_movimiento VALUES")
    o.append(",\n".join("    " + fila_sql((i, tipo, fh, obs)) for i, (fh, tipo, obs, _) in enumerate(eventos, 1)) + ";\n")
    o.append("INSERT INTO carga_detalle VALUES")
    o.append(",\n".join("    " + fila_sql((i, lote, float(q), float(p)))
                        for i, (*_, det) in enumerate(eventos, 1) for lote, q, p in det) + ";\n")
    o.append("""-- Lotes: nacen en 0; la existencia la ponen las entradas.
CREATE TEMP TABLE carga_lote_id AS
SELECT cl.ref, p.id_producto, pr.id_proveedor, cl.numero_lote, cl.fecha_ingreso, cl.fecha_vencimiento
  FROM carga_lote cl
  JOIN producto  p  ON p.codigo  = cl.codigo
  JOIN proveedor pr ON pr.nombre = cl.proveedor;

INSERT INTO lote (id_producto, id_proveedor, numero_lote, fecha_ingreso, fecha_vencimiento, cantidad_disponible)
SELECT id_producto, id_proveedor, numero_lote, fecha_ingreso, fecha_vencimiento, 0
  FROM carga_lote_id
 ORDER BY ref;

DO $$
DECLARE
    v_id_usuario    usuario.id_usuario%TYPE;
    v_id_movimiento movimiento.id_movimiento%TYPE;
    r_mov           RECORD;
BEGIN
    SELECT id_usuario INTO v_id_usuario FROM usuario WHERE usuario = 'encargado.dev';
    IF v_id_usuario IS NULL THEN
        RAISE EXCEPTION 'Falta el usuario encargado.dev. Ejecute web/seed_usuarios.py antes de este script.';
    END IF;

    IF (SELECT count(*) FROM carga_lote_id) <> (SELECT count(*) FROM carga_lote) THEN
        RAISE EXCEPTION 'Hay lotes cuyo producto o proveedor no existe. Ejecute primero 002_carga_catalogo.sql.';
    END IF;

    -- Un movimiento por registro del papel, en orden cronológico; el
    -- trigger actualiza la existencia con cada detalle.
    FOR r_mov IN SELECT * FROM carga_movimiento ORDER BY orden LOOP
        INSERT INTO movimiento (id_usuario, tipo_movimiento, fecha_hora, observacion)
        VALUES (v_id_usuario, r_mov.tipo, r_mov.fecha_hora, r_mov.observacion)
        RETURNING id_movimiento INTO v_id_movimiento;

        INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad, precio_unitario)
        SELECT v_id_movimiento, l.id_lote, cd.cantidad, cd.precio
          FROM carga_detalle cd
          JOIN carga_lote_id cl ON cl.ref = cd.ref_lote
          JOIN lote l ON l.id_producto = cl.id_producto AND l.numero_lote = cl.numero_lote
         WHERE cd.orden = r_mov.orden;
    END LOOP;
END;
$$;
""")
    desact = [p["codigo"] for p in productos.values() if not p["activo"]]
    if desact:
        o.append("-- Productos que el inventario marca como desactivados: baja lógica (estado).")
        o.append("UPDATE producto SET estado = FALSE WHERE codigo IN (" + ", ".join(sql(c) for c in desact) + ");\n")
    o.append("DROP TABLE carga_detalle, carga_movimiento, carga_lote_id, carga_lote;\n")
    o.append("COMMIT;\n\n-- Fin de 004_carga_movimientos.sql")
    SALIDA_MOVIMIENTOS.write_text("\n".join(o) + "\n", encoding="utf-8")


def celda(v):
    if v is None:
        return ""
    if isinstance(v, dt.date):
        return f"{v:%d/%m/%Y}"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def tabla(encabezado, filas):
    if not filas:
        return "_Ninguno._\n"
    t = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    t += ["| " + " | ".join(celda(v) for v in f) + " |"
          for f in filas]
    return "\n".join(t) + "\n"


def escribir_reporte(rep, productos, proveedores, lotes, eventos, precio_par, n_entradas, n_salidas):
    n_e = sum(1 for e in eventos if e[1] == "ENTRADA")
    n_s = sum(1 for e in eventos if e[1] == "SALIDA")
    cats = collections.Counter(p["categoria"] for p in productos.values())
    r = [f"""# Reporte de carga del inventario real

Generado por `sql/dml/generar_carga.py`. Fuente: inventario del laboratorio de marzo a septiembre de 2026, llevado **en papel** y transcrito a Excel. El Excel no se publica en el repositorio.

Cada registro del papel pasó por las mismas reglas que aplica la base de datos (CHECK, triggers y el criterio FEFO de `sp_registrar_salida`). Este reporte lista lo que **no** cumplía esas reglas y qué se hizo con cada caso. Es evidencia de por qué el laboratorio necesita el sistema: en papel, nada de esto se detectó.

## Resumen

| Dato | En el papel | Cargado |
|---|---|---|
| Productos | {len(productos) + len(rep['servicios'])} | {len(productos)} ({len(rep['servicios'])} servicios excluidos) |
| Proveedores | {len(proveedores)} | {len(proveedores)} reales + 24 de prueba inactivos = {len(proveedores) + 24} |
| Entradas | {n_entradas} | {n_e} |
| Salidas | {n_salidas} | {n_s} |
| Lotes | — | {len(lotes)} |
| Precios proveedor-producto | — | {len(precio_par)} |

## Problemas de calidad encontrados

### 1. Salidas anotadas antes que su entrada ({len(rep['salida_ajustada'])})

El papel registra el consumo de un insumo días antes que la entrada que lo trajo. Lo más probable es que el insumo llegó y se usó antes de anotar la factura. La base de datos rechaza estas salidas porque dejarían existencia negativa (RN-01). **Decisión del equipo:** mover cada una a la fecha de la entrada que la cubre. La observación del movimiento conserva la fecha original.

{tabla(["Salida", "Producto", "Cantidad", "Fecha en papel", "Fecha cargada"], rep['salida_ajustada'])}
### 2. Salidas rechazadas ({len(rep['salida_rechazada'])})

No existe ninguna entrada posterior que las cubra: en el papel, la existencia quedó negativa.

{tabla(["Salida", "Producto", "Fecha", "Cantidad", "Existencia al final"], rep['salida_rechazada'])}
### 3. Entradas rechazadas ({len(rep['entrada_rechazada'])})

{tabla(["Entrada", "Producto", "Ingreso", "Vence", "Motivo"], rep['entrada_rechazada'])}
### 4. Correcciones con evidencia ({len(rep['correcciones'])})

{tabla(["Entrada", "Producto", "En papel", "Cargado", "Motivo"], rep['correcciones'])}
Evidencia: con la conversión, entradas − salidas de este producto da exactamente la existencia que reporta el inventario (26 cajas), y el precio por caja coincide con las demás compras (Q475–Q487.50).

### 5. Números de lote

- {rep['entradas_sin_lote']} entradas no traen número de lote. Se creó uno por entrada con el formato `SL-<entrada>` (por ejemplo `SL-E000001`), para que cada compra siga siendo rastreable.
- Lotes que en realidad eran un número decimal generado por Excel al transcribir ({len(rep['lote_invalido'])}); se trataron como "sin lote": {', '.join(f'{a} (`{b}`)' for a, b in rep['lote_invalido']) or 'ninguno'}.
- {len(rep['lote_sufijo'])} entradas repiten un número de lote del mismo producto con **otra** fecha de vencimiento. En la base, un número de lote es único por producto, así que se les agregó un sufijo:

{tabla(["Entrada", "Producto", "Lote en papel", "Lote cargado"], rep['lote_sufijo'])}
### 6. Salidas cubiertas con un lote ya vencido ({len(rep['salida_lote_vencido'])})

Al repartir por FEFO, estas salidas solo tenían existencia en lotes vencidos a esa fecha. Se cargaron porque el consumo sí ocurrió. En la operación normal, `sp_registrar_salida` no permite usar lotes vencidos. Revisar si el vencimiento se transcribió mal o si se usó reactivo vencido.

{tabla(["Salida", "Producto", "Fecha"], rep['salida_lote_vencido'][:40])}{'_(se muestran 40)_' if len(rep['salida_lote_vencido']) > 40 else ''}
### 7. Existencia final distinta a la del Excel ({len(rep['existencia_distinta'])})

La columna "Existencias" del Excel se calculó como entradas − salidas, sin validar. Las diferencias vienen de los rechazos y correcciones anteriores.

{tabla(["Código", "Producto", "Excel", "Base de datos"], rep['existencia_distinta'])}
### 8. Otros

- **Servicios excluidos** (no son artículos de inventario): {', '.join(n for _, n in rep['servicios'])}.
- **Productos desactivados** (el código traía el prefijo `/DESACT/`): se cargan con su historial y se dan de baja lógica al final: {', '.join(f'{b} ({n})' for _, b, n in rep['desactivados'])}.
- **Nombre repetido con distinto código** (posible duplicado a revisar): {', '.join(f'{c}' for c, _ in rep['nombre_repetido'])} — {rep['nombre_repetido'][0][1] if rep['nombre_repetido'] else ''}.
- **Productos sin stock mínimo**: {len(rep['sin_minimo'])}, se cargaron con 0.
- **Proveedor-producto sin precio**: {rep['par_sin_precio']} productos tienen proveedor pero nunca se compraron ni tienen costo registrado; no se cargó esa relación porque `precio_compra` es obligatorio.

## Decisiones de la carga

| Tema | Decisión |
|---|---|
| NIT de proveedores | El papel no lo registra. NIT provisional `SIN-NIT-01`… (obligatorio y único en el modelo); se corrige desde la aplicación. |
| Proveedores personas | {rep['anonimizados']} proveedores son personas individuales: se publican como `PROVEEDOR INDIVIDUAL ##` (el repositorio es público). |
| 50 proveedores | Solo hay {len(proveedores)} reales. Se agregan 24 **de prueba**, inactivos, para cumplir el mínimo de la consigna sin mezclarlos con los reales. |
| Categorías | El papel no las trae. Se asignaron por palabras clave del nombre (reglas en `generar_carga.py`). |
| Requiere vencimiento | Si el producto tiene entradas: sí, cuando todas traen vencimiento. Si no tiene: según su categoría. |
| Responsable | El papel no registra quién hizo el movimiento: se asignan a `encargado.dev`. |
| Horas | El papel solo trae la fecha. Cada día se numeran desde las 07:00, un minuto por registro: primero las entradas, luego las salidas ajustadas y al final las salidas, en el orden del papel. |

## Productos por categoría

{tabla(["Categoría", "Productos"], sorted(cats.items()))}"""]
    SALIDA_REPORTE.write_text("\n".join(r), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
