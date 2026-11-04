# Open questions — log

Points that could not be verified at first in an official source, or that depended on a management decision.
No agent may resolve them by inventing: each one is closed here with its source, or with an explicit,
justified decision that is **configurable** (management can change it without touching the domain).

**Status: all questions are closed (0 open).** A new question is added as a new row with status *Open*.

| ID | Question | Impact | Status |
|---|---|---|---|
| D-01 | ICBPER amount per bag on the issue date. | ICBPER calculation (R-26) | **Resolved (source).** Official schedule: S/ 0.10 (2019), 0.20 (2020), 0.30 (2021), 0.40 (2022), **0.50 from 2023 onward** (Law 30884 art. 12; DS 244-2019-EF art. 5). Kept in `docs/sunat/tasas-icbper.json`, selected by issue date; the verifier checks it in the JSON and in the XML (`cbc:PerUnitAmount`) |
| D-02 | Full, current catalog 51. | Operation types | **Resolved (source).** `cat51.json` now holds the **complete** catalog (30 codes) from Annex 8 published with RS 000005-2023/SUNAT; the schema enum matches it |
| D-03 | OSE provider and its technical contract. | Submission adapter | **Resolved (decision, ADR-004 accepted).** The `CanalEnvioCpe` adapter implements the SUNAT SEE web service (`sendBill`, `sendSummary`, `getStatus`, SOAP + WS-Security). The endpoint URL and credentials are configuration; the OSE brand is a commercial choice that does not change the spec. An OSE with its own REST API is one more adapter of the same port |
| D-04 | Does the issuer operate in the Amazon region (Law 27037)? | Calculation and legends | **Resolved (decision, ADR-005 accepted).** The issuer's registered address in the examples is **Los Olivos, Lima (ubigeo 150117)**, outside the Amazon region defined in Law 27037 art. 3.1 → `amazonia = false`, treatment `10`. The previous example address (Rupa-Rupa, Leoncio Prado, Huánuco) *is* inside art. 3.1 e), so it was changed. If the company has an establishment in the region, `emisor.amazonia = true` activates ADR-005 |
| D-05 | Products subject to ISC? Which catalog 08 system? | ISC | **Resolved (decision).** ISC is **per-product configuration** (`sistemaIsc`, rate or fixed amount, start date), loaded by the accountant from the current Appendix IV of the IGV/ISC Law; no rate is hard-coded. A product flagged as alcoholic drink or tobacco stays inactive until configured (M-06). The ISC amounts in the examples only illustrate the three systems |
| D-06 | Does the legacy data have prices? | Migration | **Resolved (case statement).** The exam case defines the legacy record as `fecha, ingreso, salida, producto, nro_documento`: **no prices, no customers**. Format 12.1 is kept in **physical units**, so the migration does not need prices; the unit value is entered in the product catalog before the product is activated for sale (M-06) |
| D-07 | CDR error codes to map. | API error contract | **Resolved (design + source).** No per-code table is maintained: the system classifies by range (R-54) and stores the code and text **verbatim** from the CDR (`cbc:ResponseCode`, `cbc:Description`) in `codigoSunat` / `descripcion`. SUNAT's list changes over time; copying it would make the spec go stale |
| D-08 | One database per device (SQLite) or a central one? | Data architecture | **Resolved (decision, ADR-003 accepted).** SQLite per device with its own series per device; PostgreSQL adapter in the microservices phase |
| D-09 | Can the number of a document rejected by the OSE/SUNAT be reused? | Number assignment (R-53) | **Resolved:** codes 2000–3999 consume the number (not reused); exceptions 0100–1999 are re-sent with the same number (R-54, R-55) |
| D-10 | Does the tax-inclusive unit price (cat. 16 = 01) of a plastic bag include ICBPER? | Bag `PricingReference` | **Resolved (source).** Annex 1, field 22 *Precio de venta unitario*: "Incluye IGV o IVAP, según corresponda" — ICBPER is not part of it. ICBPER goes per line in item 37-A and as a total in field 40-A, added to field 42 (total taxes). The examples already follow this |
| D-11 | Exact XML representation of the ISC fixed amount (cat. 08 = 02). | ISC system 02 XML | **Resolved (source).** Annex 9-A item 37 defines the ISC line subtotal with only `cbc:TaxableAmount`, `cbc:TaxAmount`, `cac:TaxCategory/cbc:Percent` and `cbc:TierRange`; `cbc:BaseUnitMeasure` + `cbc:PerUnitAmount` belong to ICBPER (item 37-A). The system 02 example now uses those four tags: `Percent` = ISC amount ÷ base × 100 (37.50), so `TaxAmount = TaxableAmount × Percent` holds. The fixed amount per unit stays in the domain (`montoPorUnidad`) |
| D-14 | Does catalog 03 code `PK` (package) exist in books table 6? | Format 12.1 unit (R-63) | **Resolved:** yes, `PK PAQUETE` is in table 6 (official SPIJ publication of RS 169-2015 Annex 3); equivalence is one-to-one |
| D-15 | (a) Must the Sales Record be kept in SIRE instead of PLE 14.1? (b) What goes in empty optional PLE fields, and the amounts of voided documents? | 14.1 / 12.1 export (R-74, R-75, R-76) | **Resolved.** (a) Yes from Oct 2026 for every obligated taxpayer (RS 000125-2026; ADR-007). (b) Official PLE structure: empty optional fields stay empty, unused free fields are omitted; voided documents are entered with 0.00 (RS 112-2021 Annex 2 note 4). Copies in `docs/fuentes-oficiales/` |

## Sources used to close D-01 … D-11
- DS 244-2019-EF (ICBPER regulation), art. 5: https://www.mef.gob.pe/es/por-instrumento/decreto-supremo/20678-decreto-supremo-n-244-2019-ef/file
- Annex 8 (catalogs) published with RS 000005-2023/SUNAT: https://www.sunat.gob.pe/legislacion/superin/2023/anexo-000005-2023.pdf
- Annex 1 (invoice) fields 22, 40-A, 42 and Annex 9-A items 37 / 37-A (RS 123-2022/SUNAT): https://www.sunat.gob.pe/legislacion/superin/2022/anexo-123-2022.pdf
- Law 27037, art. 3.1 (Amazon region): https://faolex.fao.org/docs/pdf/per21100.pdf
- INEI ubigeo 150117 = Los Olivos, Lima: https://citypopulation.de/en/peru/lima/admin/lima/150117__los_olivos/
- SUNAT, Annex C – Technical aspects of the OSE (`sendBill`, `sendSummary`, `getStatus`): https://cpe.sunat.gob.pe/sites/default/files/inline-files/Aspectos%20t%C3%A9cnicos%20-%20OSE.pdf
