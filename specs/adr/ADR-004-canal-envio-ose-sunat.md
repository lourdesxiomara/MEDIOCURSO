# ADR-004 · Canal de envío: OSE principal, SUNAT alternativo

- **Estado:** Propuesto (duda D-03)
- **Contexto:** El caso permite enviar a un OSE o directamente a SUNAT. Ambos reciben el XML firmado
  en ZIP y devuelven un CDR.
- **Decisión:** El núcleo solo conoce el puerto `CanalEnvioCpe` (`specs/04-api/puertos-salida.md`).
  Se implementan dos adaptadores intercambiables por configuración: `CanalOse` (principal) y
  `CanalSunatDirecto` (alternativo). Si el canal no responde, el comprobante queda `PENDIENTE_ENVIO`
  y la cola de reenvío (CU-11) lo reintenta dentro del plazo permitido.
- **Consecuencias:** (+) Cambiar de proveedor OSE no toca el dominio. (+) Emisión posible sin conexión
  con envío diferido. (−) Hay que vigilar el plazo máximo de envío (R-05).
