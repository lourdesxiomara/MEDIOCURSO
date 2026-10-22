# ADR-003 · Persistencia

- **Estado:** Propuesto (duda D-08)
- **Contexto:** El monolito corre en Windows y Android. Los correlativos deben ser únicos por serie (R-03)
  aunque haya varios dispositivos emitiendo.
- **Decisión propuesta:**
  1. Base de datos local **SQLite** en cada dispositivo, accedida solo por el puerto `RepositorioComprobantes`.
  2. **Cada dispositivo tiene sus propias series** (ej. Windows mostrador `F001`/`B001`, Android ruta `F002`/`B002`).
     Así los correlativos nunca colisionan sin necesidad de un servidor central.
  3. El XML firmado y el CDR se guardan íntegros (son documentos legales) junto con su hash.
  4. Cuando exista un servidor central (fase microservicios), se agrega un adaptador PostgreSQL
     y sincronización; el dominio no cambia.
- **Consecuencias:** (+) Funciona sin conexión permanente y sin infraestructura nueva.
  (−) Reportes consolidados requieren exportar/sincronizar hasta que exista el servidor central.
