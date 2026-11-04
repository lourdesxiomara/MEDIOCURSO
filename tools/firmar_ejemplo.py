"""Signs the example invoice with a TEST certificate to show R-51 (enveloped XMLDSig in ext:UBLExtensions).

Usage: python tools/firmar_ejemplo.py
Generates a throw-away RSA key + self-signed certificate (never committed), signs
specs/02-dominio/ejemplos/factura-F001-1.sin-firma.xml and writes factura-F001-1.firmada.xml
and tools/cert-prueba/certificado-prueba.pem (public certificate only).
Production uses the company's digital certificate (.pfx) through the FirmadorDigital port (ADR-006).
"""
import datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree
from signxml import SignatureConstructionMethod, XMLSigner

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "specs/02-dominio/ejemplos/factura-F001-1.sin-firma.xml"
DESTINO = RAIZ / "specs/02-dominio/ejemplos/factura-F001-1.firmada.xml"
CERT = RAIZ / "tools/cert-prueba/certificado-prueba.pem"
EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
DS = "http://www.w3.org/2000/09/xmldsig#"


def main() -> None:
    clave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, "PE"),
                        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ABC SOFTWARE CORP S.A.C. - CERTIFICADO DE PRUEBA"),
                        x509.NameAttribute(NameOID.SERIAL_NUMBER, "20600123450"),
                        x509.NameAttribute(NameOID.COMMON_NAME, "PRUEBA - NO VALIDO PARA SUNAT")])
    ahora = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(nombre).issuer_name(nombre).public_key(clave.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(ahora)
            .not_valid_after(ahora + datetime.timedelta(days=3650)).sign(clave, hashes.SHA256()))
    pem = cert.public_bytes(serialization.Encoding.PEM)

    doc = etree.parse(str(ORIGEN))
    raiz = doc.getroot()
    ext = etree.Element(f"{{{EXT}}}UBLExtensions", nsmap={"ext": EXT})
    contenido = etree.SubElement(etree.SubElement(ext, f"{{{EXT}}}UBLExtension"), f"{{{EXT}}}ExtensionContent")
    etree.SubElement(contenido, f"{{{DS}}}Signature", Id="placeholder", nsmap={"ds": DS})
    raiz.insert(0, ext)

    firmador = XMLSigner(method=SignatureConstructionMethod.enveloped, signature_algorithm="rsa-sha256",
                         digest_algorithm="sha256", c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
    firmado = firmador.sign(raiz, key=clave, cert=pem)
    firmado.find(f".//{{{DS}}}Signature").set("Id", "SignatureABC")
    texto = etree.tostring(firmado, xml_declaration=True, encoding="UTF-8")
    DESTINO.write_bytes(texto)
    CERT.write_bytes(pem)
    print(f"signed: {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
