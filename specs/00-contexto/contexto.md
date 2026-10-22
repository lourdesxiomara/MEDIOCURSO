# 00 · Contexto, alcance y supuestos

## 1. Problema
ABC Software Corp vende abarrotes al por mayor y menor. Su software actual solo registra movimientos
de almacén (`fecha, ingreso, salida, producto, nro_documento`) y:

| Brecha | Consecuencia |
|---|---|
| No valida RUC | Comprobantes rechazados por SUNAT/OSE |
| No calcula IGV, ISC, ICBPER | Montos incorrectos, multas |
| No genera XML UBL 2.1 | No puede emitir comprobantes electrónicos |
| No firma digitalmente | El XML no tiene validez legal |
| No se comunica con OSE/SUNAT | No obtiene CDR (constancia de recepción) |
| `nro_documento` informal | No hay series ni correlativos formales |

## 2. Marco normativo
| Norma | Qué aporta al sistema |
|---|---|
| **RS 097-2012/SUNAT** | Crea el *SEE – Del Contribuyente* (emisión desde sistemas propios). Sus anexos definen campos obligatorios por comprobante (Anexos 1–4) y el **Anexo 8: catálogos**. |
| **RS 234-2006/SUNAT** | Libros y registros. El legado es en la práctica un **Registro de Inventario Permanente en Unidades Físicas (Formato 12.1)**: entradas, salidas y saldo por existencia, con el documento que sustenta cada movimiento. |
| **RS 117-2017/SUNAT** | Operador de Servicios Electrónicos (OSE). Ver duda D-03. |
| **Ley 30884** | ICBPER (impuesto al consumo de bolsas plásticas), tributo 7152. |
| **Ley 27037** | Exoneración de IGV en la Amazonía (relevante si el emisor opera en región selva). Ver ADR-005. |
| **OASIS UBL 2.1** | Estándar XML del comprobante (`UBL-Invoice-2.1.xsd`, `CreditNote`, `DebitNote`). |

Detalle y enlaces: `docs/sunat/fuentes.md`.

## 3. Alcance de la fase Spec-First
**Incluye:** reglas, catálogos, modelo de dominio, DTOs (JSON Schema), contratos API (OpenAPI 3.1),
contratos de puertos de salida, diagramas MVC→Hexagonal, matriz de trazabilidad, plan de migración,
decisiones de arquitectura y estrategia de distribución MSI/APK.

**No incluye:** código de negocio, firma real con certificado, envío real a OSE/SUNAT.

## 4. Comprobantes en alcance
| Código cat. 01 | Comprobante | Documento UBL | Serie |
|---|---|---|---|
| 01 | Factura | `Invoice` | `F` + 3 alfanuméricos (F001) |
| 03 | Boleta de venta | `Invoice` | `B` + 3 alfanuméricos (B001) |
| 07 | Nota de crédito | `CreditNote` | Serie del comprobante que modifica |
| 08 | Nota de débito | `DebitNote` | Serie del comprobante que modifica |

## 5. Supuestos (a confirmar con gerencia)
- S-01 El emisor es una sola empresa con un RUC.
- S-02 Moneda principal PEN; se permite USD.
- S-03 Venta interna (catálogo 51 = `0101`) es el caso dominante; no hay exportación.
- S-04 El precio de lista de los productos incluye IGV (venta minorista); el sistema descompone valor + IGV.
- S-05 El legado está en un archivo/BD exportable a CSV (`docs/legado/`).
- S-06 Se usará un OSE (proveedor por definir) como canal principal y SUNAT directo como alternativa.
