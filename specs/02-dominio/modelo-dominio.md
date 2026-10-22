# 02 · Modelo de dominio y contratos de datos

## 1. Agregados y responsabilidades
| Agregado / entidad | Responsabilidad | Invariantes principales |
|---|---|---|
| **Comprobante** (raíz) | Ciclo de vida de factura, boleta, NC y ND | Correlativo único por serie (R-03); totales = Σ líneas (R-30, R-31); transición de estados válida |
| LineaComprobante | Ítem vendido con sus tributos | Afectación ↔ tributo coherente (R-22, R-23); ISC antes que IGV (R-25) |
| Tributo (VO) | IGV, ISC, ICBPER, EXO, INA, EXP | Código ∈ cat. 05; ISC exige sistema cat. 08 |
| Emisor | Datos del contribuyente y su configuración | RUC válido (R-10) |
| Cliente | Adquirente | Doc. identidad coherente con el tipo de comprobante (R-11, R-12) |
| Producto | Maestro y configuración tributaria | Afectación ∈ cat. 07; si ISC → parámetros según cat. 08 |
| Serie | Numeración por tipo de comprobante | Formato `F###` / `B###`; correlativo monotónico |
| MovimientoInventario | Registro Formato 12.1 | Toda salida por venta referencia un comprobante |
| Migracion | Importación del legado | Toda fila legada termina en MIGRADO, CUARENTENA o DESCARTADO |

**Value objects:** `Ruc`, `NumeroComprobante`, `Monto` (decimal exacto, nunca float), `Cantidad`,
`CodigoCatalogo<N>`, `DocumentoIdentidad`, `Leyenda`.

## 2. Diagrama de clases
```mermaid
classDiagram
  direction LR
  class Comprobante {
    +UUID id
    +TipoComprobante tipo
    +Serie serie
    +int correlativo
    +TipoOperacion cat51
    +EstadoComprobante estado
    +Date fechaEmision
    +Moneda moneda
    +Totales totales
    +Leyenda[] leyendas
    +validar()
    +calcularTotales()
    +emitir(firmador, canal)
    +anular()
  }
  class LineaComprobante {
    +int numero
    +Cantidad cantidad
    +Monto valorUnitario
    +Monto precioUnitario
    +AfectacionIgv cat07
    +Monto valorVenta
    +calcularTributos(tasas)
  }
  class Tributo {
    <<value object>>
    +CodigoTributo cat05
    +Monto baseImponible
    +Porcentaje porcentaje
    +Monto monto
    +SistemaIsc cat08
  }
  class NotaCredito { +MotivoNC cat09 +String sustento }
  class NotaDebito { +MotivoND cat10 +String sustento }
  class Emisor { +Ruc ruc +String razonSocial +Direccion domicilioFiscal +bool amazonia }
  class Cliente { +DocumentoIdentidad documento +String nombre }
  class Producto { +String codigo +UnidadMedida cat03 +AfectacionIgv cat07 +ConfigIsc isc +bool esBolsaPlastica }
  class ConfigIsc { +SistemaIsc cat08 +Porcentaje tasa +Monto montoFijo +Monto precioVentaPublico }
  class Serie { +String codigo +TipoComprobante tipo +int ultimoCorrelativo +siguiente() }
  class RespuestaSunat { +String codigo +String descripcion +String[] observaciones +bytes cdrZip }
  class MovimientoInventario { +Date fecha +TipoMovimiento tipo +Cantidad cantidad +DocumentoSustento doc +String idLegado }

  Comprobante "1" *-- "1..*" LineaComprobante
  LineaComprobante "1" *-- "1..*" Tributo
  Comprobante <|-- NotaCredito
  Comprobante <|-- NotaDebito
  NotaCredito --> Comprobante : documentoAfectado
  NotaDebito --> Comprobante : documentoAfectado
  Comprobante --> Emisor
  Comprobante --> Cliente
  Comprobante --> Serie
  Comprobante --> "0..1" RespuestaSunat
  LineaComprobante --> Producto
  Producto *-- "0..1" ConfigIsc
  MovimientoInventario --> Producto
  MovimientoInventario --> "0..1" Comprobante : sustento
```

## 3. Algoritmo de cálculo por línea (CU-15)
Entrada: `cantidad`, `precioUnitario` (con impuestos, cat. 16 = 01), producto (afectación, ISC, bolsa).

1. Si afectación ∈ 10–17 y **sin ISC**: `valorUnitario = precioUnitario / 1.18`.
2. Si afectación ∈ 10–17 **con ISC sistema 01**: `valorUnitario = precioUnitario / ((1 + tasaIsc) × 1.18)`.
   Para sistemas 02 y 03 se despeja según la fórmula de `docs/sunat/catalogos/cat08.json`.
3. Si afectación ∈ 20–40: `valorUnitario = precioUnitario` (no hay IGV).
4. `valorVenta = round2(cantidad × valorUnitario − descuento)`.
5. `isc = round2(fórmula cat. 08)`.
6. `igv = round2((valorVenta + isc) × 0.18)` solo si afectación gravada (R-25).
7. `icbper = cantidadBolsas × tasaIcbper` si el producto es bolsa (R-26, D-01).

Ejemplo verificado (`ejemplos/comprobante.factura.json`, línea 2, cerveza):
precio 7.08 → valor 7.08 / (1.20 × 1.18) = 5.00 · valorVenta 60.00 · ISC 12.00 · IGV (60 + 12) × 18 % = 12.96.
El precio unitario mostrado incluye IGV e ISC; el ICBPER se totaliza aparte (duda D-10).

## 4. Contratos de datos (JSON Schema 2020-12)
| Schema | Uso | Casos de uso |
|---|---|---|
| `schemas/comun.schema.json` | Tipos y catálogos (`$defs`) | Todos |
| `schemas/emisor.schema.json` | Emisor | CU-10 |
| `schemas/cliente.schema.json` | Adquirente | CU-01 |
| `schemas/producto.schema.json` | Producto + configuración tributaria | CU-02 |
| `schemas/comprobante-crear.schema.json` | **Request** crear factura/boleta | CU-03, CU-04 |
| `schemas/nota-crear.schema.json` | **Request** nota de crédito/débito | CU-05, CU-06 |
| `schemas/comprobante.schema.json` | **Response** comprobante calculado + estado + CDR | CU-03…CU-08 |
| `schemas/movimiento-inventario.schema.json` | Movimiento Formato 12.1 | CU-14 |
| `schemas/registro-legado.schema.json` | Fila del legado | CU-13 |
| `schemas/migracion.schema.json` | Resultado de migración | CU-13 |
| `schemas/error.schema.json` | Error RFC 9457 con ID de regla | Todos |

Decisión clave: **el request no trae correlativo ni totales**. Los calcula el dominio, así el cliente
(Windows, Android o un microservicio futuro) no puede enviar montos inconsistentes.

## 5. Ejemplos
| Archivo | Valida contra |
|---|---|
| `ejemplos/comprobante-crear.factura.json` | `comprobante-crear.schema.json` |
| `ejemplos/comprobante.factura.json` | `comprobante.schema.json` |
| `ejemplos/factura-F001-1.sin-firma.xml` | XSD UBL 2.1 Invoice |
| `ejemplos/nota-crear.credito.json` | `nota-crear.schema.json` |
| `ejemplos/comprobante.nota-credito.json` | `comprobante.schema.json` |
| `ejemplos/nota-credito-FC01-1.sin-firma.xml` | XSD UBL 2.1 CreditNote |
| `ejemplos/producto-cerveza.json` | `producto.schema.json` |
| `ejemplos/movimiento-inventario.salida.json` | `movimiento-inventario.schema.json` |
| `ejemplos/error.validacion.json` | `error.schema.json` |
