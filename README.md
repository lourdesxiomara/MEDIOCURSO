# ABC Software Corp · Facturación Electrónica SUNAT (UBL 2.1)

**Fase 1 – Spec-First.** Este repositorio contiene las especificaciones técnicas que se definen *antes*
de escribir una sola línea de lógica de negocio. Examen de medio curso de Arquitectura de Software,
UNAS – Facultad de Ingeniería en Informática y Sistemas.

| | |
|---|---|
| **Alumna** | Lourdes Xiomara López Gonzalez |
| **Grupo** | "A" |
| **Curso** | Arquitectura de Software – Examen de medio curso |
| **Universidad** | Universidad Nacional Agraria de la Selva |
| **Fecha** | 19 de octubre de 2026 |

## Entregables
| # | Entregable solicitado | Dónde está |
|---|---|---|
| 1 | **Modelo de dominio y contratos (DTOs / Schemas)** | [`specs/02-dominio/modelo-dominio.md`](specs/02-dominio/modelo-dominio.md) · [`schemas/`](specs/02-dominio/schemas) (11 JSON Schema 2020-12) · [`ejemplos/`](specs/02-dominio/ejemplos) (JSON + XML UBL 2.1 validados) |
| 2 | **Diagramas de arquitectura MVC con visión a Hexagonal** | [`specs/03-arquitectura/arquitectura.md`](specs/03-arquitectura/arquitectura.md) · decisiones en [`specs/adr/`](specs/adr) |
| 3 | **Especificación de endpoints / servicios (contratos API)** | [`specs/04-api/openapi.yaml`](specs/04-api/openapi.yaml) (OpenAPI 3.1) · [`puertos-salida.md`](specs/04-api/puertos-salida.md) |
| 4 | **Matriz de trazabilidad normativa SUNAT ↔ UBL** | [`specs/05-trazabilidad/matriz.md`](specs/05-trazabilidad/matriz.md) · [`matriz.csv`](specs/05-trazabilidad/matriz.csv) (52 filas) |

Requisitos del caso que también se cubren:
| Requisito | Dónde |
|---|---|
| Casos de uso (benchmark Nubefact) | [`specs/01-casos-uso/`](specs/01-casos-uso/casos-uso.md) · [`docs/benchmark/`](docs/benchmark/nubefact.md) |
| Legado y migración de datos con trazabilidad | [`specs/06-migracion/`](specs/06-migracion/migracion.md) · [`docs/legado/`](docs/legado) |
| Normativa SUNAT, catálogos (incl. **catálogo 08**) y reglas | [`docs/sunat/`](docs/sunat) |
| Estándar UBL 2.1 (`UBL-Invoice-2.1.xsd`) | [`docs/ubl/`](docs/ubl) |
| Distribución Windows **MSI** + Android **APK** | [`specs/adr/ADR-002-stack-y-distribucion-msi-apk.md`](specs/adr/ADR-002-stack-y-distribucion-msi-apk.md) |
| **Criterios de aceptación** (37, cubren todas las reglas) | [`specs/07-aceptacion/`](specs/07-aceptacion/criterios-aceptacion.md) |
| Contratos de eventos (microservicios) | [`specs/04-api/eventos.md`](specs/04-api/eventos.md) |
| Requisitos no funcionales | [`specs/00-contexto/requisitos-no-funcionales.md`](specs/00-contexto/requisitos-no-funcionales.md) |
| Contexto, supuestos, glosario y dudas abiertas | [`specs/00-contexto/`](specs/00-contexto) |

## Cómo verificar que todo es consistente
```bash
python -m pip install -r tools/requirements.txt
python tools/verificar.py                 # 13 comprobaciones; debe terminar en "TODO CORRECTO"

cd tools && npm install
npm run mermaid                           # parsea los diagramas con el parser oficial de Mermaid
npm run openapi                           # lint del contrato con Redocly
```
`verificar.py` comprueba, entre otras cosas, que los XML de ejemplo validan contra el XSD UBL 2.1,
que los cálculos de IGV/ISC/ICBPER de los ejemplos son correctos, que cada fila de la matriz apunta a
un campo real del schema y a un nodo real del XML, y que los enums de los schemas coinciden con los
catálogos SUNAT.

## Trabajar con Claude en este repo
El agente lee [`CLAUDE.md`](CLAUDE.md) automáticamente: reglas Spec-First, mapa del repo y verificación
obligatoria antes de cada commit.
