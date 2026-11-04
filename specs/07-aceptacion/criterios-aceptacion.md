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

## E2. Payment terms

### CA-38 Every invoice declares its payment terms
- **Rules:** R-35 · **API:** `POST /comprobantes`
- **Given** an invoice request without `formaPago`
- **When** it is sent
- **Then** it returns `400` on `/formaPago`; with `formaPago.tipo = Contado` (`ejemplos/comprobante-crear.factura.json`) it returns `201` and the XML carries `cac:PaymentTerms` `FormaPago` / `Contado` (`ejemplos/factura-F001-1.sin-firma.xml`).

### CA-39 Credit sale in instalments
- **Rules:** R-36 · **API:** `POST /comprobantes`, `POST /comprobantes/{id}/emitir`
- **Given** `ejemplos/comprobante.factura-isc.json` (total 137.07, credit, 2 instalments)
- **When** it is issued
- **Then** the XML (`ejemplos/factura-F001-2-isc.sin-firma.xml`) has `FormaPago` / `Credito` / 137.07, `Cuota001` 68.54 due 2026-11-21 and `Cuota002` 68.53 due 2026-12-21.

### CA-40 Instalments that do not add up
- **Rules:** R-36 · **API:** `POST /comprobantes`
- **Given** a credit invoice with net pending 137.07 and instalments 68.54 + 60.00
- **When** it is sent
- **Then** it returns `422` with rule R-36 on `/formaPago/cuotas`.

### CA-41 Instalment due on or before the issue date
- **Rules:** R-36 · **API:** `POST /comprobantes`
- **Given** a credit invoice issued 2026-10-22 with an instalment due 2026-10-22
- **When** it is sent
- **Then** it returns `422` with rule R-36; a cash invoice (`Contado`) that includes instalments is also rejected (`400`).

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

### CA-33 Rejection CDR (2000–3999)
- **Rules:** R-53, R-54, R-55 · **API:** `POST /comprobantes/{id}/emitir`
- **Given** a simulated OSE rejecting with an error code
- **When** the document is issued
- **Then** status `RECHAZADO`, `respuestaSunat.codigoRespuesta` holds the code, `categoria = RECHAZO`, stock is **not** deducted and the number is never used again: re-issuing the sale gets the next number.

### CA-42 Exception (0100–1999) keeps the number
- **Rules:** R-54, R-55 · **API:** `POST /comprobantes/{id}/emitir`, `POST /comprobantes/reenviar-pendientes`
- **Given** a simulated OSE answering a SOAP fault with code `0109` (service unavailable)
- **When** invoice `F001-1` is issued
- **Then** `categoria = EXCEPCION`, status `PENDIENTE_ENVIO`, and the automatic retry re-sends `20600123450-01-F001-1.zip` with the **same** number until it gets code 0.

### CA-43 Observation (≥ 4000) is a valid document
- **Rules:** R-54, R-55 · **API:** `POST /comprobantes/{id}/emitir`
- **Given** a simulated OSE answering a CDR with an observation code ≥ 4000
- **When** the invoice is issued
- **Then** status `ACEPTADO_CON_OBSERVACIONES`, `categoria = OBSERVACION`, the observations are stored and stock is deducted.

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

## H. Books and records (RS 234-2006)

### CA-44 A sale produces a complete Format 12.1 row
- **Rules:** R-60, R-64 · **API:** `GET /inventario/kardex`
- **Given** invoice `F001-1` accepted, with 12 units of `CER-630`
- **When** the kardex of `CER-630` for period 2026-10 is queried
- **Then** it contains `ejemplos/movimiento-inventario.salida.json`: period `20261000`, establishment `0000` (= CPE `AddressTypeCode`), item type `01`, code `CER-630`, document `01` / `F001` / `1`, operation `01`, unit `NIU`, 12 units out, status `1`.

### CA-45 Operation type consistent with the direction
- **Rules:** R-61 · **API:** `POST /inventario/movimientos`
- **Given** a movement with `tipo = INGRESO` and `tipoOperacionTabla12 = 01` (sale)
- **When** it is recorded
- **Then** it returns `422` with rule R-61; with `tipoOperacionTabla12 = 24` (customer return, credit note `FC01-1`) it is accepted.

### CA-46 Internal documents and opening balance use table 10 code 00
- **Rules:** R-62 · **API:** `GET /inventario/kardex`
- **Given** the opening balance of `CER-630` (48 units on 2026-10-01)
- **When** the kardex is queried
- **Then** the first row has document `00` / `0` / `0` and operation `16` (`ejemplos/kardex.CER-630.2026-10.json`).

### CA-47 Unit and item type from the official tables
- **Rules:** R-63 · **API:** `POST /productos`, `GET /inventario/kardex`
- **Given** a product sold in `KGM` (catalog 03)
- **When** its movements are listed
- **Then** the unit is `KGM` in table 6 by the equivalence of `tabla06.json`, the item type is `01`; a product in `PK` is recorded in `NIU` until D-14 is resolved.

### CA-48 Running balance and closing balance
- **Rules:** R-65 · **API:** `GET /inventario/kardex`
- **Given** opening 48, sale `F001-1` (−12) and return `FC01-1` (+2)
- **When** the kardex is queried
- **Then** running balances are 48, 36, 38; totals inputs 2, outputs 12, closing 38; a movement that would leave a negative balance returns `422` with rule R-65.

### CA-49 PLE export of Format 12.1
- **Rules:** R-66 · **API:** `GET /inventario/kardex`
- **Given** the kardex of `CER-630` for 2026-10
- **When** it is requested with `formato=ple`
- **Then** the file is `LE2060012345020261000120100001111.txt`, identical to `ejemplos/LE2060012345020261000120100001111.txt`: 19 fields per line, inputs positive, outputs negative.

### CA-50 Sales Record built from the CPEs of the period
- **Rules:** R-70, R-71 · **API:** `GET /reportes/ventas`
- **Given** the CPEs issued in October 2026 (`F001-1`, `F001-2`, `B001-1`, `FC01-1`)
- **When** `GET /reportes/ventas?periodo=202610` is called
- **Then** it returns `ejemplos/registro-ventas.2026-10.json`: four rows ordered by date, type, series and number; each row's amounts equal the CPE totals and field 25 = Σ fields 13–24; `F001-2` carries the last instalment date (2026-12-21) in field 5; `FD01-1` (November) is not included.

### CA-51 Credit note recorded negative and linked
- **Rules:** R-72 · **API:** `GET /reportes/ventas`
- **Given** credit note `FC01-1` on invoice `F001-1`
- **When** the sales record of 2026-10 is generated
- **Then** its row has base −10.00, IGV −2.16, ISC −2.00, total −14.16 and fields 28–31 = 22/10/2026, `01`, `F001`, `1`.

### CA-52 Currency and exchange rate
- **Rules:** R-73 · **API:** `GET /reportes/ventas`
- **Given** documents in PEN
- **When** the sales record is generated
- **Then** field 26 = `PEN` and field 27 = `1.000`; a USD invoice carries the SBS rate of its issue date.

### CA-53 Voided document status
- **Rules:** R-74 · **API:** `POST /comprobantes/{id}/anular`, `GET /reportes/ventas`
- **Given** an invoice of the period voided through a voiding communication
- **When** the sales record is generated
- **Then** its row has field 35 = `2`; documents of the period have `1`.

### CA-54 PLE export of Format 14.1
- **Rules:** R-75 · **API:** `GET /reportes/ventas`
- **Given** the sales record of 2026-10
- **When** it is requested with `formato=ple`
- **Then** the file is `LE2060012345020261000140100001111.txt`, identical to `ejemplos/LE2060012345020261000140100001111.txt`: 35 pipe-separated fields per line, dates `DD/MM/AAAA`, amounts with 2 decimals; an invalid period (e.g. `2026-13`) returns `400`.
