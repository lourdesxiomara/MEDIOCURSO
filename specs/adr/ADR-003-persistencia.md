# ADR-003 · Persistence

- **Status:** Proposed (question D-08)
- **Context:** The monolith runs on Windows and Android. Numbers must be unique per series (R-03)
  even with several devices issuing.
- **Proposed decision:**
  1. Local **SQLite** database on each device, accessed only through the `RepositorioComprobantes` port.
  2. **Each device has its own series** (e.g. Windows counter `F001`/`B001`, Android route `F002`/`B002`),
     so numbers never collide without a central server.
  3. The signed XML and the CDR are stored intact (they are legal documents) together with their hash.
  4. When a central server exists (microservices phase), a PostgreSQL adapter and synchronization are
     added; the domain does not change.
- **Consequences:** (+) Works without a permanent connection and without new infrastructure.
  (−) Consolidated reports require export/sync until the central server exists.
