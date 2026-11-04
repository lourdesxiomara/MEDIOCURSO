// Segundo parcial: generación, validación y envío del XML de la factura UBL 2.1 (SUNAT).
// Las clases Java del documento se GENERAN desde el XSD oficial con xjc (JAXB): ese es el "migrador de XSD" (ADR-006).
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.0.21"
}

group = "pe.abc.facturacion"
version = "0.1.0"

repositories { mavenCentral() }

val xjc: Configuration by configurations.creating

dependencies {
    xjc("org.glassfish.jaxb:jaxb-xjc:4.0.5")
    xjc("org.glassfish.jaxb:jaxb-runtime:4.0.5")

    implementation("jakarta.xml.bind:jakarta.xml.bind-api:4.0.2")
    implementation("org.glassfish.jaxb:jaxb-runtime:4.0.5")          // NamespacePrefixMapper
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.17.2")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-jsr310:2.17.2")

    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.3")
    testImplementation("org.junit.jupiter:junit-jupiter-params:5.10.3")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
    testImplementation("org.xmlunit:xmlunit-core:2.10.0")
}

// Raíz del repositorio: aquí están los XSD oficiales (docs/ubl) y los ejemplos de la spec (specs/02-dominio/ejemplos).
val repo = rootDir.parentFile
val ubl = repo.resolve("docs/ubl")
val generado = layout.buildDirectory.dir("generated/xjc")

// "Migrador de XSD": xjc lee UBL-Invoice-2.1.xsd (+ esquemas de soporte que UBL importa sin schemaLocation)
// y escribe las clases Java en build/generated/xjc. Nunca se editan a mano: se regeneran en cada build.
val generateUblClasses by tasks.registering(JavaExec::class) {
    group = "build"
    description = "Genera las clases JAXB desde docs/ubl/maindoc/UBL-Invoice-2.1.xsd"
    val esquemas = listOf(
        "soporte/CCTS_CCT_SchemaModule.xsd",
        "soporte/xmldsig-core-schema.xsd",
        "soporte/XAdES01903v132-201601.xsd",
        "soporte/XAdES01903v141-201601.xsd",
        "maindoc/UBL-Invoice-2.1.xsd",
    ).map { ubl.resolve(it) }
    inputs.files(fileTree(ubl) { include("**/*.xsd") })
    outputs.dir(generado)
    classpath = xjc
    mainClass.set("com.sun.tools.xjc.XJCFacade")
    doFirst { generado.get().asFile.mkdirs() }
    args = listOf("-d", generado.get().asFile.absolutePath, "-encoding", "UTF-8", "-npa", "-no-header", "-quiet") +
        esquemas.map { it.absolutePath }
}

sourceSets.main {
    java.srcDir(generado)
}
tasks.compileJava { dependsOn(generateUblClasses) }
tasks.compileKotlin { dependsOn(generateUblClasses) }

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}
kotlin { compilerOptions { jvmTarget.set(JvmTarget.JVM_17) } }
tasks.withType<JavaCompile> { options.encoding = "UTF-8" }

tasks.test {
    useJUnitPlatform()
    systemProperty("repo.raiz", repo.absolutePath)
    testLogging { events("passed", "failed"); exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL }
}

// Demostración: ./gradlew generar --args="../specs/02-dominio/ejemplos/comprobante.factura.json build/F001-1.xml"
tasks.register<JavaExec>("generar") {
    group = "application"
    description = "Genera, valida y (opcionalmente) firma el XML de un comprobante JSON"
    classpath = sourceSets.main.get().runtimeClasspath
    mainClass.set("pe.abc.facturacion.AppKt")
    workingDir = projectDir
    systemProperty("repo.raiz", repo.absolutePath)
}
