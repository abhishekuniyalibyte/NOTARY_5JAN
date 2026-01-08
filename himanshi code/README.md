# Track B - Notarial Certificate Generation System

**Version:** Milestone 1 & 2 Complete
**Language:** Python 3.10+
**Purpose:** Document intelligence and certificate generation for Uruguayan notaries

---

## 📋 Project Overview

This system helps Uruguayan notaries automate the creation of notarial certificates by reading customer documents, extracting data, validating legal requirements, and generating properly formatted certificates in Spanish.

**Track B** handles the operational layer:
- Document reading and OCR
- Data extraction and normalization
- Certificate template learning
- Certificate draft generation
- Integration with legal validation (Track A)

---

## 🎯 Project Status

### Milestone Progress (3/9 Complete)

| # | Milestone | Status | Description |
|---|-----------|--------|-------------|
| 1 | **Project Base & Folder Model** | ✅ Complete | Local folder scanning, customer indexing |
| 2 | **Google Drive & File Ingestion** | ✅ Complete | OAuth, file downloading, metadata indexing |
| 3 | **Document Text Extraction** | ✅ Complete | PDF parsing, OCR, LLM data extraction, legal validation |
| 4 | Data Field Extraction | 🔄 Next | Entity recognition, field normalization |
| 5 | Template Discovery | ⏳ Pending | Learn certificate styles and patterns |
| 6 | Certificate Generation | ⏳ Pending | Generate Spanish certificate drafts |
| 7 | Track A Integration | ⏳ Pending | Legal validation integration |
| 8 | Feedback Loop | ⏳ Pending | Learn from notary corrections |
| 9 | Final Export & Delivery | ⏳ Pending | Production-ready outputs |

### Current Capabilities

**Milestone 1:**
- ✅ Local folder scanning and certificate indexing
- ✅ Automatic customer type detection (person vs company)
- ✅ ERROR certificate tracking
- ✅ Institution recognition (BPS, MSP, Abitab, etc.)
- ✅ Statistics and analytics

**Milestone 2:**
- ✅ Google Drive OAuth authentication
- ✅ Batch file downloading from Drive
- ✅ File type detection (PDF, DOCX, images)
- ✅ Metadata indexing with Drive IDs
- ✅ Seamless integration with registry

**Milestone 3:**
- ✅ PDF text extraction with pdfplumber
- ✅ OCR for scanned PDFs (Tesseract)
- ✅ LLM-based data extraction (Groq Llama 4)
- ✅ Legal validation (Articles 248-255 compliant)
- ✅ FastAPI server for testing

---

## 🚀 Quick Start

### Installation

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR: venv\Scripts\activate (Windows)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install libmagic (optional, for file detection)
# Linux: sudo apt-get install libmagic1
# macOS: brew install libmagic
# Windows: pip install python-magic-bin

# 4. Verify installation
python main.py --help
```

### Basic Usage

**Milestone 1: Scan Local Folders**
```bash
# Scan customer folders
python main.py --scan /path/to/customer/folders

# View statistics
python main.py --stats

# Search for customer
python main.py --customer "EMARLAN"
```

**Milestone 2: Google Drive Integration**
```bash
# Authenticate (first time only)
python main.py --drive-auth

# List folders
python main.py --drive-list

# Download all customers
python main.py --drive-download

# View metadata stats
python main.py --metadata-stats
```

> **Note:** For Google Drive setup, see [README_MILESTONE2.md](README_MILESTONE2.md)

---

## 📁 Project Files

### Core Python Files

| File | Purpose | Milestone |
|------|---------|-----------|
| `models.py` | Data schemas (Customer, Certificate, Registry) | M1, M2 |
| `folder_scanner.py` | Local folder scanning and indexing | M1 |
| `storage.py` | JSON persistence and backups | M1 |
| `certificate_tracker.py` | Certificate analysis and queries | M1 |
| `main.py` | CLI interface (all commands) | M1, M2 |
| `drive_auth.py` | Google Drive OAuth authentication | M2 |
| `drive_manager.py` | Drive file operations | M2 |
| `file_detector.py` | File type detection | M2 |
| `metadata_indexer.py` | File metadata storage | M2 |
| `drive_integration.py` | Drive-to-registry orchestration | M2 |
| `extract_pdf_data2.py` | PDF extraction & legal validation | M3 |
| `api.py` | FastAPI server for PDF extraction | M3 |

> **Detailed file descriptions:** See [FILE_STRUCTURE.md](FILE_STRUCTURE.md)

### Configuration

- **`requirements.txt`** - Python dependencies (M1 & M2)
- **`.gitignore`** - Excludes sensitive data and temp files

### Documentation

- **`README_MILESTONE1.md`** - Detailed guide for local folder scanning
- **`README_MILESTONE2.md`** - Detailed guide for Google Drive integration
- **`FILE_STRUCTURE.md`** - Complete file descriptions and architecture
- **`workflow_track_B2.md`** - 9-milestone implementation roadmap
- **`track_B_detail.txt`** - Track B scope and boundaries
- **`client_requirements.txt`** - Original client specifications

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.10+ | Core implementation |
| Data Validation | Pydantic | Schema validation |
| Storage | JSON | Lightweight persistence |
| Cloud Access | Google Drive API | File ingestion (M2) |
| File Detection | python-magic | Content-based type detection (M2) |
| OCR | Tesseract + OpenCV | Scanned document processing (M3) |
| Text Processing | pdfplumber, python-docx | Document parsing (M3) |
| NLP | spaCy (Spanish) | Entity extraction (M4) |
| Templates | Jinja2 | Certificate generation (M6) |

---

## 📊 Data Flow

### Milestone 1: Local Folders
```
Customer Folders → FolderScanner → CustomerRegistry → Storage → CLI
```

### Milestone 2: Google Drive
```
Google Drive → DriveAuth → DriveManager → FileDetector →
MetadataIndexer → DriveIntegration → CustomerRegistry → Storage → CLI
```

> **Detailed architecture:** See [FILE_STRUCTURE.md](FILE_STRUCTURE.md#architecture)

---

## 📖 Command Reference

### Milestone 1 Commands

| Command | Description |
|---------|-------------|
| `--scan <path>` | Scan local customer folders |
| `--stats` | Show detailed statistics |
| `--list` | List all customers |
| `--customer <name>` | Show customer details |
| `--search <term>` | Search certificates by filename |

### Milestone 2 Commands

| Command | Description |
|---------|-------------|
| `--drive-auth` | Authenticate with Google Drive |
| `--drive-list` | List folders in Drive |
| `--drive-download` | Download all customer folders |
| `--drive-download --folder-id <id>` | Download specific folder |
| `--drive-scan` | Re-scan local downloads |
| `--metadata-stats` | Show file metadata statistics |

### Milestone 3 Commands

**PDF Data Extraction:**

```bash
# Extract data from a PDF certificate
python3 extract_pdf_data2.py /path/to/certificate.pdf

# This generates 2 files:
# 1. *_extracted.json - Raw extracted data
# 2. *_validation_legal.json - Legal validation (Articles 248-255)
```

**FastAPI Testing:**

```bash
# Run the API server
uvicorn api:app --reload

# Access at http://localhost:8000/docs
# Upload PDFs and get extraction + validation results
```

---

## 🎓 Next Steps

**For New Users:**
1. Start with [README_MILESTONE1.md](README_MILESTONE1.md) for local folder scanning
2. Set up Google Drive following [README_MILESTONE2.md](README_MILESTONE2.md)
3. Review [FILE_STRUCTURE.md](FILE_STRUCTURE.md) to understand the architecture

**For Developers:**
1. Review [workflow_track_B2.md](workflow_track_B2.md) for the complete roadmap
2. Check [track_B_detail.txt](track_B_detail.txt) for Track B boundaries
3. See [client_requirements.txt](client_requirements.txt) for original specifications

**Coming in Milestone 4:**
- Entity recognition and field normalization
- Structured data extraction
- Multi-document processing
- Data validation and quality checks

---

## 🔒 Security & Privacy

- **Read-only Drive access** - Cannot modify or delete files
- **Local token storage** - OAuth tokens stored securely
- **No cloud processing** - All data processed locally
- **Git exclusions** - Credentials and customer data never committed

---

## 📄 License & Usage

This system is designed for Uruguayan notaries to automate certificate generation in compliance with Uruguayan notarial law (Organic Law and Notarial Regulations).

---

## 📞 Support

For detailed documentation:
- **Installation issues:** See milestone READMEs
- **Architecture questions:** See [FILE_STRUCTURE.md](FILE_STRUCTURE.md)
- **Roadmap details:** See [workflow_track_B2.md](workflow_track_B2.md)

---

**Track B - Milestones 1, 2 & 3 Complete**

*Next: Milestone 4 - Data Field Extraction (Entity Recognition & Normalization)*
