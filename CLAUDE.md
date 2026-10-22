# CLAUDE.md — ABC Software Corp · Facturación Electrónica SUNAT (UBL 2.1)

Este archivo lo lee automáticamente cualquier agente de Claude que trabaje en este repo.
Léelo completo antes de cualquier tarea.

## 1. Metodología: SPEC-FIRST (fase actual)
- **PROHIBIDO escribir lógica de negocio** en esta fase. Solo especificaciones: reglas, contratos de
  datos (JSON Schema), contratos de interfaz (OpenAPI / puertos), diagramas, matrices y ADRs.
- No modificar los XSD oficiales de OASIS (`docs/ubl/common`, `docs/ubl/maindoc`).
- Antes de cada tarea: proponer un plan corto y esperar aprobación del usuario.
- Toda afirmación normativa cita su fuente (catálogo, XPath UBL, resolución). Ver `docs/sunat/fuentes.md`.
- Si algo no se puede verificar en una fuente oficial → `specs/00-contexto/dudas-abiertas.md`. **No inventar.**
- Un commit por paso, con mensaje descriptivo. Rama de trabajo: `main`.

## 2. Contexto del caso (resumen)
- Cliente: ABC Software Corp, mayorista/minorista de abarrotes y mercadería.
- Legado: registro de almacén con `fecha, ingreso, salida, producto, nro_documento` (informal).
- Objetivo: emitir comprobantes electrónicos (factura, boleta, notas de crédito/débito) en **UBL 2.1**,
  validados, firmados (XMLDSig) y enviados a un **OSE o a SUNAT**, recibiendo el **CDR**.
- Normativa: RS 097-2012/SUNAT (SEE desde los sistemas del contribuyente, Anexo 8 = catálogos),
  RS 234-2006/SUNAT (libros y registros: Inventario Permanente Formato 12.1/13.1).
- Arquitectura: **monolito MVC limpio** hoy, diseñado con **puertos y adaptadores** para migrar a
  **Hexagonal/Clean** y después a microservicios.
- Plataformas: **Windows (instalador MSI)** y **Android (APK)**, ejecución nativa.

## 3. Mapa del repositorio
| Ruta | Contenido |
|---|---|
| `docs/ubl/` | XSD oficiales OASIS UBL 2.1 + `soporte/` (CCTS, XMLDSig, XAdES) |
| `docs/sunat/` | Catálogos SUNAT en JSON, reglas de validación, fuentes |
| `docs/legado/` | Muestra de datos del sistema legado y su descripción |
| `docs/benchmark/` | Análisis de Nubefact (casos de uso de referencia) |
| `specs/00-contexto/` | Caso, alcance, supuestos, glosario, dudas abiertas |
| `specs/01-casos-uso/` | Casos de uso |
| `specs/02-dominio/` | Modelo de dominio, `schemas/` (JSON Schema), `ejemplos/` (JSON y XML UBL) |
| `specs/03-arquitectura/` | Diagramas MVC → Hexagonal → Microservicios |
| `specs/04-api/` | `openapi.yaml` + contratos de puertos de salida (OSE/SUNAT, firma) |
| `specs/05-trazabilidad/` | Matriz SUNAT ↔ UBL ↔ Dominio ↔ Legado |
| `specs/06-migracion/` | Mapeo y plan de migración del legado |
| `specs/adr/` | Decisiones de arquitectura (ADR) |
| `tools/` | Envoltorios XSD y scripts de verificación |

## 4. Convenciones
- Idioma de documentos: español. Identificadores de schemas/API: `camelCase` en español sin tildes.
- Montos: string decimal con 2 decimales en contratos (`"118.00"`), nunca `float`.
- Fechas: ISO 8601 (`YYYY-MM-DD`), horas `HH:mm:ss`, zona `America/Lima`.
- Códigos de catálogo: siempre como string (`"01"`, `"1000"`), nunca número.
- Diagramas: Mermaid dentro de Markdown.

## 5. Verificación obligatoria (antes de cada commit)
```bash
python -m pip install -r tools/requirements.txt   # una sola vez
python tools/verificar.py                         # debe terminar en "TODO CORRECTO"
cd tools && npm install && npm run mermaid && npm run openapi
```
Comprueba: JSON Schemas válidos, ejemplos válidos contra sus schemas, enums de schemas == catálogos,
cálculos de tributos de los ejemplos, XML de ejemplo válidos contra XSD UBL 2.1 y coherentes con su JSON,
OpenAPI con `$ref` resueltos y rutas citadas en casos de uso, matriz de trazabilidad (schema + XPath +
reglas + catálogos), cobertura de la migración, referencias cruzadas, diagramas Mermaid y que los XSD
oficiales sigan intactos.

**Si cambias la matriz:** edita `matriz.csv` y ejecuta `python tools/generar_matriz_md.py`.
**Si cambias un catálogo:** actualiza también el `enum` correspondiente en `comun.schema.json`
(el verificador fallará hasta que coincidan).
