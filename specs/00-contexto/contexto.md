# 00 · Context, scope and assumptions

## 1. Problem
ABC Software Corp sells groceries wholesale and retail. Its current software only records warehouse
movements (`fecha, ingreso, salida, producto, nro_documento`) and:

| Gap | Consequence |
|---|---|
| Does not validate RUC | Documents rejected by SUNAT/OSE |
| Does not calculate IGV, ISC, ICBPER | Wrong amounts, fines |
| Does not generate UBL 2.1 XML | Cannot issue electronic documents |
| Does not sign digitally | The XML has no legal validity |
| Does not talk to OSE/SUNAT | Gets no CDR (receipt confirmation) |
| Informal `nro_documento` | No formal series or numbers |

## 2. Regulatory framework
| Regulation | What it brings to the system |
|---|---|
| **RS 097-2012/SUNAT** | Creates the *SEE – Del Contribuyente* (issuing from the taxpayer's own systems). Its annexes define mandatory fields per document (Annexes 1–4) and **Annex 8: catalogs**. |
| **RS 234-2006/SUNAT** | Books and records. The legacy system is in practice a **Permanent Inventory Record in Physical Units (Format 12.1)**: inputs, outputs and balance per item, with the supporting document of each movement. |
| **RS 117-2017/SUNAT** | Electronic Services Operator (OSE). See question D-03. |
| **Law 30884** | ICBPER (plastic bag consumption tax), tax code 7152. |
| **Law 27037** | IGV exemption in the Amazon region (relevant if the issuer operates in the jungle region). See ADR-005. |
| **OASIS UBL 2.1** | XML standard of the document (`UBL-Invoice-2.1.xsd`, `CreditNote`, `DebitNote`). |

Details and links: `docs/sunat/fuentes.md`.

## 3. Scope of the Spec-First phase
**Includes:** rules, catalogs, domain model, DTOs (JSON Schema), API contracts (OpenAPI 3.1),
output port contracts, MVC→Hexagonal diagrams, traceability matrix, migration plan,
architecture decisions and the MSI/APK distribution strategy.

**Excludes:** business code, real signing with a certificate, real submission to OSE/SUNAT.

## 4. Documents in scope
| Cat. 01 code | Document | UBL document | Series |
|---|---|---|---|
| 01 | Invoice (factura) | `Invoice` | `F` + 3 alphanumerics (F001) |
| 03 | Sales receipt (boleta) | `Invoice` | `B` + 3 alphanumerics (B001) |
| 07 | Credit note | `CreditNote` | Series of the document it modifies |
| 08 | Debit note | `DebitNote` | Series of the document it modifies |

## 5. Assumptions (to confirm with management)
- S-01 The issuer is a single company with one RUC.
- S-02 Main currency PEN; USD allowed.
- S-03 Domestic sale (catalog 51 = `0101`) is the dominant case; no exports.
- S-04 Product list prices include IGV (retail); the system splits value + IGV.
- S-05 The legacy data is in a file/DB exportable to CSV (`docs/legado/`).
- S-06 An OSE (provider TBD) is the main channel and direct SUNAT the alternative.
