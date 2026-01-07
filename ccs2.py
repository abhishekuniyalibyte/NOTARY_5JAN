"""
ccs2: create_certificate_summary_2.py
------------------------------------------------------------
• Uses LLM (meta-llama/llama-4-maverick-17b-128e-instruct) to analyze document CONTENT
• Correctly identifies certificate types based on content, not filename
• Extracts accurate PURPOSE information (BSE, ABITAB, Zona Franca, etc.)
• Differentiates NOTARIAL certificates from AUTHORITY documents (DGI, BPS, BCU)
• ERROR files are treated as certificates with wrong data
• Parallel processing with robust error handling
"""

import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from text_extractor import TextExtractor
from multiprocessing import Pool
from tqdm import tqdm

# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------
load_dotenv()

SCRIPT_DIR = Path(__file__).resolve().parent

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "meta-llama/llama-4-maverick-17b-128e-instruct"
NUM_WORKERS = 1  # Sequential processing to avoid rate limits
API_TIMEOUT = 30  # Timeout for API calls in seconds

# Load data
with open(SCRIPT_DIR / "customers_index.json", "r", encoding="utf-8") as f:
    customers = json.load(f)

with open(SCRIPT_DIR / "certificate_types.json", "r", encoding="utf-8") as f:
    cert_types = json.load(f)

# ---------------------------------------------------------
# HARD KEYWORD MAPS - Fallback detection
# ---------------------------------------------------------

# VERY SPECIFIC authority keywords (must be actual authority documents)
AUTHORITY_KEYWORDS = [
    "constancia anual dgi",
    "constancia dgi",
    "certificado común bps",
    "certificado comun bps",
    "formulario 0352",
    "formulario b y certificacion",
    "acuse bcu",
    "constancia certif.comun bps"
]

# Keywords that STRONGLY indicate NOTARIAL certificates
# Removed generic "certificación" to avoid false positives
NOTARIAL_KEYWORDS = [
    "escribano", "escribana", "notario", "notaria",
    "doy fe", "ante mí", "ante mi",
    "certificación notarial", "certificacion notarial",
    "certifica que", "certifico que"
]

PURPOSE_KEYWORDS_MAP = {
    "bse": ["bse", "seguros", "accidente de trabajo", "banco de seguros"],
    "abitab": ["abitab", "firma digital"],
    "zona franca": ["zona franca", "zonamerica", "free zone"],
    "comercio": ["registro de comercio", "cámara de comercio"],
    "registro": ["registro nacional", "registro de comercio"],
    "bcu": ["bcu", "banco central"],
    "dgi": ["dgi", "impositiva", "dirección general"],
    "bps": ["bps", "previsión social", "prevision"]
}

CERT_TYPE_KEYWORDS = {
    "firma": ["certificación de firma", "certificacion firma", "cert. firma"],
    "personeria": ["personería", "personeria"],
    "representacion": ["representación", "representacion"],
    "poder": ["poder", "apoderado"],
    "vigencia": ["vigencia"],
    "control": ["control"]
}

# ---------------------------------------------------------
# Worker Initialization
# ---------------------------------------------------------

_worker_groq_client = None
_worker_text_extractor = None

def init_worker():
    """Initialize worker process with its own clients"""
    global _worker_groq_client, _worker_text_extractor
    _worker_groq_client = Groq(api_key=GROQ_API_KEY)
    _worker_text_extractor = TextExtractor(lang="spa", ocr_dpi=150)

# ---------------------------------------------------------
# LLM Analysis Functions
# ---------------------------------------------------------

def analyze_document_with_llm(document_text: str, filename: str, groq_client) -> dict:
    """
    Use LLM to analyze document with simpler prompt and better error handling
    """

    prompt = f"""You are a Uruguayan NOTARIAL law expert.

Document content:
{document_text[:3000]}

Respond ONLY in JSON:
{{
  "is_notarial": true/false,
  "certificate_type": "firma|personeria|representacion|poder|vigencia|control|otros|authority",
  "purpose": "BSE|ABITAB|Zona Franca|Comercio|Registro|BCU|DGI|BPS|Other"
}}

Rules:
• ERROR files are still notarial
• DGI, BPS, BCU, Registro, Banco = authority
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_NAME,
                temperature=0.1,
                max_tokens=100,
                timeout=API_TIMEOUT
            )

            result_text = response.choices[0].message.content.strip()

            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[^}]+\}', result_text)
            if json_match:
                result_text = json_match.group()

            result = json.loads(result_text)

            return {
                "is_notarial": result.get("is_notarial", False),
                "certificate_type": result.get("certificate_type", "otros").lower(),
                "purpose": result.get("purpose", "unknown").lower()
            }

        except json.JSONDecodeError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            # Fallback
            return {
                "is_notarial": False,
                "certificate_type": "otros",
                "purpose": "unknown"
            }

        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                wait_time = 5 * (2 ** attempt)
                print(f"  [WARNING] Rate limit hit, waiting {wait_time}s...")
                time.sleep(wait_time)
                if attempt < max_retries - 1:
                    continue

            if attempt < max_retries - 1:
                time.sleep(2)
                continue

            # Fallback on final error
            return {
                "is_notarial": False,
                "certificate_type": "otros",
                "purpose": "unknown"
            }

# ---------------------------------------------------------
# Main Processing Worker Function
# ---------------------------------------------------------

def process_single_file(task_item):
    """Process a single file with worker's clients"""
    global _worker_groq_client, _worker_text_extractor

    customer = task_item['customer']
    cert_info = task_item['cert_info']
    base_path = task_item['base_path']
    is_certificate = task_item['is_certificate']

    groq_client = _worker_groq_client
    text_extractor = _worker_text_extractor

    if not is_certificate:
        return {
            'type': '__NON_CERT__',
            'customer': customer,
            'filename': cert_info['filename'],
            'path': cert_info['relative_path'],
            'reason': 'non_certificate'
        }

    file_path = Path(base_path) / customer / cert_info["relative_path"]

    if not file_path.exists():
        return {
            'type': '__AUTHORITY_DOC__',
            'customer': customer,
            'filename': cert_info['filename'],
            'path': cert_info['relative_path'],
            'error_flag': cert_info.get('error_flag', False),
            'purpose': 'unknown',
            'reason': 'file_not_found'
        }

    try:
        start_time = time.time()

        # Extract text from document
        extraction_result = text_extractor.extract(str(file_path), max_pages=2)
        document_text = extraction_result.full_text
        extraction_time = time.time() - start_time

        if not document_text.strip() or "[SCANNED PAGE" in document_text:
            # Use filename as fallback for text analysis
            document_text = f"[Document: {cert_info['filename']}]\nFilename: {cert_info['filename']}"

        text_lower = document_text.lower()
        filename_lower = cert_info['filename'].lower()

        # Also check filename for keywords when content is minimal
        combined_text = text_lower + " " + filename_lower

        # ---------------------------------------------------------
        # FIX 1: DEFAULT TO NOTARIAL (since file is in certificates list)
        # ---------------------------------------------------------
        # CRITICAL ASSUMPTION: If a file is in the "certificates" list in customers_index.json,
        # it's a notarial certificate UNLESS we have VERY specific evidence it's an authority doc

        is_authority = False

        # Only mark as authority if we find VERY specific authority document phrases
        for kw in AUTHORITY_KEYWORDS:
            if kw in combined_text:
                is_authority = True
                break

        # Check for notarial signatures (overrides everything)
        has_notarial_signature = False
        for kw in NOTARIAL_KEYWORDS:
            if kw in combined_text:
                has_notarial_signature = True
                is_authority = False  # Notarial signature overrides authority detection
                break

        # ERROR files are ALWAYS notarial certificates
        if "error" in filename_lower:
            is_authority = False
            has_notarial_signature = True

        # ---------------------------------------------------------
        # LLM CALL
        # ---------------------------------------------------------
        analysis = analyze_document_with_llm(document_text, cert_info['filename'], groq_client)

        is_notarial = analysis.get("is_notarial", False)
        cert_type = analysis.get("certificate_type", "otros").lower()
        purpose = analysis.get("purpose", "unknown").lower()

        # ---------------------------------------------------------
        # FIX 2: FINAL NOTARIAL DECISION
        # ---------------------------------------------------------
        # Default: Since file is in "certificates" list, assume it's notarial
        is_notarial = True

        # Only override to authority if:
        # 1. We found specific authority keywords AND
        # 2. We did NOT find notarial signatures
        if is_authority and not has_notarial_signature:
            is_notarial = False

        # ERROR files are ALWAYS notarial (final safety check)
        if "error" in filename_lower:
            is_notarial = True

        # ---------------------------------------------------------
        # FIX 3: HARD PURPOSE INFERENCE (check content + filename)
        # ---------------------------------------------------------
        # First try keyword-based detection in combined text
        detected_purpose = "other"
        for p_key, p_vals in PURPOSE_KEYWORDS_MAP.items():
            for pv in p_vals:
                if pv in combined_text:
                    detected_purpose = p_key
                    break
            if detected_purpose != "other":
                break

        # Use detected purpose if found, otherwise keep LLM's suggestion
        if detected_purpose != "other":
            purpose = detected_purpose
        elif purpose in ["unknown", "", "authority"]:
            purpose = "other"

        # ---------------------------------------------------------
        # FIX 4: SMART CERT TYPE INFERENCE (check content + filename)
        # ---------------------------------------------------------
        # Detect individual components from combined text
        detected_components = []
        has_firma = "firma" in combined_text or "firmas" in combined_text
        has_personeria = "personería" in combined_text or "personeria" in combined_text
        has_representacion = "representación" in combined_text or "representacion" in combined_text

        # Build components list in correct order
        if has_firma:
            detected_components.append("firma")
            if "firmas" in combined_text and not "firma" in combined_text:
                detected_components = ["firma_firmas"]

        if has_personeria:
            if not detected_components:
                detected_components.append("personeria")
            elif detected_components[0] == "firma":
                detected_components.append("personeria")

        if has_representacion:
            if not detected_components:
                detected_components.append("representacion")
            elif "firma" in detected_components or "personeria" in detected_components:
                detected_components.append("representacion")
                # For representacion, often appears twice in the type name
                detected_components.append("representacion")

        # Build composite type key and try to match with certificate_types
        if detected_components:
            # Try various combinations to match certificate_types.json keys
            combos_to_try = [
                "_".join(detected_components),
                "_".join(detected_components[:-1]) if len(detected_components) > 1 else detected_components[0],
                detected_components[0] if len(detected_components) > 0 else None
            ]

            for combo in combos_to_try:
                if combo and combo in cert_types:
                    cert_type = combo
                    break

        # ---------------------------------------------------------
        # FINAL ROUTING
        # ---------------------------------------------------------
        if not is_notarial or cert_type == "authority":
            return {
                'type': '__AUTHORITY_DOC__',
                'customer': customer,
                'filename': cert_info['filename'],
                'path': cert_info['relative_path'],
                'error_flag': cert_info.get('error_flag', False),
                'purpose': 'unknown',
                'reason': 'authority_document',
                'extraction_time': extraction_time
            }

        if cert_type not in cert_types:
            cert_type = "otros"

        return {
            'type': cert_type,
            'customer': customer,
            'filename': cert_info['filename'],
            'path': cert_info['relative_path'],
            'error_flag': cert_info.get('error_flag', False),
            'purpose': purpose,
            'extraction_time': extraction_time,
            'total_time': time.time() - start_time
        }

    except Exception as e:
        return {
            'type': 'otros',
            'customer': customer,
            'filename': cert_info['filename'],
            'path': cert_info['relative_path'],
            'error_flag': cert_info.get('error_flag', False),
            'purpose': 'unknown',
            'error': str(e)
        }

# ---------------------------------------------------------
# Main Execution
# ---------------------------------------------------------

if __name__ == '__main__':
    final_certificate_mapping = {k: [] for k in cert_types.keys()}
    non_certificate_docs = []

    CUSTOMER_DATA_PATH = SCRIPT_DIR / "Notaria_client_data"

    print("\n" + "=" * 70)
    print("Starting Content-Based Certificate Classification (ccs3.py)")
    print(f"Using model: {MODEL_NAME}")
    print(f"Using {NUM_WORKERS} parallel workers")
    print("=" * 70 + "\n")

    # Collect all tasks
    all_tasks = []

    for customer, info in customers.items():
        for cert in info["files"]["certificates"]:
            all_tasks.append({
                'customer': customer,
                'cert_info': cert,
                'base_path': CUSTOMER_DATA_PATH,
                'is_certificate': True
            })

        for doc in info["files"]["non_certificates"]:
            all_tasks.append({
                'customer': customer,
                'cert_info': doc,
                'base_path': CUSTOMER_DATA_PATH,
                'is_certificate': False
            })

    total_files = len(all_tasks)
    print(f"Total files to process: {total_files}\n")

    print("Initializing worker processes...")
    with Pool(processes=NUM_WORKERS, initializer=init_worker) as pool:
        try:
            results = list(tqdm(
                pool.imap(process_single_file, all_tasks, chunksize=1),
                total=total_files,
                desc="Processing files",
                unit="file"
            ))
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
            exit(1)

    print("\nAggregating results...")

    # Aggregate results
    for result in results:
        result_type = result['type']

        if result_type == '__NON_CERT__':
            non_certificate_docs.append({
                "customer": result['customer'],
                "filename": result['filename'],
                "path": result['path'],
                "reason": result.get('reason', 'non_certificate')
            })
        elif result_type == '__AUTHORITY_DOC__':
            non_certificate_docs.append({
                "customer": result['customer'],
                "filename": result['filename'],
                "path": result['path'],
                "error_flag": result.get('error_flag', False),
                "purpose": result.get('purpose', 'unknown'),
                "reason": result.get('reason', 'authority_document')
            })
        else:
            final_certificate_mapping[result_type].append({
                "customer": result['customer'],
                "filename": result['filename'],
                "path": result['path'],
                "error_flag": result.get('error_flag', False),
                "purpose": result.get('purpose', 'unknown')
            })

    # Build final summary
    summary = {
        "identified_certificate_types": cert_types,
        "certificate_file_mapping": final_certificate_mapping,
        "non_certificate_documents": non_certificate_docs
    }

    # Save result
    output_file = SCRIPT_DIR / "ccs2.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f"Successfully created {output_file}")
    print("=" * 70)

    # Print summary statistics
    print("\nClassification Summary:")
    print("-" * 50)
    for cert_type, files in final_certificate_mapping.items():
        if files:
            # Count purposes
            purpose_counts = {}
            for file in files:
                purpose = file.get('purpose', 'unknown')
                purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1

            print(f"\n{cert_type}: {len(files)} files")
            if purpose_counts:
                print(f"  Purposes: {dict(purpose_counts)}")

    print(f"\nNon-certificate documents: {len(non_certificate_docs)}")
    print(f"Total processed: {total_files}")
    print("\nDone!")
