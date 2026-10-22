# Esquemas de soporte para UBL 2.1

Los XSD oficiales de `docs/ubl/common` y `docs/ubl/maindoc` (OASIS UBL 2.1) importan estos
espacios de nombres **sin `schemaLocation`**, por eso por sí solos no compilan:

| Namespace | Archivo |
|---|---|
| `urn:un:unece:uncefact:data:specification:CoreComponentTypeSchemaModule:2` | `CCTS_CCT_SchemaModule.xsd` |
| `http://www.w3.org/2000/09/xmldsig#` | `xmldsig-core-schema.xsd` (W3C XML-DSig, usado por la firma SUNAT) |
| `http://uri.etsi.org/01903/v1.3.2#` | `XAdES01903v132-201601.xsd` (ETSI XAdES) |
| `http://uri.etsi.org/01903/v1.4.1#` | `XAdES01903v141-201601.xsd` (ETSI XAdES) |

Origen: copias publicadas en https://github.com/phax/ph-xsds (Apache 2.0), equivalentes a los
archivos `CCTS_CCT_SchemaModule-2.1.xsd`, `UBL-xmldsig-core-schema-2.1.xsd`,
`UBL-XAdESv132-2.1.xsd` y `UBL-XAdESv141-2.1.xsd` del paquete `os-UBL-2.1`.

## Cómo validar
Se usan los envoltorios de `tools/xsd/`, que cargan primero estos esquemas y luego el documento:

```bash
xmllint --noout --schema tools/xsd/validar-Invoice.xsd     mi-factura.xml
xmllint --noout --schema tools/xsd/validar-CreditNote.xsd  mi-nota-credito.xml
xmllint --noout --schema tools/xsd/validar-DebitNote.xsd   mi-nota-debito.xml
```
