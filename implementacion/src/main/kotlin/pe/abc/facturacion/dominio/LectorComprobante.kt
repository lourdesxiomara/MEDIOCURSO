package pe.abc.facturacion.dominio

import com.fasterxml.jackson.databind.DeserializationFeature
import com.fasterxml.jackson.databind.json.JsonMapper
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule
import com.fasterxml.jackson.module.kotlin.kotlinModule
import com.fasterxml.jackson.module.kotlin.readValue
import java.nio.file.Path

/** Lee un comprobante en el formato del contrato JSON (los ejemplos de specs/02-dominio/ejemplos). */
object LectorComprobante {
    private val json = JsonMapper.builder()
        .addModule(kotlinModule())
        .addModule(JavaTimeModule())
        .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)   // id, estado, enlaces... no van al XML
        .build()

    fun leer(archivo: Path): Comprobante = json.readValue(archivo.toFile())
    fun leer(texto: String): Comprobante = json.readValue(texto)
}
