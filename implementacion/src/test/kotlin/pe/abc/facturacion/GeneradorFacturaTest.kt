package pe.abc.facturacion

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.MethodSource
import org.xmlunit.builder.DiffBuilder
import pe.abc.facturacion.adaptadores.ubl.GeneradorFacturaJaxb
import pe.abc.facturacion.adaptadores.validacion.ValidadorFactura
import pe.abc.facturacion.puertos.ErrorEstructuraUbl
import java.math.BigDecimal
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Pruebas unitarias de GENERACIÓN del XML (segundo parcial). */
class GeneradorFacturaTest {
    private val generador = GeneradorFacturaJaxb()

    companion object {
        @JvmStatic fun pares() = Ejemplos.pares.entries.map { arrayOf(it.key, it.value) }
    }

    @ParameterizedTest(name = "{0} genera {1}")
    @MethodSource("pares")
    fun `el XML generado es equivalente al ejemplo de la spec`(json: String, esperado: String) {
        val generado = generador.generar(Ejemplos.comprobante(json))
        val diff = DiffBuilder.compare(Ejemplos.xml(esperado)).withTest(generado.contenido)
            .ignoreComments().ignoreWhitespace().checkForSimilar().build()
        assertFalse(diff.hasDifferences(), "Diferencias con $esperado:\n" + diff.differences.joinToString("\n"))
    }

    @ParameterizedTest(name = "{0} es válido (XSD + reglas)")
    @MethodSource("pares")
    fun `el XML generado pasa el XSD oficial y las reglas SUNAT`(json: String, @Suppress("UNUSED_PARAMETER") x: String) {
        val generado = generador.generar(Ejemplos.comprobante(json))
        assertEquals(emptyList(), ValidadorFactura().validar(generado.contenido))
    }

    @Test
    fun `cabecera de la factura`() {
        val xml = generador.generar(Ejemplos.comprobante("comprobante.factura.json"))
        assertEquals("20600123450-01-F001-1", xml.nombre)                        // base del nombre del ZIP (R-52)
        val t = xml.texto
        assertTrue("<cbc:UBLVersionID>2.1</cbc:UBLVersionID>" in t)
        assertTrue("<cbc:CustomizationID>2.0</cbc:CustomizationID>" in t)
        assertTrue("""listID="0101"""" in t, "tipo de operación en InvoiceTypeCode/@listID")
        assertTrue("""<cbc:Note languageLocaleID="1000">TRESCIENTOS CUARENTA Y CINCO CON 80/100 SOLES</cbc:Note>""" in t)
        assertTrue("<cbc:URI>#SignatureABC</cbc:URI>" in t)
        assertFalse("ns2:" in t, "usa prefijos legibles cac/cbc")
    }

    @Test
    fun `el modelo JAXB se llena desde el dominio`() {
        val inv = generador.mapear(Ejemplos.comprobante("comprobante.factura.json"))
        assertEquals("F001-1", inv.id.value)
        assertEquals("2026-10-22", inv.issueDate.value.toXMLFormat())
        assertEquals(3, inv.invoiceLine.size)
        assertEquals(BigDecimal("345.80"), inv.legalMonetaryTotal.payableAmount.value)
        assertEquals(listOf("2000", "1000", "7152"), inv.taxTotal[0].taxSubtotal.map { it.taxCategory.taxScheme.id.value })
    }

    @Test
    fun `ISC monto fijo (sistema 02) usa Percent equivalente y no PerUnitAmount (D-11)`() {
        val linea = generador.mapear(Ejemplos.comprobante("comprobante.factura-isc.json")).invoiceLine[0]
        val isc = linea.taxTotal[0].taxSubtotal.first { it.taxCategory.taxScheme.id.value == "2000" }
        assertEquals("02", isc.taxCategory.tierRange.value)
        assertEquals(BigDecimal("37.50"), isc.taxCategory.percent.value)           // 18.00 / 48.00 × 100
        assertEquals(null, isc.perUnitAmount)
        assertEquals(null, isc.baseUnitMeasure)
    }

    @Test
    fun `ICBPER va con cantidad de bolsas y monto por bolsa, sin base imponible (Anexo 9-A ítem 37-A)`() {
        val linea = generador.mapear(Ejemplos.comprobante("comprobante.factura.json")).invoiceLine[2]
        val icbper = linea.taxTotal[0].taxSubtotal.first { it.taxCategory.taxScheme.id.value == "7152" }
        assertEquals(BigDecimal("2"), icbper.baseUnitMeasure.value)
        assertEquals(BigDecimal("0.50"), icbper.taxCategory.perUnitAmount.value)
        assertEquals(BigDecimal("1.00"), icbper.taxAmount.value)
        assertEquals(null, icbper.taxableAmount)
    }

    @Test
    fun `forma de pago a credito con cuotas (RS 193-2020)`() {
        val terminos = generador.mapear(Ejemplos.comprobante("comprobante.factura-isc.json")).paymentTerms
        assertEquals(listOf("Credito", "Cuota001", "Cuota002"), terminos.map { it.paymentMeansID[0].value })
        assertTrue(terminos.all { it.id.value == "FormaPago" })
        assertEquals(BigDecimal("137.07"), terminos[0].amount.value)
        assertEquals("2026-11-21", terminos[1].paymentDueDate.value.toXMLFormat())
    }

    @Test
    fun `boleta a persona con DNI y linea exonerada`() {
        val inv = generador.mapear(Ejemplos.comprobante("comprobante.boleta.json"))
        assertEquals("03", inv.invoiceTypeCode.value)
        assertEquals("1", inv.accountingCustomerParty.party.partyIdentification[0].id.schemeID)
        assertTrue(inv.paymentTerms.isEmpty(), "la boleta del ejemplo no declara forma de pago")
        val exo = inv.invoiceLine[2].taxTotal[0].taxSubtotal[0]
        assertEquals("9997", exo.taxCategory.taxScheme.id.value)
        assertEquals("20", exo.taxCategory.taxExemptionReasonCode.value)
    }

    @Test
    fun `un comprobante sin lineas no se genera - el XSD lo rechaza antes de firmar (R-50)`() {
        val sinLineas = Ejemplos.comprobante("comprobante.factura.json").copy(lineas = emptyList())
        val e = assertThrows<ErrorEstructuraUbl> { generador.generar(sinLineas) }
        assertTrue("InvoiceLine" in e.message!!, e.message)
    }
}
