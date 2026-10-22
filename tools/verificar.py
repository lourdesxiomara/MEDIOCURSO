"""Verificación automática de las especificaciones Spec-First.

Uso (desde la raíz del repo):
    python -m pip install -r tools/requirements.txt
    python tools/verificar.py

Sale con código 0 solo si TODAS las comprobaciones pasan. Pensado para Windows, Linux y macOS.
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
    sys.exit(f"Falta una dependencia ({e.name}). Ejecuta: python -m pip install -r tools/requirements.txt")

errores: list[str] = []
avisos: list[str] = []


def check(nombre: str, fn) -> None:
    antes = len(errores)
    try:
        fn()
    except Exception as e:  # noqa: BLE001 - un fallo inesperado también es un error de verificación
        errores.append(f"{nombre}: excepción {type(e).__name__}: {e}")
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
                errores.append(f"{f.name}: $ref no resuelve: {ref}")


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


def v_calculos():
    tasa_igv = Decimal("0.18")
    for f in sorted(EJEMPLOS.glob("comprobante.*.json")):
        nombre = f.name
        c = leer_json(f)
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
                    errores.append(f"{n}: ISC sistema {trib['2000']['sistemaIsc']} mal calculado (cat. 08)")
            if af.startswith("1"):
                if "1000" not in trib:
                    errores.append(f"{n}: afectación {af} exige tributo 1000 IGV (R-22)")
                    continue
                x = trib["1000"]
                if Decimal(x["baseImponible"]) != vv + isc:
                    errores.append(f"{n}: base IGV ≠ valor + ISC (R-25)")
                if r2((vv + isc) * tasa_igv) != Decimal(x["monto"]):
                    errores.append(f"{n}: IGV mal calculado")
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
                errores.append(f"{nombre}: totales.{campo} = {tot[campo]} y debería ser {esperado} (R-30/R-31)")
        if tot["importeTotal"] != tot["precioVenta"] - tot.get("totalDescuentos", 0) - tot.get("totalAnticipos", 0):
            errores.append(f"{nombre}: importeTotal inconsistente (R-31)")
        if not any(l["codigo"] == "1000" for l in c["leyendas"]):
            errores.append(f"{nombre}: falta leyenda 1000 (R-32)")


# ---------------------------------------------------------------- XML UBL vs XSD y vs JSON
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
                errores.append(f"openapi.yaml: $ref interno no resuelve {ref}")
        elif not (OPENAPI.parent / ref.split("#")[0]).resolve().is_file():
            errores.append(f"openapi.yaml: archivo de $ref no existe {ref}")
    for ext in re.findall(r"externalValue:\s*'([^']+)'", texto):
        if not (OPENAPI.parent / ext).resolve().is_file():
            errores.append(f"openapi.yaml: externalValue no existe {ext}")
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
                errores.append(f"asyncapi.yaml: $ref no resuelve {ref}")
        elif not (ASYNCAPI.parent / ref).resolve().is_file():
            errores.append(f"asyncapi.yaml: archivo no existe {ref}")
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
    xml = {"Invoice": etree.parse(str(EJEMPLOS / "factura-F001-1.sin-firma.xml")),
           "CreditNote": etree.parse(str(EJEMPLOS / "nota-credito-FC01-1.sin-firma.xml"))}
    ids = [f["id"] for f in filas]
    if len(ids) != len(set(ids)):
        errores.append("matriz.csv: IDs duplicados")
    for f in filas:
        fid = f["id"]
        if f["schema"]:
            sch = leer_json(SCHEMAS / f"{f['schema']}.schema.json")
            if not f["campo_dominio"].startswith("(") and not _resolver_puntero(sch, f["campo_dominio"], reg):
                errores.append(f"{fid}: {f['schema']}{f['campo_dominio']} no existe en el schema")
        for r in filter(None, f["regla"].split(",")):
            if r.strip() not in reglas:
                errores.append(f"{fid}: regla {r} no está definida")
        for c in filter(None, f["catalogo"].split("/")):
            if c not in cats:
                errores.append(f"{fid}: catálogo {c} no existe en docs/sunat/catalogos")
        xp = f["xpath_ubl"]
        if xp.startswith("/"):
            raiz = xp.split("/")[1]
            if "UBLExtensions" in xp:
                avisos.append(f"{fid}: {xp} se agrega al firmar; no se comprueba en XML sin firma")
            elif not xml[raiz].xpath(xp_ns(xp), namespaces=NS):
                errores.append(f"{fid}: XPath sin resultado en el XML de ejemplo: {xp}")


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
            errores.append(f"mapeo-legado.csv: {r['schema_destino']}{r['campo_destino']} no existe")


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
            errores.append(f"{cid}: regla {r} no existe")
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
        errores.append(f"Regla {r} sin criterio de aceptación")


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
    try:
        base = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=RAIZ,
                              capture_output=True, text=True, check=True).stdout.split()[0]
        r = subprocess.run(["git", "diff", "--quiet", base, "--", "docs/ubl/common", "docs/ubl/maindoc"], cwd=RAIZ)
        if r.returncode != 0:
            errores.append("Los XSD oficiales de OASIS fueron modificados respecto del commit base")
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError):
        avisos.append("git no disponible: no se comprobó que los XSD oficiales estén intactos")


def main() -> int:
    print(f"Verificando {RAIZ}\n")
    check("Catálogos SUNAT (estructura)", v_catalogos)
    check("JSON Schemas válidos y $ref resueltos", v_schemas)
    check("Enums de schemas = catálogos SUNAT", v_enums_catalogos)
    check("Ejemplos JSON válidos contra sus schemas", v_ejemplos_json)
    check("Cálculo de IGV, ISC (cat. 08: 01/02/03), ICBPER y totales en ejemplos", v_calculos)
    check("XML de ejemplo válidos contra XSD UBL 2.1", v_xml_xsd)
    check("XML de ejemplo coinciden con su JSON", v_xml_coincide_json)
    check("OpenAPI 3.1: estructura, $ref, ejemplos y rutas de casos de uso", v_openapi)
    check("Matriz de trazabilidad: schema, XPath, reglas y catálogos", v_matriz)
    check("Migración: cobertura de la muestra legada y mapeo", v_migracion)
    check("Criterios de aceptación: cubren toda regla R-xx y M-xx", v_aceptacion)
    check("Referencias cruzadas R-xx, D-xx, ADR-xxx", v_referencias)
    check("Diagramas Mermaid (sintaxis básica)", v_mermaid)
    check("XSD oficiales OASIS sin modificar", v_xsd_oficiales_intactos)
    for a in avisos:
        print(f"[AVISO] {a}")
    print(f"\n{'TODO CORRECTO' if not errores else f'{len(errores)} ERROR(ES)'}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
