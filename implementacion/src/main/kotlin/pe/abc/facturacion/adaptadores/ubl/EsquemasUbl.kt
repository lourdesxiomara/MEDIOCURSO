package pe.abc.facturacion.adaptadores.ubl

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import javax.xml.XMLConstants
import javax.xml.validation.Schema
import javax.xml.validation.SchemaFactory

/**
 * Carga los XSD OFICIALES del repositorio (docs/ubl) a través de los envoltorios de tools/xsd,
 * los mismos que usa tools/verificar.py. No se copia ningún XSD dentro de la implementación.
 */
object EsquemasUbl {
    /** Raíz del repositorio: propiedad repo.raiz o la primera carpeta (hacia arriba) que contiene docs/ubl. */
    val raizRepo: Path by lazy {
        System.getProperty("repo.raiz")?.let { return@lazy Paths.get(it) }
        var p: Path? = Paths.get("").toAbsolutePath()
        while (p != null && !Files.isDirectory(p.resolve("docs/ubl"))) p = p.parent
        p ?: error("No se encontró docs/ubl: ejecute dentro del repositorio o defina -Drepo.raiz")
    }

    private val cache = mutableMapOf<String, Schema>()

    /** raiz = Invoice | CreditNote | DebitNote | ApplicationResponse */
    @Synchronized
    fun schema(raiz: String): Schema = cache.getOrPut(raiz) {
        val envoltorio = raizRepo.resolve("tools/xsd/validar-$raiz.xsd").toFile()
        SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI).newSchema(envoltorio)
    }
}
