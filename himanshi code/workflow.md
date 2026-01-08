# Notarial Certificate Automation – Project Milestones

## Milestone 0 – Scope Lock & Acceptance Criteria (DONE)

**Objective:** Prevent scope creep and align expectations.

**What is fixed:**

* The system is a **rule‑driven validation pipeline**, not a chatbot.
* Notary always selects the certificate type.
* The system never invents legal requirements.

**Acceptance criteria:**

* Certificate generation is blocked unless validation passes.
* ERROR certificates are explainable.

---

## Milestone 1 – Case & File Inventory (DONE)

**Objective:** Understand what data exists before reasoning.

**Code involved:**

* all_file_data.py
* customers_index.json

**Capabilities:**

* Scan all customer folders
* Classify files as certificates / non‑certificates
* Detect ERROR certificates

**Output:**

* Deterministic file inventory per customer

---

## Milestone 2 – Certificate Type Discovery & Mapping (DONE)

**Objective:** Identify real certificate types from historical data.

**Code involved:**

* normalize_certificates.py
* certificate_types.json
* create_certificate_summary.py

**Capabilities:**

* Discover certificate types from filenames
* Group certificates by type
* Identify "otros" for unsupported / unknown cases

**Output:**

* certificate_types.json
* certificate_summary_for_client.json

---

## Milestone 3 – Text Extraction & OCR (DONE)

**Objective:** Reliably read any legal document.

**Code involved:**

* text_extractor.py

**Capabilities:**

* PDF text extraction
* OCR fallback for scanned documents
* Page‑level traceability

**Non‑goals:**

* No legal interpretation
* No corrections or paraphrasing

---

## Milestone 4 – Field / Signal Extraction (PARTIAL)

**Objective:** Convert raw text into structured signals.

**Code involved:**

* field_extractor.py

**Current state:**

* Implemented for personería jurídica
* Extracts names, RUT, laws mentioned, registry mentions

**Next steps:**

* Add extractors for:

  * Identity documents
  * Powers of attorney
  * Expiry dates (generic)

---

## Milestone 5 – Requirements & Rules Definition (DONE – Phase 1)

**Objective:** Encode legal and notarial requirements deterministically.

**Artifacts:**

* certificate_requirements.json
* cross_reference_articles.json

**Capabilities:**

* Fixed requirement list per certificate type
* Mandatory vs conditional requirements
* Cross‑article dependencies

**Rule source priority:**

1. Law (Arts. 248–255 and references)
2. Notary‑provided requirements document

---

## Milestone 6 – Validation Engine (DONE)

**Objective:** Decide if a certificate can legally proceed.

**Code involved:**

* certificate_validator.py

**Capabilities:**

* GREEN / RED / UNKNOWN result
* Explicit issues with legal references
* Expiry checks
* Conditional requirements

**Output:**

* validation_result.json

---

## Milestone 7 – End‑to‑End Validation Pipeline (DONE)

**Objective:** Orchestrate extraction → validation.

**Code involved:**

* pipeline.py

**Flow:**

1. Load documents
2. Extract text
3. Extract factual signals
4. Validate against rules
5. Produce traceable report

---

## Milestone 8 – ERROR Certificate Correction Workflow (NEXT)

**Objective:** Explain and fix failed certificates.

**Requirements:**

* Detect ERROR drafts
* Re‑run validation
* Highlight missing / expired requirements

**Output:**

* Actionable correction report for notary

---

## Milestone 9 – Evidence Normalization Layer (NEXT)

**Objective:** Make validation legally auditable.

**What to build:**

* EvidenceItem schema (field, value, source, page, validity)
* Replace flat extracted_data with evidence list

**Why:**

* Multiple documents may provide the same field
* Conflicts must be explainable

---

## Milestone 10 – Certificate Draft Generation (FUTURE)

**Objective:** Generate certificates only after validation.

**Requirements:**

* Template per notary
* Versioned templates
* No legal reasoning in generation

---

## Milestone 11 – Notary Feedback & Template Adjustment (FUTURE)

**Objective:** Allow notary to correct wording and structure.

**Capabilities:**

* Save template edits
* Reuse corrected versions

---

## Milestone 12 – Optional Conversational UI (FUTURE)

**Objective:** Improve UX, not logic.

**Important:**

* Chatbot is a UI layer only
* Cannot define requirements or override validation

---
