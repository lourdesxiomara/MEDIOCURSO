# 04 · Output port contracts

Interfaces defined by the core and implemented by adapters (`specs/03-arquitectura`, §4).
Written as Kotlin pseudocode: they are **contracts, not implementation**.

```kotlin
interface RepositorioComprobantes {            // document repository
    fun guardar(c: Comprobante)
    fun buscarPorId(id: UUID): Comprobante?
    fun buscarPorNumero(tipo: TipoComprobante, serie: Serie, correlativo: Int): Comprobante?
    fun siguienteCorrelativo(serie: Serie): Int          // atomic; R-03
    fun pendientesDeEnvio(limite: Int): List<Comprobante> // CU-11
}

interface GeneradorDocumentoUbl {
    /** Returns unsigned UBL 2.1 XML already validated against the XSD (R-50). Throws ErrorEstructuraUbl. */
    fun generar(c: Comprobante): DocumentoXml
}

interface FirmadorDigital {
    /** Enveloped XMLDSig signature inside ext:UBLExtensions (R-51). Returns signed XML and DigestValue. */
    fun firmar(xml: DocumentoXml, certificado: CertificadoDigital): DocumentoFirmado
}

interface CanalEnvioCpe {                 // ADR-004
    fun enviar(doc: DocumentoFirmado): ResultadoEnvio          // sendBill
    fun consultarEstado(ticketOClave: String): ResultadoEnvio  // getStatus / getStatusCdr
    fun enviarBaja(baja: ComunicacionBaja): Ticket             // sendSummary
}

sealed interface ResultadoEnvio {
    data class Aceptado(val cdr: Cdr, val observaciones: List<String>) : ResultadoEnvio
    data class Rechazado(val cdr: Cdr, val codigo: String, val descripcion: String) : ResultadoEnvio
    data class NoDisponible(val causa: String) : ResultadoEnvio   // → PENDIENTE_ENVIO
}

interface ValidadorRuc { fun consultar(ruc: Ruc): EstadoContribuyente? }  // R-13, optional
interface Notificador  { fun enviarComprobante(c: Comprobante, correo: String) }
interface Reloj        { fun ahora(): ZonedDateTime }  // America/Lima; enables deterministic tests
```

## External contract: OSE / SUNAT (`envio-ose` adapter)
| Operation | Input | Output | Use |
|---|---|---|---|
| `sendBill` | `fileName` = `RUC-TYPE-SERIES-NUMBER.zip`, `contentFile` = base64 ZIP with the signed XML | `applicationResponse` = base64 ZIP with the CDR | Invoice, credit note, debit note (synchronous) |
| `sendSummary` | Daily summary / voiding communication ZIP | `ticket` | Receipts and voids (asynchronous) |
| `getStatus` | `ticket` | Status + CDR | Summary status query |

Protocol: SOAP 1.1 with WS-Security UsernameToken (secondary SOL user or OSE credential).
The exact endpoint and credentials depend on the chosen OSE (open question D-03); that is why the core
only knows `CanalEnvioCpe`.

## Response → document status mapping
| Response | Status |
|---|---|
| CDR with `ResponseCode` = 0 and no notes | `ACEPTADO` |
| CDR with `ResponseCode` = 0 and observation notes | `ACEPTADO_CON_OBSERVACIONES` |
| CDR with a rejection code | `RECHAZADO` (`respuestaSunat.codigoRespuesta`) |
| SOAP fault from pre-validation | `RECHAZADO` with the fault's `codigoSunat` (D-07) |
| Timeout / no connection | `PENDIENTE_ENVIO` |
