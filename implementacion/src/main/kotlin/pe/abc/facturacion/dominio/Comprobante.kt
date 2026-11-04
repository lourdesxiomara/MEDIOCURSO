package pe.abc.facturacion.dominio

import java.math.BigDecimal
import java.time.LocalDate
import java.time.LocalTime

/**
 * Modelo de dominio del comprobante (contrato: specs/02-dominio/schemas/comprobante.schema.json).
 * Solo los campos que necesita el XML de la factura/boleta; los nombres son los del schema.
 * El dominio no conoce JAXB ni XML (ADR-001).
 */
data class Comprobante(
    val tipoComprobante: String,          // catálogo 01: 01 factura, 03 boleta
    val numero: String,                   // SERIE-CORRELATIVO, p. ej. F001-1
    val tipoOperacion: String,            // catálogo 51
    val fechaEmision: LocalDate,
    val horaEmision: LocalTime? = null,
    val moneda: String,                   // ISO 4217
    val emisor: Emisor,
    val cliente: Cliente,
    val formaPago: FormaPago? = null,     // obligatoria en facturas (RS 193-2020, R-35)
    val lineas: List<Linea>,
    val totales: Totales,
    val leyendas: List<Leyenda> = emptyList(),
)

data class Emisor(
    val ruc: String,
    val razonSocial: String,
    val nombreComercial: String? = null,
    val domicilioFiscal: Direccion,
)

data class Direccion(
    val direccion: String? = null,
    val ubigeo: String? = null,
    val departamento: String? = null,
    val provincia: String? = null,
    val distrito: String? = null,
    val urbanizacion: String? = null,
    val codigoPais: String? = null,
    val codigoEstablecimiento: String = "0000",
)

data class Cliente(val documento: DocumentoIdentidad, val nombre: String)

data class DocumentoIdentidad(val tipo: String, val numero: String)   // tipo: catálogo 06

data class FormaPago(
    val tipo: String,                         // Contado | Credito
    val montoNetoPendiente: BigDecimal? = null,
    val cuotas: List<Cuota> = emptyList(),
)

data class Cuota(val numero: Int, val monto: BigDecimal, val fechaVencimiento: LocalDate)

data class Linea(
    val numero: Int,
    val codigoProducto: String? = null,
    val codigoSunat: String? = null,          // UNSPSC
    val descripcion: String,
    val unidadMedida: String,                 // catálogo 03
    val cantidad: BigDecimal,
    val valorUnitario: BigDecimal,            // sin impuestos
    val precioUnitario: BigDecimal,           // con IGV/ISC, sin ICBPER (D-10)
    val tipoPrecio: String,                   // catálogo 16
    val afectacionIgv: String,                // catálogo 07
    val valorVenta: BigDecimal,
    val tributos: List<Tributo>,
)

data class Tributo(
    val codigo: String,                       // catálogo 05: 1000 IGV, 2000 ISC, 7152 ICBPER, 9997 EXO, 9998 INA...
    val nombre: String,
    val codigoInternacional: String,
    val baseImponible: BigDecimal? = null,
    val monto: BigDecimal,
    val porcentaje: BigDecimal? = null,
    val sistemaIsc: String? = null,           // catálogo 08
    val cantidadBolsas: Int? = null,
    val montoPorUnidad: BigDecimal? = null,
)

data class Totales(
    val totalGravado: BigDecimal,
    val totalExonerado: BigDecimal,
    val totalInafecto: BigDecimal,
    val totalIgv: BigDecimal,
    val totalIsc: BigDecimal,
    val totalIcbper: BigDecimal,
    val valorVenta: BigDecimal,
    val precioVenta: BigDecimal,
    val importeTotal: BigDecimal,
)

data class Leyenda(val codigo: String, val texto: String)   // catálogo 52
