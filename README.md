# ABC Software Corp · SUNAT Electronic Invoicing (UBL 2.1)

**Phase 1 – Spec-First.** This repository contains the technical specifications defined *before*
writing a single line of business logic. Midterm exam, Software Architecture course,
UNAS – School of Computer and Systems Engineering.

| | |
|---|---|
| **Student** | Lourdes Xiomara López Gonzalez |
| **Group** | "A" |
| **Course** | Software Architecture – Midterm exam |
| **University** | Universidad Nacional Agraria de la Selva |
| **Date** | October 19, 2026 |

## Deliverables
| # | Required deliverable | Location |
|---|---|---|
| 1 | **Domain model and contracts (DTOs / Schemas)** | [`specs/02-dominio/modelo-dominio.md`](specs/02-dominio/modelo-dominio.md) · [`schemas/`](specs/02-dominio/schemas) (12 JSON Schema 2020-12) · [`ejemplos/`](specs/02-dominio/ejemplos) (validated JSON + UBL 2.1 XML) |
| 2 | **MVC architecture diagrams with a Hexagonal vision** | [`specs/03-arquitectura/arquitectura.md`](specs/03-arquitectura/arquitectura.md) · decisions in [`specs/adr/`](specs/adr) |
| 3 | **Endpoint / service specification (API contracts)** | [`specs/04-api/openapi.yaml`](specs/04-api/openapi.yaml) (OpenAPI 3.1) · [`puertos-salida.md`](specs/04-api/puertos-salida.md) · [`eventos.md`](specs/04-api/eventos.md) |
| 4 | **Regulatory traceability matrix SUNAT ↔ UBL** | [`specs/05-trazabilidad/matriz.md`](specs/05-trazabilidad/matriz.md) · [`matriz.csv`](specs/05-trazabilidad/matriz.csv) (52 rows) |

Other case requirements also covered:
| Requirement | Location |
|---|---|
| **Acceptance criteria** (37, covering every rule) | [`specs/07-aceptacion/`](specs/07-aceptacion/criterios-aceptacion.md) |
| Use cases (Nubefact benchmark) | [`specs/01-casos-uso/`](specs/01-casos-uso/casos-uso.md) · [`docs/benchmark/`](docs/benchmark/nubefact.md) |
| Legacy system and data migration with traceability | [`specs/06-migracion/`](specs/06-migracion/migracion.md) · [`docs/legado/`](docs/legado) |
| SUNAT regulations, catalogs (incl. **catalog 08**: ISC systems 01, 02, 03) and rules | [`docs/sunat/`](docs/sunat) |
| UBL 2.1 standard (`UBL-Invoice-2.1.xsd`) | [`docs/ubl/`](docs/ubl) |
| Windows **MSI** + Android **APK** distribution | [`specs/adr/ADR-002-stack-y-distribucion-msi-apk.md`](specs/adr/ADR-002-stack-y-distribucion-msi-apk.md) |
| Non-functional requirements | [`specs/00-contexto/requisitos-no-funcionales.md`](specs/00-contexto/requisitos-no-funcionales.md) |
| Context, assumptions, glossary and open questions | [`specs/00-contexto/`](specs/00-contexto) |

> UBL 2.1 (OASIS) defines the XML **structure**; SUNAT customization 2.0 defines the **values** for Peru
> (RUC, `F001-1` series-number, PEN, IGV 18 %…). This project validates against both.

## How to verify consistency
```bash
python -m pip install -r tools/requirements.txt
python tools/verificar.py                 # must end with "TODO CORRECTO (all checks passed)"

cd tools && npm install
npm run mermaid                           # parses diagrams with the official Mermaid parser
npm run openapi                           # lints the API contract with Redocly
```

## Working with Claude in this repo
The agent automatically reads [`CLAUDE.md`](CLAUDE.md): Spec-First rules, repo map and mandatory
verification before each commit.

> Field names in schemas and API (`tipoComprobante`, `importeTotal`…) are kept in Spanish on purpose:
> they mirror SUNAT's official terminology and are cross-checked by the verifier.
