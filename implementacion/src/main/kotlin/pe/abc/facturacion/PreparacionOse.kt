package pe.abc.facturacion

import pe.abc.facturacion.dominio.Comprobante
import java.time.ZoneId
import java.time.ZonedDateTime
import java.time.temporal.ChronoUnit

/**
 * Prepara un comprobante de ejemplo para enviarlo HOY a un OSE de prueba (p. ej. probar-xml.nubefact.com).
 *  - El OSE rechaza comprobantes fuera del plazo de envío (R-05): la fecha de emisión pasa a ser la de hoy en Lima
 *    y las cuotas se desplazan los mismos días.
 *  - Un número ya enviado no se puede volver a usar (R-53; error 1033 "registrado previamente"): el correlativo pasa a
 *    ser MMddHHmm de la hora actual, distinto en cada envío y dentro del máximo de 8 dígitos (R-03).
 * Los importes no cambian.
 */
object PreparacionOse {
    val zona: ZoneId = ZoneId.of("America/Lima")

    fun preparar(c: Comprobante, ahora: ZonedDateTime = ZonedDateTime.now(zona)): Comprobante {
        val lima = ahora.withZoneSameInstant(zona)
        val hoy = lima.toLocalDate()
        val correlativo = "%02d%02d%02d%02d".format(lima.monthValue, lima.dayOfMonth, lima.hour, lima.minute).toInt()
        val dias = ChronoUnit.DAYS.between(c.fechaEmision, hoy)
        return c.copy(
            numero = "${c.numero.substringBefore('-')}-$correlativo",
            fechaEmision = hoy,
            horaEmision = ahora.withZoneSameInstant(zona).toLocalTime().truncatedTo(ChronoUnit.SECONDS),
            formaPago = c.formaPago?.let { fp -> fp.copy(cuotas = fp.cuotas.map { it.copy(fechaVencimiento = it.fechaVencimiento.plusDays(dias)) }) },
        )
    }
}
