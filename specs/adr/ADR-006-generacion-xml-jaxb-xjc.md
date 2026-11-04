# ADR-006 · UBL XML generation with classes generated from the XSD (JAXB / xjc)

- **Status:** Accepted — implemented in phase 2 (`implementacion/`)
- **Context:** The `GeneradorDocumentoUbl` port (`specs/04-api/puertos-salida.md`) must produce UBL 2.1 XML
  that is valid by construction against the official OASIS XSDs (`docs/ubl/`), for Invoice, CreditNote and
  DebitNote. Writing the XML by hand (string templates) makes every missing or misplaced node a runtime
  rejection by SUNAT (R-50).

## Decision
1. **Code generation from the XSD.** The `adaptadores/ubl` module generates Java classes with **xjc**
   (Jakarta XML Binding 4, `org.glassfish.jaxb:jaxb-xjc`) from the official schemas in `docs/ubl/maindoc` and
   `docs/ubl/common`, plus the support schemas in `docs/ubl/soporte` (CCTS, XMLDSig, XAdES), using the
   wrappers in `tools/xsd/`. Generation runs in the Gradle build (`generateUblClasses` task); generated
   sources are not committed.
2. **Bindings file** `adaptadores/ubl/src/main/xjb/ubl.xjb`: one Java package per namespace
   (`…ubl.invoice`, `…ubl.cac`, `…ubl.cbc`, `…ubl.ext`), `BigDecimal` for amounts (never `double`, RNF-10)
   and `LocalDate` / `LocalTime` adapters for `IssueDate` / `IssueTime`.
3. **Mapping** `Comprobante` (domain) → generated `InvoiceType` / `CreditNoteType` / `DebitNoteType` in a Kotlin
   mapper inside the adapter; the domain never sees JAXB classes (ADR-001). Each mapper line follows a row
   of the traceability matrix (`specs/05-trazabilidad/matriz.csv`).
4. **Validation on marshalling (R-50).** The `Marshaller` is configured with `setSchema(...)` loaded from the
   same XSD wrappers, so an invalid document fails **before** signing and before consuming a number.
5. **Signature after marshalling.** The DOM produced by JAXB is signed by `FirmadorDigital` (XMLDSig enveloped,
   Apache Santuario) inside `ext:UBLExtensions` (R-51).
6. **Golden tests.** For every JSON example in `specs/02-dominio/ejemplos/` the generator must produce XML that is
   equivalent (XMLUnit, ignoring whitespace) to the matching `*.sin-firma.xml`. These files are already
   validated by `tools/verificar.py`, so the specification doubles as the test oracle.

## Android
The JAXB runtime is designed for the JVM; on Android (ART) it requires the Jakarta runtime and has
reflection limits. A **spike** validates it at the start of development. If it fails, the Android adapter keeps
the same generated model but serializes with a code-generated serializer (e.g. kotlinx-serialization +
xmlutil) produced from the same XSD, and must pass the **same golden tests**. The port contract does not change.

## Consequences
- (+) Structure and node order come from the XSD, not from hand-written templates.
- (+) Schema updates (new SUNAT nodes) = regenerate classes + adjust the mapper.
- (+) The matrix, the examples and the generator stay aligned through the golden tests.
- (−) Large generated model (UBL has hundreds of types); longer build.
- (−) Android needs the spike described above.

## Rejected alternatives
- String templates (FreeMarker, Velocity): no structural guarantee; errors appear only at SUNAT.
- DOM built by hand: verbose and error-prone in node order.

## Implementation (phase 2, `implementacion/`)
What was built, and where it differs from the text above:
- **Generation task:** `generateUblClasses` (Gradle `JavaExec` running `com.sun.tools.xjc.XJCFacade`, JAXB 4.0.5) on
  `docs/ubl/maindoc/UBL-Invoice-2.1.xsd` plus the support schemas in `docs/ubl/soporte`. The support schemas are passed
  to xjc directly, so the `tools/xsd` wrappers are only used for validation.
- **Packages:** xjc's default package per namespace (`oasis.names.specification.ubl.schema.xsd.invoice_2`,
  `…commonaggregatecomponents_2`, `…commonbasiccomponents_2`) instead of a bindings file; dates stay as
  `XMLGregorianCalendar`. Amounts are `BigDecimal`, as decided.
- **Mapper:** `GeneradorFacturaJaxb` (domain `Comprobante` → `InvoiceType`); the `Marshaller` validates with the XSD (R-50).
- **Signature:** the JDK's standard XMLDSig API (`javax.xml.crypto.dsig`, derived from Apache Santuario), so no extra dependency.
- **Golden tests:** `GeneradorFacturaTest` compares the generated XML with the invoice, ISC invoice and receipt examples.
  To make them comparable, the receipt and ISC examples now carry the full issuer address and the
  `DocumentCurrencyCode` attributes, like invoice F001-1, and line 2 of `comprobante.factura.json` carries its UNSPSC code.
