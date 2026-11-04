"""Automatic verification of the Spec-First specifications.

Usage (from the repo root):
    python -m pip install -r tools/requirements.txt
    python tools/verificar.py

Exits with code 0 only if ALL checks pass. Works on Windows, Linux and macOS.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGOS = RAIZ / "docs/sunat/catalogos"
TABLAS = RAIZ / "docs/sunat/tablas-libros"
SCHEMAS = RAIZ / "specs/02-dominio/schemas"
EJEMPLOS = RAIZ / "specs/02-dominio/ejemplos"
OPENAPI = RAIZ / "specs/04-api/openapi.yaml"
MATRIZ = RAIZ / "specs/05-trazabilidad/matriz.csv"
REGLAS = RAIZ / "docs/sunat/reglas-validacion.md"
MIGRACION = RAIZ / "specs/06-migracion/migracion.md"
CASOS_USO = RAIZ / "specs/01-casos-uso/casos-uso.md"
DUDAS = RAIZ / "specs/00-contexto/dudas-abiertas.md"
LEGADO = RAIZ / "docs/legado/legado-almacen-muestra.csv"
XSD = {"Invoice": RAIZ / "tools/xsd/validar-Invoice.xsd",
       "CreditNote": RAIZ / "tools/xsd/validar-CreditNote.xsd",
       "DebitNote": RAIZ / "tools/xsd/validar-DebitNote.xsd"}
NS = {"cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
      "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
      "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
      "ds": "http://www.w3.org/2000/09/xmldsig#",
      "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
      "cn": "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2",
      "dn": "urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2"}
PREFIJO_RAIZ = {"Invoice": "inv", "CreditNote": "cn", "DebitNote": "dn"}


def xp_ns(xp: str) -> str:
    """La matriz escribe '/Invoice/...' (legible); el elemento raíz está en el namespace UBL."""
    for raiz, pre in PREFIJO_RAIZ.items():
        if xp.startswith(f"/{raiz}/") or xp == f"/{raiz}":
            return f"/{pre}:{raiz}" + xp[len(raiz) + 1:]
    return xp

# Ejemplo JSON -> schema contra el que se valida
EJEMPLO_SCHEMA = {
    "comprobante-crear.factura.json": "comprobante-crear.schema.json",
    "comprobante.factura.json": "comprobante.schema.json",
    "comprobante.nota-credito.json": "comprobante.schema.json",
    "nota-crear.credito.json": "nota-crear.schema.json",
    "producto-cerveza.json": "producto.schema.json",
    "movimiento-inventario.salida.json": "movimiento-inventario.schema.json",
    "error.validacion.json": "error.schema.json",
    "comprobante.factura-isc.json": "comprobante.schema.json",
    "comprobante-crear.boleta.json": "comprobante-crear.schema.json",
    "comprobante.boleta.json": "comprobante.schema.json",
    "nota-crear.debito.json": "nota-crear.schema.json",
    "comprobante.nota-debito.json": "comprobante.schema.json",
    "producto-cerveza-monto-fijo.json": "producto.schema.json",
    "producto-cigarrillos.json": "producto.schema.json",
    "evento.comprobante-aceptado.json": "evento.schema.json",
    "kardex.CER-630.2026-10.json": "kardex.schema.json",
    "registro-ventas.2026-10.json": "registro-ventas.schema.json",
    "propuesta-sire.2026-10.json": "registro-ventas.schema.json",
    "conciliacion-sire.2026-10.json": "conciliacion-sire.schema.json",
}

# XML de ejemplo -> JSON equivalente (se comprueba que digan lo mismo)
XML_JSON = {
    "factura-F001-1.sin-firma.xml": "comprobante.factura.json",
    "factura-F001-2-isc.sin-firma.xml": "comprobante.factura-isc.json",
    "boleta-B001-1.sin-firma.xml": "comprobante.boleta.json",
    "nota-credito-FC01-1.sin-firma.xml": "comprobante.nota-credito.json",
    "nota-debito-FD01-1.sin-firma.xml": "comprobante.nota-debito.json",
}

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
    from lxml import etree
    from referencing import Registry, Resource
except ImportError as e:  # pragma: no cover
    sys.exit(f"Missing dependency ({e.name}). Run: python -m pip install -r tools/requirements.txt")

errores: list[str] = []
avisos: list[str] = []


def check(nombre: str, fn) -> None:
    antes = len(errores)
    try:
        fn()
    except Exception as e:  # noqa: BLE001 - un fallo inesperado también es un error de verificación
        errores.append(f"{nombre}: exception {type(e).__name__}: {e}")
    estado = "OK " if len(errores) == antes else "ERR"
    print(f"[{estado}] {nombre}")
    for err in errores[antes:]:
        print(f"      - {err}")


def leer_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- catálogos
def cargar_catalogos() -> dict[str, list[str]]:
    cats = {}
    for f in sorted(CATALOGOS.glob("cat*.json")):
        d = leer_json(f)
        codigos = [c["codigo"] for c in d["codigos"]]
        cats[d["catalogo"]] = codigos
    return cats


def cargar_tablas() -> dict[str, list[str]]:
    """Books tables of RS 234-2006 (Annex 3): tabla05, tabla06, tabla10, tabla12…"""
    return {leer_json(f)["tabla"]: [c["codigo"] for c in leer_json(f)["codigos"]] for f in sorted(TABLAS.glob("tabla*.json"))}


def v_tablas():
    for f in sorted(TABLAS.glob("tabla*.json")):
        d = leer_json(f)
        for k in ("tabla", "titulo", "fuente", "codigos"):
            if k not in d:
                errores.append(f"{f.name}: missing '{k}'")
        cods = [c["codigo"] for c in d["codigos"]]
        if len(cods) != len(set(cods)):
            errores.append(f"{f.name}: duplicated codes")
        if f.stem != f"tabla{d['tabla']}":
            errores.append(f"{f.name}: name does not match table {d['tabla']}")
    t02 = leer_json(TABLAS / "tabla02.json")
    cat06 = leer_json(CATALOGOS / "cat06.json")
    cods02 = [c["codigo"] for c in t02["codigos"]]
    for c06 in [c["codigo"] for c in cat06["codigos"]]:
        if t02["equivalenciaCatalogo06"].get(c06) not in cods02:
            errores.append(f"tabla02 equivalence: catalog 06 code {c06} has no table 2 code")
    t06 = leer_json(TABLAS / "tabla06.json")
    cat03 = cargar_catalogos()["03"]
    for c03, c06 in t06.get("equivalenciaCatalogo03", {}).items():
        if c03 not in cat03:
            errores.append(f"tabla06 equivalence: {c03} is not in catalog 03")
        if c06 is not None and c06 not in [c["codigo"] for c in t06["codigos"]]:
            errores.append(f"tabla06 equivalence: {c06} is not in table 6")
    for c03 in cat03:
        if c03 not in t06.get("equivalenciaCatalogo03", {}):
            errores.append(f"tabla06: catalog 03 code {c03} has no equivalence (map it or set null + open question)")
    comun = leer_json(SCHEMAS / "comun.schema.json")["$defs"]
    for n, cods in cargar_tablas().items():
        d = comun.get(f"tabla{n}")
        if d is None:
            errores.append(f"comun.schema.json: missing $defs/tabla{n}")
        elif d["enum"] != cods:
            errores.append(f"comun.schema.json: enum tabla{n} differs from tabla{n}.json")


def v_catalogos():
    for f in sorted(CATALOGOS.glob("cat*.json")):
        d = leer_json(f)
        for k in ("catalogo", "titulo", "fuente", "codigos"):
            if k not in d:
                errores.append(f"{f.name}: falta '{k}'")
        codigos = [c["codigo"] for c in d["codigos"]]
        if len(codigos) != len(set(codigos)):
            errores.append(f"{f.name}: códigos duplicados")
        if f.stem != f"cat{d['catalogo']}":
            errores.append(f"{f.name}: nombre no coincide con catálogo {d['catalogo']}")
        for c in d["codigos"]:
            if not isinstance(c["codigo"], str):
                errores.append(f"{f.name}: código {c['codigo']!r} debe ser texto")


# ---------------------------------------------------------------- schemas
def cargar_registro():
    recursos = []
    for f in SCHEMAS.glob("*.schema.json"):
        s = leer_json(f)
        recursos.append((s["$id"], Resource.from_contents(s)))
    return Registry().with_resources(recursos)


def v_schemas():
    for f in sorted(SCHEMAS.glob("*.schema.json")):
        s = leer_json(f)
        Draft202012Validator.check_schema(s)
        if not s.get("$id", "").endswith(f.name):
            errores.append(f"{f.name}: $id no termina en el nombre del archivo")
    # todos los $ref resuelven
    reg = cargar_registro()
    for f in sorted(SCHEMAS.glob("*.schema.json")):
        s = leer_json(f)
        resolver = reg.resolver(base_uri=s["$id"])
        for ref in re.findall(r'"\$ref":\s*"([^"]+)"', f.read_text(encoding="utf-8")):
            try:
                resolver.lookup(ref)
            except Exception:  # noqa: BLE001
                errores.append(f"{f.name}: $ref does not resolve: {ref}")


def v_enums_catalogos():
    cats = cargar_catalogos()
    comun = leer_json(SCHEMAS / "comun.schema.json")["$defs"]
    for n, codigos in cats.items():
        d = comun.get(f"catalogo{n}")
        if d is None:
            errores.append(f"comun.schema.json: falta $defs/catalogo{n}")
        elif d["enum"] != codigos:
            errores.append(f"comun.schema.json: enum catalogo{n} distinto de cat{n}.json")
    for k in comun:
        if k.startswith("catalogo") and k[8:] not in cats:
            errores.append(f"comun.schema.json: $defs/{k} sin archivo de catálogo")
    if not set(comun["tipoComprobanteEmision"]["enum"]) <= set(cats["01"]):
        errores.append("tipoComprobanteEmision no es subconjunto del catálogo 01")


def v_ejemplos_json():
    reg = cargar_registro()
    for nombre, sname in EJEMPLO_SCHEMA.items():
        schema = leer_json(SCHEMAS / sname)
        val = Draft202012Validator(schema, registry=reg, format_checker=FormatChecker())
        datos = leer_json(EJEMPLOS / nombre)
        for e in sorted(val.iter_errors(datos), key=str):
            ruta = "/" + "/".join(map(str, e.absolute_path))
            errores.append(f"{nombre} {ruta}: {e.message}")
    sin_schema = {p.name for p in EJEMPLOS.glob("*.json")} - set(EJEMPLO_SCHEMA)
    for n in sorted(sin_schema):
        errores.append(f"{n}: ejemplo sin schema asignado en verificar.py")


# ---------------------------------------------------------------- reglas de negocio sobre ejemplos
D2 = Decimal("0.01")


def r2(x: Decimal) -> Decimal:
    return x.quantize(D2, rounding=ROUND_HALF_UP)


def ruc_valido(ruc: str) -> bool:
    if not re.fullmatch(r"(10|15|16|17|20)\d{9}", ruc):
        return False
    pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    dv = 11 - sum(int(a) * b for a, b in zip(ruc[:10], pesos)) % 11
    dv = {10: 0, 11: 1}.get(dv, dv)
    return dv == int(ruc[10])


def isc_esperado(x: dict, cantidad: Decimal, vv: Decimal) -> Decimal:
    """Catálogo 08: 01 al valor, 02 monto fijo, 03 precio de venta al público × factor."""
    s = x["sistemaIsc"]
    if s == "01":
        return r2(vv * Decimal(x["porcentaje"]) / 100)
    if s == "02":
        return r2(cantidad * Decimal(x["montoPorUnidad"]))
    if s == "03":
        if x["factor"] != "0.847":
            errores.append("ISC sistema 03: factor debe ser 1/(1+IGV+IPM) a 3 decimales = 0.847")
        return r2(Decimal(x["precioVentaPublico"]) * Decimal(x["factor"]) * Decimal(x["porcentaje"]) / 100 * cantidad)
    raise ValueError(f"sistemaIsc desconocido {s}")


def reglas_comprobante(c: dict, nombre: str) -> list[str]:
    """Business rules (type N) on a calculated document (comprobante.schema.json). Returns messages tagged R-xx."""
    errores: list[str] = []
    tasa_igv = Decimal("0.18")
    if not ruc_valido(c["emisor"]["ruc"]):
        errores.append(f"{nombre}: RUC del emisor no cumple R-10")
    doc = c["cliente"]["documento"]
    if doc["tipo"] == "6" and not ruc_valido(doc["numero"]):
        errores.append(f"{nombre}: RUC del cliente no cumple R-10")
    if c["tipoComprobante"] == "01" and doc["tipo"] != "6":
        errores.append(f"{nombre}: factura exige cliente con RUC (R-11)")
    if c["tipoComprobante"] == "03" and doc["tipo"] == "1" and not re.fullmatch(r"\d{8}", doc["numero"]):
        errores.append(f"{nombre}: DNI debe tener 8 dígitos (R-12)")
    t = {k: Decimal("0") for k in ("grav", "exo", "ina", "igv", "isc", "icb", "vv")}
    for ln in c["lineas"]:
        cant, vu, vv = Decimal(ln["cantidad"]), Decimal(ln["valorUnitario"]), Decimal(ln["valorVenta"])
        n = f"{nombre} línea {ln['numero']}"
        if r2(cant * vu - Decimal(ln.get("descuento", "0"))) != vv:
            errores.append(f"{n}: valorVenta ≠ cantidad × valorUnitario (R-28)")
        trib = {x["codigo"]: x for x in ln["tributos"]}
        af = ln["afectacionIgv"]
        isc = Decimal("0")
        if "2000" in trib:
            isc = Decimal(trib["2000"]["monto"])
            if isc_esperado(trib["2000"], cant, vv) != isc:
                errores.append(f"{n}: ISC sistema {trib['2000']['sistemaIsc']} miscalculated (cat. 08, R-24)")
        if af.startswith("1"):
            if "1000" not in trib:
                errores.append(f"{n}: afectación {af} exige tributo 1000 IGV (R-22)")
                continue
            x = trib["1000"]
            if Decimal(x["baseImponible"]) != vv + isc:
                errores.append(f"{n}: base IGV ≠ valor + ISC (R-25)")
            if r2((vv + isc) * tasa_igv) != Decimal(x["monto"]):
                errores.append(f"{n}: IGV miscalculated (R-22)")
            t["grav"] += vv
            t["igv"] += Decimal(x["monto"])
        else:
            esperado = {"2": "9997", "3": "9998", "4": "9995"}[af[0]]
            if esperado not in trib or "1000" in trib:
                errores.append(f"{n}: afectación {af} exige tributo {esperado} y sin IGV (R-23)")
            t["exo" if af[0] == "2" else "ina"] += vv
        if "7152" in trib:
            x = trib["7152"]
            if Decimal(x["cantidadBolsas"]) * Decimal(x["montoPorUnidad"]) != Decimal(x["monto"]):
                errores.append(f"{n}: ICBPER ≠ bolsas × monto (R-26)")
            t["icb"] += Decimal(x["monto"])
        t["isc"] += isc
        t["vv"] += vv
    tot = {k: Decimal(v) for k, v in c["totales"].items()}
    pares = [("totalGravado", t["grav"]), ("totalExonerado", t["exo"]), ("totalInafecto", t["ina"]),
             ("totalIgv", t["igv"]), ("totalIsc", t["isc"]), ("totalIcbper", t["icb"]), ("valorVenta", t["vv"]),
             ("precioVenta", t["vv"] + t["igv"] + t["isc"] + t["icb"])]
    for campo, esperado in pares:
        if tot[campo] != esperado:
            errores.append(f"{nombre}: totales.{campo} = {tot[campo]} y should be {esperado} (R-30/R-31)")
    if tot["importeTotal"] != tot["precioVenta"] - tot.get("totalDescuentos", 0) - tot.get("totalAnticipos", 0):
        errores.append(f"{nombre}: importeTotal inconsistente (R-31)")
    if not any(l["codigo"] == "1000" for l in c["leyendas"]):
        errores.append(f"{nombre}: falta leyenda 1000 (R-32)")
    fp = c.get("formaPago")
    if c["tipoComprobante"] == "01" and not fp:
        errores.append(f"{nombre}: invoice without formaPago (R-35)")
    if fp and fp["tipo"] == "Credito":
        pend, cuotas = Decimal(fp["montoNetoPendiente"]), fp["cuotas"]
        if sum(Decimal(q["monto"]) for q in cuotas) != pend:
            errores.append(f"{nombre}: Σ instalments ≠ net pending amount (R-36)")
        if not (Decimal("0") < pend <= tot["importeTotal"]):
            errores.append(f"{nombre}: net pending amount must be > 0 and ≤ total (R-36)")
        if [q["numero"] for q in cuotas] != list(range(1, len(cuotas) + 1)):
            errores.append(f"{nombre}: instalments must be numbered 1..n (R-36)")
        for q in cuotas:
            if q["fechaVencimiento"] <= c["fechaEmision"]:
                errores.append(f"{nombre}: instalment {q['numero']} due on or before the issue date (R-36)")

    return errores


def reglas_solicitud(d: dict, nombre: str) -> list[str]:
    """Business rules (type N) that a request (comprobante-crear) must pass before calculation."""
    out: list[str] = []
    doc = d["cliente"]["documento"]
    if doc["tipo"] == "6" and not ruc_valido(doc["numero"]):
        out.append(f"{nombre}: customer RUC fails the modulo-11 check digit (R-10)")
    fp = d.get("formaPago")
    if fp and fp["tipo"] == "Credito":
        cuotas = fp["cuotas"]
        if sum(Decimal(q["monto"]) for q in cuotas) != Decimal(fp["montoNetoPendiente"]):
            out.append(f"{nombre}: Σ instalments ≠ net pending amount (R-36)")
        if [q["numero"] for q in cuotas] != list(range(1, len(cuotas) + 1)):
            out.append(f"{nombre}: instalments must be numbered 1..n (R-36)")
        for q in cuotas:
            if d.get("fechaEmision") and q["fechaVencimiento"] <= d["fechaEmision"]:
                out.append(f"{nombre}: instalment {q['numero']} due on or before the issue date (R-36)")
    return out


def v_calculos():
    for f in sorted(EJEMPLOS.glob("comprobante.*.json")):
        errores.extend(reglas_comprobante(leer_json(f), f.name))
    for f in sorted(EJEMPLOS.glob("comprobante-crear.*.json")):
        errores.extend(reglas_solicitud(leer_json(f), f.name))


def v_invalidos():
    """Every file in ejemplos/invalidos must be REJECTED, and for the expected reason (review: negative examples)."""
    carpeta = EJEMPLOS / "invalidos"
    esperados = leer_json(carpeta / "esperados.json")
    reg = cargar_registro()
    reglas = set(re.findall(r"\|\s*(R-\d{2})\s*\|", REGLAS.read_text(encoding="utf-8")))
    listados = {e["archivo"] for e in esperados}
    for f in sorted(carpeta.glob("*.json")):
        if f.name != "esperados.json" and f.name not in listados:
            errores.append(f"invalidos/{f.name}: not listed in esperados.json")
    for e in esperados:
        n = f"invalidos/{e['archivo']}"
        if e["regla"] not in reglas:
            errores.append(f"{n}: rule {e['regla']} does not exist")
        datos = leer_json(carpeta / e["archivo"])
        val = Draft202012Validator(leer_json(SCHEMAS / f"{e['schema']}.schema.json"), registry=reg, format_checker=FormatChecker())
        errs = list(val.iter_errors(datos))
        if e["rechazo"] == "schema":
            def coincide(err):
                ruta = "/" + "/".join(map(str, err.absolute_path)) if err.absolute_path else ""
                return ruta.startswith(e["campo"]) and (e.get("contiene", "") in json.dumps(err.instance, ensure_ascii=False) + err.message)
            todos = [x for err in errs for x in ([err] + list(err.context or []))]
            if not errs:
                errores.append(f"{n}: ACCEPTED by the schema, but it must be rejected ({e['regla']})")
            elif not any(coincide(x) for x in todos):
                errores.append(f"{n}: rejected, but not at {e['campo'] or '/'} ({e['regla']}); got {errs[0].message[:80]}")
        else:
            if errs:
                errores.append(f"{n}: must pass the schema and fail a business rule, but the schema rejects it: {errs[0].message[:80]}")
                continue
            msgs = reglas_comprobante(datos, n) if e["schema"] == "comprobante" else reglas_solicitud(datos, n)
            if not any(f"{e['regla']}" in m for m in msgs):
                errores.append(f"{n}: ACCEPTED by the domain rules, but it must fail {e['regla']}")

# ---------------------------------------------------------------- XML UBL vs XSD y vs JSON
# ---------------------------------------------------------------- registros 12.1 y 14.1 (RS 234-2006)
def v_registros():
    sys.path.insert(0, str(RAIZ / "tools"))
    import ple
    comps = {c["numero"]: c for c in (leer_json(f) for f in EJEMPLOS.glob("comprobante.*.json"))}
    emisor = next(iter(comps.values()))["emisor"]
    t12 = leer_json(TABLAS / "tabla12.json")["sentido"]
    equiv = leer_json(TABLAS / "tabla06.json")["equivalenciaCatalogo03"]
    permitido = {"SALDO_INICIAL": {"SALDO_INICIAL"}, "INGRESO": {"ENTRADA", "OTRO"}, "AJUSTE_POSITIVO": {"AJUSTE", "OTRO"},
                 "SALIDA": {"SALIDA", "OTRO"}, "AJUSTE_NEGATIVO": {"AJUSTE", "OTRO"}}
    # ---- Format 12.1 (kardex)
    for f in sorted(EJEMPLOS.glob("kardex.*.json")):
        k = leer_json(f)
        movs = k["movimientos"]
        if movs[0]["tipoOperacionTabla12"] != "16" or movs[0]["tipo"] != "SALDO_INICIAL":
            errores.append(f"{f.name}: first row must be the opening balance, table 12 = 16 (R-65)")
        if Decimal(movs[0]["cantidad"]) != Decimal(k["saldoInicial"]):
            errores.append(f"{f.name}: saldoInicial ≠ first row (R-65)")
        saldo, ent, sal = Decimal("0"), Decimal("0"), Decimal("0")
        for i, m in enumerate(movs, 1):
            q = Decimal(m["cantidad"])
            entra = m["tipo"] in ("SALDO_INICIAL", "INGRESO", "AJUSTE_POSITIVO")
            saldo += q if entra else -q
            if i > 1:
                ent, sal = (ent + q, sal) if entra else (ent, sal + q)
            if Decimal(m["saldoFinal"]) != saldo or saldo < 0:
                errores.append(f"{f.name} row {i}: saldoFinal {m['saldoFinal']} should be {saldo} and never negative (R-65)")
            if t12.get(m["tipoOperacionTabla12"]) not in permitido[m["tipo"]]:
                errores.append(f"{f.name} row {i}: table 12 code {m['tipoOperacionTabla12']} inconsistent with {m['tipo']} (R-61)")
            if m["periodo"] != k["periodo"] or m["fecha"][:4] + m["fecha"][5:7] + "00" != m["periodo"]:
                errores.append(f"{f.name} row {i}: period does not match the date (R-60)")
            if m["codigoEstablecimiento"] != emisor["domicilioFiscal"]["codigoEstablecimiento"]:
                errores.append(f"{f.name} row {i}: establishment ≠ CPE AddressTypeCode (R-64)")
            doc = m["documentoSustento"]
            if doc["tipoTabla10"] == "00":
                if (doc["serie"], doc["numero"]) != ("0", "0") and m["tipo"] == "SALDO_INICIAL":
                    errores.append(f"{f.name} row {i}: opening balance uses document 00 / 0 / 0 (R-62)")
            else:
                c = comps.get(f"{doc['serie']}-{doc['numero']}")
                if not c or c["tipoComprobante"] != doc["tipoTabla10"]:
                    errores.append(f"{f.name} row {i}: supporting document {doc} not found among the example CPEs (R-62)")
                else:
                    lin = [l for l in c["lineas"] if l.get("codigoProducto") == m["codigoExistencia"]]
                    if not lin or Decimal(lin[0]["cantidad"]) != q:
                        errores.append(f"{f.name} row {i}: quantity ≠ CPE line for {m['codigoExistencia']}")
                    elif equiv.get(lin[0]["unidadMedida"]) != m["unidadMedidaTabla6"]:
                        errores.append(f"{f.name} row {i}: unit ≠ table 6 equivalent of the CPE unit (R-63)")
                    if c["fechaEmision"] != m["fecha"]:
                        errores.append(f"{f.name} row {i}: date ≠ CPE issue date")
        if (Decimal(k["totalEntradas"]), Decimal(k["totalSalidas"]), Decimal(k["saldoFinal"])) != (ent, sal, saldo):
            errores.append(f"{f.name}: totals should be inputs {ent}, outputs {sal}, closing {saldo} (R-65)")
        if k["archivoPle"] != ple.nombre_archivo(k["ruc"], k["periodo"], "120100"):
            errores.append(f"{f.name}: PLE file name should be {ple.nombre_archivo(k['ruc'], k['periodo'], '120100')} (R-66)")
        txt = EJEMPLOS / k["archivoPle"]
        esperado = [ple.linea_12_1(m) for m in movs]
        if not txt.is_file() or txt.read_text(encoding="utf-8").splitlines() != esperado:
            errores.append(f"{txt.name}: PLE 12.1 file does not match {f.name} (R-66)")
        elif any(len(l.split("|")) != 20 for l in esperado):
            errores.append(f"{txt.name}: each 12.1 line must have 19 fields (R-66)")
    mov = leer_json(EJEMPLOS / "movimiento-inventario.salida.json")
    if not any(m == mov for f in EJEMPLOS.glob("kardex.*.json") for m in leer_json(f)["movimientos"]):
        errores.append("movimiento-inventario.salida.json is not a row of the example kardex")
    # ---- Format 14.1 (registro de ventas)
    for f in sorted(EJEMPLOS.glob("registro-ventas.*.json")):
        rv = leer_json(f)
        claves = []
        for i, fila in enumerate(rv["filas"], 1):
            n = f"{f.name} row {i}"
            if not fila.get("cuo") or not fila.get("correlativoAsiento"):
                errores.append(f"{n}: fields 2–3 (CUO, entry number) are mandatory in the company's record (R-75)")
            num = f"{fila['serie']}-{fila['numero']}"
            c = comps.get(num)
            if not c:
                errores.append(f"{n}: {num} is not an example CPE (R-70)")
                continue
            claves.append((fila["fechaEmision"], fila["tipoComprobanteTabla10"], fila["serie"], int(fila["numero"])))
            signo = Decimal("-1") if c["tipoComprobante"] == "07" else Decimal("1")
            tot = c["totales"]
            pares = {"baseImponibleGravada": "totalGravado", "igv": "totalIgv", "importeExonerado": "totalExonerado",
                     "importeInafecto": "totalInafecto", "isc": "totalIsc", "icbper": "totalIcbper", "importeTotal": "importeTotal"}
            for campo, t_ in pares.items():
                if Decimal(fila[campo]) != signo * Decimal(tot[t_]):
                    errores.append(f"{n}: {campo} {fila[campo]} ≠ {'−' if signo < 0 else ''}{tot[t_]} from {num} (R-71/R-72)")
            suma = sum(Decimal(fila[x]) for x in ("valorExportacion", "baseImponibleGravada", "descuentoBaseImponible", "igv",
                       "descuentoIgv", "importeExonerado", "importeInafecto", "isc", "baseIvap", "ivap", "icbper", "otrosConceptos"))
            if suma != Decimal(fila["importeTotal"]):
                errores.append(f"{n}: field 25 ≠ Σ fields 13–24 (R-71)")
            if fila["tipoComprobanteTabla10"] != c["tipoComprobante"] or fila["fechaEmision"] != c["fechaEmision"]:
                errores.append(f"{n}: type or date ≠ CPE (R-70)")
            eq06 = leer_json(TABLAS / "tabla02.json")["equivalenciaCatalogo06"]
            if (fila["tipoDocumentoCliente"], fila["numeroDocumentoCliente"], fila["nombreCliente"]) != (
                    eq06[c["cliente"]["documento"]["tipo"]], c["cliente"]["documento"]["numero"], c["cliente"]["nombre"]):
                errores.append(f"{n}: customer ≠ CPE (R-71)")
            if fila["periodo"] != rv["periodo"] or fila["fechaEmision"][:4] + fila["fechaEmision"][5:7] + "00" != rv["periodo"]:
                errores.append(f"{n}: period ≠ issue date (R-70)")
            fp = c.get("formaPago", {})
            venc = fp["cuotas"][-1]["fechaVencimiento"] if fp.get("tipo") == "Credito" else None
            if fila.get("fechaVencimiento") != venc:
                errores.append(f"{n}: field 5 should be the last instalment due date ({venc}) (R-71)")
            if fila["moneda"] != c["moneda"] or (c["moneda"] == "PEN" and fila["tipoCambio"] != "1.000"):
                errores.append(f"{n}: currency / exchange rate (R-73)")
            if c["tipoComprobante"] in ("07", "08"):
                af = c["documentoAfectado"]
                ref = comps.get(af["numero"])
                if (fila.get("modificadoTipo"), f"{fila.get('modificadoSerie')}-{fila.get('modificadoNumero')}") != (af["tipoComprobante"], af["numero"]) \
                        or not ref or fila.get("modificadoFecha") != ref["fechaEmision"]:
                    errores.append(f"{n}: fields 28–31 must reference {af['numero']} (R-72)")
            if fila["estado"] != ("2" if c["estado"] == "ANULADO" else "1"):
                errores.append(f"{n}: field 35 status (R-74)")
        if claves != sorted(claves):
            errores.append(f"{f.name}: rows must be ordered by date, type, series and number (R-70)")
        en_periodo = {k for k, c in comps.items() if c["fechaEmision"][:4] + c["fechaEmision"][5:7] + "00" == rv["periodo"]}
        if en_periodo != {f"{x['serie']}-{x['numero']}" for x in rv["filas"]}:
            errores.append(f"{f.name}: every example CPE of the period must have exactly one row (R-70)")
        if rv["archivoPle"] != ple.nombre_archivo(rv["ruc"], rv["periodo"], "140100"):
            errores.append(f"{f.name}: PLE file name (R-75)")
        txt = EJEMPLOS / rv["archivoPle"]
        esperado = [ple.linea_14_1(x) for x in rv["filas"]]
        if not txt.is_file() or txt.read_text(encoding="utf-8").splitlines() != esperado:
            errores.append(f"{txt.name}: PLE 14.1 file does not match {f.name} (R-75)")
        elif any(len(l.split("|")) != 36 for l in esperado):
            errores.append(f"{txt.name}: each 14.1 line must have 35 fields (R-75)")
    # ---- base global del IGV = valor de venta gravado (sin ISC)
    for xmlf, jsonf in XML_JSON.items():
        d = etree.parse(str(EJEMPLOS / xmlf))
        raiz = etree.QName(d.getroot()).localname
        b = d.xpath(xp_ns(f"/{raiz}/cac:TaxTotal/cac:TaxSubtotal[cac:TaxCategory/cac:TaxScheme/cbc:ID='1000']/cbc:TaxableAmount/text()"), namespaces=NS)
        if b and b[0] != leer_json(EJEMPLOS / jsonf)["totales"]["totalGravado"]:
            errores.append(f"{xmlf}: document-level IGV TaxableAmount must be the taxed sale value without ISC (14.1 field 14)")


def v_firma():
    """R-51: the signed example carries a valid enveloped XMLDSig in ext:UBLExtensions and, without it,
    is exactly the unsigned example (signing must not change the document)."""
    try:
        from signxml import XMLVerifier
    except ImportError:
        errores.append("signxml not installed: run python -m pip install -r tools/requirements.txt")
        return
    firmados = sorted(EJEMPLOS.glob("*.firmada.xml"))
    if not firmados:
        errores.append("No signed example (R-51)")
    pem = (RAIZ / "tools/cert-prueba/certificado-prueba.pem").read_text(encoding="utf-8")
    for f in firmados:
        datos = f.read_bytes()
        try:
            XMLVerifier().verify(datos, x509_cert=pem)
        except Exception as e:  # noqa: BLE001
            errores.append(f"{f.name}: signature does not verify ({type(e).__name__}: {str(e)[:80]}) (R-51)")
            continue
        doc = etree.fromstring(datos)
        raiz = etree.QName(doc).localname
        firma = doc.xpath(xp_ns(f"/{raiz}/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/ds:Signature"), namespaces=NS)
        if len(firma) != 1:
            errores.append(f"{f.name}: ds:Signature must be inside ext:UBLExtensions/…/ext:ExtensionContent (R-51)")
            continue
        uri = doc.xpath(xp_ns(f"/{raiz}/cac:Signature/cac:DigitalSignatureAttachment/cac:ExternalReference/cbc:URI/text()"), namespaces=NS)
        if not uri or uri[0] != "#" + firma[0].get("Id", ""):
            errores.append(f"{f.name}: cac:Signature URI must point to the ds:Signature Id (R-51)")
        doc.remove(doc.find(f"{{{NS['ext']}}}UBLExtensions"))
        sin = etree.parse(str(EJEMPLOS / f.name.replace(".firmada.xml", ".sin-firma.xml"))).getroot()
        norm = lambda e: etree.tostring(e, method="c14n", exclusive=False, with_comments=False)
        quitar_espacios = lambda b: b"".join(b.split())
        if quitar_espacios(norm(doc)) != quitar_espacios(norm(sin)):
            errores.append(f"{f.name}: content differs from the unsigned example (signing must not change the document)")


def conciliar(registro: dict, propuesta: dict, campos: list[str]) -> list[dict]:
    """R-76: reconcile the SIRE proposal with the company's record. Key = (table 10 type, series, number)."""
    clave = lambda x: (x["tipoComprobanteTabla10"], x["serie"], x["numero"])
    r = {clave(x): x for x in registro["filas"]}
    p = {clave(x): x for x in propuesta["filas"]}
    out = []
    for k in sorted(set(r) | set(p)):
        base = {"tipoComprobanteTabla10": k[0], "serie": k[1], "numero": k[2]}
        if k not in p:
            out.append(dict(base, tipo="FALTA_EN_PROPUESTA"))
        elif k not in r:
            out.append(dict(base, tipo="SOBRA_EN_PROPUESTA"))
        else:
            cs = [{"campo": c, "registro": r[k].get(c, ""), "propuesta": p[k].get(c, "")} for c in campos
                  if r[k].get(c, "") != p[k].get(c, "")]
            if cs:
                out.append(dict(base, tipo="CAMPOS_DIFERENTES", campos=cs))
    return out


def v_conciliacion():
    for f in sorted(EJEMPLOS.glob("conciliacion-sire.*.json")):
        c = leer_json(f)
        per = f.name.split(".")[1]
        reg = leer_json(EJEMPLOS / f"registro-ventas.{per}.json")
        prop = leer_json(EJEMPLOS / f"propuesta-sire.{per}.json")
        campos = leer_json(SCHEMAS / "conciliacion-sire.schema.json")["properties"]["diferencias"]["items"]["properties"]["campos"]["items"]["properties"]["campo"]["enum"]
        if c.get("camposComparados") != campos:
            errores.append(f"{f.name}: camposComparados must be the schema's list (R-76)")
        esperado = conciliar(reg, prop, campos)
        if c["diferencias"] != esperado:
            errores.append(f"{f.name}: differences do not match the reconciliation of {reg and 'registro'} vs proposal (R-76)")
        tipos = [d["tipo"] for d in esperado]
        comunes = len({(x["tipoComprobanteTabla10"], x["serie"], x["numero"]) for x in reg["filas"]} &
                      {(x["tipoComprobanteTabla10"], x["serie"], x["numero"]) for x in prop["filas"]})
        resumen = {"filasRegistro": len(reg["filas"]), "filasPropuesta": len(prop["filas"]),
                   "coincidentes": comunes - tipos.count("CAMPOS_DIFERENTES"), "faltanEnPropuesta": tipos.count("FALTA_EN_PROPUESTA"),
                   "sobranEnPropuesta": tipos.count("SOBRA_EN_PROPUESTA"), "conDiferencias": tipos.count("CAMPOS_DIFERENTES")}
        if c["resumen"] != resumen:
            errores.append(f"{f.name}: summary should be {resumen} (R-76)")
        if c["estado"] in ("CONCILIADA", "ACEPTADA_EN_SIRE") and esperado:
            errores.append(f"{f.name}: a period with differences cannot be {c['estado']} (R-76)")
        if c["estado"] == "CON_DIFERENCIAS" and not esperado:
            errores.append(f"{f.name}: no differences, state should be CONCILIADA (R-76)")


def v_xml_xsd():
    esquemas = {}
    for raiz, xsd in XSD.items():
        esquemas[raiz] = etree.XMLSchema(etree.parse(str(xsd)))
    xmls = sorted(EJEMPLOS.glob("*.xml"))
    if not xmls:
        errores.append("No hay XML de ejemplo")
    for x in xmls:
        doc = etree.parse(str(x))
        raiz = etree.QName(doc.getroot()).localname
        if raiz not in esquemas:
            errores.append(f"{x.name}: raíz {raiz} sin XSD")
            continue
        if not esquemas[raiz].validate(doc):
            for e in esquemas[raiz].error_log:
                errores.append(f"{x.name}:{e.line}: {e.message}")


def v_xml_coincide_json():
    sin_par = {p.name for p in EJEMPLOS.glob("comprobante.*.json")} - set(XML_JSON.values())
    for n in sorted(sin_par):
        errores.append(f"{n}: comprobante de ejemplo sin XML UBL equivalente")
    for xmlf, jsonf in XML_JSON.items():
        d = etree.parse(str(EJEMPLOS / xmlf))
        c = leer_json(EJEMPLOS / jsonf)
        raiz = etree.QName(d.getroot()).localname
        total = "RequestedMonetaryTotal" if raiz == "DebitNote" else "LegalMonetaryTotal"

        def val(xp):
            r = d.xpath(xp_ns(xp), namespaces=NS)
            return r[0] if r else None

        esperado = {
            f"/{raiz}/cbc:ID/text()": c["numero"],
            f"/{raiz}/cbc:IssueDate/text()": c["fechaEmision"],
            f"/{raiz}/cbc:DocumentCurrencyCode/text()": c["moneda"],
            f"/{raiz}/cbc:Note[@languageLocaleID='1000']/text()": c["leyendas"][0]["texto"],
            f"/{raiz}/cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID/text()": c["emisor"]["ruc"],
            f"/{raiz}/cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID/text()": c["cliente"]["documento"]["numero"],
            f"/{raiz}/cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID/@schemeID": c["cliente"]["documento"]["tipo"],
            f"/{raiz}/cac:{total}/cbc:LineExtensionAmount/text()": c["totales"]["valorVenta"],
            f"/{raiz}/cac:{total}/cbc:TaxInclusiveAmount/text()": c["totales"]["precioVenta"],
            f"/{raiz}/cac:{total}/cbc:PayableAmount/text()": c["totales"]["importeTotal"],
        }
        for cod, campo in (("1000", "totalIgv"), ("2000", "totalIsc"), ("7152", "totalIcbper")):
            xp = f"/{raiz}/cac:TaxTotal/cac:TaxSubtotal[cac:TaxCategory/cac:TaxScheme/cbc:ID='{cod}']/cbc:TaxAmount/text()"
            if val(xp) is not None or Decimal(c["totales"][campo]) != 0:
                esperado[xp] = c["totales"][campo]
        if raiz == "Invoice":
            esperado[f"/{raiz}/cbc:InvoiceTypeCode/text()"] = c["tipoComprobante"]
            esperado[f"/{raiz}/cbc:InvoiceTypeCode/@listID"] = c["tipoOperacion"]
            fp = c.get("formaPago")
            if fp:
                esperado[f"/{raiz}/cac:PaymentTerms[cbc:ID='FormaPago'][1]/cbc:PaymentMeansID/text()"] = fp["tipo"]
                n_cuotas = len(d.xpath(xp_ns(f"/{raiz}/cac:PaymentTerms[starts-with(cbc:PaymentMeansID,'Cuota')]"), namespaces=NS))
                if n_cuotas != len(fp.get("cuotas", [])):
                    errores.append(f"{xmlf}: {n_cuotas} instalments in XML, JSON has {len(fp.get('cuotas', []))}")
                if fp["tipo"] == "Credito":
                    esperado[f"/{raiz}/cac:PaymentTerms[cbc:PaymentMeansID='Credito']/cbc:Amount/text()"] = fp["montoNetoPendiente"]
                    for q in fp["cuotas"]:
                        base = f"/{raiz}/cac:PaymentTerms[cbc:PaymentMeansID='Cuota{q['numero']:03d}']"
                        esperado[f"{base}/cbc:Amount/text()"] = q["monto"]
                        esperado[f"{base}/cbc:PaymentDueDate/text()"] = q["fechaVencimiento"]
        else:
            esperado[f"/{raiz}/cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID/text()"] = c["documentoAfectado"]["numero"]
            esperado[f"/{raiz}/cac:DiscrepancyResponse/cbc:ResponseCode/text()"] = c["motivoNota"]["codigo"]
        for xp, v in esperado.items():
            if val(xp) != v:
                errores.append(f"{xmlf}: {xp} = {val(xp)!r}, JSON dice {v!r}")
        # líneas: cantidad, valor de venta y sistema ISC
        lineas = d.xpath(xp_ns(f"/{raiz}/cac:*[local-name()='InvoiceLine' or local-name()='CreditNoteLine' or local-name()='DebitNoteLine']"), namespaces=NS)
        if len(lineas) != len(c["lineas"]):
            errores.append(f"{xmlf}: {len(lineas)} líneas y el JSON tiene {len(c['lineas'])}")
        for lx, lj in zip(lineas, c["lineas"]):
            if lx.xpath("cbc:LineExtensionAmount/text()", namespaces=NS)[0] != lj["valorVenta"]:
                errores.append(f"{xmlf} línea {lj['numero']}: valor de venta distinto del JSON")
            sis = [x.get("sistemaIsc") for x in lj["tributos"] if x["codigo"] == "2000"]
            if sis and lx.xpath(".//cbc:TierRange/text()", namespaces=NS) != sis:
                errores.append(f"{xmlf} línea {lj['numero']}: TierRange ≠ sistemaIsc {sis}")
        # TaxTotal global = Σ subtotales
        tot = Decimal(val(f"/{raiz}/cac:TaxTotal/cbc:TaxAmount/text()"))
        subs = sum(Decimal(s) for s in d.xpath(xp_ns(f"/{raiz}/cac:TaxTotal/cac:TaxSubtotal/cbc:TaxAmount/text()"), namespaces=NS))
        if tot != subs:
            errores.append(f"{xmlf}: TaxTotal {tot} ≠ Σ TaxSubtotal {subs}")


# ---------------------------------------------------------------- OpenAPI
def v_openapi():
    api = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    if not str(api.get("openapi", "")).startswith("3.1"):
        errores.append("openapi.yaml: se espera OpenAPI 3.1")
    ops = []
    for ruta, item in api["paths"].items():
        for metodo, op in item.items():
            if metodo in ("get", "post", "put", "patch", "delete"):
                ops.append(op.get("operationId"))
                if "responses" not in op:
                    errores.append(f"{metodo.upper()} {ruta}: sin responses")
    if None in ops:
        errores.append("openapi.yaml: hay operaciones sin operationId")
    dup = {o for o in ops if ops.count(o) > 1}
    if dup:
        errores.append(f"openapi.yaml: operationId duplicados {dup}")
    texto = OPENAPI.read_text(encoding="utf-8")
    for ref in re.findall(r"\$ref:\s*'([^']+)'", texto):
        if ref.startswith("#/"):
            nodo = api
            for parte in ref[2:].split("/"):
                nodo = nodo.get(parte) if isinstance(nodo, dict) else None
            if nodo is None:
                errores.append(f"openapi.yaml: $ref interno does not resolve {ref}")
        elif not (OPENAPI.parent / ref.split("#")[0]).resolve().is_file():
            errores.append(f"openapi.yaml: archivo de $ref does not exist {ref}")
    for ext in re.findall(r"externalValue:\s*'([^']+)'", texto):
        if not (OPENAPI.parent / ext).resolve().is_file():
            errores.append(f"openapi.yaml: externalValue does not exist {ext}")
    # todo endpoint citado en los casos de uso existe en la API
    rutas = {r.split("?")[0] for r in api["paths"]}
    cu = CASOS_USO.read_text(encoding="utf-8")
    for ruta in set(re.findall(r"(?:GET|POST|PUT|PATCH|DELETE|GET\|PUT|GET\|POST)\s+(/[a-z0-9\-/{}|]+)", cu)):
        for variante in _expandir(ruta.rstrip("`")):
            if variante not in rutas:
                errores.append(f"casos-uso.md cita {variante} que no está en openapi.yaml")


def _expandir(ruta: str) -> list[str]:
    """'/comprobantes/{id}/xml|cdr|pdf' -> 3 rutas."""
    if "|" not in ruta:
        return [ruta]
    base, _, alts = ruta.rpartition("/")
    return [f"{base}/{a}" for a in alts.split("|")]


# ---------------------------------------------------------------- AsyncAPI (eventos)
ASYNCAPI = RAIZ / "specs/04-api/asyncapi.yaml"


def v_asyncapi():
    doc = yaml.safe_load(ASYNCAPI.read_text(encoding="utf-8"))
    if doc.get("asyncapi") != "3.0.0":
        errores.append("asyncapi.yaml: se espera AsyncAPI 3.0.0")
    texto = ASYNCAPI.read_text(encoding="utf-8")
    for ref in re.findall(r"\$ref:\s*'([^']+)'", texto):
        if ref.startswith("#/"):
            nodo = doc
            for parte in ref[2:].split("/"):
                nodo = nodo.get(parte) if isinstance(nodo, dict) else None
            if nodo is None:
                errores.append(f"asyncapi.yaml: $ref does not resolve {ref}")
        elif not (ASYNCAPI.parent / ref).resolve().is_file():
            errores.append(f"asyncapi.yaml: archivo does not exist {ref}")
    tipos = set(leer_json(SCHEMAS / "evento.schema.json")["properties"]["tipo"]["enum"])
    mensajes = set(doc["components"]["messages"])
    if tipos != mensajes:
        errores.append(f"asyncapi.yaml: mensajes {sorted(mensajes)} ≠ tipos de evento.schema.json {sorted(tipos)}")
    publicados = {c for op in doc["operations"].values() if op["action"] == "send"
                  for c in doc["channels"][op["channel"]["$ref"].split("/")[-1]]["messages"]}
    for m in sorted(mensajes - publicados):
        errores.append(f"asyncapi.yaml: el evento {m} no tiene quien lo publique")
    reg = cargar_registro()
    val = Draft202012Validator(leer_json(SCHEMAS / "evento.schema.json"), registry=reg, format_checker=FormatChecker())
    for m in doc["components"]["messages"].values():
        for ej in m.get("examples", []):
            for e in val.iter_errors(ej["payload"]):
                errores.append(f"asyncapi.yaml ejemplo {ej['name']}: {e.message}")


# ---------------------------------------------------------------- matriz de trazabilidad
def _resolver_puntero(schema: dict, puntero: str, reg) -> bool:
    """Recorre un JSON Pointer con '*' sobre un schema (properties/items/$ref/allOf)."""
    resolver = reg.resolver(base_uri=schema["$id"])

    def deref(nodo, res):
        while isinstance(nodo, dict) and "$ref" in nodo:
            r = res.lookup(nodo["$ref"])
            nodo, res = r.contents, r.resolver
        return nodo, res

    def hijos(nodo, res, clave):
        nodo, res = deref(nodo, res)
        candidatos = []
        if clave == "*":
            if "items" in nodo:
                candidatos.append((nodo["items"], res))
        elif clave in nodo.get("properties", {}):
            candidatos.append((nodo["properties"][clave], res))
        for sub in nodo.get("allOf", []):
            candidatos += hijos(sub, res, clave)
        return candidatos

    actuales = [(schema, resolver)]
    for clave in [p for p in puntero.split("/") if p]:
        siguientes = []
        for n, r in actuales:
            siguientes += hijos(n, r, clave)
        if not siguientes:
            return False
        actuales = siguientes
    return True


def v_matriz():
    filas = list(csv.DictReader(MATRIZ.open(encoding="utf-8")))
    reg = cargar_registro()
    cats = cargar_catalogos()
    reglas = set(re.findall(r"\|\s*(R-\d{2})\s*\|", REGLAS.read_text(encoding="utf-8")))
    reglas |= set(re.findall(r"\*\*(M-\d{2})\*\*", MIGRACION.read_text(encoding="utf-8")))
    reglas |= set(re.findall(r"### (CU-\d{2})", CASOS_USO.read_text(encoding="utf-8")))
    xml: dict[str, list] = {}
    for x in sorted(EJEMPLOS.glob("*.xml")):
        d = etree.parse(str(x))
        xml.setdefault(etree.QName(d.getroot()).localname, []).append(d)
    tablas = cargar_tablas()
    ids = [f["id"] for f in filas]
    if len(ids) != len(set(ids)):
        errores.append("matriz.csv: IDs duplicados")
    for f in filas:
        fid = f["id"]
        if f["schema"]:
            sch = leer_json(SCHEMAS / f"{f['schema']}.schema.json")
            if not f["campo_dominio"].startswith("(") and not _resolver_puntero(sch, f["campo_dominio"], reg):
                errores.append(f"{fid}: {f['schema']}{f['campo_dominio']} does not exist en el schema")
        for r in filter(None, f["regla"].split(",")):
            if r.strip() not in reglas:
                errores.append(f"{fid}: regla {r} no está definida")
        for c in filter(None, f["catalogo"].split("/")):
            if c.startswith("T"):
                if c[1:] not in tablas:
                    errores.append(f"{fid}: books table {c} does not exist in docs/sunat/tablas-libros")
            elif c not in cats:
                errores.append(f"{fid}: catálogo {c} does not exist en docs/sunat/catalogos")
        xp = f["xpath_ubl"]
        if xp.startswith("/"):
            raiz = xp.split("/")[1]
            if not any(d.xpath(xp_ns(xp), namespaces=NS) for d in xml.get(raiz, [])):
                errores.append(f"{fid}: XPath has no match in the example XML: {xp}")


# ---------------------------------------------------------------- migración
def v_migracion():
    ids_legado = [r["id"] for r in csv.DictReader(LEGADO.open(encoding="utf-8"))]
    texto = MIGRACION.read_text(encoding="utf-8")
    seccion = texto.split("## 5.")[1]
    cubiertos = []
    for fila in re.findall(r"^\|\s*([\d, ]+)\s*\|", seccion, flags=re.M):
        cubiertos += [x.strip() for x in fila.split(",") if x.strip()]
    if sorted(cubiertos, key=int) != sorted(ids_legado, key=int):
        errores.append(f"migracion.md §5 cubre {sorted(cubiertos, key=int)} y el legado tiene {ids_legado}")
    m = re.search(r"read (\d+) = migrated (\d+) \+ quarantined (\d+) \+ discarded (\d+)", texto)
    if not m:
        errores.append("migracion.md: falta la línea de totales M-07")
    else:
        l, mi, cu, de = map(int, m.groups())
        if l != mi + cu + de or l != len(ids_legado):
            errores.append("migracion.md: totales M-07 no cuadran")
    for r in csv.DictReader((RAIZ / "specs/06-migracion/mapeo-legado.csv").open(encoding="utf-8")):
        if r["regla"] not in re.findall(r"\*\*(M-\d{2})\*\*", texto):
            errores.append(f"mapeo-legado.csv: regla {r['regla']} no definida")
        sch = leer_json(SCHEMAS / f"{r['schema_destino']}.schema.json")
        if not _resolver_puntero(sch, r["campo_destino"], cargar_registro()):
            errores.append(f"mapeo-legado.csv: {r['schema_destino']}{r['campo_destino']} does not exist")


# ---------------------------------------------------------------- criterios de aceptación
ACEPTACION = RAIZ / "specs/07-aceptacion/criterios-aceptacion.md"


def v_aceptacion():
    texto = ACEPTACION.read_text(encoding="utf-8")
    bloques = re.split(r"^### ", texto, flags=re.M)[1:]
    ids = [b.split()[0] for b in bloques]
    if len(ids) != len(set(ids)):
        errores.append("criterios-aceptacion.md: IDs CA duplicados")
    reglas = set(re.findall(r"\|\s*(R-\d{2})\s*\|", REGLAS.read_text(encoding="utf-8")))
    reglas |= set(re.findall(r"\*\*(M-\d{2})\*\*", MIGRACION.read_text(encoding="utf-8")))
    api = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    cubiertas = set()
    for b in bloques:
        cid = b.split()[0]
        m = re.search(r"\*\*Rules:\*\*\s*([^·\n]+)", b)
        if not m:
            errores.append(f"{cid}: sin reglas")
            continue
        rs = {r.strip() for r in m.group(1).split(",")}
        for r in rs - reglas:
            errores.append(f"{cid}: regla {r} does not exist")
        cubiertas |= rs
        for paso in ("**Given**", "**When**", "**Then**"):
            if paso not in b:
                errores.append(f"{cid}: falta {paso}")
        for ej in re.findall(r"`ejemplos/([^`]+)`", b):
            if not (EJEMPLOS / ej).is_file():
                errores.append(f"{cid}: ejemplo inexistente {ej}")
        for metodo, ruta in re.findall(r"`(GET|POST|PUT|DELETE) (/[^`?]+)", b):
            if ruta not in api["paths"] or metodo.lower() not in api["paths"][ruta]:
                errores.append(f"{cid}: endpoint {metodo} {ruta} no está en openapi.yaml")
    for r in sorted(reglas - cubiertas):
        errores.append(f"Regla {r} has no acceptance criterion")


# ---------------------------------------------------------------- referencias cruzadas y Mermaid
def v_referencias():
    reglas = set(re.findall(r"\|\s*(R-\d{2})\s*\|", REGLAS.read_text(encoding="utf-8")))
    dudas = set(re.findall(r"\|\s*(D-\d{2})\s*\|", DUDAS.read_text(encoding="utf-8")))
    adrs = {p.name[:7] for p in (RAIZ / "specs/adr").glob("ADR-*.md")}
    for p in list((RAIZ / "specs").rglob("*.md")) + list((RAIZ / "docs").rglob("*.md")) + [RAIZ / "CLAUDE.md"]:
        t = p.read_text(encoding="utf-8")
        rel = p.relative_to(RAIZ)
        for r in set(re.findall(r"\bR-\d{2}\b", t)) - reglas:
            errores.append(f"{rel}: cita {r} inexistente")
        for d in set(re.findall(r"\bD-\d{2}\b", t)) - dudas:
            errores.append(f"{rel}: cita {d} inexistente")
        for a in set(re.findall(r"\bADR-\d{3}\b", t)) - adrs:
            errores.append(f"{rel}: cita {a} inexistente")


TIPOS_MERMAID = ("flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram-v2", "erDiagram")


def v_mermaid():
    for p in (RAIZ / "specs").rglob("*.md"):
        t = p.read_text(encoding="utf-8")
        bloques = re.findall(r"```mermaid\n(.*?)```", t, flags=re.S)
        for i, b in enumerate(bloques, 1):
            primera = b.strip().splitlines()[0].strip()
            if not primera.startswith(TIPOS_MERMAID):
                errores.append(f"{p.relative_to(RAIZ)} bloque {i}: tipo de diagrama desconocido '{primera}'")
            if b.count("[") != b.count("]") or b.count("(") != b.count(")") or b.count("{") != b.count("}"):
                errores.append(f"{p.relative_to(RAIZ)} bloque {i}: corchetes/paréntesis desbalanceados")


def v_xsd_oficiales_intactos():
    """Compares each official XSD with docs/ubl/MANIFEST.sha256 after normalizing CRLF → LF.
    Works without git and on Windows checkouts or ZIP copies (review finding #6)."""
    import hashlib
    manifiesto = RAIZ / "docs/ubl/MANIFEST.sha256"
    esperados = {}
    for linea in manifiesto.read_text(encoding="utf-8").splitlines():
        if linea and not linea.startswith("#"):
            h, ruta = linea.split(maxsplit=1)
            esperados[ruta] = h
    actuales = {f.relative_to(RAIZ).as_posix(): f for f in (RAIZ / "docs/ubl").glob("*/*.xsd")
                if f.parent.name in ("common", "maindoc")}
    if set(esperados) != set(actuales):
        errores.append(f"XSD set differs from the manifest: {sorted(set(esperados) ^ set(actuales))}")
    for ruta, f in actuales.items():
        h = hashlib.sha256(f.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n").rstrip(b"\n")).hexdigest()
        if ruta in esperados and h != esperados[ruta]:
            errores.append(f"{ruta}: content differs from the official OASIS file")


def main() -> int:
    print(f"Verifying {RAIZ}\n")
    check("SUNAT catalogs (structure)", v_catalogos)
    check("Valid JSON Schemas and resolved $refs", v_schemas)
    check("Schema enums = SUNAT catalogs", v_enums_catalogos)
    check("Books tables 2, 5, 6, 10, 12 (RS 234-2006): structure, enums, catalog 03/06 equivalences", v_tablas)
    check("JSON examples valid against their schemas", v_ejemplos_json)
    check("IGV, ISC (cat. 08: 01/02/03), ICBPER and totals in examples", v_calculos)
    check("Invalid examples are rejected for the expected rule", v_invalidos)
    check("Example XMLs valid against the UBL 2.1 XSD", v_xml_xsd)
    check("Example XMLs match their JSON", v_xml_coincide_json)
    check("Signed example: valid enveloped XMLDSig in ext:UBLExtensions (R-51)", v_firma)
    check("Books 12.1 (kardex) and 14.1 (sales): balances, CPE cross-check, PLE files", v_registros)
    check("SIRE: proposal vs company record reconciliation (R-76)", v_conciliacion)
    check("OpenAPI 3.1: structure, $refs, examples and use-case routes", v_openapi)
    check("Traceability matrix: schema, XPath, rules and catalogs", v_matriz)
    check("Migration: legacy sample coverage and mapping", v_migracion)
    check("Acceptance criteria cover every R-xx and M-xx rule", v_aceptacion)
    check("Cross references R-xx, D-xx, ADR-xxx", v_referencias)
    check("Mermaid diagrams (basic syntax)", v_mermaid)
    check("Official OASIS XSDs untouched", v_xsd_oficiales_intactos)
    for a in avisos:
        print(f"[WARN] {a}")
    print(f"\n{'TODO CORRECTO (all checks passed)' if not errores else f'{len(errores)} ERROR(S)'}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
