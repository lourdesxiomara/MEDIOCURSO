# 04 · Contratos de los puertos de salida

Interfaces que define el núcleo y que implementan los adaptadores (`specs/03-arquitectura`, §4).
Se expresan en pseudocódigo Kotlin: son **contratos, no implementación**.

```kotlin
interface RepositorioComprobantes {
    fun guardar(c: Comprobante)
    fun buscarPorId(id: UUID): Comprobante?
    fun buscarPorNumero(tipo: TipoComprobante, serie: Serie, correlativo: Int): Comprobante?
    fun siguienteCorrelativo(serie: Serie): Int          // atómico; R-03
    fun pendientesDeEnvio(limite: Int): List<Comprobante> // CU-11
}

interface GeneradorDocumentoUbl {
    /** Devuelve XML UBL 2.1 sin firmar, ya validado contra el XSD (R-50). Lanza ErrorEstructuraUbl. */
    fun generar(c: Comprobante): DocumentoXml
}

interface FirmadorDigital {
    /** Firma XMLDSig enveloped en ext:UBLExtensions (R-51). Devuelve XML firmado y DigestValue. */
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

interface ValidadorRuc { fun consultar(ruc: Ruc): EstadoContribuyente? }  // R-13, opcional
interface Notificador  { fun enviarComprobante(c: Comprobante, correo: String) }
interface Reloj        { fun ahora(): ZonedDateTime }  // America/Lima; permite pruebas deterministas
```

## Contrato externo: OSE / SUNAT (adaptador `envio-ose`)
| Operación | Entrada | Salida | Uso |
|---|---|---|---|
| `sendBill` | `fileName` = `RUC-TIPO-SERIE-CORRELATIVO.zip`, `contentFile` = ZIP base64 con el XML firmado | `applicationResponse` = ZIP base64 con el CDR | Factura, NC, ND (síncrono) |
| `sendSummary` | ZIP de resumen diario / comunicación de baja | `ticket` | Boletas y bajas (asíncrono) |
| `getStatus` | `ticket` | Estado + CDR | Consulta de resúmenes |

Protocolo: SOAP 1.1 con WS-Security UsernameToken (usuario SOL secundario o credencial del OSE).
Detalle exacto del endpoint y credenciales depende del OSE elegido (duda D-03); por eso el núcleo
solo conoce `CanalEnvioCpe`.

## Mapeo de respuesta → estado del comprobante
| Respuesta | Estado |
|---|---|
| CDR con `ResponseCode` = 0 y sin notas | `ACEPTADO` |
| CDR con `ResponseCode` = 0 y con notas de observación | `ACEPTADO_CON_OBSERVACIONES` |
| CDR con código de rechazo | `RECHAZADO` (`respuestaSunat.codigoRespuesta`) |
| Excepción SOAP de validación previa | `RECHAZADO` con `codigoSunat` del fault (D-07) |
| Timeout / sin conexión | `PENDIENTE_ENVIO` |
