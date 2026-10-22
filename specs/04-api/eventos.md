# 04 · Contratos de eventos (evolución a microservicios)

Contrato: `specs/02-dominio/schemas/evento.schema.json` · Ejemplo: `specs/02-dominio/ejemplos/evento.comprobante-aceptado.json`.
En el monolito los eventos viajan por un bus en memoria; al separar microservicios (ver `specs/03-arquitectura` §7) se publican en un broker con **el mismo contrato**.

| Evento | Publica | Consume | Efecto |
|---|---|---|---|
| `ComprobanteFirmado` | ms-emision | ms-envio-cpe | Envía el ZIP al OSE/SUNAT (R-52) |
| `ComprobanteAceptado` | ms-envio-cpe | ms-inventario, ms-emision | Registra salidas (CU-14) y estado `ACEPTADO` |
| `ComprobanteRechazado` | ms-envio-cpe | ms-emision | Estado `RECHAZADO` (R-53) |
| `ComprobanteAnulado` | ms-envio-cpe | ms-inventario | Revierte salidas (CU-07) |

Reglas: cada evento lleva `id` único (los consumidores son idempotentes), `version` del contrato (cambio incompatible = sube el mayor) y `fecha` en zona America/Lima.
