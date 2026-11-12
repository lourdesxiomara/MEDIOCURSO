package pe.abc.facturacion.adaptadores.envio

import pe.abc.facturacion.adaptadores.validacion.ValidadorFactura
import pe.abc.facturacion.puertos.CanalEnvioCpe
import pe.abc.facturacion.puertos.Cdr
import pe.abc.facturacion.puertos.DocumentoFirmado
import pe.abc.facturacion.puertos.Observacion
import pe.abc.facturacion.puertos.ResultadoEnvio
import org.w3c.dom.Element
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.net.http.HttpTimeoutException
import java.time.Duration
import java.util.Base64
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream

/**
 * Adaptador del puerto CanalEnvioCpe (ADR-004) para el servicio web del SEE de SUNAT, que también exponen los OSE:
 * SOAP 1.1 `sendBill` con WS-Security UsernameToken (specs/04-api/puertos-salida.md).
 *
 *  1. Comprime el XML firmado en RUC-TIPO-SERIE-NUMERO.zip (R-52) y lo envía en base64.
 *  2. Lee el CDR (ApplicationResponse) que llega en otro ZIP, o el SOAP Fault si no se pudo procesar.
 *  3. Clasifica el código por rango (R-54) en ResultadoEnvio.
 *
 * La URL y las credenciales son configuración (D-03): ambiente beta, producción o el endpoint del OSE elegido.
 */
class CanalSunatSoap(
    private val endpoint: URI,
    private val usuario: String,      // RUC + usuario SOL secundario (o credencial del OSE)
    private val clave: String,
    private val http: HttpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build(),
    private val espera: Duration = Duration.ofSeconds(30),
) : CanalEnvioCpe {

    override fun enviar(doc: DocumentoFirmado): ResultadoEnvio {
        val zip = comprimir("${doc.nombre}.xml", doc.contenido)
        val solicitud = HttpRequest.newBuilder(endpoint)
            .timeout(espera)
            .header("Content-Type", "text/xml; charset=UTF-8")
            .header("SOAPAction", "urn:sendBill")
            .POST(HttpRequest.BodyPublishers.ofString(sobre("${doc.nombre}.zip", Base64.getEncoder().encodeToString(zip))))
            .build()
        val respuesta = try {
            http.send(solicitud, HttpResponse.BodyHandlers.ofByteArray())
        } catch (e: HttpTimeoutException) {
            return ResultadoEnvio.NoDisponible("Tiempo de espera agotado: consultar estado antes de reintentar")
        } catch (e: IOException) {
            return ResultadoEnvio.NoDisponible("Sin conexión con $endpoint: ${e.message}")
        }
        val cuerpo = try { ValidadorFactura.parsear(respuesta.body()) } catch (e: Exception) {
            return ResultadoEnvio.NoDisponible("Respuesta HTTP ${respuesta.statusCode()} no es SOAP")
        }
        val fault = cuerpo.getElementsByTagNameNS(SOAP, "Fault").item(0) as Element?
        if (fault != null) {
            val codigo = hijo(fault, "faultcode").substringAfterLast('.').filter { it.isDigit() }.ifEmpty { "0" }
            return clasificarExcepcion(codigo, hijo(fault, "faultstring"))
        }
        val base64 = cuerpo.getElementsByTagName("applicationResponse").item(0)?.textContent?.trim()
            ?: return ResultadoEnvio.NoDisponible("Respuesta sin applicationResponse")
        return clasificar(leerCdr(Base64.getMimeDecoder().decode(base64)))
    }

    private fun sobre(archivo: String, contenido: String) = """
        <soapenv:Envelope xmlns:soapenv="$SOAP" xmlns:ser="http://service.sunat.gob.pe"
            xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
          <soapenv:Header>
            <wsse:Security>
              <wsse:UsernameToken>
                <wsse:Username>${escapar(usuario)}</wsse:Username>
                <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">${escapar(clave)}</wsse:Password>
              </wsse:UsernameToken>
            </wsse:Security>
          </soapenv:Header>
          <soapenv:Body>
            <ser:sendBill>
              <fileName>${escapar(archivo)}</fileName>
              <contentFile>$contenido</contentFile>
            </ser:sendBill>
          </soapenv:Body>
        </soapenv:Envelope>
    """.trimIndent()

    companion object {
        const val SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
        private const val CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

        fun comprimir(nombre: String, contenido: ByteArray): ByteArray {
            val salida = ByteArrayOutputStream()
            ZipOutputStream(salida).use { it.putNextEntry(ZipEntry(nombre)); it.write(contenido); it.closeEntry() }
            return salida.toByteArray()
        }

        /** El CDR llega comprimido: R-RUC-TIPO-SERIE-NUMERO.xml dentro del ZIP. */
        fun leerCdr(zip: ByteArray): Cdr {
            val xml = ZipInputStream(ByteArrayInputStream(zip)).use { z ->
                generateSequence { z.nextEntry }.first { it.name.endsWith(".xml") }
                z.readBytes()
            }
            val d = ValidadorFactura.parsear(xml)
            fun valor(nombre: String) = d.getElementsByTagNameNS(CBC, nombre).item(0)?.textContent?.trim().orEmpty()
            val notas = d.getElementsByTagNameNS(CBC, "Note").let { l -> (0 until l.length).map { l.item(it).textContent.trim() } }
            return Cdr(xml, valor("ResponseCode"), valor("Description"), notas)
        }

        /** R-54: 0 aceptado · 2000–3999 rechazo · ≥ 4000 aceptado con observaciones (0100–1999 llegan como SOAP Fault). */
        fun clasificar(cdr: Cdr): ResultadoEnvio {
            val n = cdr.codigo.toIntOrNull() ?: return ResultadoEnvio.NoDisponible("CDR sin ResponseCode numérico")
            return when {
                n == 0 || n >= 4000 -> ResultadoEnvio.Aceptado(cdr, cdr.notas.map(::observacion))
                n in 2000..3999 -> ResultadoEnvio.Rechazado(cdr, cdr.codigo, cdr.descripcion)
                else -> clasificarExcepcion(cdr.codigo, cdr.descripcion)
            }
        }

        /** "4287 - El precio unitario..." → Observacion("4287", "El precio unitario..."). */
        fun observacion(nota: String): Observacion =
            Regex("""^(\d{4})\s*-\s*(.*)$""").find(nota)?.let { Observacion(it.groupValues[1], it.groupValues[2]) } ?: Observacion("", nota)

        /** R-55: códigos de servicio (< 1000, p. ej. 0100, 0109) se reintentan con el mismo número; 1000–1999 exigen corregir. */
        fun clasificarExcepcion(codigo: String, descripcion: String): ResultadoEnvio.Excepcion {
            val n = codigo.toIntOrNull() ?: 0
            return ResultadoEnvio.Excepcion(codigo.padStart(4, '0'), descripcion, reintentable = n < 1000)
        }

        private fun hijo(e: Element, nombre: String) = e.getElementsByTagName(nombre).item(0)?.textContent?.trim().orEmpty()
        private fun escapar(s: String) = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    }
}
