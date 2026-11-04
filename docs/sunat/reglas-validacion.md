# Issuing validation rules

Each rule has an ID (`R-xx`) referenced from the JSON Schemas (`description`), the traceability matrix,
the acceptance criteria and the API errors.
**Type:** *E* = structural (validated by the schema) · *N* = business (validated by the domain) · *X* = external (OSE/SUNAT).

## Document identification
| ID | Rule | Type | Source |
|---|---|---|---|
| R-01 | `tipoComprobante` ∈ {01, 03, 07, 08} | E | Cat. 01 |
| R-02 | Invoice series: `^F[A-Z0-9]{3}$`; receipt: `^B[A-Z0-9]{3}$` | E/N | Annexes 1 and 2 |
| R-03 | Number: integer 1–99999999, unique per (type, series); assigned by the system, never by the user | N | Annex 1 |
| R-04 | Credit/debit note: series starting with the same letter as the document it modifies | N | Annexes 3 and 4 |
| R-05 | `fechaEmision` not later than today; maximum submission deadline per current regulation | N/X | RS 097-2012 |

## Parties
| ID | Rule | Type | Source |
|---|---|---|---|
| R-10 | RUC: 11 digits, prefix 10, 15, 16, 17 or 20, modulo-11 check digit | E/N | Cat. 06 |
| R-11 | Invoice: customer must have a RUC (`tipoDocumento` = 6) except for exports | N | Annex 1 |
| R-12 | Receipt: customer with DNI (8 digits) or another cat. 06 document; identification mandatory above the SUNAT threshold | N | Annex 2 |
| R-13 | Customer RUC status and condition (active / located) | X | SUNAT RUC registry |

**RUC check digit (R-10):** weights `5,4,3,2,7,6,5,4,3,2` over the first 10 digits;
`remainder = sum mod 11`; `dv = 11 − remainder`; if `dv = 10 → 0`, if `dv = 11 → 1`.

## Items and taxes
| ID | Rule | Type | Source |
|---|---|---|---|
| R-20 | `unidadMedida` ∈ cat. 03 | E | Cat. 03 |
| R-21 | `afectacionIgv` ∈ cat. 07 | E | Cat. 07 |
| R-22 | Treatment 10–17 → tax 1000 (IGV), category S, rate 18 % | N | Cat. 05/07 |
| R-23 | Treatment 20–21 → tax 9997, category E, IGV 0; 30–36 → 9998, O; 40 → 9995, G | N | Cat. 05/07 |
| R-24 | If the product is subject to ISC: `sistemaIsc` ∈ cat. 08 mandatory and tax 2000 (EXC) | N | Cat. 08 |
| R-25 | ISC is computed before IGV and **is part of the IGV tax base** | N | TUO IGV and ISC law |
| R-26 | ICBPER: `cantidadBolsas` integer ≥ 1, amount = bags × current rate (D-01); not part of the IGV base | N | Law 30884, Annex 1 |
| R-27 | `precioTipo` ∈ cat. 16; free-of-charge operations use `02` and legend 1002 | N | Cat. 16/52 |
| R-28 | Round to 2 decimals, half-up, per line; totals = sum of rounded lines | N | Annex 1 |

## Totals and legends
| ID | Rule | Type | Source |
|---|---|---|---|
| R-30 | `valorVenta` = Σ sale value of taxed + exempt + unaffected lines − discounts affecting the base | N | Annex 1 |
| R-31 | `importeTotal` = sale value + IGV + ISC + ICBPER + other charges − global discounts not affecting the base − advances | N | Annex 1 |
| R-32 | Legend 1000 (amount in words, in Spanish) mandatory | N | Cat. 52 |
| R-33 | `moneda` ∈ cat. 02 and all lines in the same currency | E/N | Cat. 02 |
| R-34 | `tipoOperacion` ∈ cat. 51 (invoices and receipts only) | E | Cat. 51 |

## Payment terms (RS 000193-2020/SUNAT)
| ID | Rule | Type | Source |
|---|---|---|---|
| R-35 | Every invoice declares `formaPago.tipo` = `Contado` (paid in full on the issue date) or `Credito` (all or part paid later). XML: `cac:PaymentTerms` with `cbc:ID` = `FormaPago` and `cbc:PaymentMeansID` = `Contado` / `Credito` | E/N | Annex 1 field 49-A |
| R-36 | `Credito` ⇒ `montoNetoPendiente` (> 0 and ≤ `importeTotal`, net of IGV withholding, detraction and other deductions) and at least one instalment; instalments numbered 1..n and sent as `Cuota001`, `Cuota002`…, each with amount and due date later than the issue date; Σ instalments = `montoNetoPendiente`. `Contado` ⇒ no instalments. Later changes to amounts or dates are made with a credit note reason 13 (cat. 09) | N | Annex 1 fields 64-A, 64-B; cat. 09 |

## Credit / debit notes
| ID | Rule | Type | Source |
|---|---|---|---|
| R-40 | `motivo` ∈ cat. 09 (credit note) or cat. 10 (debit note), with a written justification | E | Cat. 09/10 |
| R-41 | `documentoAfectado` must exist, be accepted by SUNAT/OSE and belong to the same issuer | N | Annexes 3/4 |
| R-42 | Credit note: amount ≤ balance of the affected document | N | Annex 3 |

## Signature, submission and response
| ID | Rule | Type | Source |
|---|---|---|---|
| R-50 | XML valid against the UBL 2.1 XSD before signing | E | OASIS UBL 2.1 |
| R-51 | Enveloped XMLDSig signature in `ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent` with a valid digital certificate; `cac:Signature/…/cbc:URI` points to the `ds:Signature` `Id`; signing must not change the document. Example: `specs/02-dominio/ejemplos/factura-F001-1.firmada.xml` (test certificate) | X | RS 097-2012 |
| R-52 | Submission to OSE/SUNAT as ZIP `RUC-TYPE-SERIES-NUMBER.zip` | X | SEE programmer manual |
| R-53 | A document only becomes `ACEPTADO` with a CDR whose response code is 0 or ≥ 4000. A number is consumed once SUNAT/OSE processed the document: a document rejected with a code 2000–3999 keeps its number and is **never** re-sent with it; the sale is issued again with a new number | N/X | SEE programmer manual (return codes) |
| R-54 | The response code is classified by range: **0** accepted · **0100–1999 exception** (the file could not be processed: the document counts as *not submitted*) · **2000–3999 rejection** (processed and invalid) · **≥ 4000 observation** (valid, accepted with observations). The category is stored in `respuestaSunat.categoria` | N/X | SEE programmer manual (return codes) |
| R-55 | Effect of each category: *exception* → status `PENDIENTE_ENVIO`; transient service codes (e.g. 0100, 0109) are retried automatically with backoff and the **same number**; format/content codes (1000–1999) need correction and are re-sent with the **same number** within the deadline (R-05). *Rejection* (invoice, notes) → `RECHAZADO`, number not reused (R-53), stock not deducted. *Rejection of a daily summary or voiding communication* → the file counts as not submitted and is re-sent with the same file name. *Observation* → `ACEPTADO_CON_OBSERVACIONES`, observations kept for review | N/X | SEE programmer manual (return codes) |

## Books and records (RS 234-2006/SUNAT)
Tables 2, 5, 6, 10 and 12 of Annex 3 are in `docs/sunat/tablas-libros/`.

### Format 12.1 – Permanent Inventory Record in Physical Units
| ID | Rule | Type | Source |
|---|---|---|---|
| R-60 | Every warehouse movement produces one Format 12.1 row with its 19 fields: period `AAAAMM00` of the movement date (field 1), CUO and entry number (2–3), establishment (4), item type and code (6–9), document date, type, series and number (10–13), operation type (14), description (15), unit (16), input or output (17–18) and status (19) | E/N | Format 12.1 |
| R-61 | `tipoOperacionTabla12` ∈ table 12 and consistent with the direction: sale 01 and returns to supplier 25 are outputs; purchase 02 and customer return 24 are inputs; opening balance is 16; inventory adjustment 28 is either. The direction of every code is in `tabla12.json` (`sentido`) | E/N | Format 12.1 field 14, table 12 |
| R-62 | Supporting document type ∈ table 10. Sales and notes link to the CPE: type = cat. 01 code, series and number split from `cbc:ID` (F001-1 → F001 / 1). Internal documents, adjustments and the opening balance use `00`, with series and number `0` when absent | E/N | Format 12.1 fields 11–13, table 10 |
| R-63 | Item type ∈ table 5 (`01` MERCADERIAS for groceries); unit ∈ table 6, derived from the CPE unit (catalog 03) with the one-to-one equivalence in `tabla06.json` (NIU, ZZ, KGM, GRM, LTR, MLT, BX, BG, DZN, PK) | E/N | Format 12.1 fields 6, 16; tables 5, 6 |
| R-64 | `codigoEstablecimiento` = SUNAT annex establishment code (4 to 7 digits, `0000` registered address), equal to the CPE `cbc:AddressTypeCode` of the issuing establishment | E/N | Format 12.1 field 4 |
| R-65 | Running balance: `saldoFinal` = previous balance + inputs − outputs, never negative. The first row of each item and period is the opening balance (table 12 = 16). Period closing = opening + Σ inputs − Σ outputs | N | Format 12.1 (saldo) |
| R-66 | PLE export: file `LE` + RUC + `AAAAMM00` + `120100` + `00` + `1111` + `.txt`; one line per movement, 19 fields separated by `|` with a trailing `|`; dates `DD/MM/AAAA`; inputs positive in field 17 and `0.00` in 18, outputs negative in field 18 and `0.00` in 17; status 1, 8 or 9. Builder: `tools/ple.py` | E | PLE structure, Format 12.1 |

### Format 14.1 – Sales Record
From October 2026 every obligated taxpayer keeps it through SIRE (R-76, ADR-007); the 14.1 structure below is the data the system reconciles against the SIRE proposal.

| ID | Rule | Type | Source |
|---|---|---|---|
| R-70 | One row per CPE issued in the period (accepted or voided), with period `AAAAMM00` of the issue date, ordered by issue date, document type, series and number. Receipts are recorded one by one (field 9 empty) | N | Format 14.1 fields 1–9 |
| R-71 | Row amounts come from the CPE totals: field 14 = `totalGravado` (UBL document-level IGV `TaxableAmount`, without ISC), 16 = `totalIgv`, 18 = `totalExonerado`, 19 = `totalInafecto`, 20 = `totalIsc`, 23 = `totalIcbper`, 25 = `importeTotal` = Σ fields 13–24; fields 13, 21, 22 = `0.00` (no exports, no rice milling). Field 5 = due date of the last instalment for credit invoices. Customer fields 10–12 from the CPE, field 10 converted from catalog 06 to books table 2 (`tabla02.json`) | N | Format 14.1 fields 5, 10–25 |
| R-72 | Credit notes are recorded with **negative** amounts; credit and debit notes fill fields 28–31 with the issue date, type, series and number of the modified document | N | Format 14.1 fields 28–31 |
| R-73 | Field 26 = document currency; field 27 = `1.000` for PEN; for USD, the SBS exchange rate of the issue date | N | Format 14.1 fields 26–27 |
| R-74 | Field 35 status: `1` document of the period, `2` voided document (amounts kept as issued unless SUNAT instructions say otherwise, D-15), `8` omitted from a previous period, `9` adjustment of a previous period | N | Format 14.1 field 35 |
| R-75 | PLE export: file `LE` + RUC + `AAAAMM00` + `140100` + `00` + `1111` + `.txt`; one line per row, 35 fields separated by `|` with a trailing `|`; dates `DD/MM/AAAA`; amounts with 2 decimals and dot; optional fields empty (placeholder conventions to confirm with the PLE validator, D-15). Builder: `tools/ple.py` | E | PLE 5.2 structure, Format 14.1 |
| R-76 | **SIRE.** From the periods in which the company is obligated (non-principal taxpayers: Jan 2025; principal taxpayers: Jan 2026 or Oct 2026 by income), the Sales Record (RVIE) is kept in **SIRE**, not filed as PLE 14.1: SUNAT builds the *proposal* from the accepted CPEs; before accepting it, the system reconciles it against its own `registro-ventas` (same CPE keys — type, series, number — and the same fields 14–25); any difference blocks acceptance and is resolved with the CPE (credit/debit note, voiding) or adjusted in SIRE. The PLE 14.1 file stays as an audit/backup export | N/X | RS 112-2021/SUNAT (SIRE), RS 000125-2026/SUNAT; ADR-007 |
