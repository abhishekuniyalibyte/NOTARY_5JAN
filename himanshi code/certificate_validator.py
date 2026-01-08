import json
from datetime import datetime
from typing import Dict, Any, List


class CertificateValidator:
    def __init__(self, legal_rules_path: str):
        with open(legal_rules_path, "r", encoding="utf-8") as f:
            self.legal_rules = json.load(f)

    def validate(
        self,
        certificate_type: str,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        if certificate_type not in self.legal_rules:
            return self._unknown_certificate_response(certificate_type)

        ruleset = self.legal_rules[certificate_type]

        issues: List[Dict[str, Any]] = []
        checked_requisitos: List[str] = []

        # --- Mandatory requisitos ---
        for req in ruleset.get("requisitos", []):
            rule_id = req["id"]
            checked_requisitos.append(rule_id)

            if req.get("obligatorio", False):
                if rule_id not in extracted_data or not extracted_data[rule_id]:
                    issues.append(
                        self._build_issue(
                            rule_id,
                            "ERROR",
                            "Requisito obligatorio no cumplido",
                            req.get("fuente_legal", {})
                        )
                    )

                if req.get("puede_vencer", False):
                    if self._is_expired(extracted_data.get(rule_id)):
                        issues.append(
                            self._build_issue(
                                rule_id,
                                "ERROR",
                                "Documento vencido",
                                req.get("fuente_legal", {})
                            )
                        )

        # --- Conditional requisitos ---
        for cond_block in ruleset.get("requisitos_condicionales", []):
            if extracted_data.get(cond_block["condicion"]) is True:
                for req in cond_block.get("requisitos", []):
                    rule_id = req["id"]
                    checked_requisitos.append(rule_id)

                    if rule_id not in extracted_data:
                        issues.append(
                            self._build_issue(
                                rule_id,
                                "ERROR",
                                "Requisito condicional no cumplido",
                                req.get("fuente_legal", {})
                            )
                        )

        status = "GREEN" if not issues else "RED"

        return {
            "certificate_type": certificate_type,
            "overall_status": status,
            "can_proceed_to_draft": status == "GREEN",
            "checked_requisitos": checked_requisitos,
            "issues": issues,
            "warnings": [],
            "missing_items": [],
            "legal_basis": ruleset.get("base_legal", {}),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    # ----------------- helpers -----------------

    def _is_expired(self, date_value: Any) -> bool:
        if not date_value:
            return False
        try:
            return datetime.fromisoformat(date_value) < datetime.utcnow()
        except Exception:
            return False

    def _build_issue(
        self,
        rule_id: str,
        severity: str,
        message: str,
        fuente_legal: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "rule_id": rule_id,
            "severity": severity,
            "message": message,
            "fuente_legal": fuente_legal
        }

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
                    "fuente_legal": {}
                }
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
