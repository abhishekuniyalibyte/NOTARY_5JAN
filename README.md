# AI-Powered Uruguayan Notarial Certificate Automation System

## 📋 Overview

This system is a **legal validation engine** that automates the creation of notarial certificates in Uruguay. It validates documents against Uruguayan notarial law (Articles 248-255), handles institution-specific requirements, and generates legally compliant certificates.

### What This System Does

- ✅ **Understands Uruguayan notarial law** - Articles 248-255 and cross-references
- ✅ **Validates documents** - Checks if all required documents are present, valid, and up-to-date
- ✅ **Extracts information** - Uses OCR and text extraction to pull data from PDFs, Word docs, images
- ✅ **Detects gaps** - Identifies missing, expired, or incorrect information
- ✅ **Generates certificates** - Creates legally compliant certificates using templates
- ✅ **Learns from feedback** - Improves based on notary corrections

---

## 🏗️ System Architecture

The system is organized into **11 phases** (workflow defined in [workflow.md](workflow.md)):

```
Phase 1: Certificate Intent Definition        ← ✅ IMPLEMENTED
Phase 2: Legal Requirement Resolution         ← ✅ IMPLEMENTED
Phase 3: Document Intake                      ← ✅ IMPLEMENTED
Phase 4: Text Extraction & Structuring        ← ✅ IMPLEMENTED
Phase 5: Legal Validation Engine              ← ✅ IMPLEMENTED
Phase 6: Gap & Error Detection                ← ✅ IMPLEMENTED
Phase 7: Data Update Attempt                  ← TODO
Phase 8: Final Legal Confirmation             ← TODO
Phase 9: Certificate Generation               ← TODO
Phase 10: Notary Review & Learning            ← TODO
Phase 11: Final Output                        ← TODO
```

### Current Implementation (Phases 1-6)

**Complete Validation Pipeline**

```
Phase 1          Phase 2           Phase 3            Phase 4           Phase 5            Phase 6
Intent     →    Legal Rules  →   Documents    →   Text Extract  →   Validation   →   Gap Analysis
                                                                                          ↓
                                                                                    Action Plan
```

---

## 📁 Project Structure

```
NOTARY_5Jan/
├── src/
│   ├── phase1_certificate_intent.py      # Phase 1: Intent capture
│   ├── phase2_legal_requirements.py      # Phase 2: Legal rules engine
│   ├── phase3_document_intake.py         # Phase 3: Document intake
│   ├── phase4_text_extraction.py         # Phase 4: Text extraction
│   ├── phase5_legal_validation.py        # Phase 5: Legal validation
│   ├── phase6_gap_detection.py           # Phase 6: Gap detection
│   └── __init__.py
├── tests/
│   ├── test_phase1.py                    # Phase 1 tests
│   ├── test_phase2.py                    # Phase 2 tests
│   ├── test_phase3.py                    # Phase 3 tests
│   ├── test_phase4.py                    # Phase 4 tests
│   ├── test_phase5.py                    # Phase 5 tests
│   ├── test_phase6.py                    # Phase 6 tests
│   └── __init__.py
├── Notaria_client_data/                  # Client documents (911+ files)
│   ├── Girtec/
│   ├── Netkla Trading/
│   ├── Saterix/
│   └── ...
├── client_requirements.txt               # Project requirements
├── workflow.md                           # Detailed workflow
└── README.md                             # This file
```

---

## 🚀 Quick Start

### Installation

```bash
# Check Python version (requires 3.7+)
python3 --version

# Install dependencies
cd /home/abhishek/Documents/NOTARY_5Jan
pip install -r requirements.txt

# Note: Phases 1-3 use only standard library
# Phases 4-6 have optional dependencies (see requirements.txt)
```

### Running Examples

```bash
cd /home/abhishek/Documents/NOTARY_5Jan

# Phase 1: Certificate Intent
python3 src/phase1_certificate_intent.py

# Phase 2: Legal Requirements
python3 src/phase2_legal_requirements.py

# Phase 3: Document Intake
python3 src/phase3_document_intake.py

# Phase 4: Text Extraction
python3 src/phase4_text_extraction.py

# Phase 5: Legal Validation
python3 src/phase5_legal_validation.py

# Phase 6: Gap Detection
python3 src/phase6_gap_detection.py
```

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Or using unittest
python3 -m unittest discover tests/

# Run specific phase tests
python3 -m pytest tests/test_phase1.py -v
python3 -m pytest tests/test_phase2.py -v
python3 -m pytest tests/test_phase3.py -v
python3 -m pytest tests/test_phase4.py -v
python3 -m pytest tests/test_phase5.py -v
python3 -m pytest tests/test_phase6.py -v
```

---

## 📘 Phase 1: Certificate Intent Definition

### What It Does

Captures the notary's intent to create a specific certificate by gathering:
- **Certificate Type** (e.g., certificación de firmas, certificado de personería)
- **Purpose/Destination** (e.g., para BPS, para Abitab)
- **Subject** (person or company name)
- **Additional Notes** (optional)

### Supported Certificate Types

1. Certificación de Firmas - Signature certification
2. Certificado de Personería - Legal personality certificate
3. Certificado de Representación - Representation certificate
4. Certificado de Situación Jurídica - Legal status certificate
5. Certificado de Vigencia - Validity certificate
6. Carta Poder - Power of attorney letter
7. Poder General - General power of attorney
8. Poder para Pleitos - Power of attorney for litigation
9. Declaratoria - Declaration
10. Otros - Other types

### Supported Purposes/Destinations

Based on client's actual use cases:
- BPS, MSP, Abitab, UTE, ANTEL, DGI
- Banco, Zona Franca, MTOP, IMM, MEF
- RUPE, Base de Datos, Migraciones

### Usage Example

```python
from src.phase1_certificate_intent import CertificateIntentCapture

# Create certificate intent
intent = CertificateIntentCapture.capture_intent_from_params(
    certificate_type="certificado_de_personeria",
    purpose="Abitab",
    subject_name="INVERSORA RINLEN S.A.",
    subject_type="company"
)

# Display summary
print(intent.get_display_summary())

# Get JSON
print(intent.to_json())
```

### Output

```json
{
  "certificate_type": "certificado_de_personeria",
  "purpose": "para_abitab",
  "subject_name": "INVERSORA RINLEN S.A.",
  "subject_type": "company"
}
```

---

## 📘 Phase 2: Legal Requirement Resolution

### What It Does

The **Rules Engine** that maps certificate types to legal requirements:
1. Determines which articles (248-255) apply
2. Defines required documents per certificate type
3. Applies institution-specific rules (BPS, Abitab, MTOP, etc.)
4. Creates structured validation checklists

### Legal Framework

Based on Uruguayan Notarial Regulations:

- **Art. 130** - Identification rules
- **Art. 248** - General certificate requirements
- **Art. 249** - Document source requirements
- **Art. 250** - Signature certification
- **Art. 251** - Signature presence
- **Art. 252** - Certification content
- **Art. 253** - Certificate format
- **Art. 254** - Special mentions
- **Art. 255** - Required elements (destination, date, etc.)

### Institution-Specific Rules

#### BPS (Banco de Previsión Social)
- Validity: 30 days
- Required: Certificado BPS, Padrón de funcionarios
- Must include: Aportes al día, número de patrón

#### Abitab
- Validity: 30 days
- Must include: Full legal representation

#### RUPE (Registro Único de Proveedores)
- Validity: 180 days
- Must include: Law 18930 (data protection), Law 17904 (anti-money laundering)

#### Zona Franca
- Required: Certificado de vigencia de Zona Franca
- Must include: Zona Franca address and authorization

#### DGI
- Required: Certificado único DGI (90-day validity)
- Must include: RUT, tax status

#### Base de Datos
- Must include: Law 18930 (data protection)

### Usage Example

```python
from src.phase1_certificate_intent import CertificateIntentCapture
from src.phase2_legal_requirements import LegalRequirementsEngine

# Step 1: Create intent
intent = CertificateIntentCapture.capture_intent_from_params(
    certificate_type="certificado_de_personeria",
    purpose="BPS",
    subject_name="GIRTEC S.A.",
    subject_type="company"
)

# Step 2: Resolve legal requirements
requirements = LegalRequirementsEngine.resolve_requirements(intent)

# Step 3: View summary
print(requirements.get_summary())

# Step 4: Export to JSON
print(requirements.to_json())
```

### Output Example

```json
{
  "certificate_type": "certificado_de_personeria",
  "purpose": "para_bps",
  "mandatory_articles": ["248", "249", "252", "255"],
  "cross_references": ["130"],
  "required_documents": [
    {
      "document_type": "estatuto",
      "description": "Estatuto social de la empresa",
      "mandatory": true,
      "expires": false,
      "legal_basis": "Art. 248"
    },
    {
      "document_type": "certificado_bps",
      "description": "Certificado de situación de BPS",
      "mandatory": true,
      "expires": true,
      "expiry_days": 30,
      "institution_specific": "BPS"
    }
  ],
  "institution_rules": {
    "institution": "BPS",
    "validity_days": 30,
    "special_requirements": [
      "Debe incluir situación de aportes al día",
      "Debe mencionar número de patrón BPS"
    ]
  }
}
```

---

## 📘 Phase 3: Document Intake

### What It Does

Handles document collection and indexing:
1. Accepts file uploads (PDF, DOCX, JPG, PNG)
2. Indexes documents by client, type, date
3. Detects document types from filenames
4. Tracks coverage (% of required documents present)
5. Identifies scanned vs digital files

### Supported File Formats
- ✅ PDF
- ✅ DOCX/DOC
- ✅ JPG/JPEG/PNG (scanned documents)
- ✅ TXT

### Document Type Detection

Uses keyword-based pattern matching:

| Document Type | Detection Keywords |
|---------------|-------------------|
| Estatuto | estatuto, estatutos |
| Acta de Directorio | acta, directorio, asamblea |
| Certificado BPS | bps, prevision |
| Certificado DGI | dgi, tributaria, impositiva |
| Cédula de Identidad | cedula, ci, identidad |
| Poder | poder, apoderado |
| Registro de Comercio | registro, comercio, rnc |

**Examples:**
- `estatuto_girtec.pdf` → ESTATUTO
- `acta_directorio_2023.pdf` → ACTA_DIRECTORIO
- `certificado_BPS.pdf` → CERTIFICADO_BPS
- `cedula_identidad.jpg` → CEDULA_IDENTIDAD

### Usage Example

```python
from src.phase1_certificate_intent import CertificateIntentCapture
from src.phase2_legal_requirements import LegalRequirementsEngine
from src.phase3_document_intake import DocumentIntake

# Create intent and requirements
intent = CertificateIntentCapture.capture_intent_from_params(
    certificate_type="certificado_de_personeria",
    purpose="BPS",
    subject_name="GIRTEC S.A.",
    subject_type="company"
)

requirements = LegalRequirementsEngine.resolve_requirements(intent)

# Create document collection
collection = DocumentIntake.create_collection(intent, requirements)

# Option 1: Add individual files
file_paths = [
    "/path/to/estatuto_girtec.pdf",
    "/path/to/acta_directorio.pdf",
    "/path/to/certificado_bps.pdf"
]
collection = DocumentIntake.add_files_to_collection(collection, file_paths)

# Option 2: Scan entire client directory
collection = DocumentIntake.scan_directory_for_client(
    directory_path="/home/abhishek/Documents/NOTARY_5Jan/Notaria_client_data/Girtec",
    client_name="GIRTEC S.A.",
    collection=collection
)

# View summary
print(collection.get_summary())

# Check coverage
coverage = collection.get_coverage_summary()
print(f"Coverage: {coverage['coverage_percentage']:.1f}%")
```

### Output Example

```
╔══════════════════════════════════════════════════════════════╗
║              COLECCIÓN DE DOCUMENTOS - FASE 3                ║
╚══════════════════════════════════════════════════════════════╝

👤 Sujeto: GIRTEC S.A.
📋 Tipo: Certificado De Personeria
🎯 Propósito: Para Bps

📊 COBERTURA DE DOCUMENTOS:
   Total requeridos: 6
   Presentes: 2
   Faltantes: 4
   Cobertura: 33.3%

📁 DOCUMENTOS CARGADOS (2 total):
   📄 estatuto_girtec.pdf [PDF] (245.3 KB) - Tipo: estatuto - Digital
   📄 certificado_bps.jpg [JPG] (871.5 KB) - Tipo: certificado_bps - Escaneado

⚠️  DOCUMENTOS FALTANTES (4):
   ❌ Inscripción en Registro de Comercio
   ❌ Acta de Directorio designando representantes
   ❌ Certificado de situación tributaria (DGI)
   ❌ Padrón de funcionarios BPS
```

---

## 📘 Phase 4: Text Extraction & Structuring

### What It Does

Extracts and structures data from documents:
1. Extracts text from PDFs, DOCX, images
2. Normalizes text (fixes OCR encoding errors)
3. Extracts structured data (RUT, CI, names, dates)
4. Detects scanned vs digital documents
5. Prepares data for validation

### Key Features

✅ **Text Normalization**
- Fixes Spanish encoding errors: `Ã³` → `ó`, `Ã±` → `ñ`
- Normalizes whitespace
- Handles OCR artifacts

✅ **Data Extraction**
- **RUT** (Uruguayan tax ID)
- **CI** (Cédula de Identidad)
- **Company names** (S.A., S.R.L.)
- **Registro de Comercio** numbers
- **Acta** numbers
- **Padrón BPS** numbers
- **Dates** (multiple formats)
- **Emails**

### Usage Example

```python
from src.phase4_text_extraction import TextExtractor, DataExtractor

# Extract from text
sample = "GIRTEC S.A. RUT: 21 234 567 8901 Registro: 12345"
company = DataExtractor.extract_company_name(sample)
rut = DataExtractor.extract_rut(sample)

# Process entire collection
extraction_result = TextExtractor.process_collection(collection)
print(extraction_result.get_summary())
```

---

## 📘 Phase 5: Legal Validation Engine

### What It Does

Validates extracted data against legal requirements:
1. Checks if all required documents are present
2. Validates document expiry dates
3. Verifies data consistency across documents
4. Checks compliance with Articles 248-255
5. Generates validation matrix

### Key Features

✅ **Document Validation**
- Presence checking
- Expiry validation (BPS 30 days, DGI 90 days)
- Missing document detection

✅ **Element Validation**
- Required elements (company name, RUT, registry)
- Cross-references with extracted data

✅ **Cross-Document Validation**
- Consistency checks between documents
- Company name/RUT matching

✅ **Severity Levels**
- 🔴 **CRITICAL** - Blocks certificate
- 🟠 **ERROR** - Should be fixed
- 🟡 **WARNING** - Recommended
- 🔵 **INFO** - Informational

### Usage Example

```python
from src.phase5_legal_validation import LegalValidator

# Run validation
validation_matrix = LegalValidator.validate(
    requirements,        # From Phase 2
    extraction_result   # From Phase 4
)

# Check result
if validation_matrix.can_issue_certificate:
    print("✅ Ready for certificate!")
else:
    print("❌ Fix issues first")
    print(validation_matrix.get_summary())
```

---

## 📘 Phase 6: Gap & Error Detection

### What It Does

Analyzes validation results and provides actionable guidance:
1. Identifies all problems (missing docs, expired docs, missing data)
2. Prioritizes issues (URGENT → HIGH → MEDIUM → LOW)
3. Provides clear guidance (what's wrong, why, how to fix)
4. Creates step-by-step action plans
5. Generates detailed reports

### Gap Types Detected

- **MISSING_DOCUMENT** - Required document not uploaded
- **EXPIRED_DOCUMENT** - Past validity period
- **MISSING_DATA** - Required information not found
- **INCONSISTENT_DATA** - Data conflicts
- **INCORRECT_FORMAT** - Format issues
- **LEGAL_NONCOMPLIANCE** - Legal violations

### Priority Levels

- 🔴 **URGENT** - Blocks certificate (must fix)
- 🟠 **HIGH** - Should fix soon (blocking)
- 🟡 **MEDIUM** - Recommended (non-blocking)
- 🟢 **LOW** - Optional (non-blocking)

### Usage Example

```python
from src.phase6_gap_detection import GapDetector

# Analyze gaps
gap_report = GapDetector.analyze(validation_matrix)

# View summary
print(gap_report.get_summary())

# View action plan
print(gap_report.get_action_plan())

# Check if ready
if gap_report.ready_for_certificate:
    print("✅ Proceed to Phase 7!")
else:
    print(f"❌ Fix {gap_report.urgent_gaps} urgent issues")
```

---

## 🔗 Complete Workflow Example (Phases 1-6)

```python
from src.phase1_certificate_intent import CertificateIntentCapture
from src.phase2_legal_requirements import LegalRequirementsEngine
from src.phase3_document_intake import DocumentIntake
from src.phase4_text_extraction import TextExtractor
from src.phase5_legal_validation import LegalValidator
from src.phase6_gap_detection import GapDetector

# ===== PHASE 1: Define Intent =====
print("PHASE 1: Certificate Intent Definition")
intent = CertificateIntentCapture.capture_intent_from_params(
    certificate_type="certificado_de_personeria",
    purpose="BPS",
    subject_name="GIRTEC S.A.",
    subject_type="company"
)
print(intent.get_display_summary())

# ===== PHASE 2: Resolve Legal Requirements =====
print("\nPHASE 2: Legal Requirement Resolution")
requirements = LegalRequirementsEngine.resolve_requirements(intent)
print(requirements.get_summary())

# ===== PHASE 3: Collect Documents =====
print("\nPHASE 3: Document Intake")
collection = DocumentIntake.create_collection(intent, requirements)
collection = DocumentIntake.scan_directory_for_client(
    directory_path="/home/abhishek/Documents/NOTARY_5Jan/Notaria_client_data/Girtec",
    client_name="GIRTEC S.A.",
    collection=collection
)
print(collection.get_summary())

# ===== PHASE 4: Extract Text & Data =====
print("\nPHASE 4: Text Extraction & Structuring")
extraction_result = TextExtractor.process_collection(collection)
print(extraction_result.get_summary())

# ===== PHASE 5: Validate =====
print("\nPHASE 5: Legal Validation")
validation_matrix = LegalValidator.validate(requirements, extraction_result)
print(validation_matrix.get_summary())

# ===== PHASE 6: Analyze Gaps =====
print("\nPHASE 6: Gap & Error Detection")
gap_report = GapDetector.analyze(validation_matrix)
print(gap_report.get_summary())

# Decision point
if gap_report.ready_for_certificate:
    print("\n✅ READY: Proceed to Phase 7 (Final Confirmation)")
else:
    print(f"\n❌ NOT READY: Fix {gap_report.urgent_gaps} urgent issues")
    print(gap_report.get_action_plan())
```

---

## 🧪 Testing

### Run All Tests

```bash
# Using pytest
python3 -m pytest tests/ -v

# Using unittest
python3 -m unittest discover tests/
```

### Test Coverage

**Phase 1:**
- ✅ Certificate type enumeration
- ✅ Purpose/destination mapping
- ✅ Intent creation and serialization
- ✅ File save/load operations
- ✅ Real-world scenarios (GIRTEC, NETKLA, SATERIX)

**Phase 2:**
- ✅ Article references
- ✅ Document requirements
- ✅ Institution rules (BPS, Abitab, RUPE, Zona Franca, etc.)
- ✅ Requirement resolution for all certificate types
- ✅ Real-world scenarios with actual client data

**Phase 3:**
- ✅ File format detection
- ✅ Document type detection from filenames
- ✅ Document collection management
- ✅ Coverage calculation
- ✅ Missing document detection
- ✅ Directory scanning
- ✅ Save/load functionality

**Phase 4:**
- ✅ Text normalization (OCR encoding fixes)
- ✅ Data extraction (RUT, CI, names, dates)
- ✅ Regex pattern matching
- ✅ Scanned vs digital detection
- ✅ Structured data output

**Phase 5:**
- ✅ Document presence validation
- ✅ Document expiry validation
- ✅ Element validation (company name, RUT, etc.)
- ✅ Cross-document consistency checks
- ✅ Validation matrix generation
- ✅ Legal compliance checking

**Phase 6:**
- ✅ Gap detection (missing docs, expired docs, missing data)
- ✅ Priority assignment (URGENT/HIGH/MEDIUM/LOW)
- ✅ Actionable recommendations
- ✅ Action plan generation
- ✅ Per-document gap reports

---

## 📊 Real-World Examples

### Example 1: GIRTEC BPS Certificate

```python
intent = CertificateIntentCapture.capture_intent_from_params(
    certificate_type="certificado_de_personeria",
    purpose="BPS",
    subject_name="GIRTEC S.A.",
    subject_type="company"
)

requirements = LegalRequirementsEngine.resolve_requirements(intent)
# Result: 30-day validity, requires BPS certificate, padrón, estatuto, acta, DGI
```

### Example 2: NETKLA Zona Franca

```python
intent = CertificateIntentCapture.capture_intent_from_params(
    certificate_type="certificado_de_personeria",
    purpose="zona franca",
    subject_name="NETKLA TRADING S.A.",
    subject_type="company"
)

requirements = LegalRequirementsEngine.resolve_requirements(intent)
# Result: Requires Zona Franca vigencia certificate, address, authorization
```

### Example 3: SATERIX Base de Datos

```python
intent = CertificateIntentCapture.capture_intent_from_params(
    certificate_type="certificado_de_personeria",
    purpose="base de datos",
    subject_name="SATERIX S.A.",
    subject_type="company"
)

requirements = LegalRequirementsEngine.resolve_requirements(intent)
# Result: Must include Law 18930 (data protection)
```

### Example 4: Poder General for Bank

```python
intent = CertificateIntentCapture.capture_intent_from_params(
    certificate_type="poder general",
    purpose="banco",
    subject_name="GIRTEC S.A.",
    subject_type="company",
    additional_notes="Poder a favor de Carolina Bomio"
)

requirements = LegalRequirementsEngine.resolve_requirements(intent)
# Result: Requires cedula, estatuto, acta authorizing power
```

---

## 📚 API Reference

### Phase 1 API

#### `CertificateIntentCapture`

**Static Methods:**
- `capture_intent_from_params(certificate_type, purpose, subject_name, subject_type, additional_notes) -> CertificateIntent`
- `capture_intent_interactive() -> CertificateIntent`
- `save_intent(intent, filepath) -> None`
- `load_intent(filepath) -> CertificateIntent`
- `get_available_certificate_types() -> List[dict]`
- `get_available_purposes() -> List[dict]`

#### `CertificateIntent`

**Methods:**
- `to_dict() -> dict`
- `to_json() -> str`
- `from_dict(data: dict) -> CertificateIntent`
- `get_display_summary() -> str`

### Phase 2 API

#### `LegalRequirementsEngine`

**Static Methods:**
- `resolve_requirements(intent: CertificateIntent) -> LegalRequirements`
- `get_all_applicable_articles(requirements: LegalRequirements) -> Set[str]`

#### `LegalRequirements`

**Methods:**
- `to_dict() -> dict`
- `to_json() -> str`
- `get_summary() -> str`

### Phase 3 API

#### `DocumentIntake`

**Static Methods:**
- `create_collection(intent, requirements) -> DocumentCollection`
- `process_file(file_path: str) -> UploadedDocument`
- `add_files_to_collection(collection, file_paths) -> DocumentCollection`
- `scan_directory_for_client(directory_path, client_name, collection) -> DocumentCollection`
- `save_collection(collection, output_path) -> None`
- `load_collection(input_path) -> DocumentCollection`

#### `DocumentCollection`

**Methods:**
- `add_document(document) -> None`
- `get_documents_by_type(doc_type) -> List[UploadedDocument]`
- `get_missing_documents() -> List[DocumentType]`
- `get_coverage_summary() -> Dict`
- `to_dict() -> dict`
- `to_json() -> str`
- `get_summary() -> str`

#### `DocumentTypeDetector`

**Static Methods:**
- `detect_from_filename(filename: str) -> Optional[DocumentType]`
- `is_likely_scanned(file_format: FileFormat) -> bool`

---

## 🗺️ Roadmap

### ✅ Completed (Phases 1-6)

- [x] Phase 1: Certificate Intent Definition
- [x] Phase 2: Legal Requirement Resolution
- [x] Phase 3: Document Intake
- [x] Phase 4: Text Extraction & Structuring
- [x] Phase 5: Legal Validation Engine
- [x] Phase 6: Gap & Error Detection

### 🚧 Next Steps (Phases 7-11)

- [ ] **Phase 7**: Data Update Attempt (Optional)
  - Fetch public registry information
  - Validate online records
  - Update outdated data
  - Highlight changes

- [ ] **Phase 8**: Final Legal Confirmation
  - Re-run all validations
  - Ensure 100% compliance
  - Generate compliance report

- [ ] **Phase 9**: Certificate Generation
  - Apply notary templates
  - Fill in verified data
  - Apply institution formatting
  - Generate draft certificate

- [ ] **Phase 10**: Notary Review & Learning
  - Present draft to notary
  - Capture corrections
  - Learn from feedback
  - Update templates

- [ ] **Phase 11**: Final Output
  - Generate final PDF/DOCX
  - Store with audit trail
  - Prepare for digital signature

### Future Enhancements

- [ ] Google Drive integration
- [ ] Mobile application (frontend)
- [ ] Automatic upload to governmental portals
- [ ] Machine learning for document classification
- [ ] Enhanced OCR with AI models
- [ ] Multi-notary support with custom templates
- [ ] API for third-party integrations

---

## 📄 License

[To be determined]

---

## 👥 Contributors

Development team working on Uruguayan notarial certificate automation.

---

## 📞 Support

For questions about the implementation, refer to:
- [client_requirements.txt](client_requirements.txt) - Project requirements and client conversations
- [workflow.md](workflow.md) - Detailed 11-phase workflow description
- Source code documentation in `src/` files
- Unit tests in `tests/` for usage examples

---

---

## 📦 Dependencies

See [requirements.txt](requirements.txt) for complete list.

**Core (Phases 1-3):**
- Python 3.7+ standard library only

**Phase 4 (Text Extraction) - Optional:**
- PyPDF2 or pdfplumber - PDF text extraction
- pytesseract - OCR for scanned documents
- python-docx - DOCX file processing
- Pillow - Image processing

**Development & Testing:**
- pytest - Testing framework
- pytest-cov - Test coverage

---

**Last Updated:** January 5, 2026
# NOTARY_5JAN
