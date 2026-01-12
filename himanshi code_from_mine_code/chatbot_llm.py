import json
import os
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

# LLM for intelligent field extraction
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("ERROR: groq library not installed. Run: pip install groq")


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
# 2) Field Extraction (Step 2) - LLM ONLY
# =========================================================

class LLMFieldExtractor:
    """
    Pure LLM-based field extractor.
    NO regex patterns. Only semantic understanding via LLM.
    """

    def __init__(self, legal_rules: Dict[str, Any]):
        """Initialize with legal rules and LLM client."""
        self.legal_rules = legal_rules

        if not GROQ_AVAILABLE:
            raise RuntimeError("Groq library not available. Install with: pip install groq")

        # Initialize Groq client
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not found in environment. Set it in .env file")

        self.llm_client = Groq(api_key=api_key)
        print("✅ LLM Field Extractor initialized with Groq API")

    def extract_fields(self, certificate_type: str, text: str) -> Dict[str, Any]:
        """
        Pure LLM extraction - semantic understanding only.
        No regex patterns at all.
        """
        if certificate_type not in self.legal_rules:
            return {}

        try:
            ruleset = self.legal_rules[certificate_type]
            requisitos = ruleset.get("requisitos", [])
            requisitos_condicionales = ruleset.get("requisitos_condicionales", [])

            # Build comprehensive prompt for LLM
            prompt = self._build_llm_prompt(certificate_type, text, requisitos, requisitos_condicionales)

            # Call Groq LLM
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Llama 4 Maverick
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert legal document analyzer specializing in Uruguayan notary certificates.

You understand:
- Legal Spanish terminology and variations
- Notarial formalities and requirements
- Semantic equivalence (e.g., "firmó ante mí" = "firma en presencia")
- Document structure and context

Analyze documents carefully and return ONLY valid JSON."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            # Parse LLM response
            llm_json = json.loads(response.choices[0].message.content)
            return llm_json.get("fields", {})

        except Exception as e:
            print(f"❌ LLM extraction error: {e}")
            # Return empty result on error
            return {}

    def _build_llm_prompt(
        self,
        certificate_type: str,
        text: str,
        requisitos: List[Dict],
        requisitos_condicionales: List[Dict]
    ) -> str:
        """
        Build a comprehensive prompt for pure LLM extraction.
        """
        # Build field definitions with examples
        field_definitions = []

        for req in requisitos:
            rule_id = req["id"]
            descripcion = req.get("descripcion", "")
            obligatorio = req.get("obligatorio", False)

            # Add semantic hints for better LLM understanding
            semantic_hints = self._get_semantic_hints(rule_id)

            field_definitions.append({
                "field_id": rule_id,
                "description": descripcion,
                "required": obligatorio,
                "semantic_variations": semantic_hints
            })

        # Add conditional fields
        conditional_fields = []
        for cond_block in requisitos_condicionales:
            condition_key = cond_block["condicion"]
            conditional_fields.append({
                "condition": condition_key,
                "description": self._get_condition_description(condition_key),
                "required_fields": [req["id"] for req in cond_block.get("requisitos", [])]
            })

        prompt = f"""Analyze this Uruguayan notary certificate and extract ALL required legal fields.

**Certificate Type:** {certificate_type}

**Document Text:**
{text[:3000]}

**Fields to Extract:**
{json.dumps(field_definitions, indent=2, ensure_ascii=False)}

**Conditional Requirements:**
{json.dumps(conditional_fields, indent=2, ensure_ascii=False)}

**Instructions:**
1. For each field, determine if the requirement is PRESENT in the document (true/false)
2. Understand semantic variations and legal terminology in Spanish
3. Examples of semantic equivalence:
   - "firmó ante mí" = "firma en presencia" = "suscribió en mi presencia" = true
   - "previa lectura" = "después de leer" = "lectura del documento" = true
   - "cédula 1.234.567-8" = "C.I. 1234567-8" = "documento de identidad" = true
4. For conditional fields, first check if the condition applies
5. Be thorough but precise - only mark true if evidence is clear

**Return Format (MUST be valid JSON):**
{{
  "fields": {{
    "field_id_1": true,
    "field_id_2": false,
    "conditional_field": false,
    ...
  }}
}}

Analyze carefully and return ONLY the JSON object."""

        return prompt

    def _get_semantic_hints(self, rule_id: str) -> List[str]:
        """
        Provide semantic hints to help LLM understand variations.
        """
        hints = {
            "individualizacion": [
                "nombre completo", "señor", "señora", "comparece",
                "nacionalidad", "mayor de edad", "nombre de la empresa"
            ],
            "identificacion": [
                "cédula", "C.I.", "pasaporte", "documento de identidad",
                "conocimiento personal", "de mi conocimiento"
            ],
            "lectura": [
                "lectura", "leído", "previa lectura", "después de leer",
                "le hice lectura", "se dio por enterado"
            ],
            "firma_en_presencia": [
                "en mi presencia", "ante mí", "firmó ante", "suscribió",
                "compareció y firmó", "otorgó el acto"
            ],
            "requerimiento": [
                "a mi requerimiento", "a solicitud", "me requirió",
                "solicitó", "pidió"
            ],
            "exhibicion": [
                "exhibió", "presentó", "mostró", "compulsa",
                "tuvo a la vista"
            ],
            "ratificacion": [
                "ratifica", "reconoce", "se ratifica en su contenido",
                "confirma", "da por válido"
            ],
            "suscripcion": [
                "suscribe", "firma", "suscripción", "autorización",
                "sello del escribano"
            ]
        }

        # Find matching hints
        for key, hint_list in hints.items():
            if key in rule_id.lower():
                return hint_list

        return []

    def _get_condition_description(self, condition_key: str) -> str:
        """
        Get human-readable description for conditional requirements.
        """
        descriptions = {
            "otorgante_no_sabe_o_no_puede_firmar": "El otorgante no sabe o no puede firmar"
        }
        return descriptions.get(condition_key, condition_key)


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

app = FastAPI(title="Notary Legal Validator Chat UI (LLM ONLY)")

# Load legal rules once at startup
with open(LEGAL_RULES_PATH, "r", encoding="utf-8") as f:
    legal_rules = json.load(f)

extractor = TextExtractor(lang="spa", ocr_dpi=300)

# Initialize LLM-only field extractor
try:
    field_extractor = LLMFieldExtractor(legal_rules=legal_rules)
    LLM_ENABLED = True
except RuntimeError as e:
    print(f"❌ Failed to initialize LLM: {e}")
    LLM_ENABLED = False
    field_extractor = None

validator = CertificateValidator(LEGAL_RULES_PATH)


@app.get("/", response_class=HTMLResponse)
def index():
    llm_status = "✅ ENABLED (LLM ONLY - No Regex)" if LLM_ENABLED else "❌ DISABLED - Configure GROQ_API_KEY"

    return HTMLResponse(
        f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Notary Validator – LLM Only (Pure AI)</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .row {{ display: flex; gap: 16px; }}
    .panel {{ flex: 1; border: 1px solid #ddd; border-radius: 8px; padding: 16px; }}
    #chat {{ height: 420px; overflow: auto; border: 1px solid #eee; padding: 12px; border-radius: 8px; background: #fafafa; }}
    .msg {{ margin: 8px 0; }}
    .me {{ font-weight: bold; }}
    .bot {{ font-weight: bold; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #fff; padding: 10px; border-radius: 8px; border: 1px solid #eee; max-height: 600px; overflow-y: auto; }}
    button {{ padding: 10px 14px; cursor: pointer; }}
    select, input[type="file"], input[type="text"] {{ width: 100%; padding: 8px; }}
    .status {{ background: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 16px; border-left: 4px solid #ffc107; }}
    .warning {{ color: #856404; }}
  </style>
</head>
<body>
  <h2>🤖 Notary Legal Validator – LLM Only (Pure AI)</h2>
  <div class="status">
    <strong>⚡ Mode:</strong> Pure LLM - Semantic Understanding Only<br>
    <strong>LLM Status:</strong> {llm_status}<br>
    <small class="warning">⚠️ This version uses ONLY LLM (no regex patterns). Best for non-standardized documents but slower (~3-5 sec/doc).</small>
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
      <button onclick="send()">🤖 Validate with AI</button>
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
  div.innerHTML = `<span class="${{role}}">${{role === 'me' ? 'Notary' : 'AI'}}:</span> ${{text}}`;
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
  addChat('bot', '🤖 Processing with LLM... (OCR + AI Semantic Analysis, ~3-5 seconds)');

  const form = new FormData();
  form.append('certificate_type', certType);
  form.append('message', msg);
  form.append('file', f);

  try {{
    const res = await fetch('/api/validate', {{ method: 'POST', body: form }});

    if (!res.ok) {{
      addChat('bot', `<span style="color:red">❌ Error: HTTP ${{res.status}}</span>`);
      return;
    }}

    const data = await res.json();

    const status = data.validation?.overall_status || 'UNKNOWN';
    const issues = (data.validation?.issues || []).length;
    const statusColor = status === 'GREEN' ? 'green' : status === 'RED' ? 'red' : 'orange';
    addChat('bot', `✅ Validation status: <b style="color:${{statusColor}}">${{status}}</b>. Issues: <b>${{issues}}</b>. (LLM Only)`);

    document.getElementById('jsonOut').textContent = JSON.stringify(data, null, 2);
  }} catch (error) {{
    addChat('bot', `<span style="color:red">❌ Error: ${{error.message}}</span>`);
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
    if not LLM_ENABLED:
        return JSONResponse(
            status_code=503,
            content={"error": "LLM not available. Configure GROQ_API_KEY in .env file"}
        )

    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF upload supported."})

    temp_path = f"/tmp/{datetime.utcnow().timestamp()}_{file.filename}"
    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)

    try:
        # Step 1: OCR
        extraction_result = extractor.extract(temp_path)

        # Step 2: Field extraction - LLM ONLY (Pure AI)
        extracted_fields = field_extractor.extract_fields(
            certificate_type=certificate_type,
            text=extraction_result.full_text
        )

        # Step 3: Validation
        validation = validator.validate(certificate_type=certificate_type, extracted_data=extracted_fields)

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
            "extraction_method": "LLM Only (Pure Semantic AI)",
        }

    finally:
        # Cleanup temp file
        try:
            os.remove(temp_path)
        except Exception:
            pass
