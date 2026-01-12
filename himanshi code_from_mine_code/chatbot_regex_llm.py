import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import pdfplumber
import pytesseract
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Optional: LLM for intelligent field extraction
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


# =========================================================
# 1) OCR / Text Extraction (Step 1)
# =========================================================

@dataclass
class ExtractedPage:
    page_number: int
    text: str
    source: str  # "pdf_text" | "ocr"


@dataclass
class ExtractionResult:
    full_text: str
    pages: List[ExtractedPage]


class TextExtractor:
    """
    OCR + text extraction only.
    NO validation. NO legal logic. NO LLM.
    """

    def __init__(self, lang: str = "spa", ocr_dpi: int = 300, tesseract_cmd: Optional[str] = None):
        self.lang = lang
        self.ocr_dpi = ocr_dpi
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract(self, file_path: str, max_pages: Optional[int] = None) -> ExtractionResult:
        ext = os.path.splitext(file_path)[1].lower()

        if ext != ".pdf":
            raise ValueError("Only PDF is supported in this UI right now (production-safe).")

        return self._extract_pdf(file_path, max_pages=max_pages)

    def _extract_pdf(self, pdf_path: str, max_pages: Optional[int]) -> ExtractionResult:
        pages_out: List[ExtractedPage] = []
        full_text_parts: List[str] = []

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            page_limit = total_pages if max_pages is None else min(total_pages, max_pages)

            for idx in range(page_limit):
                page = pdf.pages[idx]
                page_number = idx + 1

                # Try native PDF text first
                text = (page.extract_text() or "").strip()
                if text:
                    pages_out.append(ExtractedPage(page_number=page_number, text=text, source="pdf_text"))
                    full_text_parts.append(text)
                    continue

                # OCR fallback
                image = page.to_image(resolution=self.ocr_dpi).original
                ocr_text = pytesseract.image_to_string(image, lang=self.lang)
                pages_out.append(ExtractedPage(page_number=page_number, text=ocr_text, source="ocr"))
                if ocr_text.strip():
                    full_text_parts.append(ocr_text)

        return ExtractionResult(full_text="\n\n".join(full_text_parts).strip(), pages=pages_out)


# =========================================================
# 2) Field Extraction (Step 2) - HYBRID: REGEX + LLM
# =========================================================

class FieldExtractor:
    """
    HYBRID field extractor: Uses regex first, then LLM for enhancement.
    Works for ANY certificate type.
    """

    def __init__(self, legal_rules: Dict[str, Any], use_llm: bool = True):
        """Initialize with legal rules and LLM option."""
        self.legal_rules = legal_rules
        self.use_llm = use_llm and GROQ_AVAILABLE

        # Initialize Groq client if available
        if self.use_llm:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                self.llm_client = Groq(api_key=api_key)
            else:
                self.use_llm = False
                print("Warning: GROQ_API_KEY not found in environment, LLM disabled")

    def extract_fields(self, certificate_type: str, text: str) -> Dict[str, Any]:
        """
        Hybrid extraction: Regex first, then LLM enhancement.
        """
        data: Dict[str, Any] = {}

        if certificate_type not in self.legal_rules:
            return data

        # Step 1: REGEX-based extraction (fast, deterministic)
        regex_result = self._extract_with_regex(certificate_type, text)

        # Step 2: LLM enhancement (only if enabled and needed)
        if self.use_llm:
            llm_result = self._extract_with_llm(certificate_type, text, regex_result)
            # Merge: LLM overrides regex for uncertain fields
            data = self._merge_results(regex_result, llm_result)
        else:
            data = regex_result

        return data

    def _extract_with_regex(self, certificate_type: str, text: str) -> Dict[str, Any]:
        """
        Original regex-based extraction (from chatbot.py).
        Fast and reliable for common cases.
        """
        data: Dict[str, Any] = {}
        ruleset = self.legal_rules[certificate_type]
        t_upper = text.upper()
        t_lower = text.lower()

        # Get all required fields from legal rules
        requisitos = ruleset.get("requisitos", [])

        for req in requisitos:
            rule_id = req["id"]
            descripcion = req.get("descripcion", "").lower()

            # Generic pattern matching based on rule ID and description
            data[rule_id] = self._detect_field_regex(rule_id, descripcion, text, t_upper, t_lower)

        # Handle conditional requisitos
        for cond_block in ruleset.get("requisitos_condicionales", []):
            condition_key = cond_block["condicion"]
            data[condition_key] = self._detect_field_regex(condition_key, condition_key, text, t_upper, t_lower)

        return data

    def _detect_field_regex(self, rule_id: str, descripcion: str, text: str, t_upper: str, t_lower: str) -> bool:
        """
        Smart detection logic using regex patterns.
        """
        # Pattern 1: Individualizacion (name detection)
        if "individualizacion" in rule_id or "individualización" in descripcion:
            return self._detect_individualization(text)

        # Pattern 2: Identificacion (ID document detection)
        if "identificacion" in rule_id or "identificación" in descripcion:
            return self._detect_identification(text)

        # Pattern 3: Lectura del documento
        if "lectura" in rule_id or "lectura" in descripcion:
            return any(keyword in t_upper for keyword in [
                "LECTURA", "LEÍDO", "LEIDO", "LEÍ", "LEI"
            ])

        # Pattern 4: Firma en presencia
        if "firma_en_presencia" in rule_id or "presencia" in descripcion:
            return any(keyword in t_upper for keyword in [
                "EN MI PRESENCIA", "ANTE MÍ", "ANTE MI", "EN PRESENCIA"
            ])

        # Pattern 5: Requerimiento expreso
        if "requerimiento" in rule_id or "requerimiento" in descripcion:
            return any(keyword in t_upper for keyword in [
                "A MI REQUERIMIENTO", "A SOLICITUD", "REQUERIMIENTO"
            ])

        # Pattern 6: Exhibicion o compulsa
        if "exhibicion" in rule_id or "compulsa" in rule_id:
            return any(keyword in t_upper for keyword in [
                "EXHIBICIÓN", "EXHIBICION", "COMPULSA"
            ])

        # Pattern 7: Objeto del certificado
        if "objeto" in rule_id or "objeto" in descripcion:
            return len(text.strip()) > 100

        # Pattern 8: Documento fuente
        if "documento_fuente" in rule_id or "documento" in descripcion:
            return any(keyword in t_upper for keyword in [
                "DOCUMENTO", "CERTIFICADO", "ESCRITURA"
            ])

        # Pattern 9: Ratificacion
        if "ratificacion" in rule_id or "ratificación" in descripcion:
            return any(keyword in t_upper for keyword in [
                "RATIFICA", "RATIFICACIÓN", "RATIFICACION", "RECONOCE"
            ])

        # Pattern 10: Suscripcion
        if "suscripcion" in rule_id or "suscripción" in descripcion:
            return any(keyword in t_upper for keyword in [
                "SUSCRIBE", "SUSCRIPCIÓN", "SUSCRIPCION", "FIRMA"
            ])

        # Pattern 11: Conditional - no sabe/puede firmar
        if "no_sabe_o_no_puede" in rule_id:
            return any(keyword in t_upper for keyword in [
                "NO SABE FIRMAR", "NO PUEDE FIRMAR"
            ])

        return False

    def _detect_individualization(self, text: str) -> bool:
        """Detect if document contains person/company individualization."""
        patterns = [
            r"(señor|señora|sr\.|sra\.)\s+[A-ZÁÉÍÓÚÑ]",
            r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+",
            r"(uruguayo|uruguaya|extranjero|extranjera)",
            r"mayor de edad",
            r"[\"'][A-ZÁÉÍÓÚÑ\s]+S\.A\.[\"']",
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

    def _detect_identification(self, text: str) -> bool:
        """Detect if document contains identification."""
        patterns = [
            r"cédula.*?\d[\d\.\-]+",
            r"C\.I\.\s*\d[\d\.\-]+",
            r"pasaporte.*?\d+",
            r"documento.*?\d+",
            r"conocimiento personal",
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

    def _extract_with_llm(self, certificate_type: str, text: str, regex_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to validate and enhance regex results.
        LLM understands semantic variations that regex might miss.
        """
        if not self.use_llm:
            return {}

        try:
            ruleset = self.legal_rules[certificate_type]
            requisitos = ruleset.get("requisitos", [])

            # Build prompt for LLM
            prompt = self._build_llm_prompt(certificate_type, text, requisitos, regex_result)

            # Call Groq LLM
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Llama 4 Maverick
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal document analyzer for Uruguayan notary certificates. Extract fields accurately and return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            # Parse LLM response
            llm_json = json.loads(response.choices[0].message.content)
            return llm_json.get("fields", {})

        except Exception as e:
            print(f"LLM extraction error: {e}")
            return {}

    def _build_llm_prompt(self, certificate_type: str, text: str, requisitos: List[Dict], regex_result: Dict[str, Any]) -> str:
        """
        Build a focused prompt for LLM field extraction.
        """
        # Build list of fields to check
        fields_to_check = []
        for req in requisitos:
            rule_id = req["id"]
            descripcion = req.get("descripcion", "")
            regex_value = regex_result.get(rule_id, False)

            fields_to_check.append({
                "field_id": rule_id,
                "description": descripcion,
                "regex_detected": regex_value
            })

        prompt = f"""Analyze this Uruguayan notary certificate text and verify the following legal requirements.

Certificate Type: {certificate_type}

Document Text:
{text[:2000]}

Fields to verify:
{json.dumps(fields_to_check, indent=2, ensure_ascii=False)}

Instructions:
1. For each field, determine if the requirement is present in the document (true/false)
2. Understand semantic variations (e.g., "firmó ante mí" = "firma en presencia")
3. Return ONLY valid JSON in this format:

{{
  "fields": {{
    "field_id_1": true,
    "field_id_2": false,
    ...
  }}
}}

Be strict but understand legal language variations in Spanish."""

        return prompt

    def _merge_results(self, regex_result: Dict[str, Any], llm_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge regex and LLM results.
        Strategy: Use LLM result if it differs from regex (LLM is smarter for variations).
        """
        merged = regex_result.copy()

        for key, llm_value in llm_result.items():
            if key in merged:
                # LLM found something regex missed, or vice versa
                # Trust LLM for semantic understanding
                merged[key] = llm_value
            else:
                merged[key] = llm_value

        return merged


# =========================================================
# 3) Validator (Step 3) – deterministic legal engine
# =========================================================

class CertificateValidator:
    def __init__(self, legal_rules_path: str):
        with open(legal_rules_path, "r", encoding="utf-8") as f:
            self.legal_rules = json.load(f)

    def validate(self, certificate_type: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        if certificate_type not in self.legal_rules:
            return self._unknown_certificate_response(certificate_type)

        ruleset = self.legal_rules[certificate_type]

        issues: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        missing_items: List[str] = []
        checked_requisitos: List[str] = []

        # Mandatory requisitos
        for req in ruleset.get("requisitos", []):
            rule_id = req["id"]
            checked_requisitos.append(rule_id)

            value = self._resolve_rule_value(rule_id, extracted_data)

            if req.get("obligatorio", False):
                if not value:
                    issues.append(self._build_issue(rule_id, "ERROR", "Requisito obligatorio no cumplido", req.get("fuente_legal", {})))
                    missing_items.append(rule_id)
                    continue

            if req.get("puede_vencer", False):
                if self._is_expired(value):
                    issues.append(self._build_issue(rule_id, "ERROR", "Documento vencido", req.get("fuente_legal", {})))

        # Conditional requisitos
        for cond_block in ruleset.get("requisitos_condicionales", []):
            condition_key = cond_block["condicion"]
            if extracted_data.get(condition_key) is True:
                for req in cond_block.get("requisitos", []):
                    rule_id = req["id"]
                    checked_requisitos.append(rule_id)

                    value = self._resolve_rule_value(rule_id, extracted_data)
                    if not value:
                        issues.append(self._build_issue(rule_id, "ERROR", "Requisito condicional no cumplido", req.get("fuente_legal", {})))
                        missing_items.append(rule_id)

        overall_status = "GREEN" if not issues else "RED"

        return {
            "certificate_type": certificate_type,
            "overall_status": overall_status,
            "can_proceed_to_draft": overall_status == "GREEN",
            "checked_requisitos": checked_requisitos,
            "missing_items": missing_items,
            "issues": issues,
            "warnings": warnings,
            "legal_basis": ruleset.get("base_legal", {}),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def _resolve_rule_value(self, rule_id: str, extracted_data: Dict[str, Any]) -> Optional[Any]:
        RULE_MAPPING = {
            "global.constancia_cumplimiento_legal": "empresa.ley_18930",
        }

        mapped_key = RULE_MAPPING.get(rule_id)
        if mapped_key:
            return extracted_data.get(mapped_key)

        return extracted_data.get(rule_id)

    def _is_expired(self, value: Any) -> bool:
        if not value or not isinstance(value, str):
            return False
        try:
            return datetime.fromisoformat(value) < datetime.utcnow()
        except Exception:
            return False

    def _build_issue(self, rule_id: str, severity: str, message: str, fuente_legal: Dict[str, Any]) -> Dict[str, Any]:
        return {"rule_id": rule_id, "severity": severity, "message": message, "fuente_legal": fuente_legal}

    def _unknown_certificate_response(self, certificate_type: str) -> Dict[str, Any]:
        return {
            "certificate_type": certificate_type,
            "overall_status": "UNKNOWN",
            "can_proceed_to_draft": False,
            "issues": [
                {
                    "rule_id": "certificate_type",
                    "severity": "ERROR",
                    "message": "Tipo de certificado no definido en el sistema",
                    "fuente_legal": {},
                }
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


# =========================================================
# 4) FastAPI App + Chat UI
# =========================================================

LEGAL_RULES_PATH = os.environ.get("LEGAL_RULES_PATH", os.path.join("legal", "legal_rules.json"))

app = FastAPI(title="Notary Legal Validator Chat UI (LLM-Enhanced)")

# Load legal rules once at startup
with open(LEGAL_RULES_PATH, "r", encoding="utf-8") as f:
    legal_rules = json.load(f)

extractor = TextExtractor(lang="spa", ocr_dpi=300)
field_extractor = FieldExtractor(legal_rules=legal_rules, use_llm=True)  # LLM enabled
validator = CertificateValidator(LEGAL_RULES_PATH)


@app.get("/", response_class=HTMLResponse)
def index():
    llm_status = "✅ ENABLED" if field_extractor.use_llm else "❌ DISABLED (regex only)"

    return HTMLResponse(
        f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Notary Validator – LLM Enhanced</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .row {{ display: flex; gap: 16px; }}
    .panel {{ flex: 1; border: 1px solid #ddd; border-radius: 8px; padding: 16px; }}
    #chat {{ height: 420px; overflow: auto; border: 1px solid #eee; padding: 12px; border-radius: 8px; background: #fafafa; }}
    .msg {{ margin: 8px 0; }}
    .me {{ font-weight: bold; }}
    .bot {{ font-weight: bold; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #fff; padding: 10px; border-radius: 8px; border: 1px solid #eee; }}
    button {{ padding: 10px 14px; cursor: pointer; }}
    select, input[type="file"], input[type="text"] {{ width: 100%; padding: 8px; }}
    .status {{ background: #e3f2fd; padding: 8px; border-radius: 4px; margin-bottom: 16px; }}
  </style>
</head>
<body>
  <h2>Notary Legal Validator – LLM Enhanced 🚀</h2>
  <div class="status">
    <strong>LLM Status:</strong> {llm_status}<br>
    <small>Hybrid system: Regex (fast) + LLM (smart semantic understanding)</small>
  </div>

  <div class="row">
    <div class="panel">
      <label><b>Certificate Type</b></label>
      <select id="certType"></select>
      <br/><br/>
      <label><b>Upload PDF</b></label>
      <input id="pdfFile" type="file" accept="application/pdf" />
      <br/><br/>
      <label><b>Message (optional)</b></label>
      <input id="msg" type="text" placeholder="e.g., validate this certificate for personería" />
      <br/><br/>
      <button onclick="send()">Validate</button>
    </div>

    <div class="panel">
      <h4>Validation Log</h4>
      <div id="chat"></div>
      <h4>Latest JSON Output</h4>
      <pre id="jsonOut">{{}}</pre>
    </div>
  </div>

<script>
async function loadTypes() {{
  const res = await fetch('/api/certificate-types');
  const data = await res.json();
  const sel = document.getElementById('certType');
  sel.innerHTML = '';
  data.certificate_types.forEach(t => {{
    const opt = document.createElement('option');
    opt.value = t;
    opt.textContent = t;
    sel.appendChild(opt);
  }});
}}

function addChat(role, text) {{
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.className = 'msg';
  div.innerHTML = `<span class="${{role}}">${{role === 'me' ? 'Notary' : 'System'}}:</span> ${{text}}`;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}}

async function send() {{
  const certType = document.getElementById('certType').value;
  const msg = document.getElementById('msg').value || '';
  const f = document.getElementById('pdfFile').files[0];

  if (!f) {{
    addChat('bot', 'Please upload a PDF first.');
    return;
  }}

  addChat('me', `Certificate type: <b>${{certType}}</b> | Upload: <b>${{f.name}}</b>`);
  addChat('bot', 'Processing... (OCR + Regex + LLM analysis)');

  const form = new FormData();
  form.append('certificate_type', certType);
  form.append('message', msg);
  form.append('file', f);

  try {{
    const res = await fetch('/api/validate', {{ method: 'POST', body: form }});

    if (!res.ok) {{
      addChat('bot', `<span style="color:red">Error: HTTP ${{res.status}}</span>`);
      return;
    }}

    const data = await res.json();

    const status = data.validation?.overall_status || 'UNKNOWN';
    const issues = (data.validation?.issues || []).length;
    const statusColor = status === 'GREEN' ? 'green' : status === 'RED' ? 'red' : 'orange';
    const method = data.extraction_method || 'unknown';
    addChat('bot', `Validation status: <b style="color:${{statusColor}}">${{status}}</b>. Issues: <b>${{issues}}</b>. Method: ${{method}}`);

    document.getElementById('jsonOut').textContent = JSON.stringify(data, null, 2);
  }} catch (error) {{
    addChat('bot', `<span style="color:red">Error: ${{error.message}}</span>`);
    console.error('Validation error:', error);
  }}
}}

loadTypes();
</script>
</body>
</html>
        """
    )


@app.get("/api/certificate-types")
def get_certificate_types():
    all_types = validator.legal_rules.keys()
    certificate_types = [
        t for t in all_types
        if t.startswith("certificado_")
    ]
    return {"certificate_types": sorted(certificate_types)}


@app.post("/api/validate")
async def validate_pdf(
    certificate_type: str = Form(...),
    message: str = Form(""),
    file: UploadFile = File(...),
):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF upload supported."})

    temp_path = f"/tmp/{datetime.utcnow().timestamp()}_{file.filename}"
    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)

    try:
        # Step 1: OCR
        extraction_result = extractor.extract(temp_path)

        # Step 2: Field extraction - HYBRID (Regex + LLM)
        extracted_fields = field_extractor.extract_fields(
            certificate_type=certificate_type,
            text=extraction_result.full_text
        )

        # Step 3: Validation
        validation = validator.validate(certificate_type=certificate_type, extracted_data=extracted_fields)

        # Determine extraction method used
        extraction_method = "Hybrid (Regex + LLM)" if field_extractor.use_llm else "Regex only"

        # Response for UI + integration
        return {
            "input": {
                "certificate_type": certificate_type,
                "message": message,
                "filename": file.filename,
            },
            "ocr": {
                "pages": [{"page": p.page_number, "source": p.source, "chars": len(p.text)} for p in extraction_result.pages],
                "text_preview": extraction_result.full_text[:1200],
            },
            "extracted_fields": extracted_fields,
            "validation": validation,
            "extraction_method": extraction_method,
        }

    finally:
        # Cleanup temp file
        try:
            os.remove(temp_path)
        except Exception:
            pass
