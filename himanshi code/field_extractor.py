# field_extractor.py

import re
from typing import Dict


class FieldExtractor:
    """
    RESPONSIBILITY:
    - Convert OCR raw text into structured factual fields
    - NO legal decisions
    - NO validation
    """

    def extract_personeria_juridica(self, text: str) -> Dict:
        data = {}

        # --- Company name ---
        name_match = re.search(
            r"([A-ZÁÉÍÓÚÑ ]+S\.A\.)", text
        )
        if name_match:
            data["empresa.nombre"] = name_match.group(1).strip()

        # --- RUT ---
        rut_match = re.search(
            r"RUT[^0-9]*([\d\.]{6,}\-\d+|[\d\.]{6,})",
            text
        )
        if rut_match:
            data["empresa.rut"] = rut_match.group(1)

        # --- Legal existence ---
        data["empresa.plazo_vigente"] = "plazo vigente" in text.lower()

        # --- Representation info ---
        data["empresa.representacion"] = "forma de representación" in text.lower()

        # --- Law compliance flags ---
        data["empresa.ley_17904"] = "ley 17.904" in text.lower()
        data["empresa.ley_18930"] = "ley 18.930" in text.lower()
        data["empresa.ley_19484"] = "ley 19.484" in text.lower()

        # --- Registry mentions ---
        data["empresa.registro_comercio"] = "registro de personas jurídicas" in text.lower()

        return data
