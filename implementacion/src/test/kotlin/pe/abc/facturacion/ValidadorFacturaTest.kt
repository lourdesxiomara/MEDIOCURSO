package pe.abc.facturacion

import org.junit.jupiter.api.Test
import pe.abc.facturacion.adaptadores.ubl.GeneradorFacturaJaxb
import pe.abc.facturacion.adaptadores.validacion.ValidadorFactura
import java.math.BigDecimal
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * Validación del XML: se genera la factura correcta y se le inyecta UN error a la vez;
 * el validador debe detectarlo con la regla esperada (como las pruebas de mutación de tools/verificar.py).
 */
class ValidadorFacturaTest {
    private val validador = ValidadorFactura()
    private val factura = GeneradorFacturaJaxb().generar(Ejemplos.comprobante("comprobante.factura.json")).texto
    private val credito = GeneradorFacturaJaxb().generar(Ejemplos.comprobante("comprobante.factura-isc.json")).texto
    private val boleta = GeneradorFacturaJaxb().generar(Ejemplos.comprobante("comprobante.boleta.json")).texto

    private fun reglas(xml: String) = validador.validar(xml.toByteArray()).map { it.regla }.toSet()

    private fun detecta(regla: String, original: String, desde: String, hacia: String) {
        assertTrue(desde in original, "la mutación debe aplicar: $desde")
        val r = reglas(original.replaceFirst(desde, hacia))
        assertTrue(regla in r, "se esperaba $regla y se obtuvo $r")
    }

    /** Reemplaza la ÚLTIMA coincidencia de la expresión (las líneas van después de los totales del documento). */
    private fun ultima(original: String, expr: String, reemplazo: String): String {
        val m = Regex(expr).findAll(original).last()
        return original.substring(0, m.range.first) + m.value.replace(Regex(expr), reemplazo) + original.substring(m.range.last + 1)
    }

    @Test fun `la factura generada no tiene hallazgos`() = assertEquals(emptySet(), reglas(factura))
    @Test fun `la factura a credito y la boleta generadas no tienen hallazgos`() {
        assertEquals(emptySet(), reglas(credito))
        assertEquals(emptySet(), reglas(boleta))
    }

    @Test fun `los importes se comparan por valor - 345 8 y 345 80 son iguales`() =
        assertEquals(emptySet(), reglas(factura.replace(""">345.80</cbc:PayableAmount>""", """>345.8</cbc:PayableAmount>""")))

    @Test fun `tipo de comprobante que no es factura ni boleta (R-01)`() =
        detecta("R-01", factura, """listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01">01<""", """listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01">07<""")

    @Test fun `correlativo fuera de formato (R-03)`() = detecta("R-03", factura, "<cbc:ID>F001-1</cbc:ID>", "<cbc:ID>F001-0</cbc:ID>")

    @Test fun `DNI que no tiene 8 digitos (R-12)`() = detecta("R-12", boleta, """schemeID="1">45678912<""", """schemeID="1">4567891<""")

    @Test fun `afectacion IGV fuera del catalogo 07 (R-21)`() =
        detecta("R-21", factura, "<cbc:TaxExemptionReasonCode>10</cbc:TaxExemptionReasonCode>", "<cbc:TaxExemptionReasonCode>99</cbc:TaxExemptionReasonCode>")

    @Test fun `linea exonerada con importe de IGV (R-23)`() {
        val mutado = ultima(boleta, """(7\.00</cbc:TaxableAmount>\s*<cbc:TaxAmount currencyID="PEN">)0\.00""", "$11.26")
        assertTrue("R-23" in reglas(mutado), reglas(mutado).toString())
    }

    @Test fun `tipo de precio fuera del catalogo 16 (R-27)`() = detecta("R-27", factura, "<cbc:PriceTypeCode>01</cbc:PriceTypeCode>", "<cbc:PriceTypeCode>03</cbc:PriceTypeCode>")

    @Test fun `numero de lineas distinto de LineCountNumeric (R-28)`() =
        detecta("R-28", factura, "<cbc:LineCountNumeric>3</cbc:LineCountNumeric>", "<cbc:LineCountNumeric>4</cbc:LineCountNumeric>")

    @Test fun `valor de venta del documento distinto de la suma de lineas (R-30)`() =
        detecta("R-30", factura, """<cbc:LineExtensionAmount currencyID="PEN">280.20</cbc:LineExtensionAmount>""", """<cbc:LineExtensionAmount currencyID="PEN">281.20</cbc:LineExtensionAmount>""")

    @Test fun `sin leyenda 1000 del monto en letras (R-32)`() = detecta("R-32", factura, """languageLocaleID="1000"""", """languageLocaleID="1002"""")

    @Test fun `importe en una moneda distinta de la del documento (R-33)`() =
        detecta("R-33", factura, """<cbc:PriceAmount currencyID="PEN">22.00</cbc:PriceAmount>""", """<cbc:PriceAmount currencyID="USD">22.00</cbc:PriceAmount>""")

    @Test fun `estructura invalida - XSD (R-50)`() =
        detecta("R-50", factura, "<cbc:IssueDate>2026-10-22</cbc:IssueDate>", "<cbc:IssueDate>22/10/2026</cbc:IssueDate>")

    @Test fun `XML mal formado (R-50)`() = assertEquals(setOf("R-50"), reglas("<Invoice>"))

    @Test fun `serie de boleta en una factura (R-02)`() = detecta("R-02", factura, "<cbc:ID>F001-1</cbc:ID>", "<cbc:ID>B001-1</cbc:ID>")

    @Test fun `RUC del emisor con digito verificador erroneo (R-10)`() =
        detecta("R-10", factura, """<cbc:ID schemeID="6">20600123450</cbc:ID>""", """<cbc:ID schemeID="6">20600123451</cbc:ID>""")

    @Test fun `factura a cliente con DNI (R-11)`() =
        detecta("R-11", factura, """<cbc:ID schemeID="6">20456789014</cbc:ID>""", """<cbc:ID schemeID="1">45678912</cbc:ID>""")

    @Test fun `unidad de medida fuera del catalogo 03 (R-20)`() =
        detecta("R-20", factura, """unitCode="NIU">10<""", """unitCode="XYZ">10<""")

    @Test fun `tipo de operacion fuera del catalogo 51 (R-34)`() = detecta("R-34", factura, """listID="0101"""", """listID="9999"""")

    @Test fun `IGV mal calculado en la linea (R-22)`() {
        val mutado = Regex("""(220\.00</cbc:TaxableAmount>\s*<cbc:TaxAmount currencyID="PEN">)39\.60""").replace(factura, "$139.61")
        assertTrue(mutado != factura)
        assertTrue("R-22" in reglas(mutado))
    }

    @Test fun `tasa de IGV distinta de 18 (R-22)`() = detecta("R-22", factura, "<cbc:Percent>18.00</cbc:Percent>", "<cbc:Percent>19.00</cbc:Percent>")

    @Test fun `ICBPER con la tasa de 2022 (R-26, D-01)`() =
        detecta("R-26", factura, """<cbc:PerUnitAmount currencyID="PEN">0.50</cbc:PerUnitAmount>""", """<cbc:PerUnitAmount currencyID="PEN">0.40</cbc:PerUnitAmount>""")

    @Test fun `ISC al valor que no cuadra con la tasa (R-24)`() =
        detecta("R-24", factura, "<cbc:Percent>20.00</cbc:Percent>", "<cbc:Percent>25.00</cbc:Percent>")

    @Test fun `ISC con etiquetas del ICBPER (R-24, D-11)`() =
        detecta("R-24", credito, "<cbc:Percent>37.50</cbc:Percent>", """<cbc:Percent>37.50</cbc:Percent><cbc:PerUnitAmount currencyID="PEN">1.50</cbc:PerUnitAmount>""")

    @Test fun `importe a pagar que no cuadra (R-31)`() =
        detecta("R-31", factura, """<cbc:PayableAmount currencyID="PEN">345.80</cbc:PayableAmount>""", """<cbc:PayableAmount currencyID="PEN">345.00</cbc:PayableAmount>""")

    @Test fun `valor de venta de linea distinto de cantidad por valor unitario (R-28)`() =
        detecta("R-28", factura, """<cbc:PriceAmount currencyID="PEN">22.00</cbc:PriceAmount>""", """<cbc:PriceAmount currencyID="PEN">21.00</cbc:PriceAmount>""")

    @Test fun `factura sin forma de pago (R-35)`() = detecta("R-35", factura, "<cbc:PaymentMeansID>Contado</cbc:PaymentMeansID>", "<cbc:PaymentMeansID>Efectivo</cbc:PaymentMeansID>")

    @Test fun `cuotas que no suman el monto pendiente (R-36)`() =
        detecta("R-36", credito, """<cbc:Amount currencyID="PEN">68.53</cbc:Amount>""", """<cbc:Amount currencyID="PEN">60.00</cbc:Amount>""")

    @Test fun `tasa ICBPER vigente por fecha`() {
        assertEquals(BigDecimal("0.10"), ValidadorFactura.tasaIcbper("2019-08-01"))
        assertEquals(BigDecimal("0.40"), ValidadorFactura.tasaIcbper("2022-12-31"))
        assertEquals(BigDecimal("0.50"), ValidadorFactura.tasaIcbper("2026-10-22"))
    }

    @Test fun `digito verificador del RUC (R-10)`() {
        assertTrue(ValidadorFactura.rucValido("20600123450"))
        assertTrue(!ValidadorFactura.rucValido("20600123451"))
        assertTrue(!ValidadorFactura.rucValido("30600123450"))
    }
}
