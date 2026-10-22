# Benchmark: Nubefact (reference for use cases)

> **To be completed by the team** with its own DEMO account (the agent does not create accounts).
> Use the template at the end and store screenshots in `docs/benchmark/capturas/`.

## Public reference features
Nubefact is a Peruvian electronic invoicing provider with a web portal and a JSON API
(operations to generate a document, query a document, generate a void and query a void).
The features used as reference to discover use cases are:

| Observed feature | Derived use case (see `specs/01-casos-uso/`) |
|---|---|
| Issue invoice / receipt from a form | CU-03, CU-04 |
| Issue credit / debit note referencing a document | CU-05, CU-06 |
| Void documents (voiding communication / summary) | CU-07 |
| Check status and download XML, PDF and CDR | CU-08 |
| Email the document to the customer | CU-09 |
| Maintain customers and products (with IGV treatment per product) | CU-01, CU-02 |
| Series and automatic numbering | CU-10 |
| Sales reports | CU-12 |

## Public evidence found
- Nubefact's official Odoo integration confirms that it issues invoices (01), receipts (03), credit notes (07) and debit notes (08), withholding (20) and perception (40) documents, sends them through its API and emails PDF + XML to the customer (https://apps.odoo.com/apps/modules/18.0/l10n_pe_edi_odoofact). → CU-03 to CU-06, CU-09.
- DPL News (2021), quoting CONTA PERÚ: SUNAT classified at least 59 frequent errors in electronic invoicing; the most common are incomplete fields and mistyped customer data, which prevent validation by SUNAT/OSE (https://dplnews.com/peru-6-recomendaciones-para-emitir-tus-facturas-electronicas-de-forma-eficiente/). → pre-validation R-10/R-11, CA-07 to CA-10.

## Frequent pain points to verify in user reviews
Hypotheses the team must confirm or discard by reading real reviews:
- Rejections due to mistyped or non-registered RUC → pre-validation (R-10, R-13).
- Rounding errors between IGV-inclusive price and sale value → rule R-28.
- OSE/SUNAT unavailable when issuing → resend queue (CU-11).
- Need to issue without internet at fairs or in the warehouse → offline mode with deferred submission.
- Plastic bags forgotten on the receipt → "bag" product with automatic ICBPER.

## Observation template (DEMO)
| Screen / flow | Fields requested | Validations shown | Error messages | Screenshot |
|---|---|---|---|---|
| | | | | |
