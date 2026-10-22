# CLAUDE.md — ABC Software Corp · SUNAT Electronic Invoicing (UBL 2.1)

Any Claude agent working in this repo reads this file automatically. Read it fully before any task.

## 1. Methodology: SPEC-FIRST (current phase)
- **Writing business logic is FORBIDDEN** in this phase. Only specifications: rules, data contracts
  (JSON Schema), interface contracts (OpenAPI / ports / events), diagrams, matrices, acceptance criteria and ADRs.
- Do not modify the official OASIS XSDs (`docs/ubl/common`, `docs/ubl/maindoc`).
- Before each task: propose a short plan and wait for the user's approval.
- Every regulatory statement cites its source (catalog, UBL XPath, resolution). See `docs/sunat/fuentes.md`.
- If something cannot be verified in an official source → `specs/00-contexto/dudas-abiertas.md`. **Do not invent.**
- One commit per step, with a descriptive message. Working branch: `main`.

## 2. Case context (summary)
- Client: ABC Software Corp, grocery and goods wholesaler/retailer.
- Legacy: warehouse record with `fecha, ingreso, salida, producto, nro_documento` (informal).
- Goal: issue electronic documents (invoice, receipt, credit/debit notes) in **UBL 2.1**,
  validated, signed (XMLDSig) and sent to an **OSE or SUNAT**, receiving the **CDR**.
- Regulations: RS 097-2012/SUNAT (SEE from the taxpayer's systems, Annex 8 = catalogs),
  RS 234-2006/SUNAT (books and records: Permanent Inventory Format 12.1/13.1).
- Architecture: **clean MVC monolith** today, designed with **ports and adapters** to move to
  **Hexagonal/Clean** and later to microservices.
- Platforms: **Windows (MSI installer)** and **Android (APK)**, running natively.

## 3. Repository map
| Path | Content |
|---|---|
| `docs/ubl/` | Official OASIS UBL 2.1 XSDs + `soporte/` (CCTS, XMLDSig, XAdES) |
| `docs/sunat/` | SUNAT catalogs in JSON, validation rules, sources (kept in Spanish: regulatory text) |
| `docs/legado/` | Legacy data sample and description |
| `docs/benchmark/` | Nubefact analysis (reference use cases) |
| `specs/00-contexto/` | Case, scope, assumptions, glossary, open questions, non-functional requirements |
| `specs/01-casos-uso/` | Use cases |
| `specs/02-dominio/` | Domain model, `schemas/` (JSON Schema), `ejemplos/` (JSON and UBL XML) |
| `specs/03-arquitectura/` | MVC → Hexagonal → Microservices diagrams |
| `specs/04-api/` | `openapi.yaml`, output port contracts, event contracts |
| `specs/05-trazabilidad/` | SUNAT ↔ UBL ↔ Domain ↔ Legacy matrix |
| `specs/06-migracion/` | Legacy mapping and migration plan |
| `specs/07-aceptacion/` | Acceptance criteria (Given/When/Then) |
| `specs/adr/` | Architecture decision records (ADR) |
| `tools/` | XSD wrappers and verification scripts |

## 4. Conventions
- Prose in English. Schema/API identifiers in Spanish `camelCase` without accents (SUNAT terminology).
- Amounts: 2-decimal decimal strings in contracts (`"118.00"`), never `float`.
- Dates: ISO 8601 (`YYYY-MM-DD`), times `HH:mm:ss`, time zone `America/Lima`.
- Catalog codes: always strings (`"01"`, `"1000"`), never numbers.
- Diagrams: Mermaid inside Markdown.

## 5. Mandatory verification (before each commit)
```bash
python -m pip install -r tools/requirements.txt   # once
python tools/verificar.py                         # must end with "TODO CORRECTO" (all checks pass)
cd tools && npm install && npm run mermaid && npm run openapi
```
It checks: valid JSON Schemas, examples valid against their schemas, schema enums == catalogs,
tax calculations in examples (IGV, ISC systems 01/02/03, ICBPER), example XMLs valid against the UBL 2.1
XSD and consistent with their JSON, OpenAPI `$ref`s and use-case routes, traceability matrix (schema +
XPath + rules + catalogs), migration coverage, acceptance criteria covering every rule, cross references,
Mermaid diagrams and untouched official XSDs.

**If you change the matrix:** edit `matriz.csv` and run `python tools/generar_matriz_md.py`.
**If you change a catalog:** also update the matching `enum` in `comun.schema.json`
(the verifier fails until they match).
