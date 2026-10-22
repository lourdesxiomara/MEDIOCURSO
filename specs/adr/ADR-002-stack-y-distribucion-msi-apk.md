# ADR-002 · Stack multiplataforma y distribución (MSI + APK)

- **Estado:** Propuesto (requiere aprobación de gerencia)
- **Contexto:** La app debe ejecutarse de forma nativa en Windows y Android, empaquetarse como
  **instalador MSI** (escritorio) y **APK** (Android), y compartir un único dominio y reglas tributarias.

## Opciones evaluadas
| Criterio | **Kotlin Multiplatform + Compose Multiplatform** | Tauri 2 (Rust + web) | Flutter | .NET MAUI |
|---|---|---|---|---|
| Windows nativo | Sí (JVM empaquetada) | Sí (WebView2) | Sí | Sí |
| Android nativo | Sí | Sí | Sí | Sí |
| **MSI** | Nativo vía `jpackage` (`TargetFormat.Msi`, requiere WiX) | Nativo vía WiX | No nativo (requiere WiX/herramienta externa) | Por defecto MSIX; MSI requiere proyecto WiX aparte |
| **APK** | Nativo (Gradle) | Nativo | Nativo | Nativo |
| Dominio compartido | Un módulo Kotlin común | Rust compartido; UI web | Dart compartido | C# compartido |
| XML + XSD + XMLDSig | Ecosistema JVM maduro (JAXP, Apache Santuario) | Crates menos maduros | Paquetes limitados | System.Security.Cryptography.Xml |
| Encaje MVC → Hexagonal | Módulos Gradle = capas | Bueno | Bueno | Bueno |

## Decisión propuesta
**Kotlin Multiplatform + Compose Multiplatform**, con la estructura de módulos de
`specs/03-arquitectura` §5:
- `app-desktop` → `./gradlew packageMsi` produce `ABC-Facturacion-x.y.z.msi`.
- `app-android` → `./gradlew assembleRelease` produce `app-release.apk` firmado.

## Requisitos de empaquetado
| Requisito | MSI (Windows) | APK (Android) |
|---|---|---|
| Firma del instalador | Certificado de firma de código (Authenticode) | Keystore de la empresa (apksigner) |
| Versión | `versionName` común; MSI exige formato `MAJOR.MINOR.BUILD` | `versionCode` incremental |
| Actualización | `upgradeUuid` fijo para que el MSI reemplace versiones previas | Misma firma y `applicationId` |
| Datos locales | `%LOCALAPPDATA%\ABC\Facturacion` (no en Program Files) | Almacenamiento interno de la app |
| Certificado digital (.pfx) de facturación | Almacén protegido del usuario; nunca dentro del instalador | Android Keystore; nunca dentro del APK |
| Requisito de build | JDK 17+ y WiX Toolset en la máquina que empaqueta | Android SDK |

## Consecuencias
- (+) Un solo lenguaje para dominio, UI y adaptadores; reglas tributarias idénticas en ambas plataformas.
- (+) MSI y APK salen del mismo build (`./gradlew packageMsi assembleRelease`).
- (−) El MSI incluye un runtime JVM (tamaño mayor que una app nativa C++).
- (−) La firma XMLDSig en Android debe probarse con la librería elegida (riesgo técnico a validar en un *spike*).
