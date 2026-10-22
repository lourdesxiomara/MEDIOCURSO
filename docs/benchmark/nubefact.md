# Benchmark: Nubefact (referencia para casos de uso)

> **Pendiente de completar por el equipo** con una cuenta DEMO propia (la creación de cuentas no la
> hace el agente). Usar la plantilla del final y guardar capturas en `docs/benchmark/capturas/`.

## Funciones públicas de referencia
Nubefact es un proveedor peruano de facturación electrónica con portal web y API JSON
(operaciones de generar comprobante, consultar comprobante, generar anulación y consultar anulación).
Las funciones que se usan como referencia para descubrir casos de uso son:

| Función observada | Caso de uso derivado (ver `specs/01-casos-uso/`) |
|---|---|
| Emitir factura / boleta desde formulario | CU-03, CU-04 |
| Emitir nota de crédito / débito referenciando un comprobante | CU-05, CU-06 |
| Anular comprobantes (comunicación de baja / resumen) | CU-07 |
| Consultar estado y descargar XML, PDF y CDR | CU-08 |
| Enviar comprobante al cliente por correo | CU-09 |
| Mantener clientes y productos (con afectación IGV por producto) | CU-01, CU-02 |
| Series y numeración automática | CU-10 |
| Reportes de ventas | CU-12 |

## Evidencia pública encontrada
- La integración oficial de Nubefact para Odoo confirma que emite facturas (01), boletas (03), notas de crédito (07) y débito (08), comprobantes de retención (20) y percepción (40), los envía por API y remite PDF + XML al cliente por correo (https://apps.odoo.com/apps/modules/18.0/l10n_pe_edi_odoofact). → CU-03 a CU-06, CU-09.
- DPL News (2021), citando a CONTA PERÚ: SUNAT tipificó al menos 59 errores frecuentes en la facturación electrónica; los más comunes son campos incompletos y datos del cliente mal digitados, que impiden la validación por SUNAT/OSE (https://dplnews.com/peru-6-recomendaciones-para-emitir-tus-facturas-electronicas-de-forma-eficiente/). → validación previa R-10/R-11, CA-07 a CA-10.

## Dolores frecuentes a verificar en opiniones de usuarios
Hipótesis que el equipo debe confirmar o descartar revisando reseñas reales:
- Rechazos por RUC mal digitado o no habido → validación previa (R-10, R-13).
- Errores de redondeo entre precio con IGV y valor de venta → regla R-28.
- Indisponibilidad del OSE/SUNAT al momento de emitir → cola de reenvío (CU-11).
- Necesidad de emitir sin internet en ferias o almacén → modo fuera de línea con envío diferido.
- Bolsas plásticas olvidadas en la boleta → producto "bolsa" con ICBPER automático.

## Plantilla de observación (DEMO)
| Pantalla / flujo | Campos que pide | Validaciones que muestra | Mensajes de error | Captura |
|---|---|---|---|---|
| | | | | |
