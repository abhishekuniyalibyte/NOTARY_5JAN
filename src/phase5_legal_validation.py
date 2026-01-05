"""
Phase 5: Legal Validation Engine

This module validates extracted data against legal requirements:
- Checks if all required documents are present
- Validates document expiration dates
- Verifies data consistency across documents
- Checks compliance with Articles 248-255
- Generates validation matrix

This is the core validation engine that determines if a certificate can be issued.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import json

from src.phase2_legal_requirements import (
    LegalRequirements,
    DocumentType,
    DocumentRequirement,
    RequiredElement,
    ArticleReference
)
from src.phase4_text_extraction import (
    CollectionExtractionResult,
    ExtractedData,
    DocumentExtractionResult
)


class ValidationStatus(Enum):
    """Status of validation checks"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    MISSING = "missing"
    EXPIRED = "expired"
    PENDING = "pending"


class ValidationSeverity(Enum):
    """Severity level of validation issues"""
    CRITICAL = "critical"  # Blocks certificate issuance
    ERROR = "error"  # Should be fixed
    WARNING = "warning"  # Recommended to fix
    INFO = "info"  # Informational only


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""
    field: str
    issue_type: str
    severity: ValidationSeverity
    description: str
    legal_basis: Optional[str] = None  # Which article requires this
    recommendation: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "issue_type": self.issue_type,
            "severity": self.severity.value,
            "description": self.description,
            "legal_basis": self.legal_basis,
            "recommendation": self.recommendation
        }

    def get_display(self) -> str:
        """Get formatted display string"""
        severity_icon = {
            ValidationSeverity.CRITICAL: "🔴",
            ValidationSeverity.ERROR: "🟠",
            ValidationSeverity.WARNING: "🟡",
            ValidationSeverity.INFO: "🔵"
        }

        icon = severity_icon.get(self.severity, "⚪")
        display = f"{icon} {self.field}: {self.description}"

        if self.legal_basis:
            display += f"\n      Base legal: {self.legal_basis}"
        if self.recommendation:
            display += f"\n      Recomendación: {self.recommendation}"

        return display


@dataclass
class DocumentValidation:
    """Validation result for a single document"""
    document_type: DocumentType
    required: bool
    present: bool
    status: ValidationStatus
    issues: List[ValidationIssue] = field(default_factory=list)
    extracted_data: Optional[ExtractedData] = None

    def is_valid(self) -> bool:
        """Check if document passes validation"""
        if self.required and not self.present:
            return False
        if self.status in [ValidationStatus.INVALID, ValidationStatus.EXPIRED]:
            return False
        # Check for critical issues
        return not any(issue.severity == ValidationSeverity.CRITICAL for issue in self.issues)

    def to_dict(self) -> dict:
        return {
            "document_type": self.document_type.value if self.document_type else None,
            "required": self.required,
            "present": self.present,
            "status": self.status.value,
            "is_valid": self.is_valid(),
            "issues": [issue.to_dict() for issue in self.issues]
        }


@dataclass
class ElementValidation:
    """Validation result for a required element"""
    element: RequiredElement
    status: ValidationStatus
    value_found: Optional[str] = None
    issues: List[ValidationIssue] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if element passes validation"""
        return self.status == ValidationStatus.VALID

    def to_dict(self) -> dict:
        return {
            "element": self.element.value,
            "status": self.status.value,
            "value_found": self.value_found,
            "is_valid": self.is_valid(),
            "issues": [issue.to_dict() for issue in self.issues]
        }


@dataclass
class ValidationMatrix:
    """
    Complete validation matrix for a certificate request.
    This is the output of Phase 5.
    """
    legal_requirements: LegalRequirements
    extraction_result: CollectionExtractionResult

    # Validation results
    document_validations: List[DocumentValidation] = field(default_factory=list)
    element_validations: List[ElementValidation] = field(default_factory=list)
    cross_document_issues: List[ValidationIssue] = field(default_factory=list)

    # Summary
    validation_timestamp: datetime = field(default_factory=datetime.now)
    overall_status: ValidationStatus = ValidationStatus.PENDING
    can_issue_certificate: bool = False

    def get_all_issues(self) -> List[ValidationIssue]:
        """Get all validation issues"""
        all_issues = []

        for doc_val in self.document_validations:
            all_issues.extend(doc_val.issues)

        for elem_val in self.element_validations:
            all_issues.extend(elem_val.issues)

        all_issues.extend(self.cross_document_issues)

        return all_issues

    def get_critical_issues(self) -> List[ValidationIssue]:
        """Get only critical issues that block certificate issuance"""
        return [issue for issue in self.get_all_issues()
                if issue.severity == ValidationSeverity.CRITICAL]

    def get_issue_count_by_severity(self) -> Dict[ValidationSeverity, int]:
        """Get count of issues by severity"""
        counts = {severity: 0 for severity in ValidationSeverity}
        for issue in self.get_all_issues():
            counts[issue.severity] += 1
        return counts

    def to_dict(self) -> dict:
        issue_counts = self.get_issue_count_by_severity()

        return {
            "validation_timestamp": self.validation_timestamp.isoformat(),
            "overall_status": self.overall_status.value,
            "can_issue_certificate": self.can_issue_certificate,
            "issue_summary": {
                "critical": issue_counts[ValidationSeverity.CRITICAL],
                "error": issue_counts[ValidationSeverity.ERROR],
                "warning": issue_counts[ValidationSeverity.WARNING],
                "info": issue_counts[ValidationSeverity.INFO]
            },
            "document_validations": [dv.to_dict() for dv in self.document_validations],
            "element_validations": [ev.to_dict() for ev in self.element_validations],
            "cross_document_issues": [issue.to_dict() for issue in self.cross_document_issues]
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def get_summary(self) -> str:
        """Get human-readable summary in Spanish"""
        issue_counts = self.get_issue_count_by_severity()

        status_icon = {
            ValidationStatus.VALID: "✅",
            ValidationStatus.INVALID: "❌",
            ValidationStatus.WARNING: "⚠️",
            ValidationStatus.PENDING: "⏳"
        }

        icon = status_icon.get(self.overall_status, "❓")

        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║              MATRIZ DE VALIDACIÓN - FASE 5                   ║
╚══════════════════════════════════════════════════════════════╝

{icon} ESTADO GENERAL: {self.overall_status.value.upper()}
   ¿Puede emitir certificado?: {"✅ SÍ" if self.can_issue_certificate else "❌ NO"}

📊 RESUMEN DE PROBLEMAS:
   🔴 Críticos: {issue_counts[ValidationSeverity.CRITICAL]}
   🟠 Errores: {issue_counts[ValidationSeverity.ERROR]}
   🟡 Advertencias: {issue_counts[ValidationSeverity.WARNING]}
   🔵 Info: {issue_counts[ValidationSeverity.INFO]}

📄 VALIDACIÓN DE DOCUMENTOS ({len(self.document_validations)} total):
"""

        for doc_val in self.document_validations:
            doc_icon = "✅" if doc_val.is_valid() else "❌"
            doc_type = doc_val.document_type.value if doc_val.document_type else "desconocido"
            status_text = "REQUERIDO" if doc_val.required else "OPCIONAL"
            present_text = "PRESENTE" if doc_val.present else "FALTANTE"

            summary += f"\n   {doc_icon} {doc_type.upper()} [{status_text}] - {present_text}"

            if doc_val.issues:
                for issue in doc_val.issues:
                    summary += f"\n      {issue.get_display()}"

        summary += f"\n\n🔍 VALIDACIÓN DE ELEMENTOS ({len(self.element_validations)} total):\n"

        for elem_val in self.element_validations:
            elem_icon = "✅" if elem_val.is_valid() else "❌"
            elem_name = elem_val.element.value.replace('_', ' ').title()

            summary += f"\n   {elem_icon} {elem_name}: {elem_val.status.value.upper()}"
            if elem_val.value_found:
                summary += f" (Valor: {elem_val.value_found})"

            if elem_val.issues:
                for issue in elem_val.issues:
                    summary += f"\n      {issue.get_display()}"

        if self.cross_document_issues:
            summary += f"\n\n⚠️ PROBLEMAS DE CONSISTENCIA ENTRE DOCUMENTOS:\n"
            for issue in self.cross_document_issues:
                summary += f"\n   {issue.get_display()}"

        if self.can_issue_certificate:
            summary += "\n\n✅ TODOS LOS REQUISITOS CUMPLIDOS - LISTO PARA GENERAR CERTIFICADO"
        else:
            critical = self.get_critical_issues()
            if critical:
                summary += f"\n\n❌ NO PUEDE EMITIR CERTIFICADO - {len(critical)} PROBLEMAS CRÍTICOS:\n"
                for issue in critical:
                    summary += f"\n   {issue.get_display()}"

        return summary


class LegalValidator:
    """
    Main validation engine.
    Validates documents and data against legal requirements.
    """

    @staticmethod
    def validate_document_presence(
        requirements: LegalRequirements,
        extraction_result: CollectionExtractionResult
    ) -> List[DocumentValidation]:
        """
        Validate that all required documents are present.
        This is the first validation step.
        """
        validations = []

        # Get all extracted document types
        present_types = set()
        extraction_map = {}  # Map document type to extraction result

        for result in extraction_result.extraction_results:
            if result.success and result.extracted_data:
                doc_type = result.extracted_data.document_type
                if doc_type:
                    present_types.add(doc_type)
                    extraction_map[doc_type] = result.extracted_data

        # Check each required document
        for req_doc in requirements.required_documents:
            doc_type = req_doc.document_type
            is_present = doc_type in present_types

            validation = DocumentValidation(
                document_type=doc_type,
                required=req_doc.mandatory,
                present=is_present,
                status=ValidationStatus.VALID if is_present else ValidationStatus.MISSING,
                extracted_data=extraction_map.get(doc_type)
            )

            # If required but missing, add critical issue
            if req_doc.mandatory and not is_present:
                validation.issues.append(ValidationIssue(
                    field=doc_type.value,
                    issue_type="missing_document",
                    severity=ValidationSeverity.CRITICAL,
                    description=f"Falta documento obligatorio: {req_doc.description}",
                    legal_basis=req_doc.legal_basis,
                    recommendation=f"Cargar {req_doc.description}"
                ))

            validations.append(validation)

        return validations

    @staticmethod
    def validate_document_expiry(
        doc_validation: DocumentValidation,
        req_doc: DocumentRequirement,
        extracted_data: ExtractedData
    ) -> None:
        """
        Validate document expiry dates.
        Adds issues to the DocumentValidation object.
        """
        if not req_doc.expires or not req_doc.expiry_days:
            return

        # Try to find dates in the document
        if not extracted_data.dates:
            doc_validation.issues.append(ValidationIssue(
                field=f"{req_doc.document_type.value}_date",
                issue_type="missing_date",
                severity=ValidationSeverity.ERROR,
                description=f"No se pudo encontrar fecha en {req_doc.description}",
                legal_basis=req_doc.legal_basis,
                recommendation="Verificar que el documento incluya fecha de emisión"
            ))
            return

        # Parse the most recent date
        # TODO: Implement proper date parsing with multiple formats
        # For now, we'll check if ANY date is within the expiry period

        now = datetime.now()
        expiry_threshold = now - timedelta(days=req_doc.expiry_days)

        # Simple check: warn if document might be expired
        # In production, parse actual dates from extracted_data.dates
        doc_validation.issues.append(ValidationIssue(
            field=f"{req_doc.document_type.value}_expiry",
            issue_type="expiry_check_needed",
            severity=ValidationSeverity.WARNING,
            description=f"Verificar que {req_doc.description} no tenga más de {req_doc.expiry_days} días",
            legal_basis=req_doc.legal_basis,
            recommendation=f"El documento debe tener menos de {req_doc.expiry_days} días de antigüedad"
        ))

    @staticmethod
    def validate_required_elements(
        requirements: LegalRequirements,
        extraction_result: CollectionExtractionResult
    ) -> List[ElementValidation]:
        """
        Validate that all required elements are present in the extracted data.
        """
        validations = []

        # Aggregate all extracted data
        all_extracted_data = [
            result.extracted_data
            for result in extraction_result.extraction_results
            if result.success and result.extracted_data
        ]

        # Check each required element
        for element in requirements.required_elements:
            validation = LegalValidator._validate_single_element(element, all_extracted_data)
            validations.append(validation)

        return validations

    @staticmethod
    def _validate_single_element(
        element: RequiredElement,
        all_extracted_data: List[ExtractedData]
    ) -> ElementValidation:
        """Validate a single required element"""

        validation = ElementValidation(
            element=element,
            status=ValidationStatus.MISSING
        )

        # Check different element types
        if element == RequiredElement.COMPANY_NAME:
            # Look for company name in any document
            for data in all_extracted_data:
                if data.company_name:
                    validation.status = ValidationStatus.VALID
                    validation.value_found = data.company_name
                    return validation

            validation.issues.append(ValidationIssue(
                field="company_name",
                issue_type="missing_element",
                severity=ValidationSeverity.CRITICAL,
                description="No se encontró nombre de la empresa",
                legal_basis="Art. 248",
                recommendation="Verificar estatuto o documentos societarios"
            ))

        elif element == RequiredElement.RUT_NUMBER:
            for data in all_extracted_data:
                if data.rut:
                    validation.status = ValidationStatus.VALID
                    validation.value_found = data.rut
                    return validation

            validation.issues.append(ValidationIssue(
                field="rut",
                issue_type="missing_element",
                severity=ValidationSeverity.CRITICAL,
                description="No se encontró RUT",
                legal_basis="Art. 248",
                recommendation="Verificar documentos tributarios"
            ))

        elif element == RequiredElement.REGISTRY_INSCRIPTION:
            for data in all_extracted_data:
                if data.registro_comercio:
                    validation.status = ValidationStatus.VALID
                    validation.value_found = data.registro_comercio
                    return validation

            validation.issues.append(ValidationIssue(
                field="registro_comercio",
                issue_type="missing_element",
                severity=ValidationSeverity.CRITICAL,
                description="No se encontró inscripción en Registro de Comercio",
                legal_basis="Art. 249",
                recommendation="Cargar certificado de Registro de Comercio"
            ))

        elif element == RequiredElement.LEGAL_REPRESENTATIVE:
            # This would require more sophisticated name extraction
            validation.status = ValidationStatus.WARNING
            validation.issues.append(ValidationIssue(
                field="legal_representative",
                issue_type="verification_needed",
                severity=ValidationSeverity.WARNING,
                description="Verificar que se identifiquen los representantes legales",
                legal_basis="Art. 248",
                recommendation="Revisar acta de directorio"
            ))

        else:
            # Default: mark as needing verification
            validation.status = ValidationStatus.WARNING
            validation.issues.append(ValidationIssue(
                field=element.value,
                issue_type="manual_verification_needed",
                severity=ValidationSeverity.WARNING,
                description=f"Verificar manualmente: {element.value.replace('_', ' ')}",
                recommendation="Revisar documentos manualmente"
            ))

        return validation

    @staticmethod
    def validate_cross_document_consistency(
        extraction_result: CollectionExtractionResult
    ) -> List[ValidationIssue]:
        """
        Validate consistency across multiple documents.
        E.g., company name should be the same in all documents.
        """
        issues = []

        # Collect all company names
        company_names = set()
        rut_numbers = set()

        for result in extraction_result.extraction_results:
            if result.success and result.extracted_data:
                if result.extracted_data.company_name:
                    company_names.add(result.extracted_data.company_name)
                if result.extracted_data.rut:
                    rut_numbers.add(result.extracted_data.rut)

        # Check for inconsistencies
        if len(company_names) > 1:
            issues.append(ValidationIssue(
                field="company_name_consistency",
                issue_type="inconsistent_data",
                severity=ValidationSeverity.ERROR,
                description=f"Nombre de empresa inconsistente entre documentos: {', '.join(company_names)}",
                recommendation="Verificar que todos los documentos correspondan a la misma empresa"
            ))

        if len(rut_numbers) > 1:
            issues.append(ValidationIssue(
                field="rut_consistency",
                issue_type="inconsistent_data",
                severity=ValidationSeverity.ERROR,
                description=f"RUT inconsistente entre documentos: {', '.join(rut_numbers)}",
                recommendation="Verificar que todos los documentos correspondan al mismo RUT"
            ))

        return issues

    @staticmethod
    def validate(
        requirements: LegalRequirements,
        extraction_result: CollectionExtractionResult
    ) -> ValidationMatrix:
        """
        Main validation method.
        Runs all validation checks and returns complete validation matrix.
        """
        matrix = ValidationMatrix(
            legal_requirements=requirements,
            extraction_result=extraction_result
        )

        # Step 1: Validate document presence
        matrix.document_validations = LegalValidator.validate_document_presence(
            requirements, extraction_result
        )

        # Step 2: Validate document expiry
        for doc_val in matrix.document_validations:
            if doc_val.present and doc_val.extracted_data:
                # Find the requirement
                req_doc = next(
                    (req for req in requirements.required_documents
                     if req.document_type == doc_val.document_type),
                    None
                )
                if req_doc:
                    LegalValidator.validate_document_expiry(
                        doc_val, req_doc, doc_val.extracted_data
                    )

        # Step 3: Validate required elements
        matrix.element_validations = LegalValidator.validate_required_elements(
            requirements, extraction_result
        )

        # Step 4: Validate cross-document consistency
        matrix.cross_document_issues = LegalValidator.validate_cross_document_consistency(
            extraction_result
        )

        # Step 5: Determine overall status
        critical_issues = matrix.get_critical_issues()

        if critical_issues:
            matrix.overall_status = ValidationStatus.INVALID
            matrix.can_issue_certificate = False
        else:
            # Check if there are any errors
            all_issues = matrix.get_all_issues()
            has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in all_issues)

            if has_errors:
                matrix.overall_status = ValidationStatus.WARNING
                matrix.can_issue_certificate = False  # Don't issue with errors
            else:
                matrix.overall_status = ValidationStatus.VALID
                matrix.can_issue_certificate = True

        return matrix

    @staticmethod
    def save_validation_matrix(matrix: ValidationMatrix, output_path: str) -> None:
        """Save validation matrix to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(matrix.to_json())
        print(f"\n✅ Matriz de validación guardada en: {output_path}")


def example_usage():
    """Example usage of Phase 5"""

    print("\n" + "="*70)
    print("  EJEMPLOS DE USO - FASE 5: VALIDACIÓN LEGAL")
    print("="*70)

    print("\n📌 Ejemplo 1: Crear problemas de validación")
    print("-" * 70)

    issue1 = ValidationIssue(
        field="estatuto",
        issue_type="missing_document",
        severity=ValidationSeverity.CRITICAL,
        description="Falta estatuto social",
        legal_basis="Art. 248",
        recommendation="Cargar estatuto de la empresa"
    )

    print(issue1.get_display())

    issue2 = ValidationIssue(
        field="certificado_bps",
        issue_type="expired_document",
        severity=ValidationSeverity.ERROR,
        description="Certificado BPS vencido (más de 30 días)",
        legal_basis="Requisito BPS",
        recommendation="Obtener certificado BPS actualizado"
    )

    print(issue2.get_display())

    print("\n\n📌 Ejemplo 2: Flujo completo (requiere Fases 1-4)")
    print("-" * 70)
    print("Para ejecutar validación completa:")
    print("""
    # Fases 1-2: Intent y Requirements
    intent = CertificateIntentCapture.capture_intent_from_params(...)
    requirements = LegalRequirementsEngine.resolve_requirements(intent)

    # Fase 3: Document Collection
    collection = DocumentIntake.create_collection(intent, requirements)
    collection = DocumentIntake.add_files_to_collection(collection, file_paths)

    # Fase 4: Text Extraction
    extraction_result = TextExtractor.process_collection(collection)

    # Fase 5: Validation
    validation_matrix = LegalValidator.validate(requirements, extraction_result)
    print(validation_matrix.get_summary())

    if validation_matrix.can_issue_certificate:
        print("✅ Listo para generar certificado!")
    else:
        print("❌ Corregir problemas antes de emitir certificado")
    """)


if __name__ == "__main__":
    example_usage()
