# 04 · Event contracts (evolution to microservices)

Contract: `specs/02-dominio/schemas/evento.schema.json` · Example: `specs/02-dominio/ejemplos/evento.comprobante-aceptado.json`.
In the monolith, events travel through an in-memory bus; when the microservices are split out (see `specs/03-arquitectura` §7) they are published to a broker with **the same contract**.

| Event | Published by | Consumed by | Effect |
|---|---|---|---|
| `ComprobanteFirmado` (document signed) | ms-emision | ms-envio-cpe | Sends the ZIP to the OSE/SUNAT (R-52) |
| `ComprobanteAceptado` (document accepted) | ms-envio-cpe | ms-inventario, ms-emision | Records stock outputs (CU-14) and status `ACEPTADO` |
| `ComprobanteRechazado` (document rejected) | ms-envio-cpe | ms-emision | Status `RECHAZADO` (R-53) |
| `ComprobanteAnulado` (document voided) | ms-envio-cpe | ms-inventario | Reverts stock outputs (CU-07) |

Rules: each event carries a unique `id` (consumers are idempotent), a contract `version` (breaking change = major bump) and a `fecha` in the America/Lima time zone.
