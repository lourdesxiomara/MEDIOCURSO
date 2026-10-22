# 03 · Architecture: monolithic MVC with a Hexagonal vision

## 1. Guiding principle
The system is built as **an MVC monolith**, but from day one the code is split into the
**core (domain + use cases)** and **technical details (UI, DB, XML, signature, OSE)**, connected through
**interfaces (ports)**. Therefore:

- Today: the MVC *Controller* calls an *Application Service*; the *View* is Compose (Windows/Android).
- Tomorrow: that same service is a hexagonal **input port** and every technical dependency is an **adapter**.
- Later: each group of ports can be split into a **microservice** without rewriting the domain.

The rule that makes this possible (enforced in code review and by an architecture test): **dependencies
point towards the domain**. The domain imports nothing from UI, DB, HTTP, XML or signature libraries.

## 2. Context (C4 level 1)
```mermaid
flowchart TB
  vend([Seller / Warehouse clerk / Admin / Accountant])
  subgraph ABC[ABC invoicing system · monolith]
    app[Windows MSI / Android APK app]
  end
  ose[[OSE · Electronic Services Operator]]
  sunat[[SUNAT · SEE / document query]]
  padron[[RUC registry]]
  correo[[Mail server]]
  legado[(Legacy warehouse system)]
  vend --> app
  app -- signed UBL 2.1 XML / CDR --> ose
  app -. alternative channel .-> sunat
  app -. RUC lookup .-> padron
  app -- PDF + XML --> correo
  legado -- CSV export --> app
```

## 3. Current MVC view (monolith)
```mermaid
flowchart LR
  subgraph V[View · Compose Multiplatform]
    VF[InvoiceScreen]
    VN[NoteScreen]
    VC[QueryScreen]
    VI[InventoryScreen]
    VM[MigrationScreen]
  end
  subgraph C[Controller]
    CC[ComprobanteController]
    IC[InventarioController]
    MC[MigracionController]
    CFG[ConfiguracionController]
  end
  subgraph M[Model]
    direction TB
    subgraph APP[Application services = future input ports]
      S1[EmitirComprobanteService]
      S2[EmitirNotaService]
      S3[ConsultarComprobanteService]
      S4[RegistrarMovimientoService]
      S5[MigrarLegadoService]
    end
    subgraph DOM[Pure domain]
      D1[Comprobante · Line · Tax]
      D2[TaxCalculator]
      D3[Rule validator R-xx]
      D4[Product · Customer · Series]
    end
    subgraph INF[Infrastructure = future adapters]
      R1[(SQLite repository)]
      X1[UBL XML generator]
      F1[XMLDSig signer]
      O1[OSE SOAP client]
      P1[PDF generator]
    end
  end
  VF & VN & VC --> CC
  VI --> IC
  VM --> MC
  CC --> S1 & S2 & S3
  IC --> S4
  MC --> S5
  S1 & S2 & S3 & S4 & S5 --> DOM
  S1 --> R1 & X1 & F1 & O1 & P1
```

## 4. The same application seen as Hexagonal
```mermaid
flowchart LR
  subgraph AE[Input adapters]
    UI[Compose UI · MVC Controllers]
    REST[Local REST API · openapi.yaml]
    CLI[Legacy CSV importer]
  end
  subgraph NUCLEO[Core]
    subgraph PE[Input ports]
      P1[EmitirComprobante]
      P2[EmitirNota]
      P3[ConsultarComprobante]
      P4[AnularComprobante]
      P5[RegistrarMovimiento]
      P6[MigrarLegado]
    end
    DOM[Domain: Comprobante, Taxes, Rules R-xx]
    subgraph PS[Output ports]
      Q1[RepositorioComprobantes]
      Q2[RepositorioProductos]
      Q3[GeneradorDocumentoUbl]
      Q4[FirmadorDigital]
      Q5[CanalEnvioCpe]
      Q6[ValidadorRuc]
      Q7[Notificador]
      Q8[ClockAndNumbering]
    end
  end
  subgraph AS[Output adapters]
    A1[(SQLite / PostgreSQL)]
    A2[UBL 2.1 + XSD validation]
    A3[XMLDSig with .pfx certificate]
    A4[OSE SOAP billService]
    A5[SUNAT SEE direct]
    A6[RUC registry]
    A7[SMTP]
  end
  UI & REST & CLI --> PE
  PE --> DOM
  PE --> PS
  Q1 & Q2 --> A1
  Q3 --> A2
  Q4 --> A3
  Q5 --> A4
  Q5 -.alternative.-> A5
  Q6 --> A6
  Q7 --> A7
```

### MVC → Hexagonal mapping (what stays and what changes)
| Piece in today's MVC | Role in Hexagonal | Changes when migrating? |
|---|---|---|
| Compose View | Input adapter (UI) | No |
| Controller | Input adapter (translates UI events → DTO) | No |
| Application service (`EmitirComprobanteService`) | Input port implementation | No; its interface is extracted |
| Domain (`Comprobante`, tax calculator) | Core | **Never** |
| Repository, XML, signature, OSE client | Output adapters behind interfaces | Only implementations change |
| DTOs (`specs/02-dominio/schemas`) | Port contracts | No |

## 5. Module structure (applies from the first code commit)
```
abc-facturacion/
├── dominio/            # Pure Kotlin. No external deps. Entities, VOs, rules R-xx, calculation.
├── aplicacion/         # Use cases + port interfaces (input and output). Depends only on dominio.
├── adaptadores/
│   ├── persistencia/   # SQLite (SQLDelight) → implements RepositorioComprobantes…
│   ├── ubl/            # UBL 2.1 XML generation + XSD validation (R-50)
│   ├── firma/          # XMLDSig (R-51)
│   ├── envio-ose/      # SOAP sendBill / getStatus → CanalEnvioCpe
│   ├── pdf/            # Printed representation
│   └── migracion/      # Legacy CSV reader + rules M-xx
├── ui/                 # Compose Multiplatform: Views + Controllers (MVC)
├── app-desktop/        # Windows entry point → MSI installer
└── app-android/        # Android entry point → APK
```
Dependency rule, checked by an architecture test (ArchUnit/Konsist):
`ui → aplicacion → dominio` and `adaptadores → aplicacion → dominio`. `dominio` depends on nothing.

## 6. Sequence: issue an invoice (CU-03)
```mermaid
sequenceDiagram
  actor V as Seller
  participant UI as View + Controller
  participant S as EmitirComprobante (port)
  participant D as Domain
  participant R as RepositorioComprobantes
  participant X as GeneradorDocumentoUbl
  participant F as FirmadorDigital
  participant O as CanalEnvioCpe (OSE)
  V->>UI: Fills in the invoice and confirms
  UI->>S: CrearComprobanteRequest
  S->>D: validate(R-01..R-34) and calculateTaxes()
  D-->>S: Comprobante VALIDADO + totals
  S->>R: nextNumber(series)
  S->>X: generate(document)
  X-->>S: UBL 2.1 XML (validated against XSD, R-50)
  S->>F: sign(xml)
  F-->>S: Signed XML + hash
  S->>R: save(FIRMADO)
  S->>O: send(zip)
  alt CDR accepted
    O-->>S: CDR code 0
    S->>R: save(ACEPTADO, cdr)
  else OSE unavailable
    O--xS: timeout
    S->>R: save(PENDIENTE_ENVIO)
  else CDR rejected
    O-->>S: CDR with error code
    S->>R: save(RECHAZADO, cdr)
  end
  S-->>UI: Comprobante (comprobante.schema.json)
  UI-->>V: Status + PDF
```

## 7. Evolution to microservices (when the company grows)
```mermaid
flowchart LR
  GW[API Gateway] --> MS1 & MS2 & MS3 & MS4
  MS1[ms-emision<br/>Issue document · Issue note · Void]
  MS2[ms-catalogos<br/>Products · Customers · SUNAT catalogs]
  MS3[ms-envio-cpe<br/>Signature · OSE submission · CDR · Retries]
  MS4[ms-inventario<br/>Movements · Format 12.1 · Migration]
  MS1 -- event ComprobanteFirmado --> BUS{{Event bus}}
  BUS --> MS3
  MS3 -- event ComprobanteAceptado --> BUS
  BUS --> MS4
```
Each microservice is **a group of input ports that already exists in the monolith**. In-process calls
between services are replaced by the contracts in `specs/04-api/openapi.yaml` and by the events in
`specs/04-api/eventos.md`. The domain and the DTOs do not change.

## 8. Related decisions
ADR-001 (MVC with ports), ADR-002 (cross-platform stack), ADR-003 (persistence),
ADR-004 (OSE/SUNAT channel), ADR-005 (Amazon region) in `specs/adr/`.
