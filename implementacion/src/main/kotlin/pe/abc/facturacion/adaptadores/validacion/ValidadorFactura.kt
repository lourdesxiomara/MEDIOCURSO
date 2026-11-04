package pe.abc.facturacion.adaptadores.validacion

import com.fasterxml.jackson.databind.ObjectMapper
import org.w3c.dom.Document
import org.w3c.dom.Element
import org.w3c.dom.Node
import org.xml.sax.ErrorHandler
import org.xml.sax.SAXParseException
import pe.abc.facturacion.adaptadores.ubl.EsquemasUbl
import pe.abc.facturacion.puertos.Hallazgo
import pe.abc.facturacion.puertos.ValidadorDocumento
import java.io.ByteArrayInputStream
import java.math.BigDecimal
import java.math.RoundingMode
import javax.xml.XMLConstants
import javax.xml.namespace.NamespaceContext
import javax.xml.parsers.DocumentBuilderFactory
import javax.xml.transform.dom.DOMSource
import javax.xml.xpath.XPathConstants
import javax.xml.xpath.XPathFactory

/**
 * Valida el XML de una factura o boleta (Invoice) en dos niveles:
 *  1. Estructura: XSD oficial UBL 2.1 (R-50).
 *  2. Reglas SUNAT sobre el XML (docs/sunat/reglas-validacion.md); cada hallazgo indica su R-xx.
 * Los catálogos se leen de docs/sunat/catalogos y la tasa del ICBPER de docs/sunat/tasas-icbper.json:
 * la implementación usa las mismas fuentes que la spec, no copias.
 */
class ValidadorFactura : ValidadorDocumento {

    override fun validar(xml: ByteArray): List<Hallazgo> {
        val doc = try { parsear(xml) } catch (e: Exception) { return listOf(Hallazgo("R-50", "XML mal formado: ${e.message}")) }
        val raiz = doc.documentElement.localName
        if (raiz != "Invoice") return listOf(Hallazgo("R-01", "Se esperaba Invoice y llegó $raiz"))
        val hallazgos = validarXsd(doc).toMutableList()
        if (hallazgos.isEmpty()) hallazgos += Reglas(doc).aplicar()   // las reglas suponen la estructura correcta
        return hallazgos
    }

    private fun validarXsd(doc: Document): List<Hallazgo> {
        val errores = mutableListOf<Hallazgo>()
        val validador = EsquemasUbl.schema("Invoice").newValidator()
        validador.errorHandler = object : ErrorHandler {
            override fun warning(e: SAXParseException) {}
            override fun error(e: SAXParseException) { errores += Hallazgo("R-50", "XSD: ${e.message}") }
            override fun fatalError(e: SAXParseException) { errores += Hallazgo("R-50", "XSD: ${e.message}") }
        }
        validador.validate(DOMSource(doc))
        return errores
    }

    private class Reglas(private val doc: Document) {
        private val h = mutableListOf<Hallazgo>()
        private val xp = XPathFactory.newInstance().newXPath().apply { namespaceContext = Espacios }

        fun aplicar(): List<Hallazgo> {
            val tipo = texto("/inv:Invoice/cbc:InvoiceTypeCode")
            val numero = texto("/inv:Invoice/cbc:ID")
            val fecha = texto("/inv:Invoice/cbc:IssueDate")
            val moneda = texto("/inv:Invoice/cbc:DocumentCurrencyCode")

            regla(tipo in setOf("01", "03"), "R-01", "InvoiceTypeCode $tipo no es factura (01) ni boleta (03)")
            val serie = numero.substringBefore("-")
            regla(Regex(if (tipo == "01") "^F[A-Z0-9]{3}$" else "^B[A-Z0-9]{3}$").matches(serie), "R-02", "Serie $serie no corresponde al tipo $tipo")
            regla(Regex("^[A-Z0-9]{4}-[1-9][0-9]{0,7}$").matches(numero), "R-03", "Número $numero fuera de formato SERIE-1..99999999")
            enCatalogo("51", texto("/inv:Invoice/cbc:InvoiceTypeCode/@listID"), "R-34", "Tipo de operación")
            enCatalogo("02", moneda, "R-33", "Moneda")
            regla(nodos("//cbc:*[@currencyID]").all { (it as Element).getAttribute("currencyID") == moneda }, "R-33", "Hay importes en una moneda distinta de $moneda")

            val ruc = texto("/inv:Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID")
            regla(rucValido(ruc), "R-10", "RUC del emisor $ruc no válido")
            val docCliente = texto("/inv:Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID")
            val tipoDoc = texto("/inv:Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID/@schemeID")
            enCatalogo("06", tipoDoc, "R-12", "Tipo de documento del cliente")
            if (tipo == "01") regla(tipoDoc == "6" && rucValido(docCliente), "R-11", "La factura exige cliente con RUC válido (schemeID 6)")
            if (tipoDoc == "1") regla(Regex("^\\d{8}$").matches(docCliente), "R-12", "DNI $docCliente debe tener 8 dígitos")
            regla(texto("/inv:Invoice/cbc:Note[@languageLocaleID='1000']").isNotBlank(), "R-32", "Falta la leyenda 1000 (monto en letras)")

            val lineas = nodos("/inv:Invoice/cac:InvoiceLine")
            regla(numeroDe("/inv:Invoice/cbc:LineCountNumeric").compareTo(BigDecimal(lineas.size)) == 0, "R-28", "LineCountNumeric ≠ número de líneas")
            lineas.forEach { linea(it as Element, fecha) }
            totales(lineas)
            if (tipo == "01") formaPago(fecha)
            return h
        }

        private fun linea(l: Element, fecha: String) {
            val n = texto("cbc:ID", l)
            enCatalogo("03", texto("cbc:InvoicedQuantity/@unitCode", l), "R-20", "Línea $n: unidad de medida")
            val cantidad = numeroDe("cbc:InvoicedQuantity", l)
            val valorVenta = numeroDe("cbc:LineExtensionAmount", l)
            regla(r2(cantidad * numeroDe("cac:Price/cbc:PriceAmount", l)) == valorVenta, "R-28", "Línea $n: LineExtensionAmount ≠ cantidad × valor unitario")
            enCatalogo("16", texto("cac:PricingReference/cac:AlternativeConditionPrice/cbc:PriceTypeCode", l), "R-27", "Línea $n: tipo de precio")
            val subtotales = nodos("cac:TaxTotal/cac:TaxSubtotal", l).map { it as Element }
            regla(subtotales.sumOf { numeroDe("cbc:TaxAmount", it) } == numeroDe("cac:TaxTotal/cbc:TaxAmount", l), "R-28", "Línea $n: TaxTotal ≠ Σ subtotales")
            for (s in subtotales) {
                val codigo = texto("cac:TaxCategory/cac:TaxScheme/cbc:ID", s)
                val monto = numeroDe("cbc:TaxAmount", s)
                when (codigo) {
                    "1000" -> {
                        enCatalogo("07", texto("cac:TaxCategory/cbc:TaxExemptionReasonCode", s), "R-21", "Línea $n: afectación IGV")
                        val pct = numeroDe("cac:TaxCategory/cbc:Percent", s)
                        regla(pct.compareTo(BigDecimal(18)) == 0, "R-22", "Línea $n: tasa IGV $pct ≠ 18")
                        regla(r2(numeroDe("cbc:TaxableAmount", s) * pct / CIEN) == monto, "R-22", "Línea $n: IGV mal calculado")
                    }
                    "2000" -> {
                        regla(existe("cbc:BaseUnitMeasure|cac:TaxCategory/cbc:PerUnitAmount", s).not(), "R-24", "Línea $n: ISC con BaseUnitMeasure/PerUnitAmount (son del ICBPER, Anexo 9-A ítem 37-A)")
                        val sistema = texto("cac:TaxCategory/cbc:TierRange", s)
                        enCatalogo("08", sistema, "R-24", "Línea $n: sistema de ISC")
                        if (sistema == "01" || sistema == "02")
                            regla(r2(numeroDe("cbc:TaxableAmount", s) * numeroDe("cac:TaxCategory/cbc:Percent", s) / CIEN) == monto, "R-24", "Línea $n: ISC ≠ base × tasa")
                    }
                    "7152" -> {
                        val bolsas = numeroDe("cbc:BaseUnitMeasure", s)
                        val tasa = numeroDe("cac:TaxCategory/cbc:PerUnitAmount", s)
                        regla(tasa.compareTo(tasaIcbper(fecha)) == 0, "R-26", "Línea $n: ICBPER $tasa ≠ monto vigente ${tasaIcbper(fecha)} al $fecha")
                        regla(r2(bolsas * tasa) == monto, "R-26", "Línea $n: ICBPER ≠ bolsas × monto")
                    }
                    "9997", "9998", "9995" -> {
                        enCatalogo("07", texto("cac:TaxCategory/cbc:TaxExemptionReasonCode", s), "R-21", "Línea $n: afectación IGV")
                        regla(monto.signum() == 0, "R-23", "Línea $n: operación no gravada con importe de IGV")
                    }
                }
            }
        }

        private fun totales(lineas: List<Node>) {
            val suma = lineas.sumOf { numeroDe("cbc:LineExtensionAmount", it) }
            val valorVenta = numeroDe("/inv:Invoice/cac:LegalMonetaryTotal/cbc:LineExtensionAmount")
            regla(suma == valorVenta, "R-30", "Valor de venta $valorVenta ≠ Σ líneas $suma")
            val totalTributos = numeroDe("/inv:Invoice/cac:TaxTotal/cbc:TaxAmount")
            val subtotales = nodos("/inv:Invoice/cac:TaxTotal/cac:TaxSubtotal").map { it as Element }
            regla(subtotales.sumOf { numeroDe("cbc:TaxAmount", it) } == totalTributos, "R-28", "TaxTotal del documento ≠ Σ subtotales")
            for (s in subtotales) {
                val codigo = texto("cac:TaxCategory/cac:TaxScheme/cbc:ID", s)
                val deLineas = nodos("/inv:Invoice/cac:InvoiceLine/cac:TaxTotal/cac:TaxSubtotal[cac:TaxCategory/cac:TaxScheme/cbc:ID='$codigo']/cbc:TaxAmount").sumOf { BigDecimal(it.textContent.trim()) }
                regla(deLineas == numeroDe("cbc:TaxAmount", s), "R-28", "Tributo $codigo: total ≠ Σ líneas ($deLineas)")
            }
            val pagar = numeroDe("/inv:Invoice/cac:LegalMonetaryTotal/cbc:PayableAmount")
            regla(valorVenta + totalTributos == pagar, "R-31", "PayableAmount $pagar ≠ valor de venta + tributos")
        }

        private fun formaPago(fecha: String) {
            val medio = texto("/inv:Invoice/cac:PaymentTerms[cbc:ID='FormaPago'][1]/cbc:PaymentMeansID")
            regla(medio == "Contado" || medio == "Credito", "R-35", "La factura debe declarar FormaPago Contado o Credito")
            if (medio != "Credito") return
            val pendiente = numeroDe("/inv:Invoice/cac:PaymentTerms[cbc:PaymentMeansID='Credito']/cbc:Amount")
            val cuotas = nodos("/inv:Invoice/cac:PaymentTerms[starts-with(cbc:PaymentMeansID,'Cuota')]").map { it as Element }
            regla(pendiente.signum() > 0 && pendiente <= numeroDe("/inv:Invoice/cac:LegalMonetaryTotal/cbc:PayableAmount"), "R-36", "Monto neto pendiente fuera de rango")
            regla(cuotas.isNotEmpty(), "R-36", "Crédito sin cuotas")
            regla(cuotas.sumOf { numeroDe("cbc:Amount", it) } == pendiente, "R-36", "Σ cuotas ≠ monto neto pendiente")
            regla(cuotas.all { texto("cbc:PaymentDueDate", it) > fecha }, "R-36", "Cuota con vencimiento no posterior a la emisión")
        }

        // ---- utilidades ----
        private fun regla(ok: Boolean, codigo: String, mensaje: String) { if (!ok) h += Hallazgo(codigo, mensaje) }
        private fun enCatalogo(cat: String, valor: String, codigo: String, que: String) =
            regla(valor in catalogo(cat), codigo, "$que '$valor' no está en el catálogo $cat")
        private fun nodos(expr: String, ctx: Node = doc): List<Node> {
            val l = xp.evaluate(expr, ctx, XPathConstants.NODESET) as org.w3c.dom.NodeList
            return (0 until l.length).map { l.item(it) }
        }
        private fun existe(expr: String, ctx: Node) = nodos(expr, ctx).isNotEmpty()
        private fun texto(expr: String, ctx: Node = doc): String = xp.evaluate(expr, ctx).trim()
        private fun numeroDe(expr: String, ctx: Node = doc): BigDecimal = texto(expr, ctx).ifEmpty { "0" }.toBigDecimal()
    }

    private object Espacios : NamespaceContext {
        private val mapa = mapOf(
            "inv" to "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
            "cac" to "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc" to "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "ext" to "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
        )
        override fun getNamespaceURI(prefix: String) = mapa[prefix] ?: XMLConstants.NULL_NS_URI
        override fun getPrefix(uri: String) = mapa.entries.firstOrNull { it.value == uri }?.key
        override fun getPrefixes(uri: String) = listOfNotNull(getPrefix(uri)).iterator()
    }

    companion object {
        private val CIEN = BigDecimal(100)
        private val json = ObjectMapper()
        private val catalogos = mutableMapOf<String, Set<String>>()

        fun parsear(xml: ByteArray): Document = DocumentBuilderFactory.newInstance().apply {
            isNamespaceAware = true
            setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)   // sin DTD ni entidades externas
        }.newDocumentBuilder().parse(ByteArrayInputStream(xml))

        @Synchronized
        fun catalogo(numero: String): Set<String> = catalogos.getOrPut(numero) {
            val f = EsquemasUbl.raizRepo.resolve("docs/sunat/catalogos/cat$numero.json").toFile()
            json.readTree(f)["codigos"].map { it["codigo"].asText() }.toSet()
        }

        /** Monto por bolsa vigente en la fecha (Ley 30884, DS 244-2019-EF art. 5; D-01). */
        fun tasaIcbper(fecha: String): BigDecimal {
            val f = EsquemasUbl.raizRepo.resolve("docs/sunat/tasas-icbper.json").toFile()
            return json.readTree(f)["cronograma"].filter { it["desde"].asText() <= fecha }
                .maxByOrNull { it["desde"].asText() }?.let { BigDecimal(it["monto"].asText()) }
                ?: error("No había ICBPER en $fecha")
        }

        fun rucValido(ruc: String): Boolean {
            if (!Regex("^(10|15|16|17|20)\\d{9}$").matches(ruc)) return false
            val pesos = intArrayOf(5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
            var dv = 11 - (0 until 10).sumOf { (ruc[it] - '0') * pesos[it] } % 11
            dv = when (dv) { 10 -> 0; 11 -> 1; else -> dv }
            return dv == ruc[10] - '0'
        }

        private fun r2(x: BigDecimal): BigDecimal = x.setScale(2, RoundingMode.HALF_UP)
    }
}
