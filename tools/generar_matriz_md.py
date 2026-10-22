"""Regenera specs/05-trazabilidad/matriz.md a partir de matriz.csv (la fuente de verdad es el CSV).

Uso:  python3 tools/generar_matriz_md.py
"""
import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "specs/05-trazabilidad/matriz.csv"
MD = RAIZ / "specs/05-trazabilidad/matriz.md"

ENCABEZADO = """# 05 · Matriz de trazabilidad normativa (SUNAT ↔ UBL ↔ Dominio ↔ Legado)

> Archivo generado desde `matriz.csv` con `python3 tools/generar_matriz_md.py`. No editar a mano.

Cada fila responde: **qué exige SUNAT**, **dónde va en el XML UBL 2.1**, **qué campo del contrato lo
transporta**, **de qué dato del legado proviene** y **qué regla lo valida**. `tools/verificar.py`
comprueba automáticamente que:

1. cada `campo_dominio` exista en el JSON Schema indicado,
2. cada `xpath_ubl` exista en el XML de ejemplo correspondiente (factura o nota de crédito),
3. cada `regla` exista en `docs/sunat/reglas-validacion.md`, en `specs/06-migracion` o en los casos de uso,
4. cada `catalogo` exista en `docs/sunat/catalogos/`.

```mermaid
flowchart LR
  N[Norma SUNAT<br/>Anexos 1-4 · Anexo 8 · RS 234-2006] --> R[Regla R-xx]
  R --> D[Campo del contrato<br/>JSON Schema]
  D --> U[Nodo UBL 2.1<br/>XPath]
  L[(Legado<br/>fecha, ingreso, salida,<br/>producto, nro_documento)] -- reglas M-xx --> D
```

Abreviaturas: `L` = `/Invoice/cac:InvoiceLine`, `TS` = `L/cac:TaxTotal/cac:TaxSubtotal`.
En notas de crédito el prefijo es `/CreditNote` y la línea es `cac:CreditNoteLine`.
"""


def main() -> None:
    filas = list(csv.DictReader(CSV.open(encoding="utf-8")))
    out = [ENCABEZADO,
           "| ID | Dato SUNAT | Comp. | Cat. | Regla | XPath UBL 2.1 | Campo del contrato | Campo legado | Validación | Fuente |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for f in filas:
        x = (f["xpath_ubl"]
             .replace("/Invoice/cac:InvoiceLine/cac:TaxTotal/cac:TaxSubtotal", "TS")
             .replace("/Invoice/cac:InvoiceLine", "L"))
        prefijo = f["schema"] + ":" if f["schema"] and f["schema"] != "comprobante" else ""
        out.append(f"| {f['id']} | {f['dato_sunat']} | {f['comprobantes']} | {f['catalogo']} | {f['regla']} "
                   f"| `{x}` | `{prefijo}{f['campo_dominio']}` | {f['campo_legado']} | {f['validacion']} | {f['fuente']} |")
    out += ["", "## Cobertura de los campos del legado", "",
            "| Campo legado | Filas de la matriz |", "|---|---|"]
    for campo in ["fecha", "ingreso", "salida", "producto", "nro_documento", "id"]:
        ids = [f["id"] for f in filas if campo in f["campo_legado"].replace("/", " ").replace("(", " ").split()]
        out.append(f"| `{campo}` | {', '.join(ids) or '—'} |")
    out += ["", "Detalle de transformación de cada campo: `specs/06-migracion/mapeo-legado.csv`.", ""]
    MD.write_text("\n".join(out), encoding="utf-8")
    print(f"matriz.md regenerada: {len(filas)} filas")


if __name__ == "__main__":
    main()
