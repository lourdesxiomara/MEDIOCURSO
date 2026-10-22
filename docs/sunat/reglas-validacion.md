# Reglas de validación de emisión

Cada regla tiene un ID (`R-xx`) que se referencia desde los JSON Schema (`description`),
la matriz de trazabilidad y los errores de la API.
**Tipo:** *E* = estructural (la valida el schema) · *N* = de negocio (la valida el dominio) · *X* = externa (OSE/SUNAT).

## Identificación del comprobante
| ID | Regla | Tipo | Fuente |
|---|---|---|---|
| R-01 | `tipoComprobante` ∈ {01, 03, 07, 08} | E | Cat. 01 |
| R-02 | Serie de factura: `^F[A-Z0-9]{3}$`; boleta: `^B[A-Z0-9]{3}$` | E/N | Anexo 1 y 2 |
| R-03 | Correlativo: entero 1–99999999, único por (tipo, serie); asignado por el sistema, nunca por el usuario | N | Anexo 1 |
| R-04 | Nota de crédito/débito: serie con la misma letra inicial que el comprobante que modifica | N | Anexos 3 y 4 |
| R-05 | `fechaEmision` no posterior a hoy; plazo máximo de envío según normativa vigente | N/X | RS 097-2012 |

## Partes
| ID | Regla | Tipo | Fuente |
|---|---|---|---|
| R-10 | RUC: 11 dígitos, prefijo 10, 15, 16, 17 o 20, dígito verificador módulo 11 | E/N | Cat. 06 |
| R-11 | Factura: adquirente obligatoriamente con RUC (`tipoDocumento` = 6) salvo exportación | N | Anexo 1 |
| R-12 | Boleta: adquirente con DNI (8 dígitos) u otro doc. del cat. 06; identificación obligatoria cuando el importe supera el umbral fijado por SUNAT | N | Anexo 2 |
| R-13 | Estado y condición del RUC del adquirente (activo/habido) | X | Padrón SUNAT |

**Dígito verificador RUC (R-10):** pesos `5,4,3,2,7,6,5,4,3,2` sobre los 10 primeros dígitos;
`resto = suma mod 11`; `dv = 11 − resto`; si `dv = 10 → 0`, si `dv = 11 → 1`.

## Ítems y tributos
| ID | Regla | Tipo | Fuente |
|---|---|---|---|
| R-20 | `unidadMedida` ∈ cat. 03 | E | Cat. 03 |
| R-21 | `afectacionIgv` ∈ cat. 07 | E | Cat. 07 |
| R-22 | Afectación 10–17 → tributo 1000 (IGV), categoría S, tasa 18 % | N | Cat. 05/07 |
| R-23 | Afectación 20–21 → tributo 9997, categoría E, IGV 0; 30–36 → 9998, O; 40 → 9995, G | N | Cat. 05/07 |
| R-24 | Si el producto está sujeto a ISC: `sistemaIsc` ∈ cat. 08 obligatorio y tributo 2000 (EXC) | N | Cat. 08 |
| R-25 | ISC se calcula antes que el IGV y **forma parte de la base imponible del IGV** | N | TUO IGV e ISC |
| R-26 | ICBPER: `cantidadBolsas` entero ≥ 1, monto = cantidadBolsas × tasa vigente (D-01); no integra base del IGV | N | Ley 30884, Anexo 1 |
| R-27 | `precioTipo` ∈ cat. 16; operaciones gratuitas usan `02` y leyenda 1002 | N | Cat. 16/52 |
| R-28 | Redondeo a 2 decimales, half-up, por línea; totales = suma de líneas redondeadas | N | Anexo 1 |

## Totales y leyendas
| ID | Regla | Tipo | Fuente |
|---|---|---|---|
| R-30 | `valorVenta` = Σ valorVenta de ítems gravados + exonerados + inafectos − descuentos que afectan base | N | Anexo 1 |
| R-31 | `importeTotal` = valorVenta + IGV + ISC + ICBPER + otros cargos − descuentos globales que no afectan base − anticipos | N | Anexo 1 |
| R-32 | Leyenda 1000 (monto en letras) obligatoria | N | Cat. 52 |
| R-33 | `moneda` ∈ cat. 02 y todas las líneas en la misma moneda | E/N | Cat. 02 |
| R-34 | `tipoOperacion` ∈ cat. 51 (solo factura y boleta) | E | Cat. 51 |

## Notas de crédito / débito
| ID | Regla | Tipo | Fuente |
|---|---|---|---|
| R-40 | `motivo` ∈ cat. 09 (NC) o cat. 10 (ND), con sustento en texto | E | Cat. 09/10 |
| R-41 | `documentoAfectado` debe existir, estar aceptado por SUNAT/OSE y ser del mismo emisor | N | Anexos 3/4 |
| R-42 | NC: importe ≤ saldo del comprobante afectado | N | Anexo 3 |

## Firma, envío y respuesta
| ID | Regla | Tipo | Fuente |
|---|---|---|---|
| R-50 | XML válido contra XSD UBL 2.1 antes de firmar | E | OASIS UBL 2.1 |
| R-51 | Firma XMLDSig enveloped en `ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent` con certificado digital vigente | X | RS 097-2012 |
| R-52 | Envío al OSE/SUNAT como ZIP `RUC-TIPO-SERIE-CORRELATIVO.zip` | X | Manual del programador SEE |
| R-53 | Un comprobante solo pasa a `ACEPTADO` con CDR. El tratamiento del correlativo de un comprobante `RECHAZADO` queda pendiente (duda D-09) | N/X | RS 097-2012 |
