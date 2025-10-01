# Fichier: app/tools/pdf_filler.py
# VERSION 3.0 - Générique et Réutilisable
import io
from pathlib import Path
from typing import Dict, Any
from pypdf import PdfReader, PdfWriter

def fill_pdf(template_path: Path, data: Dict[str, Any]) -> bytes:
    """
    Remplit n'importe quel formulaire PDF à partir d'un template et de données.
    Cet outil est maintenant 100% agnostique du formulaire.

    Args:
        template_path: Le chemin vers le fichier PDF template.
        data: Un dictionnaire où les clés sont les noms exacts des champs du PDF.
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template PDF introuvable : {template_path}")

    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    # La valeur pour cocher une case est souvent '/Yes' ou le nom de l'option.
    # On gère les booléens pour simplifier.
    fields_to_update = {
        key: ('/Yes' if value is True else str(value))
        for key, value in data.items()
        if value is not None
    }

    if fields_to_update:
        # Essayer de mettre à jour tous les champs sur toutes les pages
        for page_num, page in enumerate(writer.pages):
            try:
                writer.update_page_form_field_values(
                    page,
                    fields=fields_to_update,
                    auto_regenerate=False  # Important pour éviter les popups
                )
            except Exception as e:
                # Certaines pages peuvent ne pas avoir de champs
                pass

    pdf_buffer = io.BytesIO()
    writer.write(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()