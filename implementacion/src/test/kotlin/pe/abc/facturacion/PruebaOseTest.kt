package pe.abc.facturacion

import org.junit.jupiter.api.Test
import pe.abc.facturacion.adaptadores.envio.CanalSunatSoap
import pe.abc.facturacion.adaptadores.firma.FirmadorXmlDsig
import pe.abc.facturacion.adaptadores.ubl.EsquemasUbl
import pe.abc.facturacion.adaptadores.ubl.GeneradorFacturaJaxb
import pe.abc.facturacion.adaptadores.validacion.ValidadorFactura
import pe.abc.facturacion.dominio.LectorComprobante
import pe.abc.facturacion.puertos.ResultadoEnvio
import java.nio.file.Paths
import java.time.LocalDate
import java.time.ZonedDateTime
import javax.xml.crypto.dsig.XMLSignature
import javax.xml.crypto.dsig.XMLSignatureFactory
import javax.xml.crypto.dsig.dom.DOMValidateContext
import javax.xml.transform.dom.DOMSource
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue

/**
 * Prueba con un OSE REAL de demostración (Nubefact, 12/11/2026). La factura generada por este programa fue ACEPTADA
 * (código 0). Se guardan el XML enviado y el CDR recibido en implementacion/evidencia/.
 */
class PruebaOseTest {
    private val raiz = EsquemasUbl.raizRepo.resolve("implementacion")
    private val evidencia = raiz.resolve("evidencia")
    private val cert = FirmadorXmlDsig.cargarPkcs12(Paths.get(javaClass.getResource("/cert-prueba.p12")!!.toURI()), "prueba".toCharArray())

    @Test fun `la factura para el OSE sale con la fecha de hoy, cliente con RUC existente y es valida`() {
        val c = PreparacionOse.preparar(LectorComprobante.leer(raiz.resolve("ejemplos-ose/factura-ose.json")))
        assertEquals(LocalDate.now(PreparacionOse.zona), c.fechaEmision)
        assertTrue(Regex("^F001-[1-9][0-9]{0,7}$").matches(c.numero), c.numero)
        assertEquals("20131312955", c.cliente.documento.numero)
        val firmado = FirmadorXmlDsig().firmar(GeneradorFacturaJaxb().generar(c), cert)
        assertEquals(emptyList(), ValidadorFactura().validar(firmado.contenido))
        assertTrue("<ds:X509Certificate>" in firmado.contenido.toString(Charsets.UTF_8), "el OSE exige X509Certificate (error 2101)")
    }

    @Test fun `fecha de hoy, correlativo nuevo y cuotas desplazadas los mismos dias`() {
        val c = Ejemplos.comprobante("comprobante.factura-isc.json")          // emitida 2026-10-22, cuotas 2026-11-21 y 2026-12-21
        val movida = PreparacionOse.preparar(c, ZonedDateTime.parse("2026-11-01T09:05:00-05:00[America/Lima]"))
        assertEquals(LocalDate.parse("2026-11-01"), movida.fechaEmision)
        assertEquals("F001-11010905", movida.numero)
        assertEquals(listOf("2026-12-01", "2026-12-31"), movida.formaPago!!.cuotas.map { it.fechaVencimiento.toString() })
        assertEquals(emptyList(), ValidadorFactura().validar(GeneradorFacturaJaxb().generar(movida).contenido))
    }

    @Test fun `el XML que se envio a Nubefact es valido y su firma de prueba verifica`() {
        val xml = evidencia.resolve("20600123450-01-F001-1-enviado.xml").toFile().readBytes()
        assertEquals(emptyList(), ValidadorFactura().validar(xml))
        val doc = ValidadorFactura.parsear(xml)
        val ctx = DOMValidateContext(cert.certificado.publicKey, doc.getElementsByTagNameNS(XMLSignature.XMLNS, "Signature").item(0))
        assertTrue(XMLSignatureFactory.getInstance("DOM").unmarshalXMLSignature(ctx).validate(ctx))
    }

    @Test fun `el CDR real de Nubefact cumple el XSD y el programa lo clasifica como ACEPTADO`() {
        val cdrXml = evidencia.resolve("R-20600123450-01-F001-1-nubefact-demo.xml").toFile().readBytes()
        EsquemasUbl.schema("ApplicationResponse").newValidator().validate(DOMSource(ValidadorFactura.parsear(cdrXml)))
        val r = CanalSunatSoap.clasificar(CanalSunatSoap.leerCdr(CanalSunatSoap.comprimir("R-20600123450-01-F001-1.xml", cdrXml)))
        assertIs<ResultadoEnvio.Aceptado>(r)
        assertEquals("0", r.cdr.codigo)
        assertEquals("La Factura Electrónica F001-1 ha sido ACEPTADA", r.cdr.descripcion)
    }
}
