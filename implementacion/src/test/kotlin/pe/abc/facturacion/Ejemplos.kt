package pe.abc.facturacion

import pe.abc.facturacion.adaptadores.ubl.EsquemasUbl
import pe.abc.facturacion.dominio.Comprobante
import pe.abc.facturacion.dominio.LectorComprobante
import java.nio.file.Path

/** Los ejemplos de la spec (primer parcial) son el oráculo de las pruebas (ADR-006, "golden tests"). */
object Ejemplos {
    val carpeta: Path = EsquemasUbl.raizRepo.resolve("specs/02-dominio/ejemplos")

    /** JSON del dominio → XML UBL esperado (ambos ya validados por tools/verificar.py). */
    val pares = mapOf(
        "comprobante.factura.json" to "factura-F001-1.sin-firma.xml",
        "comprobante.factura-isc.json" to "factura-F001-2-isc.sin-firma.xml",
        "comprobante.boleta.json" to "boleta-B001-1.sin-firma.xml",
    )

    fun comprobante(json: String): Comprobante = LectorComprobante.leer(carpeta.resolve(json))
    fun xml(nombre: String): ByteArray = carpeta.resolve(nombre).toFile().readBytes()
}
