# ADR-005 · Issuer located in the Amazon region (Law 27037)

- **Status:** Proposed (question D-04)
- **Context:** If the issuer operates in the jungle region and the goods are consumed there, the sale may be
  exempt from IGV. This changes the calculation and the XML.
- **Decision:** Modelled as issuer configuration (`emisor.amazonia`), not as special code:
  1. Products sold in the region → treatment `20` (cat. 07), tax `9997` EXO (cat. 05).
  2. Legend `2001` (cat. 52) mandatory on the document.
  3. **ICBPER is still charged**: the IGV exemption does not exempt from collecting the bag tax
     (Tax Court criterion reported by specialized sources, 2026).
  4. ISC is not affected by the IGV exemption.
- **Consequences:** The same code serves issuers inside and outside the Amazon region.
