"""SIRE – RVIE proposal file (RS 112-2021/SUNAT, Annex 2, El Peruano 31/07/2021; copy in docs/fuentes-oficiales/).

Maps the official proposal fields to the company's Format 14.1 row (registro-ventas.schema.json) so the
reconciliation (R-76) compares like with like. Used by tools/verificar.py and by the future `sire` adapter.
"""
from __future__ import annotations

# Annex 2 field number → 14.1 row field (None = not part of the comparison)
MAPEO = {
    1: None,                        # RUC del generador
    2: None,                        # Razón social del generador
    3: "periodo",                   # YYYYMM → AAAAMM00
    4: "car",                       # Código de Anotación de Registro (Annex 1, table 7)
    5: "fechaEmision",              # DD/MM/AAAA
    6: "fechaVencimiento",          # only for type 14
    7: "tipoComprobanteTabla10",
    8: "serie",
    9: "numero",
    10: "numeroFinal",
    11: "tipoDocumentoCliente",
    12: "numeroDocumentoCliente",
    13: "nombreCliente",
    14: "valorExportacion",
    15: "baseImponibleGravada",
    16: "descuentoBaseImponible",
    17: "igv",
    18: "descuentoIgv",
    19: "importeExonerado",
    20: "importeInafecto",
    21: "isc",
    22: "baseIvap",
    23: "ivap",
    24: "icbper",
    25: "otrosConceptos",
    26: "importeTotal",
    27: "moneda",
    28: "tipoCambio",               # mandatory only if currency ≠ PEN
    29: "modificadoFecha",          # YYYY-MM-DD in Annex 2
    30: "modificadoTipo",
    31: "modificadoSerie",
    32: "modificadoNumero",
    33: "contrato",
    # 34 tipo de nota, 35 estado del comprobante, 36 interno, 37 valor op. gratuitas, 38 tipo de operación,
    # 39 inconsistencias, 40 interno: referential, shown by SUNAT only (not part of the complement file)
}
N_CAMPOS = 40


def car(ruc: str, tipo: str, serie: str, numero: str) -> str:
    """Annex 1, table 7: RUC (11) + type (2) + series (4) + number (10), left-padded with zeros = 27 characters."""
    return ruc.zfill(11)[-11:] + tipo.zfill(2) + (serie or "").rjust(4, "0")[-4:] + numero.rjust(10, "0")[-10:]


def _iso_a_ddmmaaaa(iso: str) -> str:
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def _ddmmaaaa_a_iso(v: str) -> str:
    d, m, a = v.split("/")
    return f"{a}-{m}-{d}"


def linea_propuesta(fila: dict, ruc: str, razon_social: str, referencial: dict | None = None) -> str:
    """Builds one proposal line as SUNAT delivers it (fields 1–40, pipe-separated)."""
    v = [""] * (N_CAMPOS + 1)
    v[1], v[2], v[3] = ruc, razon_social, fila["periodo"][:6]
    for n, campo in MAPEO.items():
        if campo and n > 3 and campo in fila:
            v[n] = fila[campo]
    v[5] = _iso_a_ddmmaaaa(fila["fechaEmision"])
    if fila.get("fechaVencimiento"):
        v[6] = _iso_a_ddmmaaaa(fila["fechaVencimiento"])
    if fila.get("moneda") == "PEN":
        v[28] = ""                  # Annex 2 field 28: mandatory only when the currency is not PEN
    for n, x in (referencial or {}).items():
        v[n] = x
    return "|".join(v[1:]) + "|"


def leer_propuesta(texto: str) -> list[dict]:
    """Parses the proposal file into 14.1 rows (registro-ventas.schema.json `fila`)."""
    filas = []
    for linea in texto.splitlines():
        if not linea.strip():
            continue
        v = [""] + linea.split("|")
        f = {}
        for n, campo in MAPEO.items():
            if campo and v[n] != "":
                f[campo] = v[n]
        f["periodo"] = v[3] + "00"
        f["fechaEmision"] = _ddmmaaaa_a_iso(v[5])
        if v[6]:
            f["fechaVencimiento"] = _ddmmaaaa_a_iso(v[6])
        if f.get("moneda") == "PEN" and not v[28]:
            f["tipoCambio"] = "1.000"
        f["estado"] = "1"
        filas.append(f)
    return filas
