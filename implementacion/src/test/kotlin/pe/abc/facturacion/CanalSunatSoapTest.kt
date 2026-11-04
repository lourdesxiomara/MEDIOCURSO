package pe.abc.facturacion

import com.sun.net.httpserver.HttpServer
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Test
import pe.abc.facturacion.adaptadores.envio.CanalSunatSoap
import pe.abc.facturacion.adaptadores.validacion.ValidadorFactura
import pe.abc.facturacion.puertos.DocumentoFirmado
import pe.abc.facturacion.puertos.ResultadoEnvio
import java.io.ByteArrayInputStream
import java.net.InetSocketAddress
import java.net.URI
import java.util.Base64
import java.util.zip.ZipInputStream
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue

/**
 * Envío con sendBill contra un servidor SOAP SIMULADO en localhost (no se llama a SUNAT en las pruebas unitarias).
 * El CDR que devuelve es el ejemplo de la spec (specs/02-dominio/ejemplos/cdr-R-20600123450-01-F001-1.xml).
 */
class CanalSunatSoapTest {
    private var servidor: HttpServer? = null
    private var ultimaSolicitud = ""
    private val documento = DocumentoFirmado("20600123450-01-F001-1", "<Invoice/>".toByteArray(), "digest")
    private val cdrEjemplo = Ejemplos.xml("cdr-R-20600123450-01-F001-1.xml").toString(Charsets.UTF_8)

    private fun servidorQueResponde(estado: Int, cuerpo: String): URI {
        val s = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        s.createContext("/billService") { ex ->
            ultimaSolicitud = ex.requestBody.readBytes().toString(Charsets.UTF_8)
            val b = cuerpo.toByteArray()
            ex.sendResponseHeaders(estado, b.size.toLong()); ex.responseBody.use { it.write(b) }
        }
        s.start(); servidor = s
        return URI("http://127.0.0.1:${s.address.port}/billService")
    }

    private fun respuestaConCdr(cdr: String) = """
        <soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><soap-env:Body>
          <br:sendBillResponse xmlns:br="http://service.sunat.gob.pe"><applicationResponse>${
            Base64.getEncoder().encodeToString(CanalSunatSoap.comprimir("R-20600123450-01-F001-1.xml", cdr.toByteArray()))
          }</applicationResponse></br:sendBillResponse></soap-env:Body></soap-env:Envelope>"""

    private fun fault(codigo: String, texto: String) = """
        <soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><soap-env:Body>
          <soap-env:Fault><faultcode>soap-env:Client.$codigo</faultcode><faultstring>$texto</faultstring></soap-env:Fault>
        </soap-env:Body></soap-env:Envelope>"""

    private fun canal(uri: URI) = CanalSunatSoap(uri, "20600123450MODDATOS", "moddatos")

    @AfterEach fun detener() { servidor?.stop(0) }

    @Test fun `CDR con codigo 0 - aceptado`() {
        val r = canal(servidorQueResponde(200, respuestaConCdr(cdrEjemplo))).enviar(documento)
        assertIs<ResultadoEnvio.Aceptado>(r)
        assertEquals("0", r.cdr.codigo)
        assertEquals("La Factura numero F001-1, ha sido aceptada", r.cdr.descripcion)
    }

    @Test fun `la solicitud lleva WS-Security y el ZIP con el nombre de R-52`() {
        canal(servidorQueResponde(200, respuestaConCdr(cdrEjemplo))).enviar(documento)
        val sobre = ValidadorFactura.parsear(ultimaSolicitud.toByteArray())
        assertEquals("20600123450MODDATOS", sobre.getElementsByTagNameNS("*", "Username").item(0).textContent)
        assertEquals("20600123450-01-F001-1.zip", sobre.getElementsByTagName("fileName").item(0).textContent)
        val zip = Base64.getDecoder().decode(sobre.getElementsByTagName("contentFile").item(0).textContent)
        ZipInputStream(ByteArrayInputStream(zip)).use { z ->
            assertEquals("20600123450-01-F001-1.xml", z.nextEntry!!.name)
            assertEquals("<Invoice/>", z.readBytes().toString(Charsets.UTF_8))
        }
    }

    @Test fun `CDR con codigo de rechazo 2000-3999 - rechazado, no se reutiliza el numero`() {
        val cdr = cdrEjemplo.replace("<cbc:ResponseCode>0<", "<cbc:ResponseCode>2800<")
            .replace("ha sido aceptada", "fue rechazada")
        val r = canal(servidorQueResponde(200, respuestaConCdr(cdr))).enviar(documento)
        assertIs<ResultadoEnvio.Rechazado>(r)
        assertEquals("2800", r.codigo)
    }

    @Test fun `CDR con observaciones 4000 o mas - aceptado con observaciones`() {
        val cdr = cdrEjemplo.replace("<cbc:ResponseCode>0<", "<cbc:ResponseCode>4287<")
            .replace("<cbc:ResponseDate>", "<cbc:Note>4287 - Observación de ejemplo</cbc:Note>\n  <cbc:ResponseDate>")
        val r = canal(servidorQueResponde(200, respuestaConCdr(cdr))).enviar(documento)
        assertIs<ResultadoEnvio.Aceptado>(r)
        assertEquals(listOf("4287 - Observación de ejemplo"), r.observaciones)
    }

    @Test fun `SOAP Fault de servicio 0100-0999 - excepcion reintentable con el mismo numero`() {
        val r = canal(servidorQueResponde(500, fault("0109", "El sistema no puede responder su solicitud"))).enviar(documento)
        assertIs<ResultadoEnvio.Excepcion>(r)
        assertEquals("0109", r.codigo)
        assertTrue(r.reintentable)
    }

    @Test fun `SOAP Fault de contenido 1000-1999 - excepcion que exige corregir`() {
        val r = canal(servidorQueResponde(500, fault("1033", "El comprobante fue registrado previamente"))).enviar(documento)
        assertIs<ResultadoEnvio.Excepcion>(r)
        assertEquals(false, r.reintentable)
    }

    @Test fun `sin conexion - no disponible, queda PENDIENTE_ENVIO`() {
        val uri = servidorQueResponde(200, "").also { servidor!!.stop(0) }
        assertIs<ResultadoEnvio.NoDisponible>(canal(uri).enviar(documento))
    }
}
