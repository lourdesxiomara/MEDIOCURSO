package pe.abc.facturacion.adaptadores.ubl

import jakarta.xml.bind.JAXBContext
import jakarta.xml.bind.JAXBException
import jakarta.xml.bind.Marshaller
import oasis.names.specification.ubl.schema.xsd.commonaggregatecomponents_2.*
import oasis.names.specification.ubl.schema.xsd.commonbasiccomponents_2.*
import oasis.names.specification.ubl.schema.xsd.invoice_2.InvoiceType
import oasis.names.specification.ubl.schema.xsd.invoice_2.ObjectFactory
import org.glassfish.jaxb.runtime.marshaller.NamespacePrefixMapper
import pe.abc.facturacion.dominio.Comprobante
import pe.abc.facturacion.dominio.Linea
import pe.abc.facturacion.dominio.Tributo
import pe.abc.facturacion.puertos.DocumentoXml
import pe.abc.facturacion.puertos.ErrorEstructuraUbl
import pe.abc.facturacion.puertos.GeneradorDocumentoUbl
import java.io.ByteArrayOutputStream
import java.math.BigDecimal
import java.math.RoundingMode
import javax.xml.datatype.DatatypeFactory

/**
 * Adaptador del puerto GeneradorDocumentoUbl (ADR-006) para Invoice: factura (01) y boleta (03).
 *
 * Comprobante (dominio) → InvoiceType (clases generadas por xjc desde UBL-Invoice-2.1.xsd) → XML.
 * Cada asignación sigue una fila de specs/05-trazabilidad/matriz.csv (indicada como T-xx).
 * El Marshaller valida contra el XSD oficial: un documento inválido falla aquí, antes de firmar (R-50).
 */
class GeneradorFacturaJaxb(
    private val idFirma: String = "SignatureABC",      // enlaza cac:Signature con ds:Signature/@Id (R-51)
    private val tasaIgv: BigDecimal = BigDecimal("18.00"),
) : GeneradorDocumentoUbl {

    override fun generar(c: Comprobante): DocumentoXml {
        val invoice = mapear(c)
        val salida = ByteArrayOutputStream()
        try {
            contexto.createMarshaller().apply {
                setProperty(Marshaller.JAXB_ENCODING, "UTF-8")
                setProperty(Marshaller.JAXB_FORMATTED_OUTPUT, true)
                setProperty("org.glassfish.jaxb.namespacePrefixMapper", Prefijos)
                schema = EsquemasUbl.schema("Invoice")           // validación al serializar (R-50)
            }.marshal(ObjectFactory().createInvoice(invoice), salida)
        } catch (e: JAXBException) {
            val causa = e.linkedException ?: e.cause ?: e
            throw ErrorEstructuraUbl("${c.numero}: el XML no cumple UBL-Invoice-2.1.xsd: ${causa.message}", e)
        }
        return DocumentoXml("${c.emisor.ruc}-${c.tipoComprobante}-${c.numero}", salida.toByteArray())
    }

    /** Público para las pruebas: el árbol JAXB antes de serializar. */
    fun mapear(c: Comprobante): InvoiceType {
        val m = c.moneda
        return InvoiceType().apply {
            ublVersionID = UBLVersionIDType().apply { value = "2.1" }                       // T-01
            customizationID = CustomizationIDType().apply { value = "2.0" }                 // T-02
            id = IDType().apply { value = c.numero }                                        // serie-correlativo
            issueDate = IssueDateType().apply { value = fecha(c.fechaEmision.toString()) }
            c.horaEmision?.let { h -> issueTime = IssueTimeType().apply { value = fecha(h.toString().let { if (it.length == 5) "$it:00" else it }) } }
            invoiceTypeCode = InvoiceTypeCodeType().apply {                                 // cat. 01 + @listID cat. 51
                value = c.tipoComprobante
                listID = c.tipoOperacion
                listAgencyName = "PE:SUNAT"
                listName = "Tipo de Documento"
                listURI = "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01"
            }
            c.leyendas.forEach { l -> note.add(NoteType().apply { value = l.texto; languageLocaleID = l.codigo }) }
            documentCurrencyCode = DocumentCurrencyCodeType().apply {
                value = m
                listID = "ISO 4217 Alpha"
                listAgencyName = "United Nations Economic Commission for Europe"
            }
            lineCountNumeric = LineCountNumericType().apply { value = BigDecimal(c.lineas.size) }
            signature.add(firma(c))
            accountingSupplierParty = emisor(c)
            accountingCustomerParty = cliente(c)
            paymentTerms.addAll(formaPago(c))
            taxTotal.add(tributosGlobales(c))
            legalMonetaryTotal = MonetaryTotalType().apply {
                lineExtensionAmount = LineExtensionAmountType().apply { value = c.totales.valorVenta; currencyID = m }
                taxInclusiveAmount = TaxInclusiveAmountType().apply { value = c.totales.precioVenta; currencyID = m }
                payableAmount = PayableAmountType().apply { value = c.totales.importeTotal; currencyID = m }
            }
            c.lineas.forEach { invoiceLine.add(linea(it, m)) }
        }
    }

    private fun firma(c: Comprobante) = SignatureType().apply {
        id = IDType().apply { value = "IDSign" + idFirma.removePrefix("Signature") }
        signatoryParty = PartyType().apply {
            partyIdentification.add(PartyIdentificationType().apply { id = IDType().apply { value = c.emisor.ruc } })
            partyName.add(PartyNameType().apply { name = NameType().apply { value = c.emisor.razonSocial } })
        }
        digitalSignatureAttachment = AttachmentType().apply {
            externalReference = ExternalReferenceType().apply { uri = URIType().apply { value = "#$idFirma" } }
        }
    }

    private fun emisor(c: Comprobante) = SupplierPartyType().apply {
        val e = c.emisor
        val d = e.domicilioFiscal
        party = PartyType().apply {
            partyIdentification.add(PartyIdentificationType().apply { id = IDType().apply { value = e.ruc; schemeID = "6" } })
            e.nombreComercial?.let { n -> partyName.add(PartyNameType().apply { name = NameType().apply { value = n } }) }
            partyLegalEntity.add(PartyLegalEntityType().apply {
                registrationName = RegistrationNameType().apply { value = e.razonSocial }
                registrationAddress = AddressType().apply {
                    d.ubigeo?.let { id = IDType().apply { value = it } }
                    addressTypeCode = AddressTypeCodeType().apply { value = d.codigoEstablecimiento }   // T-13
                    if (d.ubigeo != null) {
                        citySubdivisionName = CitySubdivisionNameType().apply { value = d.urbanizacion ?: "-" }
                        d.provincia?.let { cityName = CityNameType().apply { value = it } }
                        d.departamento?.let { countrySubentity = CountrySubentityType().apply { value = it } }
                        d.distrito?.let { district = DistrictType().apply { value = it } }
                        d.direccion?.let { addressLine.add(AddressLineType().apply { line = LineType().apply { value = it } }) }
                        d.codigoPais?.let { country = CountryType().apply { identificationCode = IdentificationCodeType().apply { value = it } } }
                    }
                }
            })
        }
    }

    private fun cliente(c: Comprobante) = CustomerPartyType().apply {
        party = PartyType().apply {
            partyIdentification.add(PartyIdentificationType().apply {
                id = IDType().apply { value = c.cliente.documento.numero; schemeID = c.cliente.documento.tipo }   // cat. 06
            })
            partyLegalEntity.add(PartyLegalEntityType().apply { registrationName = RegistrationNameType().apply { value = c.cliente.nombre } })
        }
    }

    /** cac:PaymentTerms con cbc:ID = FormaPago (RS 193-2020, R-35, R-36). */
    private fun formaPago(c: Comprobante): List<PaymentTermsType> {
        val fp = c.formaPago ?: return emptyList()
        fun termino(medio: String, monto: BigDecimal?, vence: String?) = PaymentTermsType().apply {
            id = IDType().apply { value = "FormaPago" }
            paymentMeansID.add(PaymentMeansIDType().apply { value = medio })
            monto?.let { amount = AmountType().apply { value = it; currencyID = c.moneda } }
            vence?.let { paymentDueDate = PaymentDueDateType().apply { value = fecha(it) } }
        }
        return listOf(termino(fp.tipo, if (fp.tipo == "Credito") fp.montoNetoPendiente else null, null)) +
            fp.cuotas.map { q -> termino("Cuota%03d".format(q.numero), q.monto, q.fechaVencimiento.toString()) }
    }

    /** cac:TaxTotal del documento: un subtotal por tributo con importe (orden fijo: ISC, IGV, ICBPER, EXO, INA, GRA). */
    private fun tributosGlobales(c: Comprobante): TaxTotalType {
        val t = c.totales
        val m = c.moneda
        val baseIsc = c.lineas.flatMap { it.tributos }.filter { it.codigo == "2000" }.sumOf { it.baseImponible ?: BigDecimal.ZERO }
        fun sub(codigo: String, nombre: String, internacional: String, base: BigDecimal?, monto: BigDecimal) = TaxSubtotalType().apply {
            base?.let { taxableAmount = TaxableAmountType().apply { value = it.setScale(2); currencyID = m } }
            taxAmount = TaxAmountType().apply { value = monto; currencyID = m }
            taxCategory = TaxCategoryType().apply { taxScheme = esquema(codigo, nombre, internacional) }
        }
        val subtotales = buildList {
            if (t.totalIsc.signum() != 0) add(sub("2000", "ISC", "EXC", baseIsc, t.totalIsc))
            if (t.totalGravado.signum() != 0 || t.totalIgv.signum() != 0) add(sub("1000", "IGV", "VAT", t.totalGravado, t.totalIgv))   // base sin ISC (T-79)
            if (t.totalIcbper.signum() != 0) add(sub("7152", "ICBPER", "OTH", null, t.totalIcbper))
            if (t.totalExonerado.signum() != 0) add(sub("9997", "EXO", "VAT", t.totalExonerado, BigDecimal("0.00")))
            if (t.totalInafecto.signum() != 0) add(sub("9998", "INA", "FRE", t.totalInafecto, BigDecimal("0.00")))
        }
        return TaxTotalType().apply {
            taxAmount = TaxAmountType().apply { value = t.totalIgv + t.totalIsc + t.totalIcbper; currencyID = m }
            taxSubtotal.addAll(subtotales)
        }
    }

    private fun linea(l: Linea, m: String) = InvoiceLineType().apply {
        id = IDType().apply { value = l.numero.toString() }
        invoicedQuantity = InvoicedQuantityType().apply { value = l.cantidad; unitCode = l.unidadMedida }     // cat. 03
        lineExtensionAmount = LineExtensionAmountType().apply { value = l.valorVenta; currencyID = m }         // T-26
        pricingReference = PricingReferenceType().apply {
            alternativeConditionPrice.add(PriceType().apply {
                priceAmount = PriceAmountType().apply { value = l.precioUnitario; currencyID = m }             // Anexo 1 campo 22
                priceTypeCode = PriceTypeCodeType().apply { value = l.tipoPrecio }                              // cat. 16
            })
        }
        taxTotal.add(TaxTotalType().apply {
            taxAmount = TaxAmountType().apply { value = l.tributos.sumOf { it.monto }; currencyID = m }
            l.tributos.forEach { taxSubtotal.add(subtotalLinea(l, it, m)) }
        })
        item = ItemType().apply {
            description.add(DescriptionType().apply { value = l.descripcion })
            l.codigoProducto?.let { sellersItemIdentification = ItemIdentificationType().apply { id = IDType().apply { value = it } } }
            l.codigoSunat?.let {
                commodityClassification.add(CommodityClassificationType().apply {
                    itemClassificationCode = ItemClassificationCodeType().apply { value = it; listID = "UNSPSC" }   // T-22
                })
            }
        }
        price = PriceType().apply { priceAmount = PriceAmountType().apply { value = l.valorUnitario; currencyID = m } }
    }

    /** Anexo 9-A: ítem 36 (IGV/EXO/INA), ítem 37 (ISC) e ítem 37-A (ICBPER). */
    private fun subtotalLinea(l: Linea, t: Tributo, m: String) = TaxSubtotalType().apply {
        when (t.codigo) {
            "7152" -> {                                                   // ICBPER: sin base imponible (R-26, D-10)
                taxAmount = TaxAmountType().apply { value = t.monto; currencyID = m }
                baseUnitMeasure = BaseUnitMeasureType().apply {
                    value = BigDecimal(t.cantidadBolsas ?: throw ErrorEstructuraUbl("Línea ${l.numero}: ICBPER sin cantidadBolsas"))
                    unitCode = l.unidadMedida
                }
                taxCategory = TaxCategoryType().apply {
                    perUnitAmount = PerUnitAmountType().apply { value = t.montoPorUnidad; currencyID = m }
                    taxScheme = esquema(t)
                }
            }
            "2000" -> {                                                   // ISC: TaxableAmount, TaxAmount, Percent, TierRange (D-11)
                val base = t.baseImponible ?: throw ErrorEstructuraUbl("Línea ${l.numero}: ISC sin baseImponible")
                taxableAmount = TaxableAmountType().apply { value = base; currencyID = m }
                taxAmount = TaxAmountType().apply { value = t.monto; currencyID = m }
                taxCategory = TaxCategoryType().apply {
                    percent = PercentType().apply { value = t.porcentaje ?: tasaEquivalente(t.monto, base) }
                    tierRange = TierRangeType().apply { value = t.sistemaIsc }                          // cat. 08 (T-34)
                    taxScheme = esquema(t)
                }
            }
            else -> {                                                     // IGV 1000, EXO 9997, INA 9998, GRA 9996, EXP 9995
                taxableAmount = TaxableAmountType().apply { value = t.baseImponible ?: l.valorVenta; currencyID = m }
                taxAmount = TaxAmountType().apply { value = t.monto; currencyID = m }
                taxCategory = TaxCategoryType().apply {
                    percent = PercentType().apply { value = t.porcentaje ?: tasaIgv }
                    taxExemptionReasonCode = TaxExemptionReasonCodeType().apply { value = l.afectacionIgv }   // cat. 07
                    taxScheme = esquema(t)
                }
            }
        }
    }

    /** ISC de monto fijo (sistema 02): tasa equivalente = monto ÷ base × 100, para que TaxAmount = TaxableAmount × Percent (D-11). */
    private fun tasaEquivalente(monto: BigDecimal, base: BigDecimal): BigDecimal =
        monto.multiply(BigDecimal(100)).divide(base, 2, RoundingMode.HALF_UP)

    private fun esquema(t: Tributo) = esquema(t.codigo, t.nombre, t.codigoInternacional)
    private fun esquema(codigo: String, nombre: String, internacional: String) = TaxSchemeType().apply {   // cat. 05
        id = IDType().apply { value = codigo }
        name = NameType().apply { value = nombre }
        taxTypeCode = TaxTypeCodeType().apply { value = internacional }
    }

    private fun fecha(lexico: String) = datatypes.newXMLGregorianCalendar(lexico)

    /** Prefijos legibles (cac, cbc, ext, ds) en lugar de ns2, ns3... */
    private object Prefijos : NamespacePrefixMapper() {
        private val mapa = mapOf(
            "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" to "",
            "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" to "cac",
            "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" to "cbc",
            "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2" to "ext",
            "http://www.w3.org/2000/09/xmldsig#" to "ds",
        )
        override fun getPreferredPrefix(uri: String, sugerido: String?, requerido: Boolean) = mapa[uri] ?: sugerido
        override fun getPreDeclaredNamespaceUris(): Array<String> = arrayOf(
            "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        )
    }

    companion object {
        private val contexto: JAXBContext by lazy { JAXBContext.newInstance(InvoiceType::class.java) }
        private val datatypes = DatatypeFactory.newInstance()
    }
}
