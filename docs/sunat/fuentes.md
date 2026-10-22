# Fuentes normativas y técnicas

| Fuente | Uso en el proyecto | Enlace |
|---|---|---|
| RS 097-2012/SUNAT | Crea el SEE – Del Contribuyente. Anexos 1–4 (campos por comprobante) y Anexo 8 (catálogos). | https://www.sunat.gob.pe/legislacion/superin/2012/ (y modificatorias) |
| Anexo 8 – Catálogo de códigos (versión UBL 2.1) | Catálogos 01–58 en `docs/sunat/catalogos/` | https://www.sunat.gob.pe/legislacion/superin/2017/anexoE-245-2017.pdf |
| Anexo N.° 1 – Factura electrónica (actualización 2022) | XPath de cada campo, `InvoiceTypeCode/@listID` (cat. 51), estructura ICBPER (`BaseUnitMeasure`, `PerUnitAmount`) | https://www.sunat.gob.pe/legislacion/superin/2022/anexo-123-2022.pdf |
| Guía de elaboración de XML – Factura UBL 2.1 | Ejemplos de nodos, TierRange (cat. 08), PriceTypeCode (cat. 16) | https://cpe.sunat.gob.pe (guías XML) |
| Guías XML – Nota de crédito / débito UBL 2.1 | Estructura `CreditNote` / `DebitNote`, `DiscrepancyResponse`, `BillingReference` | https://cpe.sunat.gob.pe (guías XML) |
| RS 234-2006/SUNAT | Libros y registros: Formato 12.1 (Inventario Permanente en Unidades Físicas) y 13.1 (Valorizado) | https://www.sunat.gob.pe/legislacion/superin/2006/234.htm |
| Ley 30884 | ICBPER | Diario El Peruano |
| Ley 27037 | Exoneración IGV Amazonía | Diario El Peruano |
| OASIS UBL 2.1 | XSD en `docs/ubl/` | http://docs.oasis-open.org/ubl/os-UBL-2.1/ |
| Esquemas de soporte (CCTS, XMLDSig, XAdES) | `docs/ubl/soporte/` | https://github.com/phax/ph-xsds |

## Observaciones de las fuentes
- La guía XML de factura (versión 1.0) usaba `cbc:ProfileID` para el tipo de operación; el Anexo 1
  actualizado lo ubica en **`cbc:InvoiceTypeCode/@listID`**. Este proyecto sigue el Anexo 1 actualizado.
- La guía escribe `cac:TierRange` en un ejemplo y `cbc:TierRange` en la tabla. El XSD UBL 2.1 define
  **`cbc:TierRange`** dentro de `cac:TaxCategory`; se usa ese.
- El Anexo 8 de 2017 aún no lista el tributo 7152 (ICBPER), que fue incorporado después.
