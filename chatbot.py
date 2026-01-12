import json
import os
import re
import unicodedata
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import streamlit as st

from dotenv import load_dotenv
from groq import Groq

from src.phase1_certificate_intent import CertificateIntentCapture
from src.phase2_legal_requirements import LegalRequirementsEngine
from src.phase3_document_intake import DocumentIntake
from src.phase4_text_extraction import TextExtractor
from src.phase5_legal_validation import LegalValidator
from src.phase6_gap_detection import GapDetector
from src.phase7_data_update import DataUpdater
from src.phase8_final_confirmation import FinalConfirmationEngine
from src.phase9_certificate_generation import CertificateGenerator
from src.phase10_notary_review import NotaryReviewSystem, ReviewStatus
from src.phase11_final_output import FinalOutputGenerator


DEFAULT_SUMMARY_PATH = "cetificate from dataset/certificate_summary.json"
DEFAULT_CERT_TYPE = "certificacion_de_firmas"
DEFAULT_PURPOSE = "para_bps"
DEFAULT_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
MAX_LLM_CHARS = 3000


def get_default_option(options: List[Dict[str, str]], value: str) -> Dict[str, str]:
    for option in options:
        if option["value"] == value:
            return option
    return options[0] if options else {"value": value, "label": value}


def normalize_text(value: str) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    candidate = match.group(0) if match else text
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and "status" not in data:
        data["status"] = "ok"
    return data


def extract_text_for_llm(file_path: str) -> str:
    try:
        document = DocumentIntake.process_file(file_path)
        text, _ = TextExtractor.extract_text(document)
        return text
    except Exception:
        return ""


def normalize_purpose(value: str) -> str:
    if not value:
        return ""
    value = value.lower()
    value = value.replace("para_", "").replace("_", " ")
    return normalize_text(value)


def make_filename_keys(filename: str) -> List[str]:
    if not filename:
        return []
    path = Path(filename)
    keys = {
        normalize_text(path.name),
        normalize_text(path.stem),
    }
    return [key for key in keys if key]


@st.cache_data(show_spinner=False)
def build_llm_reference(summary: Dict[str, Any]) -> Dict[str, Any]:
    reference = {}
    for cert_type, info in summary.get("identified_certificate_types", {}).items():
        reference[cert_type] = {
            "count": info.get("count", 0),
            "purposes": list(info.get("purposes", {}).keys()),
            "attributes": info.get("attributes", []),
            "examples": info.get("examples", [])[:3],
        }
    return reference


def keyword_classification(doc_text: str, summary_reference: Dict[str, Any]) -> Dict[str, Any]:
    text_norm = normalize_text(doc_text)
    if not text_norm:
        return {"status": "error", "message": "No text for keyword classification."}

    best_type = None
    best_score = 0
    matched_attrs: List[str] = []

    for cert_type, info in summary_reference.items():
        attrs = [normalize_text(attr) for attr in info.get("attributes", [])]
        score = 0
        hits = []
        for attr in attrs:
            if attr and attr in text_norm:
                score += 1
                hits.append(attr)
        if score > best_score:
            best_score = score
            best_type = cert_type
            matched_attrs = hits

    detected_purpose = ""
    for cert_type, info in summary_reference.items():
        for purpose in info.get("purposes", []):
            purpose_norm = normalize_purpose(purpose)
            if purpose_norm and purpose_norm in text_norm:
                detected_purpose = purpose
                break
        if detected_purpose:
            break

    if best_type and best_score > 0:
        confidence = min(0.8, 0.2 + 0.1 * best_score)
        return {
            "status": "ok",
            "is_certificate": True,
            "certificate_type": best_type,
            "purpose": detected_purpose or "",
            "confidence": confidence,
            "reason": f"Matched attributes: {', '.join(matched_attrs)}" if matched_attrs else "Matched attributes.",
        }

    return {"status": "error", "message": "No keyword match found."}


def map_summary_type_to_intent(cert_type: str) -> str:
    cert_norm = normalize_text(cert_type)
    if "firma" in cert_norm:
        return "certificacion_de_firmas"
    if "personeria" in cert_norm:
        return "certificado_de_personeria"
    if "representacion" in cert_norm:
        return "certificado_de_representacion"
    if "vigencia" in cert_norm:
        return "certificado_de_vigencia"
    if "situacion" in cert_norm or "juridica" in cert_norm:
        return "certificado_de_situacion_juridica"
    if "poder" in cert_norm:
        return "poder_general"
    return "otros"


def map_summary_purpose_to_intent(purpose: str) -> str:
    if not purpose:
        return "otros"
    purpose_norm = normalize_text(purpose)
    if purpose.lower().startswith("para_"):
        return purpose.lower()

    mapping = {
        "bps": "para_bps",
        "abitab": "para_abitab",
        "dgi": "para_dgi",
        "zona franca": "para_zona_franca",
        "zona_franca": "para_zona_franca",
        "zonafranca": "para_zona_franca",
        "msp": "para_msp",
        "ute": "para_ute",
        "antel": "para_antel",
        "rupe": "para_rupe",
        "mef": "para_mef",
        "imm": "para_imm",
        "mtop": "para_mtop",
        "migraciones": "para_migraciones",
        "banco": "para_banco",
        "compraventa": "para_compraventa",
        "base de datos": "para_base_datos",
        "base datos": "para_base_datos",
    }

    for key, value in mapping.items():
        if key in purpose_norm:
            return value
    return "otros"


def is_positive_classification(result: Optional[Dict[str, Any]]) -> bool:
    if not result or result.get("status") == "error":
        return False
    if result.get("is_certificate") is False:
        return False
    cert_type = result.get("certificate_type")
    if not cert_type or cert_type == "non_certificate":
        return False
    return True


def choose_classification(
    llm_result: Optional[Dict[str, Any]],
    keyword_result: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if is_positive_classification(llm_result):
        return llm_result
    if is_positive_classification(keyword_result):
        return keyword_result
    return None


def derive_intent_override(classification: Dict[str, Any]) -> Optional[Dict[str, str]]:
    if not is_positive_classification(classification):
        return None
    cert_type = map_summary_type_to_intent(classification.get("certificate_type", ""))
    if cert_type == "otros":
        return None
    purpose = map_summary_purpose_to_intent(classification.get("purpose", ""))
    return {"certificate_type": cert_type, "purpose": purpose}


def call_groq_classification(
    model: str,
    api_key: str,
    doc_text: str,
    summary_reference: Dict[str, Any],
) -> Dict[str, Any]:
    if not api_key:
        return {"status": "error", "message": "Missing GROQ_API_KEY."}

    client = Groq(api_key=api_key)
    context_lines = []
    for cert_type, info in summary_reference.items():
        purposes = ", ".join(info.get("purposes", [])) or "none"
        examples = "; ".join(info.get("examples", [])) or "none"
        context_lines.append(
            f"- {cert_type}: purposes={purposes}; examples={examples}"
        )
    context_text = "\n".join(context_lines)

    prompt = (
        "You classify Uruguayan notarial documents.\n"
        "Use ONLY the categories provided. Reply with JSON only.\n"
        "Do not use Markdown or code fences.\n\n"
        "Categories (from certificate_summary.json):\n"
        f"{context_text}\n\n"
        "Return JSON with keys:\n"
        "is_certificate (true/false), certificate_type, purpose, confidence (0-1), reason.\n"
        "If non-certificate, set certificate_type='non_certificate'.\n\n"
        "Document text:\n"
        f"{doc_text[:MAX_LLM_CHARS]}\n"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a precise document classifier."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        content = response.choices[0].message.content or ""
        parsed = parse_json_from_text(content)
        if parsed is not None:
            return parsed
        return {
            "status": "error",
            "message": "LLM did not return valid JSON.",
            "raw": content,
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Groq request failed: {exc}",
        }


@st.cache_data(show_spinner=False)
def load_summary(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


@st.cache_data(show_spinner=False)
def build_summary_index(summary: Dict[str, Any]) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []

    for group, group_entries in summary.get("certificate_file_mapping", {}).items():
        for entry in group_entries:
            item = dict(entry)
            item["group"] = group
            item["entry_type"] = "certificate"
            entries.append(item)

    for entry in summary.get("non_certificate_documents", []):
        item = dict(entry)
        item["group"] = "non_certificate"
        item["entry_type"] = "non_certificate"
        entries.append(item)

    filename_index: Dict[str, List[Dict[str, Any]]] = {}
    customer_index: Dict[str, List[Dict[str, Any]]] = {}
    all_filenames_display: List[str] = []
    all_customers_display: List[str] = []

    for entry in entries:
        filename = entry.get("filename") or entry.get("path") or ""
        if filename:
            all_filenames_display.append(filename)
        for key in make_filename_keys(filename):
            filename_index.setdefault(key, []).append(entry)

        customer = entry.get("customer") or ""
        if customer:
            all_customers_display.append(customer)
        customer_key = normalize_text(customer)
        if customer_key:
            customer_index.setdefault(customer_key, []).append(entry)

    return {
        "entries": entries,
        "filename_index": filename_index,
        "customer_index": customer_index,
        "all_filenames_display": sorted(set(all_filenames_display)),
        "all_customers_display": sorted(set(all_customers_display)),
    }


def is_certificate_entry(entry: Dict[str, Any]) -> bool:
    return entry.get("entry_type") == "certificate"


def entry_has_error(entry: Dict[str, Any]) -> bool:
    return bool(entry.get("error_flag"))


def purpose_matches(entry_purpose: str, user_purpose: str) -> bool:
    if not entry_purpose or not user_purpose:
        return False
    entry_norm = normalize_purpose(entry_purpose)
    user_norm = normalize_purpose(user_purpose)
    if not entry_norm or not user_norm:
        return False
    return entry_norm == user_norm or entry_norm in user_norm or user_norm in entry_norm


def top_fuzzy_matches(query: str, candidates: List[str], limit: int = 5) -> List[Tuple[str, float]]:
    query_norm = normalize_text(query)
    if not query_norm:
        return []
    scored = []
    for candidate in candidates:
        candidate_norm = normalize_text(candidate)
        ratio = difflib.SequenceMatcher(None, query_norm, candidate_norm).ratio()
        scored.append((candidate, ratio))
    scored.sort(key=lambda item: item[1], reverse=True)
    return [(cand, score) for cand, score in scored[:limit] if score > 0]


def dedupe_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for entry in entries:
        key = (entry.get("customer"), entry.get("filename"), entry.get("path"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def match_document(
    filename: str,
    subject_name: str,
    extracted_company: Optional[str],
    purpose_value: str,
    summary_index: Dict[str, Any],
    llm_result: Optional[Dict[str, Any]] = None,
    keyword_result: Optional[Dict[str, Any]] = None,
    content_text: str = "",
    content_only: bool = False,
) -> Dict[str, Any]:
    if not content_only:
        filename_keys = make_filename_keys(filename)
        matched_entries: List[Dict[str, Any]] = []

        for key in filename_keys:
            matched_entries.extend(summary_index["filename_index"].get(key, []))

        matched_entries = dedupe_entries(matched_entries)

        if matched_entries:
            cert_entries = [e for e in matched_entries if is_certificate_entry(e)]
            non_cert_entries = [e for e in matched_entries if not is_certificate_entry(e)]
            if cert_entries:
                if any(entry_has_error(entry) for entry in cert_entries):
                    return {
                        "status": "not_found",
                        "match_type": "filename_error",
                        "confidence": 0.6,
                        "reason": "Filename matched, but entry is flagged as error in dataset.",
                        "matches": cert_entries,
                    }
                return {
                    "status": "correct",
                    "match_type": "filename",
                    "confidence": 1.0,
                    "reason": "Exact filename match found in certificate dataset.",
                    "matches": cert_entries,
                }
            if non_cert_entries:
                if llm_result and llm_result.get("is_certificate") is True:
                    return {
                        "status": "needs_review",
                        "match_type": "filename_non_certificate_llm_conflict",
                        "confidence": 0.6,
                        "reason": "Filename is non-certificate, but LLM classified as certificate.",
                        "matches": non_cert_entries,
                        "llm_result": llm_result,
                    }
                return {
                    "status": "not_found",
                    "match_type": "filename_non_certificate",
                    "confidence": 0.8,
                    "reason": "Filename matched, but document is classified as non-certificate.",
                    "matches": non_cert_entries,
                }

    customer_keys = []
    if subject_name:
        customer_keys.append(normalize_text(subject_name))
    if extracted_company and normalize_text(extracted_company) not in customer_keys:
        customer_keys.append(normalize_text(extracted_company))

    customer_matches: List[Dict[str, Any]] = []
    for key in customer_keys:
        customer_matches.extend(summary_index["customer_index"].get(key, []))
    customer_matches = dedupe_entries(customer_matches)

    if customer_matches:
        purpose_matches_entries = [
            entry for entry in customer_matches
            if purpose_matches(entry.get("purpose", ""), purpose_value)
        ]
        cert_entries = [e for e in purpose_matches_entries if is_certificate_entry(e)]
        if cert_entries:
            return {
                "status": "correct",
                "match_type": "customer_purpose",
                "confidence": 0.7,
                "reason": "Customer and purpose match found in certificate dataset.",
                "matches": cert_entries,
            }
        return {
            "status": "not_found",
            "match_type": "customer_only",
            "confidence": 0.5,
            "reason": "Customer match found, but no purpose match for this document.",
            "matches": customer_matches[:5],
        }

    if llm_result and llm_result.get("is_certificate") is True:
        llm_type = llm_result.get("certificate_type", "")
        llm_purpose = llm_result.get("purpose", "")
        summary_types = summary_index.get("summary_reference", {})
        if llm_type in summary_types:
            purpose_list = summary_types[llm_type].get("purposes", [])
            if not purpose_list or normalize_purpose(llm_purpose) in [
                normalize_purpose(p) for p in purpose_list
            ]:
                return {
                    "status": "correct",
                    "match_type": "llm_only",
                    "confidence": float(llm_result.get("confidence", 0.5)),
                    "reason": "LLM classified document type matches summary taxonomy.",
                    "matches": [],
                    "llm_result": llm_result,
                }

    if content_text:
        if not keyword_result:
            keyword_result = keyword_classification(content_text, summary_index.get("summary_reference", {}))
        if keyword_result.get("status") == "ok":
            return {
                "status": "correct",
                "match_type": "content_keywords",
                "confidence": float(keyword_result.get("confidence", 0.5)),
                "reason": keyword_result.get("reason", "Keyword match from content."),
                "matches": [],
                "llm_result": llm_result,
                "keyword_result": keyword_result,
            }

    filename_suggestions = top_fuzzy_matches(filename, summary_index["all_filenames_display"])
    customer_suggestions = top_fuzzy_matches(subject_name, summary_index["all_customers_display"])

    return {
        "status": "not_found",
        "match_type": "none",
        "confidence": 0.0,
        "reason": "No strong match found in certificate_summary.json.",
        "matches": [],
        "suggestions": {
            "filename": filename_suggestions,
            "customer": customer_suggestions,
        },
    }


def perform_web_search(query: str, provider: str, api_key: str) -> Dict[str, Any]:
    if not query:
        return {"status": "skipped", "message": "Empty query."}
    if not provider or provider == "none":
        return {"status": "skipped", "message": "Search provider not configured."}
    if not api_key:
        return {"status": "skipped", "message": "API key not provided."}
    return {
        "status": "not_implemented",
        "message": "Web search is not implemented yet. Add provider integration here.",
        "query": query,
    }


def extract_company_name(extraction_result) -> Optional[str]:
    for result in extraction_result.extraction_results:
        if result.success and result.extracted_data and result.extracted_data.company_name:
            return result.extracted_data.company_name
    return None


def run_flow(
    uploaded_path: str,
    original_filename: str,
    intent_inputs: Dict[str, str],
    summary_index: Dict[str, Any],
    notary_inputs: Dict[str, str],
    search_settings: Dict[str, str],
    llm_settings: Dict[str, str],
    content_only: bool,
) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    intent = CertificateIntentCapture.capture_intent_from_params(
        certificate_type=intent_inputs["certificate_type"],
        purpose=intent_inputs["purpose"],
        subject_name=intent_inputs["subject_name"],
        subject_type=intent_inputs["subject_type"],
        additional_notes=intent_inputs.get("additional_notes") or None,
    )

    requirements = LegalRequirementsEngine.resolve_requirements(intent)

    collection = DocumentIntake.create_collection(intent, requirements)
    collection = DocumentIntake.add_files_to_collection(collection, [uploaded_path])

    extraction = TextExtractor.process_collection(collection)
    results["phase4"] = extraction.get_summary()

    extracted_company = extract_company_name(extraction)
    subject_name = intent.subject_name.strip() or extracted_company or intent.subject_name
    if subject_name != intent.subject_name:
        intent.subject_name = subject_name

    doc_text = ""
    if content_only or llm_settings.get("enabled"):
        doc_text = extract_text_for_llm(uploaded_path)

    llm_result = None
    if llm_settings.get("enabled"):
        if doc_text:
            llm_result = call_groq_classification(
                model=llm_settings.get("model", DEFAULT_MODEL),
                api_key=llm_settings.get("api_key", ""),
                doc_text=doc_text,
                summary_reference=summary_index.get("summary_reference", {}),
            )
        else:
            llm_result = {"status": "error", "message": "No text extracted for LLM."}
        results["llm_result"] = llm_result

    keyword_result = None
    if doc_text:
        keyword_result = keyword_classification(doc_text, summary_index.get("summary_reference", {}))
        results["keyword_result"] = keyword_result

    chosen_classification = choose_classification(llm_result, keyword_result)
    intent_override = derive_intent_override(chosen_classification) if chosen_classification else None
    if intent_override:
        intent = CertificateIntentCapture.capture_intent_from_params(
            certificate_type=intent_override["certificate_type"],
            purpose=intent_override["purpose"],
            subject_name=subject_name,
            subject_type=intent.subject_type,
            additional_notes=intent.additional_notes,
        )
        requirements = LegalRequirementsEngine.resolve_requirements(intent)
        collection.certificate_intent = intent
        collection.legal_requirements = requirements
        results["intent_override"] = {
            "certificate_type": intent_override["certificate_type"],
            "purpose": intent_override["purpose"],
            "source": "llm" if chosen_classification == llm_result else "keywords",
            "confidence": chosen_classification.get("confidence", 0.0),
        }

    results["phase1"] = intent.get_display_summary()
    results["phase2"] = requirements.get_summary()
    results["phase3"] = collection.get_summary()

    match_result = match_document(
        filename=original_filename,
        subject_name=intent.subject_name,
        extracted_company=extracted_company,
        purpose_value=intent.purpose.value,
        summary_index=summary_index,
        llm_result=llm_result,
        keyword_result=keyword_result,
        content_text=doc_text,
        content_only=content_only,
    )
    results["match"] = match_result

    validation = LegalValidator.validate(requirements, extraction)
    results["phase5"] = validation.get_summary()

    gap_report = GapDetector.analyze(validation)
    results["phase6"] = gap_report.get_summary()

    update_result = DataUpdater.create_update_session(gap_report, collection)
    update_result.updated_extraction_result = extraction
    results["phase7"] = update_result.get_summary()

    confirmation = FinalConfirmationEngine.confirm(requirements, update_result)
    results["phase8"] = confirmation.get_summary()
    results["confirmation_report"] = confirmation

    if confirmation.can_proceed_to_phase9():
        certificate = CertificateGenerator.generate(
            certificate_intent=intent,
            legal_requirements=requirements,
            extraction_result=update_result.updated_extraction_result,
            confirmation_report=confirmation,
            notary_name=notary_inputs.get("notary_name"),
            notary_office=notary_inputs.get("notary_office"),
        )
        results["phase9"] = certificate.get_summary()
        results["certificate_text"] = certificate.get_formatted_text()

        review_session = NotaryReviewSystem.start_review(
            certificate=certificate,
            reviewer_name=notary_inputs.get("reviewer_name") or "Notary",
        )
        review_session = NotaryReviewSystem.approve_certificate(
            session=review_session,
            notes=notary_inputs.get("review_notes", ""),
        )
        results["phase10"] = review_session.get_summary()

        if review_session.status in [ReviewStatus.APPROVED, ReviewStatus.APPROVED_WITH_CHANGES]:
            final_cert = FinalOutputGenerator.generate_final_certificate(
                certificate=certificate,
                review_session=review_session,
                certificate_number=notary_inputs.get("certificate_number") or "AUTO-0001",
                issuing_notary=notary_inputs.get("notary_name") or "Notary",
                notary_office=notary_inputs.get("notary_office") or "Notary Office",
            )
            results["phase11"] = final_cert.get_summary()
    else:
        results["phase9"] = "Skipped: Phase 8 did not approve certificate generation."
        results["phase10"] = "Skipped: Phase 9 was not generated."
        results["phase11"] = "Skipped: Phase 10 was not approved."

    if match_result.get("status") == "not_found" and search_settings.get("enabled"):
        query = f"{intent.subject_name} {intent.purpose.value.replace('para_', '')}"
        search_result = perform_web_search(
            query=query,
            provider=search_settings.get("provider", "none"),
            api_key=search_settings.get("api_key", ""),
        )
        results["web_search"] = search_result

    return results


def render_match_result(match_result: Dict[str, Any]) -> None:
    status = match_result.get("status")
    reason = match_result.get("reason", "")
    confidence = match_result.get("confidence", 0.0)

    if status == "correct":
        st.success(f"Correct: {reason} (confidence {confidence:.2f})")
    elif status == "needs_review":
        st.warning(f"Needs review: {reason} (confidence {confidence:.2f})")
    else:
        st.error(f"Not found: {reason} (confidence {confidence:.2f})")

    matches = match_result.get("matches", [])
    if matches:
        st.write("Matched entries:")
        st.dataframe(matches)

    suggestions = match_result.get("suggestions", {})
    if suggestions:
        if suggestions.get("filename"):
            st.write("Top filename suggestions:")
            st.dataframe(suggestions["filename"], use_container_width=True)
        if suggestions.get("customer"):
            st.write("Top customer suggestions:")
            st.dataframe(suggestions["customer"], use_container_width=True)

    llm_result = match_result.get("llm_result")
    if llm_result:
        st.write("LLM classification:")
        st.json(llm_result)
    keyword_result = match_result.get("keyword_result")
    if keyword_result:
        st.write("Keyword classification:")
        st.json(keyword_result)


def main() -> None:
    st.set_page_config(page_title="Notarial Chatbot Flow", layout="wide")
    st.title("Notarial Chatbot Flow")
    st.write("Streamlit UI for phases 1-11, dataset matching, and optional web search stub.")
    st.info("Note: OCR requires Tesseract + Poppler installed on your system.")

    st.sidebar.header("Settings")
    with st.sidebar.expander("Dataset settings", expanded=False):
        summary_path = st.text_input("certificate_summary.json path", DEFAULT_SUMMARY_PATH)
    enable_llm = st.sidebar.checkbox("Enable LLM classification (Groq)", value=False)
    content_only = st.sidebar.checkbox("Match by content only", value=True)
    if enable_llm:
        load_dotenv()
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        llm_model = st.sidebar.text_input("Groq model", value=DEFAULT_MODEL)
        if groq_api_key:
            st.sidebar.caption("GROQ API key loaded from .env")
        else:
            st.sidebar.warning("GROQ API key not found in .env")
    else:
        groq_api_key = ""
        llm_model = DEFAULT_MODEL
    enable_search = st.sidebar.checkbox("Enable web search fallback (stub)", value=False)
    if enable_search:
        search_provider = st.sidebar.selectbox("Search provider", ["none", "serpapi", "bing"])
        search_api_key = st.sidebar.text_input("API key", type="password")
    else:
        search_provider = "none"
        search_api_key = ""

    summary_path_obj = Path(summary_path)
    if not summary_path_obj.exists():
        st.error(f"Summary file not found: {summary_path}")
        st.stop()

    summary_data = load_summary(summary_path)
    summary_index = build_summary_index(summary_data)
    summary_index["summary_reference"] = build_llm_reference(summary_data)

    st.sidebar.markdown("### Summary stats")
    st.sidebar.write(f"Total entries: {len(summary_index['entries'])}")
    st.sidebar.write(f"Certificates: {len([e for e in summary_index['entries'] if e['entry_type'] == 'certificate'])}")
    st.sidebar.write(f"Non-certificates: {len([e for e in summary_index['entries'] if e['entry_type'] == 'non_certificate'])}")

    st.subheader("Inputs")
    cert_types = CertificateIntentCapture.get_available_certificate_types()
    purposes = CertificateIntentCapture.get_available_purposes()
    default_cert_type = get_default_option(cert_types, DEFAULT_CERT_TYPE)
    default_purpose = get_default_option(purposes, DEFAULT_PURPOSE)

    simple_mode = st.checkbox("Simple mode (use defaults)", value=True)
    if simple_mode:
        st.caption(
            f"Defaults: {default_cert_type['label']} / {default_purpose['label']} / subject type = company."
        )

    cert_type = default_cert_type
    purpose = default_purpose
    subject_type = "company"
    additional_notes = ""
    notary_name = "Dr. Juan Perez"
    notary_office = "Notary Office"
    reviewer_name = "Dr. Juan Perez"
    certificate_number = "AUTO-0001"
    review_notes = "Auto-approved (demo)"

    with st.form("flow_form"):
        uploaded_file = st.file_uploader("Upload document", type=None)
        subject_name = st.text_input("Subject name (optional)", value="")

        if not simple_mode:
            with st.expander("Certificate details", expanded=True):
                cert_type_index = next(
                    (idx for idx, item in enumerate(cert_types) if item["value"] == default_cert_type["value"]),
                    0,
                )
                purpose_index = next(
                    (idx for idx, item in enumerate(purposes) if item["value"] == default_purpose["value"]),
                    0,
                )
                col1, col2 = st.columns(2)
                with col1:
                    cert_type = st.selectbox(
                        "Certificate type",
                        options=cert_types,
                        index=cert_type_index,
                        format_func=lambda x: x["label"],
                    )
                with col2:
                    purpose = st.selectbox(
                        "Purpose",
                        options=purposes,
                        index=purpose_index,
                        format_func=lambda x: x["label"],
                    )
                subject_type = st.selectbox("Subject type", ["company", "person"])
                additional_notes = st.text_input("Additional notes (optional)", value="")

            with st.expander("Notary info", expanded=False):
                notary_name = st.text_input("Notary name", value=notary_name)
                notary_office = st.text_input("Notary office", value=notary_office)
                reviewer_name = st.text_input("Reviewer name", value=reviewer_name)
                certificate_number = st.text_input("Certificate number", value=certificate_number)
                review_notes = st.text_input("Review notes", value=review_notes)

        submit = st.form_submit_button("Run flow")

    if not submit:
        return

    if not uploaded_file:
        st.error("Please upload a document before running the flow.")
        return

    tmp_dir = Path(".tmp_uploads")
    tmp_dir.mkdir(exist_ok=True)
    tmp_filename = f"{uuid4().hex}_{uploaded_file.name}"
    tmp_path = tmp_dir / tmp_filename
    tmp_path.write_bytes(uploaded_file.getbuffer())

    intent_inputs = {
        "certificate_type": cert_type["value"],
        "purpose": purpose["value"],
        "subject_name": subject_name.strip(),
        "subject_type": subject_type,
        "additional_notes": additional_notes.strip(),
    }
    notary_inputs = {
        "notary_name": notary_name.strip(),
        "notary_office": notary_office.strip(),
        "reviewer_name": reviewer_name.strip(),
        "certificate_number": certificate_number.strip(),
        "review_notes": review_notes.strip(),
    }
    search_settings = {
        "enabled": enable_search,
        "provider": search_provider,
        "api_key": search_api_key,
    }
    llm_settings = {
        "enabled": enable_llm,
        "model": llm_model,
        "api_key": groq_api_key,
    }

    try:
        results = run_flow(
            uploaded_path=str(tmp_path),
            original_filename=uploaded_file.name,
            intent_inputs=intent_inputs,
            summary_index=summary_index,
            notary_inputs=notary_inputs,
            search_settings=search_settings,
            llm_settings=llm_settings,
            content_only=content_only,
        )
    except Exception as exc:
        st.exception(exc)
        return
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    st.subheader("Dataset match result")
    render_match_result(results.get("match", {}))
    if results.get("intent_override"):
        override = results["intent_override"]
        st.info(
            "Intent overridden from content: "
            f"{override['certificate_type']} / {override['purpose']} "
            f"(source: {override['source']}, confidence: {override['confidence']:.2f})"
        )

    if results.get("web_search"):
        st.subheader("Web search fallback")
        st.write(results["web_search"])

    st.subheader("Phase outputs")
    phase_sections = [
        ("Phase 1", "phase1"),
        ("Phase 2", "phase2"),
        ("Phase 3", "phase3"),
        ("Phase 4", "phase4"),
        ("Phase 5", "phase5"),
        ("Phase 6", "phase6"),
        ("Phase 7", "phase7"),
        ("Phase 8", "phase8"),
        ("Phase 9", "phase9"),
        ("Phase 10", "phase10"),
        ("Phase 11", "phase11"),
    ]

    for label, key in phase_sections:
        with st.expander(label, expanded=False):
            st.code(str(results.get(key, "No output")), language="text")

    if results.get("certificate_text"):
        st.subheader("Generated certificate text")
        st.code(results["certificate_text"], language="text")


if __name__ == "__main__":
    main()
