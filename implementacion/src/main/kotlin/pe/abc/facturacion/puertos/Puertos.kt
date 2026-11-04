package pe.abc.facturacion.puertos

import pe.abc.facturacion.dominio.Comprobante
import java.security.PrivateKey
import java.security.cert.X509Certificate

/** XML UBL sin firma, ya validado contra el XSD (R-50). */
class DocumentoXml(val nombre: String, val contenido: ByteArray) {
    val texto: String get() = String(contenido, Charsets.UTF_8)
}

/** XML firmado (R-51) y el DigestValue que va en la representación impresa. */
class DocumentoFirmado(val nombre: String, val contenido: ByteArray, val digestValue: String)

class CertificadoDigital(val clavePrivada: PrivateKey, val certificado: X509Certificate)

/** Un hallazgo de validación, con la regla de docs/sunat/reglas-validacion.md que lo origina. */
data class Hallazgo(val regla: String, val mensaje: String)

class ErrorEstructuraUbl(mensaje: String, causa: Throwable? = null) : RuntimeException(mensaje, causa)

// ---- Puertos de salida (specs/04-api/puertos-salida.md) ----

interface GeneradorDocumentoUbl {
    /** Devuelve el XML UBL 2.1 sin firmar, validado contra el XSD. Lanza ErrorEstructuraUbl si no cumple (R-50). */
    fun generar(c: Comprobante): DocumentoXml
}

interface ValidadorDocumento {
    /** XSD oficial + reglas SUNAT sobre el XML. Lista vacía = válido. */
    fun validar(xml: ByteArray): List<Hallazgo>
}

interface FirmadorDigital {
    /** Firma XMLDSig enveloped dentro de ext:UBLExtensions (R-51). */
    fun firmar(xml: DocumentoXml, certificado: CertificadoDigital): DocumentoFirmado
}

interface CanalEnvioCpe {
    /** sendBill: envía el ZIP con el XML firmado y devuelve el resultado clasificado por R-54. */
    fun enviar(doc: DocumentoFirmado): ResultadoEnvio
}

/** CDR recibido: el XML íntegro (documento legal) y sus datos principales. */
class Cdr(val xml: ByteArray, val codigo: String, val descripcion: String, val notas: List<String>)

sealed interface ResultadoEnvio {
    data class Aceptado(val cdr: Cdr, val observaciones: List<String>) : ResultadoEnvio           // 0 o ≥ 4000
    data class Rechazado(val cdr: Cdr, val codigo: String, val descripcion: String) : ResultadoEnvio  // 2000–3999
    data class Excepcion(val codigo: String, val descripcion: String, val reintentable: Boolean) : ResultadoEnvio  // 0100–1999
    data class NoDisponible(val causa: String) : ResultadoEnvio                                     // timeout / sin conexión
}
