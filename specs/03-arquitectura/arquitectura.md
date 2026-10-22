# 03 · Arquitectura: MVC monolítico con visión Hexagonal

## 1. Principio rector
El sistema se construye como **un monolito MVC**, pero el código se separa desde el día uno en
**núcleo (dominio + casos de uso)** y **detalles técnicos (UI, BD, XML, firma, OSE)**, comunicados por
**interfaces (puertos)**. Así:

- Hoy: el *Controlador* del MVC llama a un *Servicio de aplicación*; la *Vista* es Compose (Windows/Android).
- Mañana: ese mismo servicio es un **puerto de entrada** hexagonal y cada dependencia técnica es un **adaptador**.
- Después: cada grupo de puertos puede separarse en un **microservicio** sin reescribir el dominio.

La regla que lo hace posible (y que se verifica en revisión de código): **las dependencias apuntan hacia
el dominio**. El dominio no importa nada de UI, BD, HTTP, XML ni firma.

## 2. Contexto (C4 nivel 1)
```mermaid
flowchart TB
  vend([Vendedor / Almacenero / Admin / Contador])
  subgraph ABC[Sistema de facturación ABC · monolito]
    app[App Windows MSI / Android APK]
  end
  ose[[OSE · Operador de Servicios Electrónicos]]
  sunat[[SUNAT · SEE / consulta CPE]]
  padron[[Padrón RUC]]
  correo[[Servidor de correo]]
  legado[(Sistema legado de almacén)]
  vend --> app
  app -- XML UBL 2.1 firmado / CDR --> ose
  app -. canal alternativo .-> sunat
  app -. consulta RUC .-> padron
  app -- PDF + XML --> correo
  legado -- exportación CSV --> app
```

## 3. Vista MVC actual (monolito)
```mermaid
flowchart LR
  subgraph V[Vista · Compose Multiplatform]
    VF[PantallaFactura]
    VN[PantallaNota]
    VC[PantallaConsulta]
    VI[PantallaInventario]
    VM[PantallaMigracion]
  end
  subgraph C[Controlador]
    CC[ComprobanteController]
    IC[InventarioController]
    MC[MigracionController]
    CFG[ConfiguracionController]
  end
  subgraph M[Modelo]
    direction TB
    subgraph APP[Servicios de aplicación = futuros puertos de entrada]
      S1[EmitirComprobanteService]
      S2[EmitirNotaService]
      S3[ConsultarComprobanteService]
      S4[RegistrarMovimientoService]
      S5[MigrarLegadoService]
    end
    subgraph DOM[Dominio puro]
      D1[Comprobante · Linea · Tributo]
      D2[CalculadoraTributos]
      D3[ValidadorReglas R-xx]
      D4[Producto · Cliente · Serie]
    end
    subgraph INF[Infraestructura = futuros adaptadores]
      R1[(Repositorio SQLite)]
      X1[GeneradorXmlUbl]
      F1[FirmadorXmlDsig]
      O1[ClienteOse SOAP]
      P1[GeneradorPdf]
    end
  end
  VF & VN & VC --> CC
  VI --> IC
  VM --> MC
  CC --> S1 & S2 & S3
  IC --> S4
  MC --> S5
  S1 & S2 & S3 & S4 & S5 --> DOM
  S1 --> R1 & X1 & F1 & O1 & P1
```

## 4. La misma aplicación vista como Hexagonal
```mermaid
flowchart LR
  subgraph AE[Adaptadores de entrada]
    UI[UI Compose · Controllers MVC]
    REST[API REST local · openapi.yaml]
    CLI[Importador CSV legado]
  end
  subgraph NUCLEO[Núcleo]
    subgraph PE[Puertos de entrada]
      P1[EmitirComprobante]
      P2[EmitirNota]
      P3[ConsultarComprobante]
      P4[AnularComprobante]
      P5[RegistrarMovimiento]
      P6[MigrarLegado]
    end
    DOM[Dominio: Comprobante, Tributos, Reglas R-xx]
    subgraph PS[Puertos de salida]
      Q1[RepositorioComprobantes]
      Q2[RepositorioProductos]
      Q3[GeneradorDocumentoUbl]
      Q4[FirmadorDigital]
      Q5[CanalEnvioCpe]
      Q6[ValidadorRuc]
      Q7[Notificador]
      Q8[RelojYNumeracion]
    end
  end
  subgraph AS[Adaptadores de salida]
    A1[(SQLite / PostgreSQL)]
    A2[UBL 2.1 + validación XSD]
    A3[XMLDSig con certificado .pfx]
    A4[OSE SOAP billService]
    A5[SUNAT SEE directo]
    A6[Padrón RUC]
    A7[SMTP]
  end
  UI & REST & CLI --> PE
  PE --> DOM
  PE --> PS
  Q1 & Q2 --> A1
  Q3 --> A2
  Q4 --> A3
  Q5 --> A4
  Q5 -.alternativa.-> A5
  Q6 --> A6
  Q7 --> A7
```

### Correspondencia MVC → Hexagonal (lo que se mantiene y lo que cambia)
| Pieza en el MVC de hoy | Rol en Hexagonal | ¿Cambia al migrar? |
|---|---|---|
| Vista Compose | Adaptador de entrada (UI) | No |
| Controller | Adaptador de entrada (traduce eventos UI → DTO) | No |
| Servicio de aplicación (`EmitirComprobanteService`) | Implementación del puerto de entrada | No; se le extrae la interfaz |
| Dominio (`Comprobante`, `CalculadoraTributos`) | Núcleo | **Nunca** |
| Repositorio, XML, firma, cliente OSE | Adaptadores de salida detrás de interfaces | Solo se cambian implementaciones |
| DTOs (`specs/02-dominio/schemas`) | Contratos de los puertos | No |

## 5. Estructura de módulos (aplicable desde el primer commit de código)
```
abc-facturacion/
├── dominio/            # Kotlin puro. Sin dependencias externas. Entidades, VO, reglas R-xx, cálculo.
├── aplicacion/         # Casos de uso + interfaces de puertos (entrada y salida). Depende solo de dominio.
├── adaptadores/
│   ├── persistencia/   # SQLite (SQLDelight) → implementa RepositorioComprobantes…
│   ├── ubl/            # Generación XML UBL 2.1 + validación XSD (R-50)
│   ├── firma/          # XMLDSig (R-51)
│   ├── envio-ose/      # SOAP sendBill / getStatus → CanalEnvioCpe
│   ├── pdf/            # Representación impresa
│   └── migracion/      # Lector CSV legado + reglas M-xx
├── ui/                 # Compose Multiplatform: Vistas + Controllers (MVC)
├── app-desktop/        # Punto de entrada Windows → instalador MSI
└── app-android/        # Punto de entrada Android → APK
```
Regla de dependencias, verificable con una prueba de arquitectura (ArchUnit/Konsist):
`ui → aplicacion → dominio` y `adaptadores → aplicacion → dominio`. `dominio` no depende de nada.

## 6. Secuencia: emitir factura (CU-03)
```mermaid
sequenceDiagram
  actor V as Vendedor
  participant UI as Vista + Controller
  participant S as EmitirComprobante (puerto)
  participant D as Dominio
  participant R as RepositorioComprobantes
  participant X as GeneradorDocumentoUbl
  participant F as FirmadorDigital
  participant O as CanalEnvioCpe (OSE)
  V->>UI: Completa factura y confirma
  UI->>S: CrearComprobanteRequest
  S->>D: validar(R-01..R-34) y calcularTributos()
  D-->>S: Comprobante VALIDADO + totales
  S->>R: siguienteCorrelativo(serie)
  S->>X: generar(comprobante)
  X-->>S: XML UBL 2.1 (validado contra XSD, R-50)
  S->>F: firmar(xml)
  F-->>S: XML firmado + hash
  S->>R: guardar(FIRMADO)
  S->>O: enviar(zip)
  alt CDR aceptado
    O-->>S: CDR código 0
    S->>R: guardar(ACEPTADO, cdr)
  else OSE no disponible
    O--xS: timeout
    S->>R: guardar(PENDIENTE_ENVIO)
  else CDR rechazado
    O-->>S: CDR con código de error
    S->>R: guardar(RECHAZADO, cdr)
  end
  S-->>UI: Comprobante (comprobante.schema.json)
  UI-->>V: Estado + PDF
```

## 7. Evolución a microservicios (cuando la empresa crezca)
```mermaid
flowchart LR
  GW[API Gateway] --> MS1 & MS2 & MS3 & MS4
  MS1[ms-emision<br/>EmitirComprobante · EmitirNota · Anular]
  MS2[ms-catalogos<br/>Productos · Clientes · Catálogos SUNAT]
  MS3[ms-envio-cpe<br/>Firma · Envío OSE · CDR · Reintentos]
  MS4[ms-inventario<br/>Movimientos · Formato 12.1 · Migración]
  MS1 -- evento ComprobanteFirmado --> BUS{{Bus de eventos}}
  BUS --> MS3
  MS3 -- evento ComprobanteAceptado --> BUS
  BUS --> MS4
```
Cada microservicio es **un grupo de puertos de entrada que ya existe en el monolito**. Las llamadas
en proceso entre servicios se reemplazan por los contratos de `specs/04-api/openapi.yaml` y por eventos.
El dominio y los DTOs no cambian.

## 8. Decisiones relacionadas
ADR-001 (MVC con puertos), ADR-002 (stack multiplataforma), ADR-003 (persistencia),
ADR-004 (canal OSE/SUNAT), ADR-005 (Amazonía) en `specs/adr/`.
