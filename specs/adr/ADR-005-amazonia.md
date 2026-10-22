# ADR-005 · Emisor ubicado en la Amazonía (Ley 27037)

- **Estado:** Propuesto (duda D-04)
- **Contexto:** Si el emisor opera en la región selva y los bienes se consumen allí, la venta puede estar
  exonerada de IGV. Esto cambia el cálculo y el XML.
- **Decisión:** Se modela como configuración del emisor (`emisor.amazonia`), no como código especial:
  1. Productos vendidos en la zona → afectación `20` (cat. 07), tributo `9997` EXO (cat. 05).
  2. Leyenda `2001` (cat. 52) obligatoria en el comprobante.
  3. **El ICBPER se sigue cobrando**: la exoneración del IGV no exime de percibir el impuesto a las bolsas
     (criterio del Tribunal Fiscal comentado en fuentes especializadas, 2026).
  4. El ISC no se ve afectado por la exoneración del IGV.
- **Consecuencias:** El mismo código sirve para emisores dentro y fuera de la Amazonía.
