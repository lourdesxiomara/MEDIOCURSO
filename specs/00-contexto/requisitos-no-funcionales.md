# Requisitos no funcionales (medibles)

| ID | Atributo | Requisito | Cómo se verifica |
|---|---|---|---|
| RNF-01 | Disponibilidad offline | Se puede crear, firmar y guardar comprobantes sin internet; quedan `PENDIENTE_ENVIO` y se reenvían solos (CU-11, ADR-004) | CA-32 |
| RNF-02 | Rendimiento | Validar y calcular un comprobante de 50 líneas en < 300 ms en el equipo mínimo | Prueba de carga |
| RNF-03 | Rendimiento | Generar + firmar el XML en < 1 s (p95), sin contar la respuesta del OSE | Prueba de carga |
| RNF-04 | Conservación legal | XML firmado y CDR se guardan íntegros, con hash, durante el plazo de prescripción tributaria | Auditoría de la BD |
| RNF-05 | Seguridad | Certificado digital (.pfx) en el almacén seguro del SO (Windows) / Android Keystore; nunca en el instalador ni en texto plano | Revisión de ADR-002 |
| RNF-06 | Seguridad | Acceso por roles (Vendedor, Almacenero, Contador, Administrador); anular y migrar solo Administrador | OpenAPI `security` |
| RNF-07 | Auditoría | Todo cambio de estado de un comprobante queda registrado con usuario, fecha y origen | Prueba de integración |
| RNF-08 | Portabilidad | Mismo dominio en Windows (MSI) y Android (APK); resultados de cálculo idénticos en ambos | Pruebas del módulo `dominio` en ambas plataformas |
| RNF-09 | Mantenibilidad | `dominio` sin dependencias técnicas, verificado por prueba de arquitectura (ADR-001) | ArchUnit/Konsist |
| RNF-10 | Exactitud | Montos con decimal exacto, nunca `float`; redondeo half-up por línea (R-28) | CA-20 |
| RNF-11 | Usabilidad | Emitir una boleta de 3 ítems en < 60 s; errores con mensaje y campo exactos | Prueba con usuarios |
| RNF-12 | Localización | Español (Perú), zona America/Lima, moneda PEN por defecto | Revisión |
