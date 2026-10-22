# ADR-004 · Submission channel: OSE as primary, SUNAT as fallback

- **Status:** Proposed (question D-03)
- **Context:** The case allows sending to an OSE or directly to SUNAT. Both receive the signed XML in a ZIP
  and return a CDR.
- **Decision:** The core only knows the `CanalEnvioCpe` port (`specs/04-api/puertos-salida.md`).
  Two interchangeable adapters are implemented and chosen by configuration: `CanalOse` (primary) and
  `CanalSunatDirecto` (fallback). If the channel does not respond, the document stays `PENDIENTE_ENVIO`
  and the resend queue (CU-11) retries it within the allowed deadline.
- **Consequences:** (+) Changing OSE provider does not touch the domain. (+) Issuing is possible offline
  with deferred submission. (−) The maximum submission deadline must be monitored (R-05).
