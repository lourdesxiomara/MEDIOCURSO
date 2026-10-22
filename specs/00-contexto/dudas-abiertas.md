# Open questions

Points that could **not** be verified in an official source or that depend on a management decision.
No agent may resolve them by inventing: they are answered here, recording the source.

| ID | Question | Impact | Status |
|---|---|---|---|
| D-01 | ICBPER rate in force on the issue date. S/ 0.50 per bag assumed (final step of Law 30884 since 2023). | ICBPER calculation | Parameterized in configuration; confirm |
| D-02 | Full, current catalog 51. `docs/sunat/catalogos/cat51.json` holds only the subset relevant to groceries. | Operation types | Confirm with the current Annex 8 on cpe.sunat.gob.pe |
| D-03 | OSE provider and its technical contract (standard `billService` SOAP or its own REST API). | Submission adapter | Pending management |
| D-04 | Does the issuer operate in the Amazon region (Law 27037)? Changes IGV treatment (`20`) and legend `2001`. | Calculation and legends | Pending management (see ADR-005) |
| D-05 | Products subject to ISC (alcoholic drinks, cigarettes)? Defines which catalog 08 system is used. | ISC | Pending product inventory |
| D-06 | Does the legacy data have prices? The sample has no prices or customers. | Migration | Pending review of the real DB |
| D-07 | CDR error codes to map (SUNAT official exception list). | API error contract | Modelled generically (`codigoSunat`, `descripcion`) |
| D-08 | Database: one per device (SQLite) or a central one shared by Windows and Android. | Data architecture | Proposal in ADR-003 |
| D-09 | Can the number of a document rejected by the OSE/SUNAT be reused? | Number assignment (R-53) | Check the SEE programmer manual |
| D-10 | Should the tax-inclusive unit price (cat. 16 = 01) of a plastic bag include ICBPER? Examples exclude it and total ICBPER separately. | Bag `PricingReference` | Check the current XML guide |
| D-11 | Exact XML representation of the ISC fixed amount (cat. 08 = 02): the example uses `cbc:BaseUnitMeasure` + `cbc:PerUnitAmount` in the subtotal, which is valid UBL. | ISC system 02 XML | Check the current SUNAT XML guide |
