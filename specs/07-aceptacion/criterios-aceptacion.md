# 07 · Criterios de aceptación (especificación ejecutable)

En Spec-First el código se escribe **para pasar estas pruebas**. Cada criterio:
- tiene un ID `CA-xx`, las reglas que comprueba (`R-xx` de `docs/sunat/reglas-validacion.md`,
  `M-xx` de `specs/06-migracion`) y el endpoint de `specs/04-api/openapi.yaml` que lo ejerce;
- usa los datos de `specs/02-dominio/ejemplos/` como entrada o salida esperada.

`tools/verificar.py` comprueba que **toda regla R-xx y M-xx tenga al menos un criterio** y que los
archivos de ejemplo citados existan. Las reglas de tipo *X* (externas) se prueban contra un OSE simulado.

Formato: **Dado** (contexto) · **Cuando** (acción) · **Entonces** (resultado observable).

## A. Identificación del comprobante

### CA-01 Factura válida se crea con totales calculados por el sistema
- **Reglas:** R-01, R-03, R-30, R-31, R-32, R-34 · **API:** `POST /comprobantes`
- **Dado** el emisor de `ejemplos/comprobante.factura.json` con serie `F001` activa
- **Cuando** se envía `ejemplos/comprobante-crear.factura.json`
- **Entonces** responde `201` y el cuerpo coincide con `ejemplos/comprobante.factura.json` en líneas, tributos, totales y leyenda 1000; el request no contenía correlativo ni totales.

### CA-02 Tipo de comprobante fuera de alcance
- **Reglas:** R-01 · **API:** `POST /comprobantes`
- **Dado** un request con `tipoComprobante = "09"`
- **Cuando** se envía
- **Entonces** responde `400` con error de schema en `/tipoComprobante`.

### CA-03 Serie que no corresponde al tipo
- **Reglas:** R-02 · **API:** `POST /comprobantes`
- **Dado** una factura (`01`) con serie `B001`
- **Cuando** se envía
- **Entonces** responde `400` indicando `/serie`; con serie `F001` responde `201`.

### CA-04 Correlativo único y sin huecos por serie
- **Reglas:** R-03, R-53 · **API:** `POST /comprobantes/{id}/emitir`
- **Dado** que el último correlativo de `F001` es 1
- **Cuando** se emiten dos facturas en paralelo
- **Entonces** reciben 2 y 3, nunca el mismo número; reintentar `emitir` con el mismo `Idempotency-Key` no consume un correlativo nuevo.

### CA-05 Serie de nota coherente con el comprobante afectado
- **Reglas:** R-04 · **API:** `POST /comprobantes/{id}/notas-credito`
- **Dado** la factura `F001-1` aceptada
- **Cuando** se emite una nota con serie `BC01`
- **Entonces** responde `422` con regla R-04; con serie `FC01` se acepta.

### CA-06 Fecha de emisión futura
- **Reglas:** R-05 · **API:** `POST /comprobantes`
- **Dado** el reloj del sistema en `2026-10-22`
- **Cuando** se crea una factura con `fechaEmision = 2026-10-23`
- **Entonces** responde `422` con regla R-05.

## B. Partes

### CA-07 RUC con dígito verificador inválido
- **Reglas:** R-10 · **API:** `POST /clientes`, `POST /comprobantes`
- **Dado** el RUC `20456789015` (dígito verificador correcto: 4)
- **Cuando** se registra como cliente o adquirente
- **Entonces** responde `422` como `ejemplos/error.validacion.json` (regla R-10, campo `/cliente/documento/numero`).

### CA-08 Factura a cliente sin RUC
- **Reglas:** R-11 · **API:** `POST /comprobantes`
- **Dado** el cliente con DNI de `ejemplos/comprobante.boleta.json`
- **Cuando** se intenta emitir una factura (`01`) a su nombre
- **Entonces** responde `400` indicando que el documento debe ser tipo 6.

### CA-09 Boleta a persona con DNI
- **Reglas:** R-12 · **API:** `POST /comprobantes`
- **Dado** `ejemplos/comprobante-crear.boleta.json` (DNI de 8 dígitos)
- **Cuando** se envía
- **Entonces** responde `201` y el resultado coincide con `ejemplos/comprobante.boleta.json`; con DNI de 7 dígitos responde `400`.

### CA-10 RUC del adquirente no activo
- **Reglas:** R-13 · **API:** `POST /comprobantes` (puerto `ValidadorRuc` simulado)
- **Dado** que el padrón simulado devuelve el RUC como "BAJA DE OFICIO"
- **Cuando** se crea la factura
- **Entonces** responde `422` con regla R-13; si el padrón no responde, se crea con una advertencia y no se bloquea la venta.

## C. Ítems y tributos

### CA-11 Unidad de medida y afectación fuera de catálogo
- **Reglas:** R-20, R-21 · **API:** `POST /productos`
- **Dado** un producto con `unidadMedida = "XYZ"` o `afectacionIgv = "99"`
- **Cuando** se registra
- **Entonces** responde `400` indicando el campo y el catálogo (03 o 07).

### CA-12 Ítem gravado: IGV 18 % sobre el valor de venta
- **Reglas:** R-22, R-28 · **API:** `POST /comprobantes/validar`
- **Dado** 10 unidades a precio 25.96 con afectación `10`
- **Cuando** se valida
- **Entonces** valor unitario 22.00, valor de venta 220.00, IGV 39.60 (línea 1 de `ejemplos/comprobante.factura.json`).

### CA-13 Ítem inafecto o exonerado: sin IGV
- **Reglas:** R-23 · **API:** `POST /comprobantes/{id}/notas-debito`
- **Dado** `ejemplos/nota-crear.debito.json` (intereses por mora, afectación `30`)
- **Cuando** se emite
- **Entonces** el tributo es `9998` INA categoría `O`, IGV 0.00 y `totalInafecto` 50.00, como `ejemplos/comprobante.nota-debito.json`.

### CA-14 ISC sistema 01 (al valor)
- **Reglas:** R-24, R-25 · **API:** `POST /comprobantes/validar`
- **Dado** el producto `ejemplos/producto-cerveza.json` (sistema `01`, tasa 20 %)
- **Cuando** se venden 12 unidades a 7.08
- **Entonces** valor 60.00, ISC 12.00, base IGV 72.00 (valor + ISC), IGV 12.96 y XML con `cbc:TierRange = 01`.

### CA-15 ISC sistema 02 (monto fijo)
- **Reglas:** R-24, R-25 · **API:** `POST /comprobantes/validar`
- **Dado** `ejemplos/producto-cerveza-monto-fijo.json` (monto fijo 1.50 por unidad)
- **Cuando** se venden 12 unidades a 6.49
- **Entonces** ISC = 12 × 1.50 = 18.00, base IGV 66.00, IGV 11.88 y XML con `cbc:TierRange = 02` (`ejemplos/factura-F001-2-isc.sin-firma.xml`, línea 1).

### CA-16 ISC sistema 03 (precio de venta al público)
- **Reglas:** R-24, R-25 · **API:** `POST /comprobantes/validar`
- **Dado** `ejemplos/producto-cigarrillos.json` (PVP 12.00, tasa 20 %)
- **Cuando** se venden 5 unidades
- **Entonces** ISC = 12.00 × 0.847 × 20 % × 5 = 10.16, base IGV 50.16, IGV 9.03 y `cbc:TierRange = 03` (`ejemplos/factura-F001-2-isc.sin-firma.xml`, línea 2).

### CA-17 Producto con ISC sin sistema de cálculo
- **Reglas:** R-24 · **API:** `POST /comprobantes`
- **Dado** un producto marcado con ISC pero sin `isc.sistema`
- **Cuando** se factura
- **Entonces** responde `422` con regla R-24 (segundo error de `ejemplos/error.validacion.json`).

### CA-18 ICBPER por bolsa plástica
- **Reglas:** R-26 · **API:** `POST /comprobantes/validar`
- **Dado** 2 bolsas y tasa configurada 0.50
- **Cuando** se valida
- **Entonces** ICBPER = 1.00, no forma parte de la base del IGV y el XML usa `cbc:BaseUnitMeasure = 2` y `cbc:PerUnitAmount = 0.50` (línea 3 de `ejemplos/factura-F001-1.sin-firma.xml`).

### CA-19 Operación gratuita
- **Reglas:** R-27 · **API:** `POST /comprobantes/validar`
- **Dado** un ítem entregado como bonificación (afectación `15`)
- **Cuando** se valida
- **Entonces** `tipoPrecio = 02` (valor referencial) y se agrega la leyenda 1002.

### CA-20 Redondeo por línea
- **Reglas:** R-28 · **API:** `POST /comprobantes/validar`
- **Dado** una línea con IGV calculado 0.036
- **Cuando** se valida
- **Entonces** el IGV de la línea es 0.04 (half-up) y el total es la suma de líneas ya redondeadas.

## D. Totales, moneda y operación

### CA-21 Totales del comprobante
- **Reglas:** R-30, R-31 · **API:** `GET /comprobantes/{id}`
- **Dado** `ejemplos/comprobante.factura-isc.json`
- **Cuando** se consulta
- **Entonces** valor de venta 88.00, ISC 28.16, IGV 20.91 e importe total 137.07 = valor + ISC + IGV.

### CA-22 Leyenda de monto en letras
- **Reglas:** R-32 · **API:** `POST /comprobantes`
- **Dado** un importe total de 345.80 PEN
- **Cuando** se crea el comprobante
- **Entonces** incluye la leyenda 1000 "TRESCIENTOS CUARENTA Y CINCO CON 80/100 SOLES".

### CA-23 Moneda fuera de catálogo o mezclada
- **Reglas:** R-33 · **API:** `POST /comprobantes`
- **Dado** `moneda = "ABC"`
- **Cuando** se envía
- **Entonces** responde `400` indicando el catálogo 02.

### CA-24 Tipo de operación
- **Reglas:** R-34 · **API:** `POST /comprobantes`
- **Dado** una factura sin `tipoOperacion`
- **Cuando** se crea
- **Entonces** se asume `0101` y el XML lo lleva en `cbc:InvoiceTypeCode/@listID`; un valor fuera del catálogo 51 responde `400`.

## E. Notas de crédito y débito

### CA-25 Nota de crédito por devolución de ítem
- **Reglas:** R-40, R-41 · **API:** `POST /comprobantes/{id}/notas-credito`
- **Dado** la factura `F001-1` aceptada
- **Cuando** se envía `ejemplos/nota-crear.credito.json` (motivo `07`)
- **Entonces** se emite `ejemplos/comprobante.nota-credito.json` y se registra un ingreso de 2 unidades al inventario (CU-14).

### CA-26 Nota sobre comprobante inexistente o no aceptado
- **Reglas:** R-41 · **API:** `POST /comprobantes/{id}/notas-credito`
- **Dado** una factura en estado `RECHAZADO`
- **Cuando** se intenta emitir una nota de crédito
- **Entonces** responde `409` (estado inválido).

### CA-27 Nota de crédito por más del saldo
- **Reglas:** R-42 · **API:** `POST /comprobantes/{id}/notas-credito`
- **Dado** la factura `F001-1` (importe 345.80) con una nota previa por 14.16
- **Cuando** se emite una nota por 340.00
- **Entonces** responde `422` con regla R-42 (saldo disponible 331.64).

### CA-28 Nota de débito por intereses
- **Reglas:** R-40 · **API:** `POST /comprobantes/{id}/notas-debito`
- **Dado** la factura `F001-1` aceptada
- **Cuando** se envía `ejemplos/nota-crear.debito.json`
- **Entonces** se emite `ejemplos/comprobante.nota-debito.json` con motivo `01` del catálogo 10 y el XML `DebitNote` valida contra el XSD.

## F. XML, firma y envío

### CA-29 XML generado válido contra UBL 2.1
- **Reglas:** R-50 · **API:** `GET /comprobantes/{id}/xml`
- **Dado** cada comprobante de ejemplo
- **Cuando** se genera su XML
- **Entonces** valida contra `tools/xsd/validar-*.xsd` y coincide con los cinco archivos `.sin-firma.xml` de `specs/02-dominio/ejemplos/`.

### CA-30 Firma digital
- **Reglas:** R-51 · **API:** `POST /comprobantes/{id}/emitir`
- **Dado** un certificado de prueba vigente
- **Cuando** se emite
- **Entonces** el XML contiene `ds:Signature` en `ext:UBLExtensions`, la firma verifica y `firma.hash` es su `DigestValue`; con un certificado vencido responde `422` sin consumir correlativo.

### CA-31 Empaquetado y envío al OSE
- **Reglas:** R-52, R-53 · **API:** `POST /comprobantes/{id}/emitir` (OSE simulado)
- **Dado** un OSE simulado que responde CDR con código 0
- **Cuando** se emite la factura
- **Entonces** se envió `20600123450-01-F001-1.zip` y el estado final es `ACEPTADO` con el CDR guardado.

### CA-32 OSE no disponible
- **Reglas:** R-53, R-05 · **API:** `POST /comprobantes/{id}/emitir`, `POST /comprobantes/reenviar-pendientes`
- **Dado** un OSE simulado que no responde
- **Cuando** se emite
- **Entonces** responde `202`, estado `PENDIENTE_ENVIO`; al recuperar el OSE, el reenvío lo deja `ACEPTADO` con el mismo correlativo.

### CA-33 CDR de rechazo
- **Reglas:** R-53 · **API:** `POST /comprobantes/{id}/emitir`
- **Dado** un OSE simulado que rechaza con un código de error
- **Cuando** se emite
- **Entonces** estado `RECHAZADO`, `respuestaSunat.codigoRespuesta` con el código y **no** se descuenta stock.

## G. Migración del legado

### CA-34 Simulación de migración con la muestra
- **Reglas:** M-01, M-02, M-03, M-04, M-05, M-06, M-07 · **API:** `POST /migraciones?simulacion=true`
- **Dado** `docs/legado/legado-almacen-muestra.csv`
- **Cuando** se ejecuta la simulación
- **Entonces** el resultado es: leídos 15, migrados 10, cuarentena 4 (ids 7, 13, 14, 15), descartados 1 (id 11); no se escribió nada.

### CA-35 Trazabilidad fila a fila
- **Reglas:** M-07 · **API:** `GET /migraciones/{id}/trazabilidad`
- **Dado** una migración completada
- **Cuando** se consulta la trazabilidad
- **Entonces** cada `id` del CSV aparece exactamente una vez, con sus reglas aplicadas e ids nuevos.

### CA-36 Reversión
- **Reglas:** M-07 · **API:** `POST /migraciones/{id}/revertir`
- **Dado** una migración completada y una factura emitida después por el sistema
- **Cuando** se revierte la migración
- **Entonces** desaparecen solo los registros con `origen = MIGRACION`; la factura sigue intacta.

### CA-37 Saldos cuadran tras migrar
- **Reglas:** M-02, M-05, M-07 · **API:** `GET /inventario/kardex`
- **Dado** la migración de la muestra
- **Cuando** se consulta el kardex de ARROZ COSTENO 5KG
- **Entonces** saldo = Σ ingresos − Σ salidas de sus filas migradas (100 − 10 − 2 = 88), sin contar la cuarentena.
