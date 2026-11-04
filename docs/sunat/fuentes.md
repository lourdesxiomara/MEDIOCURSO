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
| RS 234-2006 – Annex 3 Tables (RS 169-2015 version) | Tables 5, 6, 10 and 12 in `docs/sunat/tablas-libros/` | https://www.sunat.gob.pe/legislacion/superin/2015/anexo3-rs169-2015.pdf |
| Electronic books structure – Format 12.1 (19 fields) | Kardex contract and PLE 12.1 export (R-60 to R-66) | https://www.sunat.gob.pe/legislacion/superin/2018/anexoI-315-2018.pdf |
| Electronic books structure – Format 14.1 (RS 361-2015; PLE 5.2 adds ICBPER as field 23) | Sales Record contract and PLE 14.1 export (R-70 to R-75) | https://www.sunat.gob.pe/legislacion/superin/2015/anexo1-361-2015.pdf · https://noticierocontable.com/estructura-libros-electronicos/ |
| RS 000193-2020/SUNAT – payment terms | `formaPago`, credit instalments (R-35, R-36); credit note reason 13 | https://www.sunat.gob.pe/legislacion/superin/2020/193-2020.pdf · https://www.sunat.gob.pe/legislacion/superin/2020/anexo1-193-2020.pdf |
| SEE programmer manual – return codes | CDR ranges: exceptions 0100–1999, rejections 2000–3999, observations ≥ 4000 (R-53 to R-55) | https://llama.pe/listado-de-errores-manual-del-programador-factura-electronica-sunat |
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
