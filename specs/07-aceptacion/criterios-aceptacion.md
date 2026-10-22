# 07 · Acceptance criteria (executable specification)

In Spec-First, code is written **to pass these tests**. Each criterion:
- has an ID `CA-xx`, the rules it checks (`R-xx` from `docs/sunat/reglas-validacion.md`,
  `M-xx` from `specs/06-migracion`) and the `specs/04-api/openapi.yaml` endpoint that exercises it;
- uses the data in `specs/02-dominio/ejemplos/` as input or expected output.

`tools/verificar.py` checks that **every rule R-xx and M-xx has at least one criterion** and that the
cited example files exist. Type *X* (external) rules are tested against a simulated OSE.

Format: **Given** (context) · **When** (action) · **Then** (observable result).

## A. Document identification

### CA-01 A valid invoice is created with system-calculated totals
- **Rules:** R-01, R-03, R-30, R-31, R-32, R-34 · **API:** `POST /comprobantes`
- **Given** the issuer in `ejemplos/comprobante.factura.json` with series `F001` active
- **When** `ejemplos/comprobante-crear.factura.json` is sent
- **Then** it returns `201` and the body matches `ejemplos/comprobante.factura.json` in lines, taxes, totals and legend 1000; the request carried no number and no totals.

### CA-02 Document type out of scope
- **Rules:** R-01 · **API:** `POST /comprobantes`
- **Given** a request with `tipoComprobante = "09"`
- **When** it is sent
- **Then** it returns `400` with a schema error on `/tipoComprobante`.

### CA-03 Series that does not match the type
- **Rules:** R-02 · **API:** `POST /comprobantes`
- **Given** an invoice (`01`) with series `B001`
- **When** it is sent
- **Then** it returns `400` pointing at `/serie`; with series `F001` it returns `201`.

### CA-04 Unique number per series
- **Rules:** R-03, R-53 · **API:** `POST /comprobantes/{id}/emitir`
- **Given** the last number of `F001` is 1
- **When** two invoices are issued concurrently
- **Then** they get 2 and 3, never the same number; retrying `emitir` with the same `Idempotency-Key` does not consume a new number.

### CA-05 Note series consistent with the affected document
- **Rules:** R-04 · **API:** `POST /comprobantes/{id}/notas-credito`
- **Given** invoice `F001-1` accepted
- **When** a note with series `BC01` is issued
- **Then** it returns `422` with rule R-04; with series `FC01` it is accepted.

### CA-06 Future issue date
- **Rules:** R-05 · **API:** `POST /comprobantes`
- **Given** the system clock at `2026-10-22`
- **When** an invoice with `fechaEmision = 2026-10-23` is created
- **Then** it returns `422` with rule R-05.

## B. Parties

### CA-07 RUC with an invalid check digit
- **Rules:** R-10 · **API:** `POST /clientes`, `POST /comprobantes`
- **Given** RUC `20456789015` (correct check digit: 4)
- **When** it is registered as a customer
- **Then** it returns `422` like `ejemplos/error.validacion.json` (rule R-10, field `/cliente/documento/numero`).

### CA-08 Invoice to a customer without RUC
- **Rules:** R-11 · **API:** `POST /comprobantes`
- **Given** the DNI customer in `ejemplos/comprobante.boleta.json`
- **When** an invoice (`01`) is issued to them
- **Then** it returns `400` stating the document must be type 6.

### CA-09 Receipt to a person with DNI
- **Rules:** R-12 · **API:** `POST /comprobantes`
- **Given** `ejemplos/comprobante-crear.boleta.json` (8-digit DNI)
- **When** it is sent
- **Then** it returns `201` and matches `ejemplos/comprobante.boleta.json`; with a 7-digit DNI it returns `400`.

### CA-10 Customer RUC not active
- **Rules:** R-13 · **API:** `POST /comprobantes` (simulated `ValidadorRuc` port)
- **Given** the simulated registry returns the RUC as deregistered
- **When** the invoice is created
- **Then** it returns `422` with rule R-13; if the registry does not respond, it is created with a warning and the sale is not blocked.

## C. Items and taxes

### CA-11 Unit of measure or treatment outside the catalog
- **Rules:** R-20, R-21 · **API:** `POST /productos`
- **Given** a product with `unidadMedida = "XYZ"` or `afectacionIgv = "99"`
- **When** it is registered
- **Then** it returns `400` naming the field and the catalog (03 or 07).

### CA-12 Taxed item: IGV 18 % on the sale value
- **Rules:** R-22, R-28 · **API:** `POST /comprobantes/validar`
- **Given** 10 units at price 25.96 with treatment `10`
- **When** it is validated
- **Then** unit value 22.00, sale value 220.00, IGV 39.60 (line 1 of `ejemplos/comprobante.factura.json`).

### CA-13 Unaffected or exempt item: no IGV
- **Rules:** R-23 · **API:** `POST /comprobantes/{id}/notas-debito`
- **Given** `ejemplos/nota-crear.debito.json` (late-payment interest, treatment `30`)
- **When** it is issued
- **Then** the tax is `9998` INA category `O`, IGV 0.00 and `totalInafecto` 50.00, as in `ejemplos/comprobante.nota-debito.json`.

### CA-14 ISC system 01 (ad valorem)
- **Rules:** R-24, R-25 · **API:** `POST /comprobantes/validar`
- **Given** product `ejemplos/producto-cerveza.json` (system `01`, rate 20 %)
- **When** 12 units are sold at 7.08
- **Then** value 60.00, ISC 12.00, IGV base 72.00 (value + ISC), IGV 12.96 and XML with `cbc:TierRange = 01`.

### CA-15 ISC system 02 (fixed amount)
- **Rules:** R-24, R-25 · **API:** `POST /comprobantes/validar`
- **Given** `ejemplos/producto-cerveza-monto-fijo.json` (fixed amount 1.50 per unit)
- **When** 12 units are sold at 6.49
- **Then** ISC = 12 × 1.50 = 18.00, IGV base 66.00, IGV 11.88 and XML with `cbc:TierRange = 02` (`ejemplos/factura-F001-2-isc.sin-firma.xml`, line 1).

### CA-16 ISC system 03 (retail sale price)
- **Rules:** R-24, R-25 · **API:** `POST /comprobantes/validar`
- **Given** `ejemplos/producto-cigarrillos.json` (retail price 12.00, rate 20 %)
- **When** 5 units are sold
- **Then** ISC = 12.00 × 0.847 × 20 % × 5 = 10.16, IGV base 50.16, IGV 9.03 and `cbc:TierRange = 03` (`ejemplos/factura-F001-2-isc.sin-firma.xml`, line 2).

### CA-17 ISC product without a calculation system
- **Rules:** R-24 · **API:** `POST /comprobantes`
- **Given** a product flagged with ISC but without `isc.sistema`
- **When** it is invoiced
- **Then** it returns `422` with rule R-24 (second error in `ejemplos/error.validacion.json`).

### CA-18 ICBPER per plastic bag
- **Rules:** R-26 · **API:** `POST /comprobantes/validar`
- **Given** 2 bags and a configured rate of 0.50
- **When** it is validated
- **Then** ICBPER = 1.00, it is not part of the IGV base and the XML uses `cbc:BaseUnitMeasure = 2` and `cbc:PerUnitAmount = 0.50` (line 3 of `ejemplos/factura-F001-1.sin-firma.xml`).

### CA-19 Free-of-charge transaction
- **Rules:** R-27 · **API:** `POST /comprobantes/validar`
- **Given** an item delivered as a bonus (treatment `15`)
- **When** it is validated
- **Then** `tipoPrecio = 02` (reference value) and legend 1002 is added.

### CA-20 Per-line rounding
- **Rules:** R-28 · **API:** `POST /comprobantes/validar`
- **Given** a line with a calculated IGV of 0.036
- **When** it is validated
- **Then** the line IGV is 0.04 (half-up) and the total is the sum of the already-rounded lines.

## D. Totals, currency and operation

### CA-21 Document totals
- **Rules:** R-30, R-31 · **API:** `GET /comprobantes/{id}`
- **Given** `ejemplos/comprobante.factura-isc.json`
- **When** it is queried
- **Then** sale value 88.00, ISC 28.16, IGV 20.91 and payable amount 137.07 = value + ISC + IGV.

### CA-22 Amount-in-words legend
- **Rules:** R-32 · **API:** `POST /comprobantes`
- **Given** a total of 345.80 PEN
- **When** the document is created
- **Then** it includes legend 1000 "TRESCIENTOS CUARENTA Y CINCO CON 80/100 SOLES" (in Spanish, as SUNAT requires).

### CA-23 Currency outside the catalog
- **Rules:** R-33 · **API:** `POST /comprobantes`
- **Given** `moneda = "ABC"`
- **When** it is sent
- **Then** it returns `400` citing catalog 02.

### CA-24 Operation type
- **Rules:** R-34 · **API:** `POST /comprobantes`
- **Given** an invoice without `tipoOperacion`
- **When** it is created
- **Then** `0101` is assumed and the XML carries it in `cbc:InvoiceTypeCode/@listID`; a value outside catalog 51 returns `400`.

## E. Credit and debit notes

### CA-25 Credit note for an item return
- **Rules:** R-40, R-41 · **API:** `POST /comprobantes/{id}/notas-credito`
- **Given** invoice `F001-1` accepted
- **When** `ejemplos/nota-crear.credito.json` is sent (reason `07`)
- **Then** `ejemplos/comprobante.nota-credito.json` is issued and an input of 2 units is recorded in inventory (CU-14).

### CA-26 Note on a missing or non-accepted document
- **Rules:** R-41 · **API:** `POST /comprobantes/{id}/notas-credito`
- **Given** an invoice in status `RECHAZADO`
- **When** a credit note is attempted
- **Then** it returns `409` (invalid state).

### CA-27 Credit note above the balance
- **Rules:** R-42 · **API:** `POST /comprobantes/{id}/notas-credito`
- **Given** invoice `F001-1` (amount 345.80) with a previous note for 14.16
- **When** a note for 340.00 is issued
- **Then** it returns `422` with rule R-42 (available balance 331.64).

### CA-28 Debit note for interest
- **Rules:** R-40 · **API:** `POST /comprobantes/{id}/notas-debito`
- **Given** invoice `F001-1` accepted
- **When** `ejemplos/nota-crear.debito.json` is sent
- **Then** `ejemplos/comprobante.nota-debito.json` is issued with catalog 10 reason `01` and the `DebitNote` XML validates against the XSD.

## F. XML, signature and submission

### CA-29 Generated XML valid against UBL 2.1
- **Rules:** R-50 · **API:** `GET /comprobantes/{id}/xml`
- **Given** each example document
- **When** its XML is generated
- **Then** it validates against `tools/xsd/validar-*.xsd` and matches the five `.sin-firma.xml` files in `specs/02-dominio/ejemplos/`.

### CA-30 Digital signature
- **Rules:** R-51 · **API:** `POST /comprobantes/{id}/emitir`
- **Given** a valid test certificate
- **When** the document is issued
- **Then** the XML contains `ds:Signature` in `ext:UBLExtensions`, the signature verifies and `firma.hash` is its `DigestValue`; with an expired certificate it returns `422` without consuming a number.

### CA-31 Packaging and submission to the OSE
- **Rules:** R-52, R-53 · **API:** `POST /comprobantes/{id}/emitir` (simulated OSE)
- **Given** a simulated OSE answering a CDR with code 0
- **When** the invoice is issued
- **Then** `20600123450-01-F001-1.zip` was sent and the final status is `ACEPTADO` with the CDR stored.

### CA-32 OSE unavailable
- **Rules:** R-53, R-05 · **API:** `POST /comprobantes/{id}/emitir`, `POST /comprobantes/reenviar-pendientes`
- **Given** a simulated OSE that does not respond
- **When** the document is issued
- **Then** it returns `202`, status `PENDIENTE_ENVIO`; once the OSE recovers, the resend leaves it `ACEPTADO` with the same number.

### CA-33 Rejection CDR
- **Rules:** R-53 · **API:** `POST /comprobantes/{id}/emitir`
- **Given** a simulated OSE rejecting with an error code
- **When** the document is issued
- **Then** status `RECHAZADO`, `respuestaSunat.codigoRespuesta` holds the code and stock is **not** deducted.

## G. Legacy migration

### CA-34 Migration dry run with the sample
- **Rules:** M-01, M-02, M-03, M-04, M-05, M-06, M-07 · **API:** `POST /migraciones?simulacion=true`
- **Given** `docs/legado/legado-almacen-muestra.csv`
- **When** the dry run is executed
- **Then** the result is: read 15, migrated 10, quarantined 4 (ids 7, 13, 14, 15), discarded 1 (id 11); nothing was written.

### CA-35 Row-by-row traceability
- **Rules:** M-07 · **API:** `GET /migraciones/{id}/trazabilidad`
- **Given** a completed migration
- **When** its traceability is queried
- **Then** every CSV `id` appears exactly once, with the rules applied and the new ids.

### CA-36 Rollback
- **Rules:** M-07 · **API:** `POST /migraciones/{id}/revertir`
- **Given** a completed migration and an invoice issued afterwards by the system
- **When** the migration is rolled back
- **Then** only records with `origen = MIGRACION` disappear; the invoice remains intact.

### CA-37 Balances reconcile after migrating
- **Rules:** M-02, M-05, M-07 · **API:** `GET /inventario/kardex`
- **Given** the migration of the sample
- **When** the kardex of ARROZ COSTENO 5KG is queried
- **Then** balance = Σ inputs − Σ outputs of its migrated rows (100 − 10 − 2 = 88), excluding quarantine.
