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
 * Demostración por consola:  ./gradlew generar --args="<comprobante.json> [salida.xml | carpeta/] [certificado.p12 clave] [--para-ose]"
 * Genera el XML UBL 2.1, lo valida (XSD + reglas) y, si se da un certificado, lo firma.
 * --para-ose emite el comprobante con la fecha de hoy y un correlativo nuevo (para enviarlo a un OSE de prueba).
 */
fun main(argumentos: Array<String>) {
    val paraOse = "--para-ose" in argumentos
    val args = argumentos.filter { it != "--para-ose" }
    if (args.isEmpty()) {
        System.err.println("Uso: generar <comprobante.json> [salida.xml | carpeta/] [certificado.p12 clave] [--para-ose]"); exitProcess(2)
    }
    val leido = LectorComprobante.leer(Paths.get(args[0]))
    val comprobante = if (paraOse) PreparacionOse.preparar(leido) else leido
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
    // Nombre SUNAT: RUC-TIPO-SERIE-NUMERO.xml (R-52). Si la salida es una carpeta, el archivo se nombra así.
    val destino = Paths.get(args.getOrElse(1) { "." })
    val salida = if (Files.isDirectory(destino) || args.getOrElse(1) { "." }.endsWith("/")) destino.resolve("${xml.nombre}.xml") else destino
    salida.toAbsolutePath().parent?.let { Files.createDirectories(it) }
    Files.write(salida, contenido)
    println(if (hallazgos.isEmpty()) "OK: ${xml.nombre} valido -> $salida" else "${hallazgos.size} hallazgo(s) -> $salida")
    if (paraOse) println("Comprobante ${comprobante.numero}, fecha ${comprobante.fechaEmision}. Pegue el archivo en probar-xml.nubefact.com, marque 'Firmar' y pulse ENVIAR.")
    exitProcess(if (hallazgos.isEmpty()) 0 else 1)
}
