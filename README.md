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
Phase 1: Certificate Intent Definition        ← ✅ IMPLEMENTED & TESTED
Phase 2: Legal Requirement Resolution         ← ✅ IMPLEMENTED & TESTED
Phase 3: Document Intake                      ← ✅ IMPLEMENTED & TESTED
Phase 4: Text Extraction & Structuring        ← ✅ IMPLEMENTED & TESTED
Phase 5: Legal Validation Engine              ← ✅ IMPLEMENTED & TESTED
Phase 6: Gap & Error Detection                ← ✅ IMPLEMENTED & TESTED
Phase 7: Data Update Attempt                  ← ✅ IMPLEMENTED & TESTED
Phase 8: Final Legal Confirmation             ← ✅ IMPLEMENTED & TESTED
Phase 9: Certificate Generation               ← ✅ IMPLEMENTED & TESTED
Phase 10: Notary Review & Learning            ← ✅ IMPLEMENTED & TESTED
Phase 11: Final Output & Delivery             ← ✅ IMPLEMENTED & TESTED
```

### Complete Implementation (All 11 Phases)

**Full End-to-End Pipeline**

```
Phase 1-6: Document Collection & Validation
Intent → Legal Rules → Documents → Text Extract → Validation → Gap Analysis
                                                                      ↓
Phase 7-11: Certificate Generation & Output
Data Update → Final Confirmation → Certificate Gen → Notary Review → Final Output
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
│   ├── phase7_data_update.py             # Phase 7: Data update
│   ├── phase8_final_confirmation.py      # Phase 8: Final confirmation
│   ├── phase9_certificate_generation.py  # Phase 9: Certificate generation
│   ├── phase10_notary_review.py          # Phase 10: Notary review
│   ├── phase11_final_output.py           # Phase 11: Final output
│   └── __init__.py
├── tests/
│   ├── test_phase1.py                    # Phase 1 tests (20 tests)
│   ├── test_phase2.py                    # Phase 2 tests (36 tests)
│   ├── test_phase3.py                    # Phase 3 tests (24 tests)
│   ├── test_phase4.py                    # Phase 4 tests (17 tests)
│   ├── test_phase5.py                    # Phase 5 tests (20 tests)
│   ├── test_phase6.py                    # Phase 6 tests (21 tests)
│   ├── test_phase7.py                    # Phase 7 tests (13 tests)
│   ├── test_phase8.py                    # Phase 8 tests (17 tests)
│   ├── test_phase9.py                    # Phase 9 tests (21 tests)
│   ├── test_phase10.py                   # Phase 10 tests (16 tests)
│   ├── test_phase11.py                   # Phase 11 tests (19 tests)
│   └── __init__.py
├── Notaria_client_data/                  # Client documents (911+ files)
│   ├── Girtec/
│   ├── Netkla Trading/
│   ├── Saterix/
│   └── ...
├── analyze_historical_certificates.py    # 🆕 Historical data analyzer (preprocessing)
├── test_analyzer.py                      # 🆕 Tests for historical analyzer
├── HISTORICAL_ANALYSIS_README.md         # 🆕 Documentation for analyzer tool
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

# Phase 7: Data Update
python3 src/phase7_data_update.py

# Phase 8: Final Confirmation
python3 src/phase8_final_confirmation.py

# Phase 9: Certificate Generation
python3 src/phase9_certificate_generation.py

# Phase 10: Notary Review
python3 src/phase10_notary_review.py

# Phase 11: Final Output
python3 src/phase11_final_output.py
```

### Running Tests

```bash
# Run all tests (224 total tests across 11 phases)
python3 -m pytest tests/ -v

# Or using unittest
python3 -m unittest discover tests/

# Run specific phase tests
python3 tests/test_phase1.py   # 20 tests
python3 tests/test_phase2.py   # 36 tests
python3 tests/test_phase3.py   # 24 tests
python3 tests/test_phase4.py   # 17 tests
python3 tests/test_phase5.py   # 20 tests
python3 tests/test_phase6.py   # 21 tests
python3 tests/test_phase7.py   # 13 tests
python3 tests/test_phase8.py   # 17 tests
python3 tests/test_phase9.py   # 21 tests
python3 tests/test_phase10.py  # 16 tests
python3 tests/test_phase11.py  # 19 tests
```

---

## 🔍 Historical Certificate Analysis (Preprocessing Tool)

**NEW**: Content-based analysis of historical certificates

### What It Does

The `analyze_historical_certificates.py` tool is a **ONE-TIME preprocessing script** that analyzes your 911+ historical certificate files to build a knowledge base. This addresses the client requirement:

> "You need to analyse the content too, not only the file name" - Client Requirements, line 189

**Key Features:**
- ✅ Analyzes document **CONTENT** (not just filenames) using LLM or keywords
- ✅ Classifies certificate types (firma, personería, representación, etc.)
- ✅ Extracts purposes (BSE, Abitab, Zona Franca, BPS, etc.)
- ✅ Distinguishes notarial certificates from authority documents (DGI, BPS, BCU)
- ✅ Handles ERROR files (certificates with wrong data)
- ✅ Generates JSON knowledge base for Phase 9 and Phase 10

### Quick Start

```bash
# Test the analyzer first
python3 test_analyzer.py

# Run basic analysis (keyword-based, no API key needed)
python3 analyze_historical_certificates.py

# Run with LLM for better accuracy (requires Groq API key)
export GROQ_API_KEY="your-key-here"
python3 analyze_historical_certificates.py --use-llm
```

**Output**: Creates `historical_certificates_analysis.json` with:
- Certificate type breakdown
- Purpose/destination statistics
- Per-customer analysis
- Complete classification data

### How It Integrates

This tool is **separate from the 11-phase runtime workflow**:

- **11 phases** = Runtime (when notary creates new certificate)
- **This analyzer** = Preprocessing (analyze historical data once)

The output feeds into:
- **Phase 9**: Use historical certificates as template references
- **Phase 10**: Learn patterns from notary's previous work

### Documentation

See [HISTORICAL_ANALYSIS_README.md](HISTORICAL_ANALYSIS_README.md) for:
- Detailed installation instructions
- LLM vs keyword classification comparison
- Performance benchmarks
- Integration examples
- Troubleshooting guide

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

## 📘 Phase 7: Data Update Attempt

### What It Does

Handles document updates after gap detection:
1. Allows manual document uploads to address gaps
2. Tracks all update attempts (success/failure)
3. Re-extracts data from new documents
4. Monitors remaining gaps
5. Creates comprehensive update audit trail

### Key Features

✅ **Document Upload Management**
- Upload replacement or additional documents
- Track which gaps each upload addresses
- Record previous state vs new state

✅ **Update Tracking**
- Success/failure status
- Update source (manual upload, public registry, system correction)
- Timestamps and notes

✅ **Gap Resolution**
- Identify which gaps were resolved
- Track remaining gaps
- Priority-based resolution tracking

### Usage Example

```python
from src.phase7_data_update import DataUpdater, UpdateSource

# Start update session from gap report
update_result = DataUpdater.start_update_session(gap_report)

# Upload new document to address a gap
gap = gap_report.gaps[0]  # First urgent gap
update_result = DataUpdater.upload_updated_document(
    update_result,
    gap,
    file_path="/path/to/new_certificado_bps.pdf",
    notes="Updated BPS certificate obtained today"
)

# Re-extract data from updated collection
update_result = DataUpdater.re_extract_data(update_result)

# Check remaining gaps
remaining = DataUpdater.get_remaining_gaps(update_result)
print(f"Remaining gaps: {len(remaining)}")

# View summary
print(update_result.get_summary())
```

---

## 📘 Phase 8: Final Legal Confirmation

### What It Does

Final comprehensive validation before certificate generation:
1. Re-runs all validation checks
2. Performs 8-point compliance checklist
3. Determines compliance level
4. Makes final APPROVE/REJECT decision
5. Provides detailed rationale

### Compliance Levels

- **FULLY_COMPLIANT** - All requirements met, ready for certificate
- **SUBSTANTIALLY_COMPLIANT** - Minor issues, may proceed with warnings
- **PARTIALLY_COMPLIANT** - Significant issues, needs review
- **NON_COMPLIANT** - Critical issues, cannot issue certificate

### Certificate Decisions

- **APPROVED** - Issue certificate
- **APPROVED_WITH_WARNINGS** - Issue with noted concerns
- **REJECTED** - Cannot issue
- **REQUIRES_REVIEW** - Needs manual notary review

### 8-Point Compliance Checklist

1. ✓ All required documents present
2. ✓ No expired documents
3. ✓ Required elements present (name, RUT, etc.)
4. ✓ Data consistency across documents
5. ✓ No critical validation issues
6. ✓ All urgent gaps resolved
7. ✓ Institution-specific requirements met
8. ✓ Articles 248-255 compliance

### Usage Example

```python
from src.phase8_final_confirmation import FinalConfirmationEngine

# Run final confirmation
confirmation_report = FinalConfirmationEngine.confirm(
    legal_requirements,
    update_result
)

# Check decision
if confirmation_report.certificate_decision == CertificateDecision.APPROVED:
    print("✅ APPROVED - Proceed to Phase 9")
    print(confirmation_report.get_summary())
else:
    print(f"❌ {confirmation_report.certificate_decision.value}")
    print(confirmation_report.decision_rationale)
```

---

## 📘 Phase 9: Certificate Generation

### What It Does

Generates the actual notarial certificate text:
1. Applies appropriate certificate template
2. Performs variable substitution (names, RUT, dates, etc.)
3. Includes all legally required sections
4. Applies institution-specific formatting
5. Creates draft for notary review

### Certificate Structure (9 Sections)

1. **Header** - Notary identification
2. **Introduction** - "CERTIFICO:"
3. **Legal Basis** - Referenced articles
4. **Subject Identification** - Who/what is certified
5. **Document Sources** - Documents reviewed
6. **Certifications** - Main certification content
7. **Special Mentions** - Institution requirements
8. **Destination** - Purpose/recipient
9. **Closing** - Date, signature block

### Output Formats

- **PLAIN_TEXT** - Simple text format
- **FORMATTED_TEXT** - Formatted with line breaks
- **STRUCTURED_JSON** - JSON with metadata
- **HTML** - Web-ready format

### Usage Example

```python
from src.phase9_certificate_generation import CertificateGenerator

# Generate certificate
certificate = CertificateGenerator.generate(
    intent,
    legal_requirements,
    extraction_result,
    confirmation_report,
    notary_name="Dr. Juan Pérez",
    notary_office="Montevideo, Uruguay"
)

# View formatted text
print(certificate.get_formatted_text())

# Export to file
CertificateGenerator.export_certificate(
    certificate,
    "certificate_draft.html",
    format=CertificateFormat.HTML
)
```

---

## 📘 Phase 10: Notary Review & Learning

### What It Does

Human-in-the-loop review and system learning:
1. Presents draft certificate to notary for review
2. Tracks all edits made by notary
3. Categorizes changes (wording, legal accuracy, data correction)
4. Collects structured feedback
5. Extracts learning insights for template improvement

### Review Process

1. **Start Review** - Begin review session
2. **Add Edits** - Track changes made by notary
3. **Add Feedback** - Collect structured improvement suggestions
4. **Approve/Reject** - Final decision

### Change Types

- **WORDING** - Style/phrasing improvements
- **LEGAL_ACCURACY** - Legal corrections
- **DATA_CORRECTION** - Fix extracted data
- **FORMATTING** - Layout/format changes
- **ADDITION** - Add missing content
- **DELETION** - Remove unnecessary content

### Feedback Categories

- **TEMPLATE_IMPROVEMENT** - Template needs updating
- **DATA_EXTRACTION** - Extraction issues
- **LEGAL_INTERPRETATION** - Legal rule issues
- **FORMATTING** - Format improvements
- **INSTITUTION_RULES** - Institution-specific issues

### Usage Example

```python
from src.phase10_notary_review import NotaryReviewSystem

# Start review
review_session = NotaryReviewSystem.start_review(
    certificate,
    reviewer_name="Dr. María González"
)

# Add edit
review_session = NotaryReviewSystem.add_edit(
    review_session,
    original_text="sociedad constituida",
    edited_text="sociedad debidamente constituida",
    change_type=ChangeType.WORDING,
    reason="Better legal phrasing"
)

# Add feedback for system learning
review_session = NotaryReviewSystem.add_feedback(
    review_session,
    category=FeedbackCategory.TEMPLATE_IMPROVEMENT,
    feedback_text="Template should include registration date",
    severity="medium",
    actionable=True
)

# Approve
review_session = NotaryReviewSystem.approve_certificate(
    review_session,
    notes="Approved with minor wording improvements"
)

# Extract learning insights
insights = NotaryReviewSystem.get_learning_insights(review_session)
print(f"Total edits: {insights['total_edits']}")
print(f"Common issues: {insights['common_issues']}")
```

---

## 📘 Phase 11: Final Output & Delivery

### What It Does

Generates final output and prepares for delivery:
1. Creates final certificate package
2. Exports to multiple formats (PDF, DOCX, HTML, JSON)
3. Prepares for digital signature
4. Archives with complete audit trail
5. Tracks delivery status

### Key Features

✅ **Multiple Output Formats**
- PDF (placeholder - requires reportlab)
- DOCX (placeholder - requires python-docx)
- HTML (fully functional)
- JSON (fully functional)
- TXT (fully functional)

✅ **Digital Signature Preparation**
- SHA256 hash generation
- Signature status tracking
- Verification support

✅ **Comprehensive Metadata**
- Tracks all 11 phases
- Complete audit trail
- Processing time tracking

✅ **Archival System**
- Date-based folder structure (YYYY/MM)
- Metadata preservation
- Full package JSON

### Signature Status Flow

NOT_SIGNED → PENDING_SIGNATURE → SIGNED → VERIFIED

### Usage Example

```python
from src.phase11_final_output import FinalOutputGenerator, OutputFormat

# Generate final certificate
final_cert = FinalOutputGenerator.generate_final_certificate(
    certificate,
    review_session,
    certificate_number="2026-001",
    issuing_notary="Dr. Juan Pérez",
    notary_office="Montevideo, Uruguay"
)

# Prepare for signature
final_cert = FinalOutputGenerator.prepare_for_signature(final_cert)

# Export to HTML
FinalOutputGenerator.export_to_format(
    final_cert,
    OutputFormat.HTML,
    "certificate_2026-001.html"
)

# Archive
final_cert = FinalOutputGenerator.archive_certificate(
    final_cert,
    archive_directory="/archive"
)

# View summary
print(final_cert.get_summary())
```

---

## 🔗 Complete Workflow Example (All 11 Phases)

```python
from src.phase1_certificate_intent import CertificateIntentCapture
from src.phase2_legal_requirements import LegalRequirementsEngine
from src.phase3_document_intake import DocumentIntake
from src.phase4_text_extraction import TextExtractor
from src.phase5_legal_validation import LegalValidator
from src.phase6_gap_detection import GapDetector
from src.phase7_data_update import DataUpdater
from src.phase8_final_confirmation import FinalConfirmationEngine, CertificateDecision
from src.phase9_certificate_generation import CertificateGenerator, CertificateFormat
from src.phase10_notary_review import NotaryReviewSystem
from src.phase11_final_output import FinalOutputGenerator, OutputFormat

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
    directory_path="/path/to/client/documents",
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

# ===== PHASE 7: Update Data (if needed) =====
if not gap_report.ready_for_certificate:
    print("\nPHASE 7: Data Update Attempt")
    update_result = DataUpdater.start_update_session(gap_report)

    # Upload missing documents
    for gap in gap_report.get_urgent_gaps():
        if gap.gap_type == GapType.MISSING_DOCUMENT:
            update_result = DataUpdater.upload_updated_document(
                update_result, gap,
                file_path="/path/to/updated/document.pdf"
            )

    # Re-extract data
    update_result = DataUpdater.re_extract_data(update_result)
    print(update_result.get_summary())
else:
    # No updates needed
    update_result = DataUpdater.start_update_session(gap_report)

# ===== PHASE 8: Final Confirmation =====
print("\nPHASE 8: Final Legal Confirmation")
confirmation_report = FinalConfirmationEngine.confirm(
    requirements,
    update_result
)
print(confirmation_report.get_summary())

if confirmation_report.certificate_decision != CertificateDecision.APPROVED:
    print(f"\n❌ Certificate rejected: {confirmation_report.decision_rationale}")
    exit(1)

# ===== PHASE 9: Generate Certificate =====
print("\nPHASE 9: Certificate Generation")
certificate = CertificateGenerator.generate(
    intent,
    requirements,
    update_result.updated_extraction_result,
    confirmation_report,
    notary_name="Dr. Juan Pérez",
    notary_office="Montevideo, Uruguay"
)
print(certificate.get_summary())

# ===== PHASE 10: Notary Review =====
print("\nPHASE 10: Notary Review & Learning")
review_session = NotaryReviewSystem.start_review(
    certificate,
    reviewer_name="Dr. María González"
)

# Notary makes edits (if needed)
# review_session = NotaryReviewSystem.add_edit(...)

# Approve certificate
review_session = NotaryReviewSystem.approve_certificate(
    review_session,
    notes="Approved - ready for signature"
)
print(review_session.get_summary())

# ===== PHASE 11: Final Output =====
print("\nPHASE 11: Final Output & Delivery")
final_cert = FinalOutputGenerator.generate_final_certificate(
    certificate,
    review_session,
    certificate_number="2026-001",
    issuing_notary="Dr. Juan Pérez",
    notary_office="Montevideo, Uruguay"
)

# Prepare for signature
final_cert = FinalOutputGenerator.prepare_for_signature(final_cert)

# Export to HTML
FinalOutputGenerator.export_to_format(
    final_cert,
    OutputFormat.HTML,
    "certificate_2026-001.html"
)

# Archive
final_cert = FinalOutputGenerator.archive_certificate(
    final_cert,
    archive_directory="/archive"
)

print(final_cert.get_summary())
print("\n✅ COMPLETE: Certificate generated, reviewed, and archived!")
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

### Test Coverage (224 Total Tests)

**Phase 1: Certificate Intent (20 tests)**
- ✅ Certificate type enumeration
- ✅ Purpose/destination mapping
- ✅ Intent creation and serialization
- ✅ File save/load operations
- ✅ Real-world scenarios (GIRTEC, NETKLA, SATERIX)

**Phase 2: Legal Requirements (36 tests)**
- ✅ Article references
- ✅ Document requirements
- ✅ Institution rules (BPS, Abitab, RUPE, Zona Franca, etc.)
- ✅ Requirement resolution for all certificate types
- ✅ Real-world scenarios with actual client data

**Phase 3: Document Intake (24 tests)**
- ✅ File format detection
- ✅ Document type detection from filenames
- ✅ Document collection management
- ✅ Coverage calculation
- ✅ Missing document detection
- ✅ Directory scanning
- ✅ Save/load functionality

**Phase 4: Text Extraction (17 tests)**
- ✅ Text normalization (OCR encoding fixes)
- ✅ Data extraction (RUT, CI, names, dates)
- ✅ Regex pattern matching
- ✅ Scanned vs digital detection
- ✅ Structured data output

**Phase 5: Legal Validation (20 tests)**
- ✅ Document presence validation
- ✅ Document expiry validation
- ✅ Element validation (company name, RUT, etc.)
- ✅ Cross-document consistency checks
- ✅ Validation matrix generation
- ✅ Legal compliance checking

**Phase 6: Gap Detection (21 tests)**
- ✅ Gap detection (missing docs, expired docs, missing data)
- ✅ Priority assignment (URGENT/HIGH/MEDIUM/LOW)
- ✅ Actionable recommendations
- ✅ Action plan generation
- ✅ Per-document gap reports

**Phase 7: Data Update (13 tests)**
- ✅ Update session management
- ✅ Document upload tracking
- ✅ Gap resolution tracking
- ✅ Update status management
- ✅ Re-extraction after updates

**Phase 8: Final Confirmation (17 tests)**
- ✅ 8-point compliance checklist
- ✅ Compliance level determination
- ✅ Certificate decision logic
- ✅ Approval/rejection scenarios
- ✅ Detailed compliance reporting

**Phase 9: Certificate Generation (21 tests)**
- ✅ Template application
- ✅ Variable substitution
- ✅ Section generation (9 sections)
- ✅ Multiple certificate types
- ✅ Export to multiple formats (TXT, HTML, JSON)

**Phase 10: Notary Review (16 tests)**
- ✅ Review session management
- ✅ Edit tracking with change types
- ✅ Feedback collection
- ✅ Approval/rejection workflow
- ✅ Learning insights extraction

**Phase 11: Final Output (19 tests)**
- ✅ Final certificate generation
- ✅ Multiple output formats
- ✅ Digital signature preparation
- ✅ Archive management
- ✅ Delivery tracking
- ✅ Complete metadata tracking

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

### ✅ Completed - Core System (All 11 Phases)

- [x] **Phase 1**: Certificate Intent Definition
  - All certificate types supported
  - Interactive and programmatic modes
  - 20 comprehensive tests

- [x] **Phase 2**: Legal Requirement Resolution
  - Articles 248-255 implementation
  - 12+ institution-specific rules
  - 36 comprehensive tests

- [x] **Phase 3**: Document Intake
  - Multi-format support (PDF, DOCX, JPG, PNG)
  - Intelligent document type detection
  - Directory scanning
  - 24 comprehensive tests

- [x] **Phase 4**: Text Extraction & Structuring
  - OCR encoding normalization
  - Regex-based data extraction
  - Structured output
  - 17 comprehensive tests

- [x] **Phase 5**: Legal Validation Engine
  - Document/element/cross-document validation
  - Severity-based issue tracking
  - Compliance determination
  - 20 comprehensive tests

- [x] **Phase 6**: Gap & Error Detection
  - Priority-based gap analysis
  - Actionable recommendations
  - Action plan generation
  - 21 comprehensive tests

- [x] **Phase 7**: Data Update Attempt
  - Manual document upload
  - Update tracking and audit trail
  - Gap resolution monitoring
  - 13 comprehensive tests

- [x] **Phase 8**: Final Legal Confirmation
  - 8-point compliance checklist
  - Compliance level determination
  - APPROVE/REJECT decision engine
  - 17 comprehensive tests

- [x] **Phase 9**: Certificate Generation
  - Template-based generation
  - 9-section certificate structure
  - Multiple output formats
  - 21 comprehensive tests

- [x] **Phase 10**: Notary Review & Learning
  - Edit tracking with categorization
  - Structured feedback collection
  - Learning insights extraction
  - 16 comprehensive tests

- [x] **Phase 11**: Final Output & Delivery
  - Multi-format export (TXT, HTML, JSON, PDF*, DOCX*)
  - Digital signature preparation
  - Archive management
  - Delivery tracking
  - 19 comprehensive tests

**Total: 224 passing tests across all phases**

### 🚧 Future Enhancements

**Integration & APIs:**
- [ ] Public registry API integration (DGI, BPS, Registro de Comercio)
- [ ] Google Drive/cloud storage integration
- [ ] Automatic upload to governmental portals
- [ ] RESTful API for third-party integrations

**Output Formats:**
- [ ] Complete PDF generation (requires reportlab installation)
- [ ] Complete DOCX generation (requires python-docx installation)
- [ ] Digital signature integration (Uruguayan e-signature systems)

**AI & Machine Learning:**
- [ ] Machine learning for document classification
- [ ] Enhanced OCR with AI models (Tesseract, AWS Textract)
- [ ] Template learning from notary corrections
- [ ] Predictive gap detection

**User Experience:**
- [ ] Web-based frontend interface
- [ ] Mobile application
- [ ] Multi-notary support with custom templates
- [ ] Dashboard and analytics

**Advanced Features:**
- [ ] Workflow automation
- [ ] Batch certificate processing
- [ ] Real-time collaboration
- [ ] Version control for certificates

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

## 📈 Project Statistics

- **Total Lines of Code**: ~11,000+ lines across 11 phases
- **Total Tests**: 224 tests (all passing)
- **Test Coverage**: Comprehensive coverage across all phases
- **Phases Completed**: 11/11 (100%)
- **Institution Rules**: 12+ supported destinations
- **Certificate Types**: 10 types supported
- **Document Types**: 20+ document types recognized

---

**Last Updated:** January 5, 2026

**Status:** ✅ All 11 phases implemented and tested. Complete end-to-end pipeline operational.

---

# NOTARY_5JAN
