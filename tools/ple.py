"""PLE (Programa de Libros Electrónicos) line builders for Formats 12.1 and 14.1.

Shared by tools/verificar.py and by the future implementation: the specification and the code
render the same lines. Rules R-66 (12.1) and R-75 (14.1) in docs/sunat/reglas-validacion.md.
"""
from __future__ import annotations


def fecha_ple(iso: str | None) -> str:
    """ISO 8601 (YYYY-MM-DD) → DD/MM/YYYY; empty when absent (placeholder conventions: question D-15)."""
    if not iso:
        return ""
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def cantidad2(x: str) -> str:
    entero, _, dec = x.partition(".")
    return f"{entero}.{(dec + '00')[:2]}"


def nombre_archivo(ruc: str, periodo: str, libro: str, con_info: bool = True, moneda: str = "PEN") -> str:
    """LE + RUC + AAAAMM00 + book code (140100 / 120100) + 00 + operations + content + currency + PLE."""
    return f"LE{ruc}{periodo}{libro}00{1}{1 if con_info else 0}{1 if moneda == 'PEN' else 2}1.txt"


def linea_12_1(m: dict) -> str:
    """Format 12.1: 19 fields, pipe-separated, trailing pipe. Inputs positive, outputs negative."""
    entrada = m["tipo"] in ("SALDO_INICIAL", "INGRESO", "AJUSTE_POSITIVO")
    q = cantidad2(m["cantidad"])
    doc = m["documentoSustento"]
    campos = [m["periodo"], m.get("cuo", ""), m.get("correlativoAsiento", ""), m["codigoEstablecimiento"], "9",
              m["tipoExistencia"], m["codigoExistencia"], "1" if m.get("codigoSunat") else "", m.get("codigoSunat", ""),
              fecha_ple(m["fecha"]), doc["tipoTabla10"], doc["serie"], doc["numero"], m["tipoOperacionTabla12"],
              m["descripcionExistencia"], m["unidadMedidaTabla6"], q if entrada else "0.00",
              "0.00" if entrada else f"-{q}", m["estadoOperacion"]]
    return "|".join(campos) + "|"


CAMPOS_14_1 = ["periodo", "cuo", "correlativoAsiento", "fechaEmision", "fechaVencimiento", "tipoComprobanteTabla10",
               "serie", "numero", "numeroFinal", "tipoDocumentoCliente", "numeroDocumentoCliente", "nombreCliente",
               "valorExportacion", "baseImponibleGravada", "descuentoBaseImponible", "igv", "descuentoIgv",
               "importeExonerado", "importeInafecto", "isc", "baseIvap", "ivap", "icbper", "otrosConceptos",
               "importeTotal", "moneda", "tipoCambio", "modificadoFecha", "modificadoTipo", "modificadoSerie",
               "modificadoNumero", "contrato", "errorTipoCambio", "indicadorMedioPago", "estado"]


def linea_14_1(f: dict) -> str:
    """Format 14.1 (PLE 5.2): 35 fields in CAMPOS_14_1 order, pipe-separated, trailing pipe."""
    out = []
    for c in CAMPOS_14_1:
        v = f.get(c, "")
        out.append(fecha_ple(v) if c in ("fechaEmision", "fechaVencimiento", "modificadoFecha") else v)
    return "|".join(out) + "|"
