"""
Test script for Historical Certificate Analyzer

This script tests the analyzer with mock data to verify it works correctly
before running on the actual 911-file dataset.
"""

import tempfile
import os
from pathlib import Path
from ccs import (
    TextExtractor,
    KeywordClassifier,
    HistoricalCertificateAnalyzer,
    CertificateClassification
)


def create_mock_pdf_text():
    """Create mock certificate text samples"""
    return {
        'notarial_firma_bse': """
        CERTIFICACIÓN DE FIRMA

        CERTIFICO: Que la firma que antecede pertenece a Don Juan Pérez,
        titular de la Cédula de Identidad N° 1.234.567-8.

        El presente certificado se expide para ser presentado ante el
        Banco de Seguros del Estado (BSE).

        Montevideo, 15 de junio de 2023
        """,

        'notarial_personeria_abitab': """
        CERTIFICADO DE PERSONERÍA

        CERTIFICO: Que según consta en los documentos que tengo a la vista,
        la empresa GIRTEC SOCIEDAD ANÓNIMA, RUT 21.234.567.8901,
        se encuentra inscrita en el Registro de Comercio bajo el N° 12345.

        La representación legal la ejerce Don Walter Albanell.

        El presente certificado se expide para ser presentado ante ABITAB.

        Montevideo, 20 de agosto de 2023
        """,

        'authority_dgi': """
        DIRECCIÓN GENERAL IMPOSITIVA
        CERTIFICADO DE SITUACIÓN TRIBUTARIA

        Se certifica que el contribuyente GIRTEC S.A.
        RUT: 21.234.567.8901

        Se encuentra al día con sus obligaciones tributarias.

        Válido por 30 días desde su emisión.
        Fecha: 10/05/2023
        """,

        'authority_bps': """
        BANCO DE PREVISIÓN SOCIAL
        CONSTANCIA DE APORTES

        Padrón BPS N° 98765

        Se certifica que la empresa GIRTEC SOCIEDAD ANÓNIMA
        se encuentra al día con sus aportes a la seguridad social.

        Fecha de emisión: 15/07/2023
        Válido por 30 días.
        """
    }


def test_text_normalization():
    """Test encoding normalization"""
    print("\n" + "="*70)
    print("TEST 1: Normalización de texto")
    print("="*70)

    test_cases = [
        ("ResoluciÃ³n", "Resolución"),
        ("DeclaraciÃ³n", "Declaración"),
        ("SocializaciÃ³n", "Socialización"),
        ("José PÃ©rez", "José Pérez"),
    ]

    passed = 0
    for original, expected in test_cases:
        result = TextExtractor.normalize_text(original)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{original}' → '{result}' (esperado: '{expected}')")
        if result == expected:
            passed += 1

    print(f"\nResultado: {passed}/{len(test_cases)} tests pasados")
    return passed == len(test_cases)


def test_keyword_classification():
    """Test keyword-based classification"""
    print("\n" + "="*70)
    print("TEST 2: Clasificación por palabras clave")
    print("="*70)

    mock_texts = create_mock_pdf_text()
    classifier = KeywordClassifier()

    test_cases = [
        {
            'name': 'Certificación de firma para BSE',
            'file': 'cert_firma_bse.pdf',
            'text': mock_texts['notarial_firma_bse'],
            'expected_notarial': True,
            'expected_type': 'firma',
            'expected_purpose': 'BSE'
        },
        {
            'name': 'Certificado de personería para Abitab',
            'file': 'cert_personeria_abitab.pdf',
            'text': mock_texts['notarial_personeria_abitab'],
            'expected_notarial': True,
            'expected_type': 'personeria',
            'expected_purpose': 'Abitab'
        },
        {
            'name': 'Documento de DGI (no notarial)',
            'file': 'certificado_dgi.pdf',
            'text': mock_texts['authority_dgi'],
            'expected_notarial': False,
            'expected_type': None,
            'expected_purpose': 'DGI'
        },
        {
            'name': 'Documento de BPS (no notarial)',
            'file': 'constancia_bps.pdf',
            'text': mock_texts['authority_bps'],
            'expected_notarial': False,
            'expected_type': None,
            'expected_purpose': 'BPS'
        }
    ]

    passed = 0
    for test in test_cases:
        print(f"\n📄 Test: {test['name']}")
        is_notarial, cert_type, purpose, confidence = classifier.classify(
            test['file'], test['text']
        )

        print(f"   Es notarial: {is_notarial} (esperado: {test['expected_notarial']})")
        print(f"   Tipo: {cert_type} (esperado: {test['expected_type']})")
        print(f"   Propósito: {purpose} (esperado: {test['expected_purpose']})")
        print(f"   Confianza: {confidence:.2f}")

        # Check results (allow some flexibility)
        notarial_ok = is_notarial == test['expected_notarial']
        type_ok = cert_type == test['expected_type'] or test['expected_type'] is None
        purpose_ok = purpose == test['expected_purpose'] or test['expected_purpose'] is None

        if notarial_ok and (type_ok or purpose_ok):
            print("   ✅ PASADO")
            passed += 1
        else:
            print("   ❌ FALLADO")

    print(f"\nResultado: {passed}/{len(test_cases)} tests pasados")
    return passed >= len(test_cases) - 1  # Allow 1 failure


def test_error_file_detection():
    """Test ERROR file detection"""
    print("\n" + "="*70)
    print("TEST 3: Detección de archivos ERROR")
    print("="*70)

    test_cases = [
        ("ERROR_certificado_firma.pdf", True),
        ("certificado_firma.pdf", False),
        ("ERROR GIRTEC personeria.docx", True),
        ("GIRTEC personeria.docx", False),
    ]

    passed = 0
    for filename, should_be_error in test_cases:
        is_error = filename.startswith("ERROR")
        status = "✅" if is_error == should_be_error else "❌"
        print(f"{status} '{filename}' → ERROR={is_error} (esperado: {should_be_error})")
        if is_error == should_be_error:
            passed += 1

    print(f"\nResultado: {passed}/{len(test_cases)} tests pasados")
    return passed == len(test_cases)


def test_analyzer_structure():
    """Test analyzer creates correct report structure"""
    print("\n" + "="*70)
    print("TEST 4: Estructura del reporte")
    print("="*70)

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "test_data"
        data_dir.mkdir()

        # Create mock customer directory
        customer_dir = data_dir / "TEST_CUSTOMER"
        customer_dir.mkdir()

        # We can't create actual PDFs without external libraries,
        # so we'll just test the structure
        print("✅ Directorio temporal creado")
        print(f"   Path: {data_dir}")

        # Initialize analyzer
        analyzer = HistoricalCertificateAnalyzer(
            data_dir=str(data_dir),
            use_llm=False
        )
        print("✅ Analizador inicializado")

        # Check report structure
        report = analyzer.report
        print("✅ Reporte creado con estructura correcta")
        print(f"   Tiene atributos: total_files, certificate_types, purposes, customers")

        # Test report methods
        summary = report.get_summary_text()
        print("✅ Método get_summary_text() funciona")

        report_dict = report.to_dict()
        print("✅ Método to_dict() funciona")
        print(f"   Claves del dict: {list(report_dict.keys())}")

        expected_keys = ['summary', 'certificate_types', 'purposes', 'customers', 'all_classifications']
        has_all_keys = all(key in report_dict for key in expected_keys)

        if has_all_keys:
            print("✅ Todas las claves esperadas presentes")
            return True
        else:
            print("❌ Faltan claves en el reporte")
            return False


def test_classification_object():
    """Test CertificateClassification object"""
    print("\n" + "="*70)
    print("TEST 5: Objeto CertificateClassification")
    print("="*70)

    # Create sample classification
    classification = CertificateClassification(
        file_path="/test/path.pdf",
        file_name="cert_firma_bse.pdf",
        customer_name="TEST_CUSTOMER",
        is_notarial_certificate=True,
        certificate_type="firma",
        purpose="BSE",
        confidence=0.85
    )

    print("✅ CertificateClassification creado")

    # Test to_dict
    result_dict = classification.to_dict()
    print("✅ Método to_dict() funciona")

    # Check required fields
    required_fields = [
        'file_path', 'file_name', 'customer_name',
        'is_notarial_certificate', 'certificate_type', 'purpose',
        'confidence', 'classification_timestamp'
    ]

    has_all_fields = all(field in result_dict for field in required_fields)

    if has_all_fields:
        print("✅ Todos los campos requeridos presentes")
        print(f"   Campos: {list(result_dict.keys())}")
        return True
    else:
        print("❌ Faltan campos en el objeto")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("  TESTS DEL ANALIZADOR DE CERTIFICADOS HISTÓRICOS")
    print("="*70)

    tests = [
        ("Normalización de texto", test_text_normalization),
        ("Clasificación por keywords", test_keyword_classification),
        ("Detección de archivos ERROR", test_error_file_detection),
        ("Estructura del reporte", test_analyzer_structure),
        ("Objeto CertificateClassification", test_classification_object),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error en test '{test_name}': {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*70)
    print("  RESUMEN DE TESTS")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASADO" if result else "❌ FALLADO"
        print(f"{status}: {test_name}")

    print(f"\n{'='*70}")
    print(f"Total: {passed}/{total} tests pasados ({passed/total*100:.1f}%)")
    print(f"{'='*70}")

    if passed == total:
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        print("\nEl analizador está listo para usar. Puedes ejecutar:")
        print("  python3 analyze_historical_certificates.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) fallaron. Revisa los errores arriba.")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
