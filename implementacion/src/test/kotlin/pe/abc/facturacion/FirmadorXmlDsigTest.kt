package pe.abc.facturacion

import org.junit.jupiter.api.Test
import org.w3c.dom.Element
import org.xmlunit.builder.DiffBuilder
import pe.abc.facturacion.adaptadores.firma.FirmadorXmlDsig
import pe.abc.facturacion.adaptadores.ubl.GeneradorFacturaJaxb
import pe.abc.facturacion.adaptadores.validacion.ValidadorFactura
import java.nio.file.Paths
import javax.xml.crypto.dsig.XMLSignature
import javax.xml.crypto.dsig.XMLSignatureFactory
import javax.xml.crypto.dsig.dom.DOMValidateContext
import javax.xml.transform.TransformerFactory
import javax.xml.transform.dom.DOMSource
import javax.xml.transform.stream.StreamResult
import java.io.StringWriter
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Firma XMLDSig enveloped (R-51) con un certificado de PRUEBA (src/test/resources/cert-prueba.p12, no válido para SUNAT). */
class FirmadorXmlDsigTest {
    private val cert = FirmadorXmlDsig.cargarPkcs12(Paths.get(javaClass.getResource("/cert-prueba.p12")!!.toURI()), "prueba".toCharArray())
    private val sinFirma = GeneradorFacturaJaxb().generar(Ejemplos.comprobante("comprobante.factura.json"))
    private val firmado = FirmadorXmlDsig().firmar(sinFirma, cert)

    private fun firmaValida(xml: ByteArray): Boolean {
        val doc = ValidadorFactura.parsear(xml)
        val nodo = doc.getElementsByTagNameNS(XMLSignature.XMLNS, "Signature").item(0)
        val ctx = DOMValidateContext(cert.certificado.publicKey, nodo)
        return XMLSignatureFactory.getInstance("DOM").unmarshalXMLSignature(ctx).validate(ctx)
    }

    @Test fun `la firma es valida con la clave publica del certificado`() = assertTrue(firmaValida(firmado.contenido))

    @Test fun `la firma va en ext UBLExtensions como primer hijo y con el Id referenciado`() {
        val raiz = ValidadorFactura.parsear(firmado.contenido).documentElement
        val primero = generateSequence(raiz.firstChild) { it.nextSibling }.first { it is Element } as Element
        assertEquals("UBLExtensions", primero.localName)
        val firma = primero.getElementsByTagNameNS(XMLSignature.XMLNS, "Signature").item(0) as Element
        assertEquals("SignatureABC", firma.getAttribute("Id"))
        assertTrue(firmado.digestValue.isNotBlank())
    }

    @Test fun `SignatureValue y X509Certificate van en una sola linea, sin saltos ni retornos de carro`() {
        val doc = ValidadorFactura.parsear(firmado.contenido)
        for (nombre in listOf("SignatureValue", "X509Certificate")) {
            val valor = doc.getElementsByTagNameNS(XMLSignature.XMLNS, nombre).item(0).textContent
            assertFalse(valor.any { it == '\n' || it == '\r' }, "$nombre con saltos de línea")
        }
        assertFalse("&#13;" in firmado.contenido.toString(Charsets.UTF_8))
    }

    @Test fun `el XML firmado sigue siendo valido (XSD y reglas)`() =
        assertEquals(emptyList(), ValidadorFactura().validar(firmado.contenido))

    @Test fun `alterar un importe despues de firmar invalida la firma`() {
        val alterado = firmado.contenido.toString(Charsets.UTF_8).replace(">345.80<", ">999.80<").toByteArray()
        assertFalse(firmaValida(alterado))
    }

    @Test fun `firmar no cambia el documento - sin UBLExtensions es igual al original`() {
        val doc = ValidadorFactura.parsear(firmado.contenido)
        val ext = doc.documentElement.getElementsByTagNameNS(FirmadorXmlDsig.EXT, "UBLExtensions").item(0)
        doc.documentElement.removeChild(ext)
        val texto = StringWriter().also { TransformerFactory.newInstance().newTransformer().transform(DOMSource(doc), StreamResult(it)) }.toString()
        val diff = DiffBuilder.compare(sinFirma.contenido).withTest(texto).ignoreWhitespace().checkForSimilar().build()
        assertFalse(diff.hasDifferences(), diff.toString())
    }
}
