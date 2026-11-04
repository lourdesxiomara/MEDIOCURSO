package pe.abc.facturacion

import pe.abc.facturacion.adaptadores.firma.FirmadorXmlDsig
import pe.abc.facturacion.adaptadores.ubl.GeneradorFacturaJaxb
import pe.abc.facturacion.adaptadores.validacion.ValidadorFactura
import pe.abc.facturacion.dominio.LectorComprobante
import pe.abc.facturacion.puertos.ErrorEstructuraUbl
import java.nio.file.Files
import java.nio.file.Paths
import kotlin.system.exitProcess

/**
 * Demostración por consola:  ./gradlew generar --args="<comprobante.json> [salida.xml] [certificado.p12 clave]"
 * Genera el XML UBL 2.1, lo valida (XSD + reglas) y, si se da un certificado, lo firma.
 */
fun main(args: Array<String>) {
    if (args.isEmpty()) {
        System.err.println("Uso: generar <comprobante.json> [salida.xml] [certificado.p12 clave]"); exitProcess(2)
    }
    val comprobante = LectorComprobante.leer(Paths.get(args[0]))
    val xml = try { GeneradorFacturaJaxb().generar(comprobante) } catch (e: ErrorEstructuraUbl) {
        System.err.println("R-50: ${e.message}"); exitProcess(1)
    }
    val hallazgos = ValidadorFactura().validar(xml.contenido)
    hallazgos.forEach { println("${it.regla}: ${it.mensaje}") }
    var contenido = xml.contenido
    if (args.size >= 4) {
        val firmado = FirmadorXmlDsig().firmar(xml, FirmadorXmlDsig.cargarPkcs12(Paths.get(args[2]), args[3].toCharArray()))
        contenido = firmado.contenido
        println("Firmado (R-51). DigestValue: ${firmado.digestValue}")
    }
    val salida = Paths.get(args.getOrElse(1) { "${xml.nombre}.xml" })
    Files.write(salida, contenido)
    println(if (hallazgos.isEmpty()) "OK: ${xml.nombre} valido -> $salida" else "${hallazgos.size} hallazgo(s) -> $salida")
    exitProcess(if (hallazgos.isEmpty()) 0 else 1)
}
