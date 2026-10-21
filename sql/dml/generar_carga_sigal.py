"""
Archivo:      generar_carga_sigal.py
Propósito:    Poner al día el inventario con los movimientos que el
              laboratorio registró en SIGAL después de la carga del papel.
Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
              Privado Quetzaltenango
Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
              — generado con apoyo de IA (Claude Code); ver
              docs/bitacora-ia/ENTREGA4_BITACORA_IA.md.

Genera:
  sql/dml/005_carga_sigal.sql                     productos y proveedores nuevos,
                                                  lotes, entradas y salidas
  docs/entrega-4/ENTREGA4_REPORTE_CARGA_SIGAL.md  hallazgos y decisiones (la sección
                                                  "Verificación después de cargar" se
                                                  agregó a mano tras aplicar la carga)

Uso (el respaldo de SIGAL NO está en el repositorio: son datos internos):
  1. La base debe estar cargada hasta sql/dml/004_carga_movimientos.sql: el
     generador lee de ella la existencia de cada lote para repartir las
     salidas por FEFO, igual que la carga del papel.
  2. cd web  (usa el .env de la raíz para conectarse)
     python ../sql/dml/generar_carga_sigal.py "ruta/respaldo_sigal.sql"

Decisiones (las mismas de generar_carga.py, detalladas en el reporte):
  1. Se cargan solo los movimientos de SIGAL posteriores al 23/09/2026 (último
     registro del papel) cuyo código (E######, S######) no esté ya en la base.
     SIGAL conservó la numeración del papel, así que el código identifica el
     mismo registro en los dos sistemas.
  2. Servicios (mantenimientos, reparaciones, fletes, rentas) no son
     inventario: se excluyen, con la misma expresión de generar_carga.py.
  3. Entradas sin número de lote: lote "SL-<entrada>".
  4. Si el lote (producto + número) ya existe, la entrada se suma a él y
     conserva su vencimiento original, igual que sp_registrar_entrada.
  5. Salidas: se reparten por FEFO (sin lotes vencidos, como
     sp_registrar_salida). Si a esa fecha solo hay existencia en lotes
     vencidos, se usan y se anotan. Si no hay existencia, la salida se mueve
     a la fecha de la entrada que la cubre; si ninguna la cubre, se rechaza.
  6. Responsable: encargado.dev, igual que la carga del papel (en SIGAL los
     usuarios son personas con nombre; el repositorio es público). La
     observación conserva el código y, en las salidas, el área solicitante.
  7. Fechas: SIGAL las guarda en UTC; se convierten a hora de Guatemala.
  8. Proveedores nuevos: NIT provisional SIN-NIT-##, como en la carga del
     papel. Si apareciera un proveedor persona individual, el generador se
     detiene (habría que anonimizarlo antes de publicar).
"""

import collections
import datetime as dt
import hashlib
import re
import sys
import types
from decimal import Decimal
from pathlib import Path

import psycopg

RAIZ = Path(__file__).resolve().parents[2]
SALIDA_SQL = RAIZ / "sql" / "dml" / "005_carga_sigal.sql"
SALIDA_REPORTE = RAIZ / "docs" / "entrega-4" / "ENTREGA4_REPORTE_CARGA_SIGAL.md"
CORTE = dt.date(2026, 9, 23)          # último día del registro en papel
GT = dt.timezone(dt.timedelta(hours=-6))
NULO = "\\N"

# Mismas reglas de categoría, servicios y proveedores-persona que la carga del
# papel. generar_carga.py importa openpyxl (para leer el Excel), que aquí no
# se usa: se registra un módulo vacío para poder importar sus reglas.
sys.modules.setdefault("openpyxl", types.ModuleType("openpyxl"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar_carga as papel  # noqa: E402

sys.path.insert(0, str(RAIZ / "web"))
from config import Config  # noqa: E402


def leer_dump(ruta):
    """Tablas del respaldo de pg_dump como listas de dict (bloques COPY)."""
    tablas, actual, columnas = {}, None, None
    for linea in open(ruta, encoding="utf-8"):
        if linea.startswith("COPY public."):
            actual = linea.split()[1].split(".")[1]
            columnas = linea[linea.index("(") + 1:linea.index(")")].split(", ")
            tablas[actual] = []
        elif actual:
            if linea.rstrip("\n") == "\\.":
                actual = None
            else:
                tablas[actual].append(dict(zip(columnas, linea.rstrip("\n").split("\t"))))
    return tablas


def valor(texto):
    return None if texto in (NULO, "") else texto


def hora_local(texto):
    """'2026-09-28 12:53:55.714225+00' (UTC) -> hora de Guatemala sin zona."""
    base = texto.split(".")[0].split("+")[0]
    utc = dt.datetime.fromisoformat(base).replace(tzinfo=dt.timezone.utc)
    return utc.astimezone(GT).replace(tzinfo=None, microsecond=0)


def sql_texto(t):
    return "NULL" if t is None else "'" + str(t).replace("'", "''") + "'"


def conectar():
    if Config.DATABASE_URL:
        return psycopg.connect(Config.DATABASE_URL)
    return psycopg.connect(host=Config.DB_HOST, port=Config.DB_PORT, dbname=Config.DB_NAME,
                           user=Config.DB_USER, password=Config.DB_PASSWORD)


def main(ruta_respaldo):
    S = leer_dump(ruta_respaldo)
    productos_s = {p["id"]: p for p in S["productos"]}
    proveedores_s = {p["id"]: p["nombre"].strip() for p in S["proveedores"]}
    presentacion_s = {p["id"]: p["nombre"].strip().upper() for p in S["catalogo_presentacion"]}
    areas_s = {a["id"]: a["nombre"].strip() for a in S["areas"]}
    area_usuario = {u["id"]: areas_s.get(u["area_id"]) for u in S["usuarios"]}

    with conectar() as c:
        if c.execute("SELECT count(*) FROM movimiento WHERE observacion LIKE '%(SIGAL)%'").fetchone()[0]:
            sys.exit("La base ya tiene movimientos de SIGAL: el generador debe correr sobre la base cargada solo hasta 004.")
        observaciones = " ".join(r[0] or "" for r in c.execute("SELECT observacion FROM movimiento"))
        productos_db = {r[0]: {"vence": r[1], "estado": r[2]} for r in c.execute(
            "SELECT codigo, requiere_vencimiento, estado FROM producto")}
        proveedores_db = {r[0] for r in c.execute("SELECT nombre FROM proveedor")}
        nit_max = max(int(r[0].rsplit("-", 1)[1]) for r in c.execute(
            "SELECT nit FROM proveedor WHERE nit LIKE 'SIN-NIT-%'"))
        lotes = {}
        for codigo, numero, vence, ingreso, cantidad, estado, id_lote in c.execute(
                """SELECT p.codigo, l.numero_lote, l.fecha_vencimiento, l.fecha_ingreso, l.cantidad_disponible,
                          l.estado, l.id_lote
                     FROM lote l JOIN producto p ON p.id_producto = l.id_producto
                    WHERE p.codigo NOT LIKE 'PRUEBA-%'"""):
            lotes[(codigo, numero)] = {"vence": vence, "ingreso": ingreso, "cant": Decimal(cantidad),
                                       "estado": estado, "orden": id_lote, "nuevo": False}
    ya_cargados = set(re.findall(r"\b([ES]\d{6})\b", observaciones))

    hallazgos = collections.defaultdict(list)

    def es_servicio(p):
        return bool(papel.SERVICIO.search(p["nombre"].upper())) or p["codigo"].startswith("/DESACT/")

    def elegir(filas, tipo):
        elegidas = []
        for f in filas:
            fecha = hora_local(f["fecha_hora"])
            if f["codigo"] in ya_cargados or fecha.date() <= CORTE:
                continue
            producto = productos_s[f["producto_id"]]
            if es_servicio(producto):
                hallazgos["servicios"].append((f["codigo"], producto["codigo"], producto["nombre"]))
                continue
            elegidas.append({**f, "fecha": fecha, "producto": producto, "tipo": tipo})
        return elegidas

    entradas = elegir(S["entradas"], "ENTRADA")
    salidas = elegir(S["salidas"], "SALIDA")

    # ---- Productos y proveedores nuevos --------------------------------------
    productos_nuevos = {}
    for e in entradas + salidas:
        p = e["producto"]
        if p["codigo"] in productos_db or p["codigo"] in productos_nuevos:
            continue
        sus_entradas = [x for x in entradas if x["producto"]["codigo"] == p["codigo"]]
        proveedor = proveedores_s.get(sus_entradas[0]["proveedor_id"]) if sus_entradas else None
        productos_nuevos[p["codigo"]] = {
            "codigo": p["codigo"], "nombre": p["nombre"].strip(),
            "categoria": papel.categoria_de(p["nombre"].upper(), proveedor),
            "unidad": presentacion_s.get(p["presentacion_id"], "UNIDAD"),
            "minimo": Decimal(valor(p["min_stock"]) or 0).quantize(Decimal("0.01")),
            "vence": bool(sus_entradas) and all(valor(x["expira"]) for x in sus_entradas),
        }
        productos_db[p["codigo"]] = {"vence": productos_nuevos[p["codigo"]]["vence"], "estado": True}

    proveedores_nuevos = {}
    for e in entradas:
        nombre = proveedores_s.get(e["proveedor_id"])
        if nombre is None or nombre in proveedores_db or nombre in proveedores_nuevos:
            continue
        if hashlib.sha256(nombre.upper().encode()).hexdigest() in papel.PERSONAS:
            sys.exit("Un proveedor nuevo es una persona individual: anonimícelo antes de generar la carga.")
        nit_max += 1
        proveedores_nuevos[nombre] = f"SIN-NIT-{nit_max:02d}"

    # ---- Movimientos en orden cronológico ---------------------------------------
    eventos = sorted(entradas + salidas, key=lambda x: (x["fecha"], x["tipo"] != "ENTRADA", x["codigo"]))
    movimientos, pendientes = [], collections.defaultdict(list)
    precio_prov = {}

    def repartir(codigo, cantidad, dia):
        """FEFO sin lotes vencidos; si no alcanza, también vencidos. None si no hay."""
        del_producto = [(k, l) for k, l in lotes.items() if k[0] == codigo and l["estado"] and l["cant"] > 0]
        orden = lambda kl: (kl[1]["vence"] is None, kl[1]["vence"] or dt.date.max, kl[1]["ingreso"], kl[1]["orden"])
        vigentes = sorted([kl for kl in del_producto if kl[1]["vence"] is None or kl[1]["vence"] >= dia], key=orden)
        vencidos = sorted([kl for kl in del_producto if kl[1]["vence"] is not None and kl[1]["vence"] < dia], key=orden)
        if sum(l["cant"] for _, l in vigentes + vencidos) < cantidad:
            return None, False
        uso_vencido = sum(l["cant"] for _, l in vigentes) < cantidad
        partes, falta = [], cantidad
        for k, l in vigentes + vencidos:
            if falta <= 0:
                break
            toma = min(falta, l["cant"])
            l["cant"] -= toma
            falta -= toma
            partes.append((k, toma))
        return partes, uso_vencido

    def registrar_salida(s, fecha, movida_de=None):
        codigo = s["producto"]["codigo"]
        cantidad = Decimal(s["cantidad"])
        partes, uso_vencido = repartir(codigo, cantidad, fecha.date())
        if partes is None:
            return False
        if uso_vencido:
            hallazgos["vencidos"].append((s["codigo"], codigo, fecha.date()))
        area = area_usuario.get(s["solicita_usuario_id"])
        obs = f"Salida {s['codigo']} (SIGAL)" + (f", área {area}" if area and area.lower() != "prueba" else "")
        if movida_de:
            obs += f"; registrada en SIGAL el {movida_de:%d/%m/%Y}"
            hallazgos["movidas"].append((s["codigo"], codigo, cantidad, movida_de, fecha.date()))
        movimientos.append({"tipo": "SALIDA", "fecha": fecha, "obs": obs,
                            "detalle": [(k, q, Decimal(0)) for k, q in partes]})
        return True

    for ev in eventos:
        codigo = ev["producto"]["codigo"]
        if ev["tipo"] == "ENTRADA":
            numero = (valor(ev["lote"]) or "").strip() or f"SL-{ev['codigo']}"
            if not valor(ev["lote"]):
                hallazgos["sin_lote"].append((ev["codigo"], codigo, numero))
            vence = dt.date.fromisoformat(valor(ev["expira"])[:10]) if valor(ev["expira"]) else None
            proveedor = proveedores_s.get(ev["proveedor_id"])
            clave = (codigo, numero)
            if clave not in lotes:
                if vence and vence < ev["fecha"].date():
                    hallazgos["rechazadas"].append((ev["codigo"], codigo, "Vencimiento anterior al ingreso."))
                    continue
                if vence is None and productos_db[codigo]["vence"]:
                    hallazgos["rechazadas"].append((ev["codigo"], codigo, "Sin vencimiento en un producto que lo requiere (RN-07)."))
                    continue
                lotes[clave] = {"vence": vence, "ingreso": ev["fecha"].date(), "cant": Decimal(0), "estado": True,
                                "orden": 10**9 + len(lotes), "nuevo": True, "proveedor": proveedor}
            elif not lotes[clave]["estado"]:
                hallazgos["rechazadas"].append((ev["codigo"], codigo, f"El lote {numero} está dado de baja."))
                continue
            elif vence and lotes[clave]["vence"] and vence != lotes[clave]["vence"]:
                hallazgos["vence_distinto"].append((ev["codigo"], codigo, numero, lotes[clave]["vence"], vence))
            cantidad, precio = Decimal(ev["cantidad"]), Decimal(ev["precio_unitario"]).quantize(Decimal("0.01"))
            lotes[clave]["cant"] += cantidad
            movimientos.append({"tipo": "ENTRADA", "fecha": ev["fecha"], "obs": f"Entrada {ev['codigo']} (SIGAL)",
                                "detalle": [(clave, cantidad, precio)]})
            if proveedor:
                precio_prov[(proveedor, codigo)] = precio
            # Salidas que esperaban existencia de este producto (decisión 5).
            for s in list(pendientes[codigo]):
                if registrar_salida(s, ev["fecha"] + dt.timedelta(seconds=1), movida_de=s["fecha"].date()):
                    pendientes[codigo].remove(s)
        elif not registrar_salida(ev, ev["fecha"]):
            pendientes[codigo].append(ev)

    for codigo, lista in pendientes.items():
        for s in lista:
            hallazgos["salidas_rechazadas"].append((s["codigo"], codigo, Decimal(s["cantidad"]), s["fecha"].date()))

    movimientos.sort(key=lambda m: m["fecha"])
    escribir_sql(movimientos, lotes, productos_nuevos, proveedores_nuevos, precio_prov)
    escribir_reporte(movimientos, lotes, productos_nuevos, proveedores_nuevos, hallazgos, precio_prov)
    n_ent = sum(m["tipo"] == "ENTRADA" for m in movimientos)
    print(f"{SALIDA_SQL.name}: {n_ent} entradas, {len(movimientos) - n_ent} salidas, "
          f"{sum(l['nuevo'] for l in lotes.values())} lotes nuevos, {len(productos_nuevos)} productos y "
          f"{len(proveedores_nuevos)} proveedores nuevos.")


def escribir_sql(movimientos, lotes, productos_nuevos, proveedores_nuevos, precio_prov):
    n_ent = sum(m["tipo"] == "ENTRADA" for m in movimientos)
    nuevos = [(k, l) for k, l in lotes.items() if l["nuevo"]]
    desde = min(m["fecha"] for m in movimientos)
    hasta = max(m["fecha"] for m in movimientos)
    o = []
    o.append(f"""-- =============================================================================
-- Archivo:      005_carga_sigal.sql
-- Propósito:    Poner al día el inventario con los movimientos registrados en
--               SIGAL después del registro en papel ({desde:%d/%m/%Y} a {hasta:%d/%m/%Y}).
-- Proyecto:     Sistema Web de Gestión y Control de Inventario — Laboratorio
--               Privado Quetzaltenango
-- Autor:        Equipo (José Eduardo Escobar, Cristopher Alexis Castellanos Paz)
--               — generado con apoyo de IA (Claude Code); ver
--               docs/bitacora-ia/ENTREGA4_BITACORA_IA.md.
-- ARCHIVO GENERADO por sql/dml/generar_carga_sigal.py a partir del respaldo
-- de SIGAL del 21/10/2026. No editar a mano: corregir el generador.
-- Hallazgos y decisiones: docs/entrega-4/ENTREGA4_REPORTE_CARGA_SIGAL.md
-- Descripción:  {len(productos_nuevos)} productos y {len(proveedores_nuevos)} proveedores nuevos,
--               {len(nuevos)} lotes nuevos y {len(movimientos)} movimientos
--               ({n_ent} entradas, {len(movimientos) - n_ent} salidas). Mismo método que
--               004_carga_movimientos.sql: lotes nuevos en 0, movimientos en
--               orden de fecha y el trigger de existencia valida cada uno.
--               Las salidas ya vienen repartidas por FEFO.
-- Dependencias: 004_carga_movimientos.sql (y las migraciones de devolución,
--               baja de exámenes y corrección de entradas, si ya se aplicaron)
-- SGBD:         PostgreSQL 14+
-- Ejecutar:     psql -U usuario_app -d inventario_laboratorio -f 005_carga_sigal.sql
-- =============================================================================

BEGIN;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM movimiento WHERE observacion LIKE '%(SIGAL)%') THEN
        RAISE EXCEPTION 'Esta carga ya se aplicó: la base tiene movimientos de SIGAL.';
    END IF;
END;
$$;
""")
    if proveedores_nuevos:
        o.append("-- Proveedores nuevos (NIT provisional, como en la carga del papel).")
        o.append("INSERT INTO proveedor (nombre, nit) VALUES\n" + ",\n".join(
            f"    ({sql_texto(n)}, {sql_texto(nit)})" for n, nit in proveedores_nuevos.items()) + ";\n")
    if productos_nuevos:
        o.append("-- Productos nuevos: categoría por palabras clave (reglas de generar_carga.py).")
        o.append("INSERT INTO producto (id_categoria, codigo, nombre, unidad_medida, stock_minimo, requiere_vencimiento)\n"
                 "SELECT c.id_categoria, v.codigo, v.nombre, v.unidad, v.minimo, v.vence\n  FROM (VALUES\n" + ",\n".join(
                     f"    ({sql_texto(p['categoria'])}, {sql_texto(p['codigo'])}, {sql_texto(p['nombre'])}, "
                     f"{sql_texto(p['unidad'])}, {p['minimo']}, {'TRUE' if p['vence'] else 'FALSE'})"
                     for p in productos_nuevos.values())
                 + "\n  ) AS v (categoria, codigo, nombre, unidad, minimo, vence)\n  JOIN categoria c ON c.nombre = v.categoria;\n")
    o.append("""CREATE TEMP TABLE carga_lote (codigo VARCHAR(30), numero_lote VARCHAR(50), proveedor VARCHAR(150),
                              fecha_ingreso DATE, fecha_vencimiento DATE);
CREATE TEMP TABLE carga_movimiento (orden INTEGER, tipo VARCHAR(10), fecha_hora TIMESTAMP, observacion VARCHAR(255));
CREATE TEMP TABLE carga_detalle (orden INTEGER, codigo VARCHAR(30), numero_lote VARCHAR(50),
                                 cantidad NUMERIC(10,2), precio NUMERIC(10,2));
""")
    if nuevos:
        o.append("INSERT INTO carga_lote VALUES\n" + ",\n".join(
            f"    ({sql_texto(k[0])}, {sql_texto(k[1])}, {sql_texto(l['proveedor'])}, '{l['ingreso']}', "
            f"{sql_texto(l['vence'].isoformat() if l['vence'] else None)})" for k, l in nuevos) + ";\n")
    o.append("INSERT INTO carga_movimiento VALUES\n" + ",\n".join(
        f"    ({n}, '{m['tipo']}', '{m['fecha']:%Y-%m-%d %H:%M:%S}', {sql_texto(m['obs'])})"
        for n, m in enumerate(movimientos, 1)) + ";\n")
    o.append("INSERT INTO carga_detalle VALUES\n" + ",\n".join(
        f"    ({n}, {sql_texto(k[0])}, {sql_texto(k[1])}, {q}, {p})"
        for n, m in enumerate(movimientos, 1) for k, q, p in m["detalle"]) + ";\n")
    total_detalles = sum(len(m["detalle"]) for m in movimientos)
    o.append(f"""-- Lotes nuevos: nacen en 0; la existencia la ponen las entradas.
INSERT INTO lote (id_producto, id_proveedor, numero_lote, fecha_ingreso, fecha_vencimiento, cantidad_disponible)
SELECT p.id_producto, pr.id_proveedor, cl.numero_lote, cl.fecha_ingreso, cl.fecha_vencimiento, 0
  FROM carga_lote cl
  JOIN producto  p  ON p.codigo  = cl.codigo
  JOIN proveedor pr ON pr.nombre = cl.proveedor;

DO $$
DECLARE
    v_id_usuario    usuario.id_usuario%TYPE;
    v_id_movimiento movimiento.id_movimiento%TYPE;
    v_detalles      INTEGER := 0;
    v_filas         INTEGER;
    r_mov           RECORD;
BEGIN
    SELECT id_usuario INTO v_id_usuario FROM usuario WHERE usuario = 'encargado.dev';
    IF v_id_usuario IS NULL THEN
        RAISE EXCEPTION 'Falta el usuario encargado.dev (responsable de las cargas históricas).';
    END IF;
    IF (SELECT count(*) FROM lote l JOIN producto p ON p.id_producto = l.id_producto
          JOIN carga_lote cl ON cl.codigo = p.codigo AND cl.numero_lote = l.numero_lote) <> (SELECT count(*) FROM carga_lote) THEN
        RAISE EXCEPTION 'No se crearon todos los lotes nuevos: falta un producto o un proveedor.';
    END IF;

    -- En orden de fecha; el trigger suma o resta cada detalle y aborta la
    -- carga completa si una salida dejara existencia negativa (RN-01).
    FOR r_mov IN SELECT * FROM carga_movimiento ORDER BY orden LOOP
        INSERT INTO movimiento (id_usuario, tipo_movimiento, fecha_hora, observacion)
        VALUES (v_id_usuario, r_mov.tipo, r_mov.fecha_hora, r_mov.observacion)
        RETURNING id_movimiento INTO v_id_movimiento;

        INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad, precio_unitario)
        SELECT v_id_movimiento, l.id_lote, cd.cantidad, cd.precio
          FROM carga_detalle cd
          JOIN producto p ON p.codigo = cd.codigo
          JOIN lote l ON l.id_producto = p.id_producto AND l.numero_lote = cd.numero_lote
         WHERE cd.orden = r_mov.orden;
        GET DIAGNOSTICS v_filas = ROW_COUNT;
        v_detalles := v_detalles + v_filas;
    END LOOP;

    IF v_detalles <> {total_detalles} THEN
        RAISE EXCEPTION 'Se esperaban {total_detalles} detalles y se insertaron %: falta un lote.', v_detalles;
    END IF;
END;
$$;
""")
    if precio_prov:
        o.append("-- Último precio de compra por proveedor y producto (RN-16).")
        o.append("INSERT INTO proveedor_producto (id_proveedor, id_producto, precio_compra)\n"
                 "SELECT pr.id_proveedor, p.id_producto, v.precio\n  FROM (VALUES\n" + ",\n".join(
                     f"    ({sql_texto(prov)}, {sql_texto(cod)}, {precio})" for (prov, cod), precio in sorted(precio_prov.items()))
                 + "\n  ) AS v (proveedor, codigo, precio)\n"
                   "  JOIN proveedor pr ON pr.nombre = v.proveedor\n  JOIN producto p ON p.codigo = v.codigo\n"
                   "ON CONFLICT (id_proveedor, id_producto) DO UPDATE SET precio_compra = EXCLUDED.precio_compra;\n")
    o.append("DROP TABLE carga_detalle, carga_movimiento, carga_lote;\n\nCOMMIT;\n\n-- Fin de 005_carga_sigal.sql\n")
    SALIDA_SQL.write_text("\n".join(o), encoding="utf-8")


def escribir_reporte(movimientos, lotes, productos_nuevos, proveedores_nuevos, h, precio_prov):
    n_ent = sum(m["tipo"] == "ENTRADA" for m in movimientos)
    nuevos = sum(l["nuevo"] for l in lotes.values())
    r = [f"""# Reporte de la carga de SIGAL — Entrega 4

Movimientos que el laboratorio registró en **SIGAL** después del registro en papel, cargados con `sql/dml/005_carga_sigal.sql` (generado por `sql/dml/generar_carga_sigal.py` a partir del respaldo de SIGAL del 21/10/2026, que no se publica). Mismo método y decisiones que la carga del papel (`docs/entrega-3/ENTREGA3_REPORTE_CARGA_DATOS.md`).

## Resumen

| Dato | Cargado |
|---|---|
| Período | {min(m['fecha'] for m in movimientos):%d/%m/%Y} a {max(m['fecha'] for m in movimientos):%d/%m/%Y} |
| Entradas | {n_ent} |
| Salidas | {len(movimientos) - n_ent} |
| Lotes nuevos | {nuevos} |
| Productos nuevos | {len(productos_nuevos)} |
| Proveedores nuevos | {len(proveedores_nuevos)} |
| Precios proveedor–producto actualizados | {len(precio_prov)} |

**Cómo se evita duplicar:** SIGAL conservó la numeración del papel (E######, S######). Se cargan solo los registros posteriores al 23/09/2026 cuyo código no estaba ya en la base. Hasta esa fecha los dos sistemas coinciden.
"""]
    def tabla(titulo, explicacion, cabecera, filas):
        if not filas:
            return
        r.append(f"## {titulo} ({len(filas)})\n\n{explicacion}\n")
        r.append("| " + " | ".join(cabecera) + " |\n|" + "---|" * len(cabecera))
        for f in filas:
            r.append("| " + " | ".join(str(x.strftime('%d/%m/%Y') if isinstance(x, dt.date) else x) for x in f) + " |")
        r.append("")
    tabla("Productos nuevos", "Categoría asignada por palabras clave del nombre (mismas reglas que la carga del papel).",
          ["Código", "Producto", "Categoría", "Presentación", "Mínimo", "Requiere vencimiento"],
          [(p["codigo"], p["nombre"], p["categoria"], p["unidad"], p["minimo"], "Sí" if p["vence"] else "No") for p in productos_nuevos.values()])
    tabla("Proveedores nuevos", "NIT provisional; se corrige desde la aplicación.", ["Proveedor", "NIT"], list(proveedores_nuevos.items()))
    tabla("Servicios excluidos", "No son artículos de inventario (decisión 2).", ["Registro", "Código", "Concepto"], sorted(set(h["servicios"])))
    tabla("Entradas sin número de lote", "Se les asignó el lote `SL-<entrada>` (decisión 3).", ["Entrada", "Producto", "Lote asignado"], h["sin_lote"])
    tabla("Entradas a un lote existente con otro vencimiento", "Se sumaron al lote existente, que conserva su vencimiento (decisión 4, igual que `sp_registrar_entrada`). Revisar cuál fecha es la correcta y, si hace falta, usar *Corregir entrada*.",
          ["Entrada", "Producto", "Lote", "Vencimiento del lote", "Vencimiento en SIGAL"], h["vence_distinto"])
    tabla("Salidas movidas a la fecha de la entrada que las cubre", "SIGAL registró el consumo antes que la entrada (decisión 5).",
          ["Salida", "Producto", "Cantidad", "Fecha en SIGAL", "Fecha cargada"], h["movidas"])
    tabla("Salidas cubiertas con un lote vencido", "A esa fecha solo había existencia en lotes vencidos; el consumo sí ocurrió.", ["Salida", "Producto", "Fecha"], h["vencidos"])
    tabla("Entradas rechazadas", "La base no las admite.", ["Entrada", "Producto", "Motivo"], h["rechazadas"])
    tabla("Salidas rechazadas", "Ninguna entrada las cubre: la existencia quedaría negativa (RN-01).", ["Salida", "Producto", "Cantidad", "Fecha"], h["salidas_rechazadas"])
    r.append("""## Decisiones

| Tema | Decisión |
|---|---|
| Qué se carga | Registros de SIGAL posteriores al 23/09/2026 cuyo código no está en la base |
| Responsable | `encargado.dev`, igual que la carga del papel; en SIGAL los usuarios son personas con nombre y el repositorio es público. La observación de cada salida conserva el área solicitante |
| Fechas | SIGAL las guarda en UTC; se convierten a hora de Guatemala |
| Salidas | Repartidas por FEFO sin lotes vencidos, como `sp_registrar_salida` |
| Datos de SIGAL que no tienen lugar en este modelo | Requisiciones, pedidos, avisos, descuentos y retenciones de las facturas: no se cargan |
""")
    SALIDA_REPORTE.write_text("\n".join(r), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python sql/dml/generar_carga_sigal.py ruta/respaldo_sigal.sql")
    main(sys.argv[1])
