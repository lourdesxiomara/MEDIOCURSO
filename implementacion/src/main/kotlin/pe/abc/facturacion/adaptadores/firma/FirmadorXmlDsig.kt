package pe.abc.facturacion.adaptadores.firma

import pe.abc.facturacion.adaptadores.validacion.ValidadorFactura
import pe.abc.facturacion.puertos.CertificadoDigital
import pe.abc.facturacion.puertos.DocumentoFirmado
import pe.abc.facturacion.puertos.DocumentoXml
import pe.abc.facturacion.puertos.FirmadorDigital
import java.io.ByteArrayOutputStream
import java.io.FileInputStream
import java.nio.file.Path
import java.security.KeyStore
import java.security.PrivateKey
import java.security.cert.X509Certificate
import javax.xml.crypto.dsig.CanonicalizationMethod
import javax.xml.crypto.dsig.DigestMethod
import javax.xml.crypto.dsig.Reference
import javax.xml.crypto.dsig.SignatureMethod
import javax.xml.crypto.dsig.Transform
import javax.xml.crypto.dsig.XMLSignatureFactory
import javax.xml.crypto.dsig.dom.DOMSignContext
import javax.xml.crypto.dsig.spec.C14NMethodParameterSpec
import javax.xml.crypto.dsig.spec.TransformParameterSpec
import javax.xml.transform.OutputKeys
import javax.xml.transform.TransformerFactory
import javax.xml.transform.dom.DOMSource
import javax.xml.transform.stream.StreamResult

/**
 * Firma XMLDSig enveloped (R-51) con la API estándar de Java (javax.xml.crypto, basada en Apache Santuario):
 * RSA-SHA256, digest SHA-256, C14N inclusiva, X509Data con el certificado; la firma va dentro de
 * ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent, primer hijo del documento. Su Id coincide con
 * cac:Signature/cac:DigitalSignatureAttachment/cac:ExternalReference/cbc:URI (sin '#').
 */
class FirmadorXmlDsig(private val idFirma: String = "SignatureABC") : FirmadorDigital {

    override fun firmar(xml: DocumentoXml, certificado: CertificadoDigital): DocumentoFirmado {
        val doc = ValidadorFactura.parsear(xml.contenido)
        val raiz = doc.documentElement
        val extensiones = doc.createElementNS(EXT, "ext:UBLExtensions")
        val contenido = doc.createElementNS(EXT, "ext:ExtensionContent")
        extensiones.appendChild(doc.createElementNS(EXT, "ext:UBLExtension")).appendChild(contenido)
        raiz.insertBefore(extensiones, raiz.firstChild)     // UBLExtensions es el primer elemento de Invoice (XSD)

        val f = XMLSignatureFactory.getInstance("DOM")
        val referencia = f.newReference(
            "", f.newDigestMethod(DigestMethod.SHA256, null),
            listOf(f.newTransform(Transform.ENVELOPED, null as TransformParameterSpec?)), null, null,
        )
        val info = f.newSignedInfo(
            f.newCanonicalizationMethod(CanonicalizationMethod.INCLUSIVE, null as C14NMethodParameterSpec?),
            f.newSignatureMethod(SignatureMethod.RSA_SHA256, null),
            listOf(referencia),
        )
        val kif = f.keyInfoFactory
        val keyInfo = kif.newKeyInfo(listOf(kif.newX509Data(listOf(certificado.certificado))))
        f.newXMLSignature(info, keyInfo, null, idFirma, null)
            .sign(DOMSignContext(certificado.clavePrivada, contenido).apply { defaultNamespacePrefix = "ds" })

        val salida = ByteArrayOutputStream()
        TransformerFactory.newInstance().newTransformer().apply {
            setOutputProperty(OutputKeys.ENCODING, "UTF-8")
        }.transform(DOMSource(doc), StreamResult(salida))
        val digest = (referencia as Reference).digestValue.let { java.util.Base64.getEncoder().encodeToString(it) }
        return DocumentoFirmado(xml.nombre, salida.toByteArray(), digest)
    }

    companion object {
        init {
            // Base64 de SignatureValue y X509Certificate en una sola línea: sin saltos ni "&#13;" (en Windows) dentro de la firma.
            System.setProperty("com.sun.org.apache.xml.internal.security.ignoreLineBreaks", "true")
        }

        const val EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"

        /** Carga el certificado digital de la empresa desde un .pfx / .p12 (PKCS#12). */
        fun cargarPkcs12(archivo: Path, clave: CharArray): CertificadoDigital {
            val ks = KeyStore.getInstance("PKCS12").apply { FileInputStream(archivo.toFile()).use { load(it, clave) } }
            val alias = ks.aliases().toList().first { ks.isKeyEntry(it) }
            return CertificadoDigital(ks.getKey(alias, clave) as PrivateKey, ks.getCertificate(alias) as X509Certificate)
        }
    }
}
