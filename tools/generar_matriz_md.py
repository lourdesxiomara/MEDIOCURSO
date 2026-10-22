"""Regenerates specs/05-trazabilidad/matriz.md from matriz.csv (the CSV is the source of truth).

Usage:  python3 tools/generar_matriz_md.py
"""
import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "specs/05-trazabilidad/matriz.csv"
MD = RAIZ / "specs/05-trazabilidad/matriz.md"

ENCABEZADO = """# 05 · Regulatory traceability matrix (SUNAT ↔ UBL ↔ Domain ↔ Legacy)

> Generated from `matriz.csv` with `python tools/generar_matriz_md.py`. Do not edit by hand.

Each row answers: **what SUNAT requires**, **where it goes in the UBL 2.1 XML**, **which contract field
carries it**, **which legacy field it comes from** and **which rule validates it**. `tools/verificar.py`
automatically checks that:

1. every `campo_dominio` exists in the given JSON Schema,
2. every `xpath_ubl` exists in the matching example XML (invoice or credit note),
3. every `regla` exists in `docs/sunat/reglas-validacion.md`, `specs/06-migracion` or the use cases,
4. every `catalogo` exists in `docs/sunat/catalogos/`.

```mermaid
flowchart LR
  N[SUNAT regulation<br/>Annexes 1-4 · Annex 8 · RS 234-2006] --> R[Rule R-xx]
  R --> D[Contract field<br/>JSON Schema]
  D --> U[UBL 2.1 node<br/>XPath]
  L[(Legacy<br/>fecha, ingreso, salida,<br/>producto, nro_documento)] -- rules M-xx --> D
```

Abbreviations: `L` = `/Invoice/cac:InvoiceLine`, `TS` = `L/cac:TaxTotal/cac:TaxSubtotal`.
In credit notes the prefix is `/CreditNote` and the line is `cac:CreditNoteLine`.
"""


def main() -> None:
    filas = list(csv.DictReader(CSV.open(encoding="utf-8")))
    out = [ENCABEZADO,
           "| ID | SUNAT data | Docs | Cat. | Rule | UBL 2.1 XPath | Contract field | Legacy field | Validation | Source |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for f in filas:
        x = (f["xpath_ubl"]
             .replace("/Invoice/cac:InvoiceLine/cac:TaxTotal/cac:TaxSubtotal", "TS")
             .replace("/Invoice/cac:InvoiceLine", "L"))
        prefijo = f["schema"] + ":" if f["schema"] and f["schema"] != "comprobante" else ""
        out.append(f"| {f['id']} | {f['dato_sunat']} | {f['comprobantes']} | {f['catalogo']} | {f['regla']} "
                   f"| `{x}` | `{prefijo}{f['campo_dominio']}` | {f['campo_legado']} | {f['validacion']} | {f['fuente']} |")
    out += ["", "## Legacy field coverage", "",
            "| Legacy field | Matrix rows |", "|---|---|"]
    for campo in ["fecha", "ingreso", "salida", "producto", "nro_documento", "id"]:
        ids = [f["id"] for f in filas if campo in f["campo_legado"].replace("/", " ").replace("(", " ").split()]
        out.append(f"| `{campo}` | {', '.join(ids) or '—'} |")
    out += ["", "Per-field transformation details: `specs/06-migracion/mapeo-legado.csv`.", ""]
    MD.write_text("\n".join(out), encoding="utf-8")
    print(f"matriz.md regenerated: {len(filas)} rows")


if __name__ == "__main__":
    main()
