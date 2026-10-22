# ADR-001 · MVC monolith with ports and adapters

- **Status:** Accepted (Spec-First phase)
- **Context:** Management requires starting with a clean MVC monolith that can later move to
  Hexagonal/Clean and then to microservices without a rewrite.
- **Decision:**
  1. The MVC *Model* is split into three layers: pure domain, application services and adapters.
  2. Each application service implements an **input port interface** (`EmitirComprobante`, …).
  3. Every technical dependency (DB, XML, signature, OSE, mail, clock) is reached through an **output port**
     (`specs/04-api/puertos-salida.md`).
  4. Controllers only translate View events into DTOs (`specs/02-dominio/schemas`) and call ports.
  5. Dependency rule checked by an architecture test: `dominio` depends on nothing.
- **Consequences:**
  - (+) Moving to Hexagonal means renaming layers, not rewriting: see the table in `specs/03-arquitectura` §4.
  - (+) The domain (tax calculation, rules R-xx) is tested without DB or network.
  - (+) Changing OSE or DB = writing another adapter.
  - (−) Slightly more initial code (interfaces) than a "flat" MVC.
- **Rejected alternatives:** MVC with logic in Controllers (blocks the migration); full Hexagonal from day
  one (contradicts management's condition).
