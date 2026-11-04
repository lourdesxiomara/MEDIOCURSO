# ADR-007 · Sales Record through SIRE, with the 14.1 structure as the reconciliation contract

- **Status:** Accepted
- **Context:** The exam asks for Format 14.1 (Sales Record) with PLE output. SUNAT's current schedule moves the
  Sales Record (RVIE) to **SIRE** (Integrated System of Electronic Records, RS 112-2021/SUNAT): non-principal
  taxpayers since the January 2025 period, principal taxpayers with 2024 net income up to 2,300 UIT since January 2026,
  and above 2,300 UIT since October 2026 (RS 000125-2026/SUNAT). For the example period (October 2026) SIRE applies
  to ABC Software Corp whatever its size, so this decision does not depend on unknown company data.
- **Decision:**
  1. The system keeps its own Sales Record with the 14.1 structure (`registro-ventas.schema.json`, rules R-70 to R-75),
     built from the accepted and voided CPEs. It is the company's ledger of what it issued.
  2. Every period, SUNAT generates the RVIE **proposal** in SIRE from the CPEs received through the OSE/SUNAT. The
     system downloads it through the `PropuestaRegistroVentas` output port, which uses SUNAT's official SIRE API
     (token, `exportapropuesta`, ticket, `archivoreporte`, `aceptapropuesta`; see `specs/04-api/puertos-salida.md`),
     and **reconciles** it with its own record (R-76): key = type, series, number; compared = issue date, customer
     document and fields 13–26. API: `POST /reportes/ventas/conciliaciones-sire`, result in `conciliacion-sire.schema.json`.
  3. Only a reconciled proposal is accepted in SIRE. Differences are fixed at the source (credit/debit note, voiding)
     or adjusted in SIRE, never by editing the internal record by hand.
  4. The PLE 14.1 text file (`tools/ple.py`, R-75) remains as an audit and backup export, and for any period in which
     the company is not obligated to SIRE.
- **Consequences:**
  - (+) The specification matches the current regulation and still delivers the 14.1 structure the exam requires.
  - (+) Reconciliation catches CPEs that SUNAT did not receive or received with different amounts.
  - (+) The SIRE calls are taken from SUNAT's official API manual (v30, June 2026), so the adapter contract is verifiable.

## Proposal file → 14.1 mapping (RS 112-2021, Annex 2)
Official source kept in the repository: `docs/fuentes-oficiales/RS-112-2021-SUNAT-separata-El-Peruano.pdf` (El Peruano, 31/07/2021, pages 27–36).
Implemented in `tools/sire.py` and checked by `tools/verificar.py` with `ejemplos/propuesta-sire.2026-10.txt`.

| Annex 2 field | Meaning | 14.1 row field | Note |
|---|---|---|---|
| 1, 2 | Generator RUC and name | — | Must be the company |
| 3 | Period YYYYMM | `periodo` | + `00` |
| 4 | CAR | `car` | Annex 1 table 7: RUC + type + series + number (27) |
| 5 | Issue date DD/MM/AAAA | `fechaEmision` | |
| 6 | Due / payment date | `fechaVencimiento` | Type 14 only |
| 7, 8, 9, 10 | Type, series, number, final number | `tipoComprobanteTabla10`, `serie`, `numero`, `numeroFinal` | Key of the reconciliation |
| 11, 12, 13 | Customer ID type, number, name | `tipoDocumentoCliente`, `numeroDocumentoCliente`, `nombreCliente` | |
| 14 – 26 | Export, taxed base, discounts, IGV, exempt, unaffected, ISC, IVAP base and tax, ICBPER, other, total | 14.1 fields 13 – 25 | Base without ISC; credit notes negative; voided = 0.00 (note 4) |
| 27, 28 | Currency, exchange rate | `moneda`, `tipoCambio` | Rate mandatory only if ≠ PEN |
| 29 – 32 | Modified document date (YYYY-MM-DD), type, series, number | `modificadoFecha`, `modificadoTipo`, `modificadoSerie`, `modificadoNumero` | Notes only |
| 33 | Project ID | `contrato` | |
| 34 – 40 | Note type, document status, internal, free-of-charge value, operation type, inconsistencies | — | Referential, shown by SUNAT only |
