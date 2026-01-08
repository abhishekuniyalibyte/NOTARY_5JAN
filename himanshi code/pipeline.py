from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from text_extractor import TextExtractor
from field_extractor import FieldExtractor
from certificate_validator import CertificateValidator


class CertificatePipeline:
    """
    End-to-end orchestration pipeline.

    Input:
        - certificate_type (selected by notary)
        - list of document paths (uploaded or downloaded from Drive)

    Output:
        - deterministic legal validation report (GREEN / RED / UNKNOWN)
    """

    def __init__(
        self,
        legal_rules_path: str
    ):
        self.text_extractor = TextExtractor()
        self.field_extractor = FieldExtractor()
        self.validator = CertificateValidator(legal_rules_path)

    def run(
        self,
        certificate_type: str,
        document_paths: List[str]
    ) -> Dict[str, Any]:
        """
        Executes the full validation pipeline.
        """

        if not document_paths:
            return self._empty_documents_response(certificate_type)

        extracted_facts: Dict[str, Any] = {}
        document_trace: List[Dict[str, Any]] = []

        # ----------------------------
        # 1. Extract text from each document
        # ----------------------------
        for doc_path in document_paths:
            path = Path(doc_path)

            if not path.exists():
                document_trace.append({
                    "file": doc_path,
                    "status": "NOT_FOUND"
                })
                continue

            text_result = self.text_extractor.extract(str(path))

            document_trace.append({
                "file": path.name,
                "pages": [
                    {
                        "page": p.page_number,
                        "source": p.source,
                        "chars": len(p.text)
                    }
                    for p in text_result.pages
                ],
                "chars": len(text_result.full_text),
                "status": "READ"
            })

            # ----------------------------
            # 2. Extract factual fields from text
            # ----------------------------
            facts = self.field_extractor.extract_personeria_juridica(
                text_result.full_text
            )


            # Merge facts (later documents can override earlier ones)
            extracted_facts.update(facts)

        # ----------------------------
        # 3. Validate against legal rules
        # ----------------------------
        validation_result = self.validator.validate(
            certificate_type=certificate_type,
            extracted_data=extracted_facts
        )

        # ----------------------------
        # 4. Enrich response with traceability
        # ----------------------------
        validation_result["documents_processed"] = document_trace
        validation_result["extracted_data_keys"] = sorted(extracted_facts.keys())
        validation_result["pipeline_timestamp"] = datetime.utcnow().isoformat() + "Z"

        return validation_result

    # --------------------------------------------------
    # Helper responses
    # --------------------------------------------------

    def _empty_documents_response(self, certificate_type: str) -> Dict[str, Any]:
        return {
            "certificate_type": certificate_type,
            "overall_status": "RED",
            "can_proceed_to_draft": False,
            "issues": [
                {
                    "rule_id": "documents",
                    "severity": "ERROR",
                    "message": "No se proporcionaron documentos para validar",
                    "fuente_legal": {}
                }
            ],
            "documents_processed": [],
            "pipeline_timestamp": datetime.utcnow().isoformat() + "Z"
        }
