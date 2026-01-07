"""
Phase 7: Data Update Attempt

This module handles:
- Attempting to fetch missing/outdated information
- Accepting manual document updates from notary
- Validating updated documents
- Tracking what was changed
- Preparing updated data for Phase 8 (final validation)

This is an OPTIONAL phase that reduces manual work by attempting
to auto-fetch public registry information or accepting updated uploads.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import os

from src.phase2_legal_requirements import DocumentType, LegalRequirements
from src.phase3_document_intake import UploadedDocument, DocumentCollection, DocumentIntake
from src.phase4_text_extraction import TextExtractor, CollectionExtractionResult
from src.phase6_gap_detection import Gap, GapType, GapAnalysisReport, ActionPriority


class UpdateSource(Enum):
    """Source of the update"""
    MANUAL_UPLOAD = "manual_upload"  # Notary uploaded new document
    PUBLIC_REGISTRY = "public_registry"  # Fetched from online registry
    SYSTEM_CORRECTION = "system_correction"  # Auto-corrected by system
    NOT_UPDATED = "not_updated"  # No update attempted/successful


class UpdateStatus(Enum):
    """Status of update attempt"""
    SUCCESS = "success"
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"
    PARTIAL = "partial"  # Some data updated, some not


@dataclass
class DocumentUpdate:
    """
    Represents an update to a single document or data field.
    """
    document_type: DocumentType
    gap_addressed: Gap
    update_source: UpdateSource
    update_status: UpdateStatus
    timestamp: datetime = field(default_factory=datetime.now)

    # Before/after tracking
    previous_state: Optional[str] = None
    new_state: Optional[str] = None

    # New document info (if uploaded)
    new_document: Optional[UploadedDocument] = None

    # Fetched data (if from registry)
    fetched_data: Optional[Dict] = None

    # Error info (if failed)
    error_message: Optional[str] = None

    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "document_type": self.document_type.value,
            "gap_addressed": self.gap_addressed.to_dict(),
            "update_source": self.update_source.value,
            "update_status": self.update_status.value,
            "timestamp": self.timestamp.isoformat(),
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "new_document": self.new_document.to_dict() if self.new_document else None,
            "fetched_data": self.fetched_data,
            "error_message": self.error_message,
            "notes": self.notes
        }

    def get_display(self) -> str:
        """Get formatted display string"""
        status_icons = {
            UpdateStatus.SUCCESS: "✅",
            UpdateStatus.FAILED: "❌",
            UpdateStatus.PARTIAL: "⚠️",
            UpdateStatus.NOT_ATTEMPTED: "⏭️"
        }

        icon = status_icons.get(self.update_status, "❓")

        display = f"""
{icon} Update: {self.document_type.value.upper()}
   Gap: {self.gap_addressed.title}
   Source: {self.update_source.value}
   Status: {self.update_status.value}
   Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M')}
"""

        if self.previous_state:
            display += f"   Before: {self.previous_state}\n"

        if self.new_state:
            display += f"   After: {self.new_state}\n"

        if self.new_document:
            display += f"   New Document: {self.new_document.filename}\n"

        if self.error_message:
            display += f"   Error: {self.error_message}\n"

        if self.notes:
            display += f"   Notes: {self.notes}\n"

        return display


@dataclass
class UpdateAttemptResult:
    """
    Results from attempting to update missing/outdated data.
    Contains the original gap report, all update attempts, and updated collection.
    """
    original_gap_report: GapAnalysisReport
    updates: List[DocumentUpdate] = field(default_factory=list)
    updated_collection: Optional[DocumentCollection] = None
    updated_extraction_result: Optional[CollectionExtractionResult] = None

    # Summary stats
    total_gaps: int = 0
    gaps_addressed: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    not_attempted: int = 0

    timestamp: datetime = field(default_factory=datetime.now)

    def calculate_summary(self):
        """Calculate summary statistics"""
        self.total_gaps = len(self.original_gap_report.gaps)

        for update in self.updates:
            if update.update_status == UpdateStatus.SUCCESS:
                self.successful_updates += 1
                self.gaps_addressed += 1
            elif update.update_status == UpdateStatus.FAILED:
                self.failed_updates += 1
            elif update.update_status == UpdateStatus.PARTIAL:
                self.gaps_addressed += 1
            elif update.update_status == UpdateStatus.NOT_ATTEMPTED:
                self.not_attempted += 1

    def to_dict(self) -> dict:
        return {
            "original_gap_report": self.original_gap_report.to_dict(),
            "updates": [u.to_dict() for u in self.updates],
            "updated_collection": self.updated_collection.to_dict() if self.updated_collection else None,
            "total_gaps": self.total_gaps,
            "gaps_addressed": self.gaps_addressed,
            "successful_updates": self.successful_updates,
            "failed_updates": self.failed_updates,
            "not_attempted": self.not_attempted,
            "timestamp": self.timestamp.isoformat()
        }

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def get_summary(self) -> str:
        """Get formatted summary"""
        self.calculate_summary()

        border = "=" * 70

        summary = f"""
{border}
           FASE 7: RESULTADO DE ACTUALIZACIÓN DE DATOS
{border}

📊 RESUMEN DE ACTUALIZACIONES:
   Total de brechas detectadas: {self.total_gaps}
   Brechas atendidas: {self.gaps_addressed}
   Actualizaciones exitosas: {self.successful_updates} ✅
   Actualizaciones fallidas: {self.failed_updates} ❌
   No intentadas: {self.not_attempted} ⏭️

📁 ESTADO DE COLECCIÓN:
   Documentos antes: {len(self.original_gap_report.validation_matrix.document_validations)}
   Documentos después: {len(self.updated_collection.documents) if self.updated_collection else 0}

⏰ Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

"""

        if self.successful_updates > 0:
            summary += "\n✅ ACTUALIZACIONES EXITOSAS:\n"
            summary += "-" * 70 + "\n"
            for update in self.updates:
                if update.update_status == UpdateStatus.SUCCESS:
                    summary += update.get_display() + "\n"

        if self.failed_updates > 0:
            summary += "\n❌ ACTUALIZACIONES FALLIDAS:\n"
            summary += "-" * 70 + "\n"
            for update in self.updates:
                if update.update_status == UpdateStatus.FAILED:
                    summary += update.get_display() + "\n"

        summary += "\n" + border + "\n"

        return summary

    def get_changes_report(self) -> str:
        """Get detailed report of what changed"""
        report = "\n" + "=" * 70 + "\n"
        report += "         REPORTE DETALLADO DE CAMBIOS - FASE 7\n"
        report += "=" * 70 + "\n\n"

        if not self.updates:
            report += "ℹ️  No se realizaron actualizaciones.\n"
            return report

        # Group by document type
        by_doc_type: Dict[DocumentType, List[DocumentUpdate]] = {}
        for update in self.updates:
            if update.document_type not in by_doc_type:
                by_doc_type[update.document_type] = []
            by_doc_type[update.document_type].append(update)

        for doc_type, updates_list in by_doc_type.items():
            report += f"\n📄 {doc_type.value.upper()}\n"
            report += "-" * 70 + "\n"

            for update in updates_list:
                report += update.get_display()

            report += "\n"

        return report


class DataUpdater:
    """
    Main class for Phase 7: Data Update Attempt
    """

    @staticmethod
    def create_update_session(gap_report: GapAnalysisReport, collection: DocumentCollection) -> UpdateAttemptResult:
        """
        Create a new update session from gap analysis report.

        Args:
            gap_report: GapAnalysisReport from Phase 6
            collection: Current DocumentCollection

        Returns:
            UpdateAttemptResult (initially empty, to be filled)
        """
        return UpdateAttemptResult(
            original_gap_report=gap_report,
            updated_collection=collection
        )

    @staticmethod
    def upload_updated_document(
        update_result: UpdateAttemptResult,
        gap: Gap,
        file_path: str,
        notes: str = ""
    ) -> UpdateAttemptResult:
        """
        Upload a new/updated document to address a gap.

        Args:
            update_result: Current UpdateAttemptResult
            gap: The gap being addressed
            file_path: Path to the new document file
            notes: Optional notes about this update

        Returns:
            Updated UpdateAttemptResult
        """
        try:
            # Verify file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Process the new document
            new_doc = DocumentIntake.process_file(file_path)

            # Get previous state
            previous_docs = update_result.updated_collection.get_documents_by_type(gap.affected_document)
            previous_state = f"{len(previous_docs)} documento(s) previo(s)" if previous_docs else "Sin documento previo"

            # Add to collection
            update_result.updated_collection.add_document(new_doc)

            # Create update record
            update = DocumentUpdate(
                document_type=gap.affected_document if gap.affected_document else DocumentType.DECLARACION_JURADA,
                gap_addressed=gap,
                update_source=UpdateSource.MANUAL_UPLOAD,
                update_status=UpdateStatus.SUCCESS,
                previous_state=previous_state,
                new_state=f"Documento cargado: {new_doc.file_name}",
                new_document=new_doc,
                notes=notes
            )

            update_result.updates.append(update)

            print(f"✅ Documento cargado exitosamente: {new_doc.file_name}")

        except Exception as e:
            # Record failed update
            update = DocumentUpdate(
                document_type=gap.affected_document if gap.affected_document else DocumentType.DECLARACION_JURADA,
                gap_addressed=gap,
                update_source=UpdateSource.MANUAL_UPLOAD,
                update_status=UpdateStatus.FAILED,
                error_message=str(e),
                notes=notes
            )

            update_result.updates.append(update)

            print(f"❌ Error al cargar documento: {str(e)}")

        return update_result

    @staticmethod
    def upload_multiple_documents(
        update_result: UpdateAttemptResult,
        gap_file_map: Dict[Gap, str],
        notes: str = ""
    ) -> UpdateAttemptResult:
        """
        Upload multiple documents at once.

        Args:
            update_result: Current UpdateAttemptResult
            gap_file_map: Dictionary mapping gaps to file paths
            notes: Optional notes

        Returns:
            Updated UpdateAttemptResult
        """
        for gap, file_path in gap_file_map.items():
            update_result = DataUpdater.upload_updated_document(
                update_result, gap, file_path, notes
            )

        return update_result

    @staticmethod
    def attempt_public_registry_fetch(
        update_result: UpdateAttemptResult,
        gap: Gap,
        company_name: Optional[str] = None,
        rut: Optional[str] = None
    ) -> UpdateAttemptResult:
        """
        Attempt to fetch missing data from public registries.

        NOTE: This is a PLACEHOLDER for future implementation.
        In production, this would:
        - Connect to Registro de Comercio API
        - Connect to DGI API
        - Connect to BPS API
        - Fetch and validate public records

        Args:
            update_result: Current UpdateAttemptResult
            gap: The gap being addressed
            company_name: Company name (for search)
            rut: RUT number (for search)

        Returns:
            Updated UpdateAttemptResult
        """
        # PLACEHOLDER IMPLEMENTATION
        # In real system, would call external APIs here

        update = DocumentUpdate(
            document_type=gap.affected_document if gap.affected_document else DocumentType.DECLARACION_JURADA,
            gap_addressed=gap,
            update_source=UpdateSource.PUBLIC_REGISTRY,
            update_status=UpdateStatus.NOT_ATTEMPTED,
            error_message="Función de consulta de registros públicos no implementada aún",
            notes="Requiere integración con APIs de: Registro de Comercio, DGI, BPS"
        )

        update_result.updates.append(update)

        print(f"⏭️  Consulta de registro público no disponible aún para: {gap.title}")

        return update_result

    @staticmethod
    def mark_gap_not_addressed(
        update_result: UpdateAttemptResult,
        gap: Gap,
        reason: str = "No se intentó actualización"
    ) -> UpdateAttemptResult:
        """
        Mark a gap as not being addressed.

        Args:
            update_result: Current UpdateAttemptResult
            gap: The gap not being addressed
            reason: Reason why not addressed

        Returns:
            Updated UpdateAttemptResult
        """
        update = DocumentUpdate(
            document_type=gap.affected_document if gap.affected_document else DocumentType.DECLARACION_JURADA,
            gap_addressed=gap,
            update_source=UpdateSource.NOT_UPDATED,
            update_status=UpdateStatus.NOT_ATTEMPTED,
            notes=reason
        )

        update_result.updates.append(update)

        return update_result

    @staticmethod
    def re_extract_data(update_result: UpdateAttemptResult) -> UpdateAttemptResult:
        """
        Re-run text extraction on the updated collection.

        Args:
            update_result: UpdateAttemptResult with updated documents

        Returns:
            UpdateAttemptResult with updated_extraction_result populated
        """
        if not update_result.updated_collection:
            print("⚠️  No hay colección actualizada para re-extraer")
            return update_result

        print("\n🔄 Re-extrayendo datos de documentos actualizados...")

        try:
            extraction_result = TextExtractor.process_collection(
                update_result.updated_collection
            )

            update_result.updated_extraction_result = extraction_result

            print(f"✅ Extracción completada: {len(extraction_result.document_extractions)} documentos procesados")

        except Exception as e:
            print(f"❌ Error en re-extracción: {str(e)}")

        return update_result

    @staticmethod
    def get_remaining_gaps(update_result: UpdateAttemptResult) -> List[Gap]:
        """
        Get list of gaps that were not successfully addressed.

        Args:
            update_result: UpdateAttemptResult

        Returns:
            List of remaining gaps
        """
        addressed_gap_ids = set()

        for update in update_result.updates:
            if update.update_status == UpdateStatus.SUCCESS:
                # Create unique ID from gap
                gap_id = f"{update.gap_addressed.gap_type.value}_{update.gap_addressed.affected_document.value if update.gap_addressed.affected_document else 'none'}"
                addressed_gap_ids.add(gap_id)

        remaining = []
        for gap in update_result.original_gap_report.gaps:
            gap_id = f"{gap.gap_type.value}_{gap.affected_document.value if gap.affected_document else 'none'}"
            if gap_id not in addressed_gap_ids:
                remaining.append(gap)

        return remaining

    @staticmethod
    def save_update_result(update_result: UpdateAttemptResult, output_path: str) -> None:
        """Save update result to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(update_result.to_json())
        print(f"\n✅ Resultado de actualización guardado en: {output_path}")

    @staticmethod
    def load_update_result(input_path: str) -> UpdateAttemptResult:
        """Load update result from JSON file (simplified)"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # NOTE: This is a simplified loader
        # In production, would need full deserialization
        print(f"✅ Resultado de actualización cargado desde: {input_path}")
        return data


def example_usage():
    """Example usage of Phase 7"""

    print("\n" + "="*70)
    print("  EJEMPLOS DE USO - FASE 7: ACTUALIZACIÓN DE DATOS")
    print("="*70)

    print("\n📌 Ejemplo 1: Crear sesión de actualización")
    print("-" * 70)
    print("""
# Asumiendo que tienes gap_report de Fase 6 y collection de Fase 3:
from src.phase7_data_update import DataUpdater

# Crear sesión de actualización
update_result = DataUpdater.create_update_session(gap_report, collection)
    """)

    print("\n📌 Ejemplo 2: Cargar documento actualizado")
    print("-" * 70)
    print("""
# Obtener gap urgente (documento faltante)
urgent_gap = gap_report.gaps[0]  # Por ejemplo, estatuto faltante

# Cargar el documento
update_result = DataUpdater.upload_updated_document(
    update_result=update_result,
    gap=urgent_gap,
    file_path="/path/to/estatuto_actualizado.pdf",
    notes="Estatuto actualizado con nueva acta"
)

print(update_result.get_summary())
    """)

    print("\n📌 Ejemplo 3: Cargar múltiples documentos")
    print("-" * 70)
    print("""
# Mapear gaps a archivos
gap_file_map = {
    gaps[0]: "/path/to/estatuto.pdf",
    gaps[1]: "/path/to/certificado_bps_nuevo.pdf",
    gaps[2]: "/path/to/acta_directorio.pdf"
}

# Cargar todos
update_result = DataUpdater.upload_multiple_documents(
    update_result=update_result,
    gap_file_map=gap_file_map,
    notes="Documentos actualizados del cliente"
)
    """)

    print("\n📌 Ejemplo 4: Re-extraer datos")
    print("-" * 70)
    print("""
# Después de cargar documentos, re-extraer datos
update_result = DataUpdater.re_extract_data(update_result)

# Ver resultado
print(update_result.get_summary())
print(update_result.get_changes_report())
    """)

    print("\n📌 Ejemplo 5: Verificar brechas restantes")
    print("-" * 70)
    print("""
# Ver qué gaps aún no se han resuelto
remaining_gaps = DataUpdater.get_remaining_gaps(update_result)

print(f"Brechas restantes: {len(remaining_gaps)}")
for gap in remaining_gaps:
    print(f"  - {gap.title} ({gap.priority.value})")
    """)

    print("\n📌 Ejemplo 6: Flujo completo (Fase 6 → Fase 7)")
    print("-" * 70)
    print("""
from src.phase6_gap_detection import GapDetector
from src.phase7_data_update import DataUpdater

# Fase 6: Análisis de brechas
gap_report = GapDetector.analyze(validation_matrix)

# Fase 7: Crear sesión de actualización
update_result = DataUpdater.create_update_session(gap_report, collection)

# Cargar documentos faltantes
for gap in gap_report.gaps:
    if gap.priority == ActionPriority.URGENT:
        if gap.gap_type == GapType.MISSING_DOCUMENT:
            # Aquí el notario carga el documento
            file_path = input(f"Cargar documento para {gap.title}: ")
            update_result = DataUpdater.upload_updated_document(
                update_result, gap, file_path
            )

# Re-extraer datos
update_result = DataUpdater.re_extract_data(update_result)

# Verificar resultado
print(update_result.get_summary())

# Guardar para Fase 8
DataUpdater.save_update_result(update_result, "update_result.json")

# Si todo está bien, continuar a Fase 8 (validación final)
if len(DataUpdater.get_remaining_gaps(update_result)) == 0:
    print("✅ Todas las brechas resueltas. Continuar a Fase 8.")
else:
    print("⚠️  Aún hay brechas sin resolver.")
    """)


if __name__ == "__main__":
    example_usage()
