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
     system downloads it (future `PropuestaRegistroVentas` output port, SIRE web services) and **reconciles** it row by
     row with its own record: same key (type, series, number) and same fields 14–25 (R-76).
  3. Only a reconciled proposal is accepted in SIRE. Differences are fixed at the source (credit/debit note, voiding)
     or adjusted in SIRE, never by editing the internal record by hand.
  4. The PLE 14.1 text file (`tools/ple.py`, R-75) remains as an audit and backup export, and for any period in which
     the company is not obligated to SIRE.
- **Consequences:**
  - (+) The specification matches the current regulation and still delivers the 14.1 structure the exam requires.
  - (+) Reconciliation catches CPEs that SUNAT did not receive or received with different amounts.
  - (−) The SIRE web-service contract (authentication, download format) is specified in the implementation phase,
    from SUNAT's SIRE API manual; the core only depends on the port.
