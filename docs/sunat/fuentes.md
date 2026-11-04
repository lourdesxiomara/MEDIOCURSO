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
| RS 234-2006 – Annex 3 Tables (RS 169-2015 version) | Tables 2, 5, 6, 10 and 12 in `docs/sunat/tablas-libros/` | https://www.sunat.gob.pe/legislacion/superin/2015/anexo3-rs169-2015.pdf |
| Electronic books structure – Format 12.1 (19 fields) | Kardex contract and PLE 12.1 export (R-60 to R-66) | https://www.sunat.gob.pe/legislacion/superin/2018/anexoI-315-2018.pdf |
| Electronic books structure – Format 14.1 (RS 361-2015; PLE 5.2 adds ICBPER as field 23) | Sales Record contract and PLE 14.1 export (R-70 to R-75) | https://www.sunat.gob.pe/legislacion/superin/2015/anexo1-361-2015.pdf · https://noticierocontable.com/estructura-libros-electronicos/ |
| RS 000193-2020/SUNAT – payment terms | `formaPago`, credit instalments (R-35, R-36); credit note reason 13 | https://www.sunat.gob.pe/legislacion/superin/2020/193-2020.pdf · https://www.sunat.gob.pe/legislacion/superin/2020/anexo1-193-2020.pdf |
| SEE programmer manual – return codes | CDR ranges: exceptions 0100–1999, rejections 2000–3999, observations ≥ 4000 (R-53 to R-55) | https://llama.pe/listado-de-errores-manual-del-programador-factura-electronica-sunat |
| RS 112-2021/SUNAT (SIRE) · RS 000125-2026/SUNAT (schedule) | Sales Record kept in SIRE; obligation dates by taxpayer type (R-76, ADR-007) | https://elperuano.pe/noticia/299237-sunat-extiende-plazo-del-sire-para-empresas-con-ingresos-superiores-a-2300-uit · https://www.invyperu.com/blog/que-es-el-sire-sunat |
| RS 169-2015/SUNAT Annex 3 – official SPIJ publication | Full table 6, including `PK PAQUETE` (D-14) | https://spij.minjus.gob.pe/Graficos/Peru/2015/Junio/30/RS-169-2015-SUNAT-ANX-3.pdf |
| SUNAT – Manual del servicio API del Registro de Ventas e Información Electrónica (SIRE), v30, June 2026 | Official endpoints for token, proposal download, ticket, acceptance and replacement (port `PropuestaRegistroVentas`) | https://cpe.sunat.gob.pe/sites/default/files/2026-06/Manual%20del%20servicio%20API%20del%20Registro%20de%20Ventas%20e%20Informaci%C3%B3n%20Electr%C3%B3nica.%20v30.pdf |
| RS 112-2021/SUNAT (text) | RVIE proposal: accept, complement or replace (art. 8); CAR; Annex 2 = proposal structure | https://www.sunat.gob.pe/legislacion/superin/2021/112-2021.pdf |
| Law 30884 · DS 244-2019-EF (regulation), art. 5 | ICBPER amount per bag by year (`docs/sunat/tasas-icbper.json`, D-01) | https://www.mef.gob.pe/es/por-instrumento/decreto-supremo/20678-decreto-supremo-n-244-2019-ef/file |
| Annex 8 published with RS 000005-2023/SUNAT | Full catalog 51 (D-02) | https://www.sunat.gob.pe/legislacion/superin/2023/anexo-000005-2023.pdf |
| Annex 1 field 22 / Annex 9-A items 37 and 37-A (RS 123-2022) | Unit price includes IGV/IVAP, not ICBPER (D-10); ISC and ICBPER line tags (D-11) | https://www.sunat.gob.pe/legislacion/superin/2022/anexo-123-2022.pdf |
| SUNAT Annex C – Technical aspects of the OSE | `sendBill`, `sendSummary`, `getStatus` (D-03) | https://cpe.sunat.gob.pe/sites/default/files/inline-files/Aspectos%20t%C3%A9cnicos%20-%20OSE.pdf |
| INEI ubigeo 150117 (Los Olivos, Lima) | Issuer address in the examples (D-04) | https://citypopulation.de/en/peru/lima/admin/lima/150117__los_olivos/ |
| Law 27037, art. 3.1 | Definition of the Amazon region (D-04, ADR-005) | https://faolex.fao.org/docs/pdf/per21100.pdf |
| OASIS UBL 2.1 | XSDs in `docs/ubl/` | http://docs.oasis-open.org/ubl/os-UBL-2.1/ |
| OASIS UBL 2.1 `UBL-ApplicationResponse-2.1.xsd` (CDR) | Validates the CDR example (R-53 to R-55, matrix T-95…T-98). Copy from the ph-ubl distribution, whose `UBL-Invoice-2.1.xsd` has the same SHA-256 as the one in this repo | https://raw.githubusercontent.com/phax/ph-ubl/master/ph-ubl21/src/main/resources/external/schemas/ubl21/maindoc/UBL-ApplicationResponse-2.1.xsd |
| Support schemas (CCTS, XMLDSig, XAdES) | `docs/ubl/soporte/` | https://github.com/phax/ph-xsds |

## Official documents kept in the repository (`docs/fuentes-oficiales/`)
| File | Content | Origin | SHA-256 |
|---|---|---|---|
| `SUNAT-Estructura-PLE-v5-Anexo2.xls` | SUNAT, Annex 2 – structures of electronic books (PLE 5): naming rules, general rules, table 2 lengths, Formats 12.1 and 14.1 field by field | https://cdn.www.gob.pe/uploads/document/file/1763321/Estructura%20del%20PLE.xls | `76dcad111b8d07a0cc2931ac058b88224717e43879959abc6125491ee6b5742c` |
| `RS-112-2021-SUNAT-separata-El-Peruano.pdf` | RS 112-2021/SUNAT with annexes (El Peruano, 31/07/2021): RVIE proposal structure (Annex 2), CAR (Annex 1 table 7), document status (table 9) | https://cdn.www.gob.pe/uploads/document/file/2131205/RS%20112-2021.pdf.pdf | `6d437e28d6c60c789428b87361283947baa01aaf50b804bac15ed045fc33b1ab` |

## Notes on the sources
- The invoice XML guide (version 1.0) used `cbc:ProfileID` for the operation type; the updated Annex 1
  places it in **`cbc:InvoiceTypeCode/@listID`**. This project follows the updated Annex 1.
- The guide writes `cac:TierRange` in one example and `cbc:TierRange` in the table. The UBL 2.1 XSD defines
  **`cbc:TierRange`** inside `cac:TaxCategory`; that one is used.
- The 2017 Annex 8 does not yet list tax 7152 (ICBPER), which was added later.
- The return-code ranges come from a secondary transcription of the SEE programmer manual; the system does not
  depend on the per-code list, it stores the CDR code and text verbatim (D-07).
- Catalog descriptions in `docs/sunat/catalogos/` are kept in Spanish, exactly as SUNAT publishes them.
