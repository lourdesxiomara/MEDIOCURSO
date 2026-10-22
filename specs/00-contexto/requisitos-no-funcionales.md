# Non-functional requirements (measurable)

| ID | Attribute | Requirement | How it is verified |
|---|---|---|---|
| RNF-01 | Offline availability | Documents can be created, signed and saved without internet; they stay `PENDIENTE_ENVIO` and are resent automatically (CU-11, ADR-004) | CA-32 |
| RNF-02 | Performance | Validate and calculate a 50-line document in < 300 ms on the minimum hardware | Load test |
| RNF-03 | Performance | Generate + sign the XML in < 1 s (p95), excluding the OSE response | Load test |
| RNF-04 | Legal retention | Signed XML and CDR stored intact, with hash, for the tax statute-of-limitations period | DB audit |
| RNF-05 | Security | Digital certificate (.pfx) in the OS secure store (Windows) / Android Keystore; never inside the installer or in plain text | ADR-002 review |
| RNF-06 | Security | Role-based access (Seller, Warehouse clerk, Accountant, Administrator); voiding and migrating are Administrator-only | OpenAPI `security` |
| RNF-07 | Audit | Every status change of a document is logged with user, date and origin | Integration test |
| RNF-08 | Portability | Same domain on Windows (MSI) and Android (APK); identical calculation results on both | Domain module tests on both platforms |
| RNF-09 | Maintainability | `dominio` free of technical dependencies, checked by an architecture test (ADR-001) | ArchUnit/Konsist |
| RNF-10 | Accuracy | Amounts as exact decimals, never `float`; half-up rounding per line (R-28) | CA-20 |
| RNF-11 | Usability | Issue a 3-item receipt in < 60 s; errors with exact message and field | User testing |
| RNF-12 | Localization | Spanish (Peru) UI, America/Lima time zone, PEN as default currency | Review |
