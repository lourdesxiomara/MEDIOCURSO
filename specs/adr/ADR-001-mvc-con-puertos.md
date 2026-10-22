# ADR-001 · Monolito MVC con puertos y adaptadores

- **Estado:** Aceptado (fase Spec-First)
- **Contexto:** La gerencia exige arrancar con un monolito MVC limpio, pero que permita migrar a
  Hexagonal/Clean y luego a microservicios sin reescritura.
- **Decisión:**
  1. El *Modelo* del MVC se divide en tres capas: dominio puro, servicios de aplicación y adaptadores.
  2. Cada servicio de aplicación implementa una **interfaz de puerto de entrada** (`EmitirComprobante`, …).
  3. Toda dependencia técnica (BD, XML, firma, OSE, correo, reloj) se accede por un **puerto de salida**
     (`specs/04-api/puertos-salida.md`).
  4. Los Controllers solo traducen eventos de la Vista a DTOs (`specs/02-dominio/schemas`) y llaman a puertos.
  5. Regla de dependencias verificada por prueba de arquitectura: `dominio` no depende de nada.
- **Consecuencias:**
  - (+) Migrar a Hexagonal es renombrar capas, no reescribir: ver tabla en `specs/03-arquitectura` §4.
  - (+) El dominio (cálculo de tributos, reglas R-xx) se prueba sin BD ni red.
  - (+) Cambiar de OSE o de BD = escribir otro adaptador.
  - (−) Algo más de código inicial (interfaces) que un MVC "plano".
- **Alternativas descartadas:** MVC con lógica en Controllers (bloquea la migración); Hexagonal pleno
  desde el día uno (contradice la condición de la gerencia).
