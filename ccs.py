"""
ccs.py create_certificate_summary.py Tool

This script performs ONE-TIME preprocessing of the historical certificate dataset
(911 files in Notaria_client_data/) to build a knowledge base for the system.

Purpose:
- Analyze document CONTENT (not just filenames) using LLM
- Classify certificate types (firma, personeria, representacion, etc.)
- Extract purposes (BSE, Abitab, Zona Franca, BPS, etc.)
- Distinguish notarial certificates from authority documents (DGI, BPS, BCU)
- Handle ERROR files (certificates with wrong data)
- Generate JSON knowledge base for Phase 9 (template selection) and Phase 10 (learning)

This is SEPARATE from the 11-phase runtime workflow.
Run this once to analyze historical data.

Based on client requirements line 189: "You need to analyse the content too, not only the file name"
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict
import re

# For text extraction
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("⚠️  python-docx not installed. Install with: pip install python-docx")

# For LLM-based classification (optional - fallback to keyword-based if not available)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  Groq not installed. Using fallback keyword-based classification.")
    print("   For LLM classification, install with: pip install groq")


@dataclass
class CertificateClassification:
    """Result of classifying a single certificate"""
    file_path: str
    file_name: str
    customer_name: str

    # Classification results
    is_notarial_certificate: bool = False  # True if created by notary, False if authority document
    is_error_file: bool = False  # True if filename starts with ERROR

    certificate_type: Optional[str] = None  # firma, personeria, representacion, etc.
    purpose: Optional[str] = None  # BSE, Abitab, Zona Franca, BPS, etc.
    attributes: List[str] = field(default_factory=list)  # Additional attributes

    # Text extraction info
    text_preview: str = ""  # First 500 chars of extracted text
    extraction_method: str = "none"  # pdf, docx, ocr, or none
    extraction_success: bool = False

    # Metadata
    classification_timestamp: datetime = field(default_factory=datetime.now)
    classification_method: str = "keyword"  # llm or keyword
    confidence: float = 0.0  # 0.0 to 1.0

    def to_dict(self) -> dict:
        result = asdict(self)
        result['classification_timestamp'] = self.classification_timestamp.isoformat()
        return result


@dataclass
class AnalysisReport:
    """Overall analysis report for all certificates"""
    total_files: int = 0
    total_customers: int = 0

    # Certificate counts
    notarial_certificates: int = 0
    authority_documents: int = 0
    error_files: int = 0
    unclassified: int = 0

    # Certificate types breakdown
    certificate_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Purposes breakdown
    purposes: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Customer breakdown
    customers: Dict[str, Dict] = field(default_factory=dict)

    # All classifications
    classifications: List[CertificateClassification] = field(default_factory=list)

    analysis_timestamp: datetime = field(default_factory=datetime.now)

    def add_classification(self, classification: CertificateClassification):
        """Add a classification and update counters"""
        self.classifications.append(classification)
        self.total_files += 1

        if classification.is_error_file:
            self.error_files += 1

        if classification.is_notarial_certificate:
            self.notarial_certificates += 1
        elif classification.extraction_success:
            self.authority_documents += 1
        else:
            self.unclassified += 1

        if classification.certificate_type:
            self.certificate_types[classification.certificate_type] += 1

        if classification.purpose:
            self.purposes[classification.purpose] += 1

        # Update customer stats
        customer = classification.customer_name
        if customer not in self.customers:
            self.customers[customer] = {
                'total_files': 0,
                'certificate_types': defaultdict(int),
                'purposes': defaultdict(int),
                'examples': []
            }

        self.customers[customer]['total_files'] += 1
        if classification.certificate_type:
            self.customers[customer]['certificate_types'][classification.certificate_type] += 1
        if classification.purpose:
            self.customers[customer]['purposes'][classification.purpose] += 1
        if len(self.customers[customer]['examples']) < 5:
            self.customers[customer]['examples'].append(classification.file_name)

    def to_dict(self) -> dict:
        return {
            'summary': {
                'total_files': self.total_files,
                'total_customers': self.total_customers,
                'notarial_certificates': self.notarial_certificates,
                'authority_documents': self.authority_documents,
                'error_files': self.error_files,
                'unclassified': self.unclassified,
                'analysis_timestamp': self.analysis_timestamp.isoformat()
            },
            'certificate_types': dict(self.certificate_types),
            'purposes': dict(self.purposes),
            'customers': {
                customer: {
                    'total_files': data['total_files'],
                    'certificate_types': dict(data['certificate_types']),
                    'purposes': dict(data['purposes']),
                    'examples': data['examples']
                }
                for customer, data in self.customers.items()
            },
            'all_classifications': [c.to_dict() for c in self.classifications]
        }

    def get_summary_text(self) -> str:
        """Get human-readable summary in Spanish"""
        self.total_customers = len(self.customers)

        summary = f"""
╔══════════════════════════════════════════════════════════════════════╗
║       ANÁLISIS DE CERTIFICADOS HISTÓRICOS - RESULTADOS              ║
╚══════════════════════════════════════════════════════════════════════╝

📊 RESUMEN GENERAL:
   Total archivos analizados: {self.total_files}
   Total clientes: {self.total_customers}

   Certificados notariales: {self.notarial_certificates}
   Documentos de autoridades: {self.authority_documents}
   Archivos con ERROR: {self.error_files}
   No clasificados: {self.unclassified}

📋 TIPOS DE CERTIFICADOS (Top 10):
"""
        sorted_types = sorted(self.certificate_types.items(), key=lambda x: x[1], reverse=True)
        for cert_type, count in sorted_types[:10]:
            summary += f"   {cert_type}: {count}\n"

        summary += f"\n🎯 PROPÓSITOS DETECTADOS (Top 10):\n"
        sorted_purposes = sorted(self.purposes.items(), key=lambda x: x[1], reverse=True)
        for purpose, count in sorted_purposes[:10]:
            summary += f"   {purpose}: {count}\n"

        summary += f"\n👥 CLIENTES (Top 10 por cantidad de archivos):\n"
        sorted_customers = sorted(self.customers.items(), key=lambda x: x[1]['total_files'], reverse=True)
        for customer, data in sorted_customers[:10]:
            summary += f"   {customer}: {data['total_files']} archivos\n"

        return summary


class TextExtractor:
    """Extract text from various file formats"""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Fix common encoding issues (Ã³ → ó)"""
        encoding_fixes = {
            'Ã³': 'ó', 'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ãº': 'ú',
            'Ã±': 'ñ', 'Ã': 'Á', 'Ã‰': 'É', 'Ã': 'Í', 'Ã"': 'Ó',
            'Ãš': 'Ú', 'Â°': '°', 'Âº': 'º', 'Âª': 'ª',
        }
        for wrong, correct in encoding_fixes.items():
            text = text.replace(wrong, correct)
        return text

    @staticmethod
    def extract_from_pdf(file_path: Path) -> Tuple[str, bool]:
        """Extract text from PDF. Returns (text, success)"""
        if not PDF_AVAILABLE:
            return "", False

        try:
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages[:5]:  # First 5 pages only
                    text += page.extract_text() + "\n"

            text = TextExtractor.normalize_text(text)
            return text, len(text.strip()) > 50
        except Exception as e:
            return f"[Error extracting PDF: {str(e)}]", False

    @staticmethod
    def extract_from_docx(file_path: Path) -> Tuple[str, bool]:
        """Extract text from DOCX. Returns (text, success)"""
        if not DOCX_AVAILABLE:
            return "", False

        try:
            doc = DocxDocument(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            text = TextExtractor.normalize_text(text)
            return text, len(text.strip()) > 50
        except Exception as e:
            return f"[Error extracting DOCX: {str(e)}]", False

    @staticmethod
    def extract_from_file(file_path: Path) -> Tuple[str, str, bool]:
        """
        Extract text from file based on extension.
        Returns (text, method, success)
        """
        extension = file_path.suffix.lower()

        if extension == '.pdf':
            text, success = TextExtractor.extract_from_pdf(file_path)
            return text, 'pdf', success
        elif extension in ['.docx', '.doc']:
            text, success = TextExtractor.extract_from_docx(file_path)
            return text, 'docx', success
        else:
            return "", "unsupported", False


class LLMClassifier:
    """Classify certificates using LLM (Groq API)"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = None

        if GROQ_AVAILABLE and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                self.model = "llama-3.3-70b-versatile"  # Using available model
                print(f"✅ LLM classifier initialized with model: {self.model}")
            except Exception as e:
                print(f"⚠️  Failed to initialize Groq client: {e}")
                self.client = None
        else:
            if not GROQ_AVAILABLE:
                print("⚠️  Groq library not available")
            if not self.api_key:
                print("⚠️  GROQ_API_KEY not set in environment")

    def classify(self, file_name: str, text: str) -> Tuple[bool, Optional[str], Optional[str], float]:
        """
        Classify certificate using LLM.
        Returns (is_notarial, certificate_type, purpose, confidence)
        """
        if not self.client:
            return False, None, None, 0.0

        # Limit text length
        text_sample = text[:3000] if len(text) > 3000 else text

        prompt = f"""Analiza este certificado uruguayo y responde en formato JSON:

Nombre del archivo: {file_name}
Texto del documento: {text_sample}

Por favor determina:
1. ¿Es un certificado NOTARIAL (creado por el notario) o un documento de AUTORIDAD (DGI, BPS, BCU, etc.)?
2. ¿Qué tipo de certificado es? (firma, personería, representación, etc.)
3. ¿Para qué propósito/destino? (BSE, Abitab, Zona Franca, BPS, etc.)

Responde SOLO con JSON válido en este formato:
{{
  "is_notarial": true/false,
  "certificate_type": "tipo",
  "purpose": "propósito",
  "confidence": 0.0-1.0
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )

            result_text = response.choices[0].message.content.strip()

            # Try to extract JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return (
                    result.get('is_notarial', False),
                    result.get('certificate_type'),
                    result.get('purpose'),
                    result.get('confidence', 0.5)
                )
        except Exception as e:
            print(f"⚠️  LLM classification failed: {e}")

        return False, None, None, 0.0


class KeywordClassifier:
    """Fallback classifier using keyword matching"""

    # Certificate type keywords
    CERT_TYPE_KEYWORDS = {
        'firma': ['certificación firma', 'certificación de firma', 'cert firma', 'firma digital'],
        'personeria': ['personería', 'personeria', 'cert personería', 'certificado personería'],
        'representacion': ['representación', 'representacion', 'cert representación'],
        'vigencia': ['vigencia', 'cert vigencia', 'certificado vigencia'],
        'situacion_juridica': ['situación jurídica', 'situacion juridica'],
        'autenticacion': ['autenticación', 'autenticacion'],
    }

    # Purpose keywords
    PURPOSE_KEYWORDS = {
        'BSE': ['bse', 'banco de seguros'],
        'Abitab': ['abitab'],
        'Zona Franca': ['zona franca', 'zona_franca'],
        'BPS': ['bps', 'banco de previsión'],
        'BCU': ['bcu', 'banco central'],
        'DGI': ['dgi', 'dirección general impositiva'],
        'MSP': ['msp', 'ministerio salud'],
    }

    # Authority document keywords (NOT notarial certificates)
    AUTHORITY_KEYWORDS = [
        'dirección general impositiva',
        'banco de previsión social',
        'banco central del uruguay',
        'certificado bps',
        'certificado dgi',
        'constancia dgi',
        'constancia bps',
    ]

    @staticmethod
    def classify(file_name: str, text: str) -> Tuple[bool, Optional[str], Optional[str], float]:
        """
        Classify using keyword matching.
        Returns (is_notarial, certificate_type, purpose, confidence)
        """
        text_lower = text.lower()
        name_lower = file_name.lower()
        combined = text_lower + " " + name_lower

        # Check if authority document
        is_authority = any(keyword in combined for keyword in KeywordClassifier.AUTHORITY_KEYWORDS)
        is_notarial = not is_authority

        # Detect certificate type
        cert_type = None
        cert_score = 0
        for ctype, keywords in KeywordClassifier.CERT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > cert_score:
                cert_score = score
                cert_type = ctype

        # Detect purpose
        purpose = None
        purpose_score = 0
        for purp, keywords in KeywordClassifier.PURPOSE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > purpose_score:
                purpose_score = score
                purpose = purp

        # Calculate confidence
        confidence = 0.3 if (cert_type or purpose) else 0.1

        return is_notarial, cert_type, purpose, confidence


class HistoricalCertificateAnalyzer:
    """Main analyzer for historical certificates"""

    def __init__(self, data_dir: str, use_llm: bool = False, api_key: Optional[str] = None):
        self.data_dir = Path(data_dir)
        self.report = AnalysisReport()

        # Initialize classifiers
        self.llm_classifier = LLMClassifier(api_key) if use_llm else None
        self.keyword_classifier = KeywordClassifier()

        self.use_llm = use_llm and self.llm_classifier and self.llm_classifier.client

        if self.use_llm:
            print("✅ Using LLM-based classification")
        else:
            print("✅ Using keyword-based classification")

    def analyze_file(self, file_path: Path, customer_name: str) -> CertificateClassification:
        """Analyze a single certificate file"""

        classification = CertificateClassification(
            file_path=str(file_path),
            file_name=file_path.name,
            customer_name=customer_name
        )

        # Check if ERROR file
        if file_path.name.startswith("ERROR"):
            classification.is_error_file = True

        # Extract text
        text, method, success = TextExtractor.extract_from_file(file_path)
        classification.extraction_method = method
        classification.extraction_success = success
        classification.text_preview = text[:500] if text else ""

        # Classify
        if success and len(text.strip()) > 50:
            if self.use_llm:
                is_notarial, cert_type, purpose, confidence = self.llm_classifier.classify(
                    file_path.name, text
                )
                classification.classification_method = "llm"
            else:
                is_notarial, cert_type, purpose, confidence = self.keyword_classifier.classify(
                    file_path.name, text
                )
                classification.classification_method = "keyword"

            classification.is_notarial_certificate = is_notarial
            classification.certificate_type = cert_type
            classification.purpose = purpose
            classification.confidence = confidence

        return classification

    def analyze_customer_directory(self, customer_dir: Path) -> List[CertificateClassification]:
        """Analyze all files for a single customer"""
        customer_name = customer_dir.name
        classifications = []

        # Find all PDF and DOCX files
        file_extensions = ['*.pdf', '*.docx', '*.doc']
        files = []
        for ext in file_extensions:
            files.extend(customer_dir.glob(ext))

        print(f"\n📂 Analizando cliente: {customer_name}")
        print(f"   Archivos encontrados: {len(files)}")

        for i, file_path in enumerate(files, 1):
            if i % 10 == 0:
                print(f"   Progreso: {i}/{len(files)}")

            classification = self.analyze_file(file_path, customer_name)
            classifications.append(classification)
            self.report.add_classification(classification)

        return classifications

    def analyze_all(self) -> AnalysisReport:
        """Analyze all customers in the data directory"""
        if not self.data_dir.exists():
            raise ValueError(f"Data directory not found: {self.data_dir}")

        # Get all customer directories
        customer_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]

        print(f"\n{'='*70}")
        print(f"  ANÁLISIS DE CERTIFICADOS HISTÓRICOS")
        print(f"{'='*70}")
        print(f"Directorio de datos: {self.data_dir}")
        print(f"Clientes encontrados: {len(customer_dirs)}")
        print(f"Método de clasificación: {'LLM' if self.use_llm else 'Keywords'}")

        # Analyze each customer
        for customer_dir in customer_dirs:
            try:
                self.analyze_customer_directory(customer_dir)
            except Exception as e:
                print(f"⚠️  Error analizando {customer_dir.name}: {e}")

        return self.report

    def save_report(self, output_path: str):
        """Save analysis report to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"\n✅ Reporte guardado en: {output_path}")


def print_summary_statistics(report: AnalysisReport):
    """Print concise classification summary"""
    print("\nCLASIFICACIÓN - RESUMEN")
    print("-" * 60)
    print(f"Total archivos: {report.total_files}")
    print(f"Certificados notariales: {report.notarial_certificates}")
    print(f"Documentos de autoridades: {report.authority_documents}")
    print(f"Archivos con ERROR: {report.error_files}")
    print(f"No clasificados: {report.unclassified}")

    if report.certificate_types:
        print("\nTipos de certificado:")
        for cert_type, count in sorted(report.certificate_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {cert_type}: {count}")

    if report.purposes:
        print("\nPropósitos detectados:")
        for purpose, count in sorted(report.purposes.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {purpose}: {count}")

    if report.customers:
        print("\nClientes (Top 10 por archivos):")
        top_customers = sorted(report.customers.items(), key=lambda x: x[1]['total_files'], reverse=True)[:10]
        for customer, data in top_customers:
            print(f"  - {customer}: {data['total_files']} archivos")


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analizar certificados históricos del notario"
    )
    parser.add_argument(
        '--data-dir',
        default='Notaria_client_data',
        help='Directorio con datos de clientes (default: Notaria_client_data)'
    )
    parser.add_argument(
        '--output',
        default='ccs.json',
        help='Archivo de salida JSON (default: ccs.json)'
    )
    parser.add_argument(
        '--use-llm',
        action='store_true',
        help='Usar clasificación LLM (requiere GROQ_API_KEY)'
    )
    parser.add_argument(
        '--api-key',
        help='Groq API key (o usar variable GROQ_API_KEY)'
    )

    args = parser.parse_args()

    # Resolve paths relative to this script's directory so data/output stay with the code
    script_dir = Path(__file__).resolve().parent
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = script_dir / data_dir

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = script_dir / output_path

    # Create analyzer
    analyzer = HistoricalCertificateAnalyzer(
        data_dir=data_dir,
        use_llm=args.use_llm,
        api_key=args.api_key
    )

    # Run analysis
    try:
        report = analyzer.analyze_all()

        # Print summary
        print(report.get_summary_text())

        # Save report
        analyzer.save_report(str(output_path))

        # Print concise statistics
        print_summary_statistics(report)

        print(f"\n{'='*70}")
        print("✅ Análisis completado exitosamente")
        print(f"{'='*70}")

    except Exception as e:
        print(f"\n❌ Error durante el análisis: {e}")
        raise


if __name__ == "__main__":
    main()
