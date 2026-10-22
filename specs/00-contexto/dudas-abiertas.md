# Dudas abiertas

Puntos que **no** se pudieron verificar en fuente oficial o que dependen de una decisión de gerencia.
Ningún agente debe resolverlos inventando: se responden aquí y se registra la fuente.

| ID | Duda | Impacto | Estado |
|---|---|---|---|
| D-01 | Tasa ICBPER vigente en la fecha de emisión. Se asumió S/ 0.50 por bolsa (tramo final de la Ley 30884 desde 2023). | Cálculo de ICBPER | Parametrizado en `configuracion.tasaIcbper`; confirmar |
| D-02 | Lista completa y vigente del catálogo 51. `docs/sunat/catalogos/cat51.json` contiene solo el subconjunto aplicable a abarrotes. | Tipos de operación | Confirmar con Anexo 8 vigente en cpe.sunat.gob.pe |
| D-03 | Proveedor OSE y su contrato técnico (SOAP `billService` estándar o API REST propia). | Adaptador de envío | Pendiente gerencia |
| D-04 | ¿El emisor opera en la Amazonía (Ley 27037)? Cambia afectación IGV (`20`) y leyenda `2001`. | Cálculo y leyendas | Pendiente gerencia (ver ADR-005) |
| D-05 | ¿Productos sujetos a ISC (bebidas alcohólicas, cigarrillos)? Define qué sistema del catálogo 08 se usa. | ISC | Pendiente inventario de productos |
| D-06 | ¿El legado tiene precios? La muestra no tiene precios ni clientes. | Migración | Pendiente revisar BD real |
| D-07 | Códigos de error del CDR a mapear (lista oficial de excepciones SUNAT). | Contrato de errores API | Se modelan genéricamente (`codigoSunat`, `descripcion`) |
| D-08 | Base de datos: una por dispositivo (SQLite) o central compartida entre Windows y Android. | Arquitectura de datos | Propuesta en ADR-003 |
| D-09 | ¿Se puede reutilizar el correlativo de un comprobante rechazado por el OSE/SUNAT? | Asignación de correlativos (R-53) | Verificar en manual del programador SEE |
| D-10 | ¿El precio unitario con impuestos (cat. 16 = 01) de una bolsa plástica debe incluir el ICBPER? En los ejemplos se excluye y el ICBPER se totaliza aparte. | `PricingReference` de bolsas | Verificar en guía XML vigente |
