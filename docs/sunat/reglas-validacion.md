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
| R-51 | Enveloped XMLDSig signature in `ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent` with a valid digital certificate | X | RS 097-2012 |
| R-52 | Submission to OSE/SUNAT as ZIP `RUC-TYPE-SERIES-NUMBER.zip` | X | SEE programmer manual |
| R-53 | A document only becomes `ACEPTADO` with a CDR. Handling of the number of a `RECHAZADO` document is pending (question D-09) | N/X | RS 097-2012 |
