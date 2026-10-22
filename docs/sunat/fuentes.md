# Regulatory and technical sources

| Source | Use in the project | Link |
|---|---|---|
| RS 097-2012/SUNAT | Creates the SEE – Del Contribuyente. Annexes 1–4 (fields per document) and Annex 8 (catalogs). | https://www.sunat.gob.pe/legislacion/superin/2012/ (and amendments) |
| Annex 8 – Code catalogs (UBL 2.1 version) | Catalogs 01–58 in `docs/sunat/catalogos/` | https://www.sunat.gob.pe/legislacion/superin/2017/anexoE-245-2017.pdf |
| Annex 1 – Electronic invoice (2022 update) | XPath of each field, `InvoiceTypeCode/@listID` (cat. 51), ICBPER structure (`BaseUnitMeasure`, `PerUnitAmount`) | https://www.sunat.gob.pe/legislacion/superin/2022/anexo-123-2022.pdf |
| XML guide – UBL 2.1 Invoice | Node examples, TierRange (cat. 08), PriceTypeCode (cat. 16) | https://cpe.sunat.gob.pe (XML guides) |
| XML guides – UBL 2.1 credit / debit note | `CreditNote` / `DebitNote` structure, `DiscrepancyResponse`, `BillingReference` | https://cpe.sunat.gob.pe (XML guides) |
| SUNAT tax guidance – ISC calculation | Catalog 08 systems; retail-price factor = 1/(1+IGV+IPM) to 3 decimals (0.847) | https://orientacion.sunat.gob.pe/node/1809 |
| RS 234-2006/SUNAT | Books and records: Format 12.1 (Permanent Inventory in Physical Units) and 13.1 (Valued) | https://www.sunat.gob.pe/legislacion/superin/2006/234.htm |
| Law 30884 | ICBPER | Diario El Peruano |
| Law 27037 | IGV exemption in the Amazon region | Diario El Peruano |
| OASIS UBL 2.1 | XSDs in `docs/ubl/` | http://docs.oasis-open.org/ubl/os-UBL-2.1/ |
| Support schemas (CCTS, XMLDSig, XAdES) | `docs/ubl/soporte/` | https://github.com/phax/ph-xsds |

## Notes on the sources
- The invoice XML guide (version 1.0) used `cbc:ProfileID` for the operation type; the updated Annex 1
  places it in **`cbc:InvoiceTypeCode/@listID`**. This project follows the updated Annex 1.
- The guide writes `cac:TierRange` in one example and `cbc:TierRange` in the table. The UBL 2.1 XSD defines
  **`cbc:TierRange`** inside `cac:TaxCategory`; that one is used.
- The 2017 Annex 8 does not yet list tax 7152 (ICBPER), which was added later.
- Catalog descriptions in `docs/sunat/catalogos/` are kept in Spanish, exactly as SUNAT publishes them.
