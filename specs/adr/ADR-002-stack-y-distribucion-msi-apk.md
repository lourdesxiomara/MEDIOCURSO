# ADR-002 · Cross-platform stack and distribution (MSI + APK)

- **Status:** Proposed (requires management approval)
- **Context:** The app must run natively on Windows and Android, be packaged as an **MSI installer**
  (desktop) and an **APK** (Android), and share a single domain and tax rules.

## Options evaluated
| Criterion | **Kotlin Multiplatform + Compose Multiplatform** | Tauri 2 (Rust + web) | Flutter | .NET MAUI |
|---|---|---|---|---|
| Native Windows | Yes (bundled JVM) | Yes (WebView2) | Yes | Yes |
| Native Android | Yes | Yes | Yes | Yes |
| **MSI** | Native via `jpackage` (`TargetFormat.Msi`, needs WiX) | Native via WiX | Not native (needs WiX/external tool) | MSIX by default; MSI needs a separate WiX project |
| **APK** | Native (Gradle) | Native | Native | Native |
| Shared domain | One common Kotlin module | Shared Rust; web UI | Shared Dart | Shared C# |
| XML + XSD + XMLDSig | Mature JVM ecosystem (JAXP, Apache Santuario) | Less mature crates | Limited packages | System.Security.Cryptography.Xml |
| MVC → Hexagonal fit | Gradle modules = layers | Good | Good | Good |

## Proposed decision
**Kotlin Multiplatform + Compose Multiplatform**, with the module structure of
`specs/03-arquitectura` §5:
- `app-desktop` → `./gradlew packageMsi` produces `ABC-Facturacion-x.y.z.msi`.
- `app-android` → `./gradlew assembleRelease` produces a signed `app-release.apk`.

## Packaging requirements
| Requirement | MSI (Windows) | APK (Android) |
|---|---|---|
| Installer signing | Code-signing certificate (Authenticode) | Company keystore (apksigner) |
| Version | Shared `versionName`; MSI requires `MAJOR.MINOR.BUILD` | Incremental `versionCode` |
| Updates | Fixed `upgradeUuid` so the MSI replaces previous versions | Same signature and `applicationId` |
| Local data | `%LOCALAPPDATA%\ABC\Facturacion` (not Program Files) | App internal storage |
| Invoicing certificate (.pfx) | User's protected store; never inside the installer | Android Keystore; never inside the APK |
| Build requirement | JDK 17+ and WiX Toolset on the packaging machine | Android SDK |

## Consequences
- (+) One language for domain, UI and adapters; identical tax rules on both platforms.
- (+) MSI and APK come from the same build (`./gradlew packageMsi assembleRelease`).
- (−) The MSI bundles a JVM runtime (larger than a native C++ app).
- (−) XMLDSig signing on Android must be proven with the chosen library (technical risk for a *spike*).
