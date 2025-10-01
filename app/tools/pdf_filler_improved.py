# Fichier: app/tools/pdf_filler_improved.py
# VERSION 5.0 - Amélioration de pypdf pour support multi-pages
import io
from pathlib import Path
from typing import Dict, Any, List, Optional
from pypdf import PdfReader, PdfWriter
import logging

logger = logging.getLogger(__name__)

def fill_pdf(template_path: Path, data: Dict[str, Any]) -> bytes:
    """
    Remplit un formulaire PDF sur TOUTES les pages.
    Gère correctement les cases à cocher et les champs texte.

    Args:
        template_path: Le chemin vers le fichier PDF template.
        data: Un dictionnaire où les clés sont les noms exacts des champs du PDF.

    Returns:
        bytes: Le PDF rempli sous forme de bytes.
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template PDF introuvable : {template_path}")

    reader = PdfReader(template_path)
    writer = PdfWriter()

    # Cloner le document
    writer.clone_document_from_reader(reader)

    # Préparer les données
    fields_to_update = {}
    for key, value in data.items():
        if value is not None:
            # Gérer les différents types de valeurs
            if isinstance(value, bool):
                # Pour les cases à cocher
                fields_to_update[key] = '/Yes' if value else '/Off'
            elif value == "Yes" or value == "yes" or value == "X":
                # Autres façons de dire "coché"
                fields_to_update[key] = '/Yes'
            elif value == "No" or value == "no" or value == "":
                fields_to_update[key] = '/Off'
            else:
                # Pour les champs texte
                fields_to_update[key] = str(value)

    logger.info(f"Remplissage de {len(fields_to_update)} champs sur le PDF")

    # Mettre à jour les champs sur TOUTES les pages
    if fields_to_update:
        # Méthode 1: Essayer de mettre à jour tous les champs globalement
        try:
            writer.update_page_form_field_values(
                writer.pages[0],  # Page de référence
                fields=fields_to_update,
                auto_regenerate=False  # Important pour éviter les popups
            )
        except Exception as e:
            logger.warning(f"Mise à jour globale échouée: {e}")

            # Méthode 2: Mettre à jour page par page
            for page_num, page in enumerate(writer.pages):
                try:
                    writer.update_page_form_field_values(
                        page,
                        fields=fields_to_update,
                        auto_regenerate=False
                    )
                    logger.debug(f"Page {page_num} mise à jour")
                except Exception as e:
                    logger.debug(f"Page {page_num}: {e}")

    # Convertir en bytes
    pdf_buffer = io.BytesIO()
    writer.write(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


def inspect_pdf_fields(template_path: Path) -> Dict[str, Any]:
    """
    Inspecte un PDF pour lister tous les champs disponibles.

    Args:
        template_path: Le chemin vers le fichier PDF.

    Returns:
        Dict avec les informations sur les champs.
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template PDF introuvable : {template_path}")

    reader = PdfReader(template_path)
    fields = reader.get_fields()

    if not fields:
        return {
            "field_count": 0,
            "fields": {},
            "field_names": []
        }

    field_info = {}
    for field_name, field_obj in fields.items():
        field_info[field_name] = {
            "type": field_obj.get("/FT", "Unknown"),
            "value": field_obj.get("/V", None),
            "default": field_obj.get("/DV", None),
            "options": field_obj.get("/Opt", None)
        }

    return {
        "field_count": len(fields),
        "fields": field_info,
        "field_names": list(fields.keys()),
        "text_fields": [k for k, v in field_info.items() if v["type"] == "/Tx"],
        "checkboxes": [k for k, v in field_info.items() if v["type"] == "/Btn"],
        "dropdowns": [k for k, v in field_info.items() if v["type"] == "/Ch"]
    }


def fill_pdf_with_mapping(template_path: Path, data: Dict[str, Any],
                          checkbox_fields: Optional[List[str]] = None) -> bytes:
    """
    Version améliorée qui connaît les types de champs.

    Args:
        template_path: Le chemin vers le fichier PDF.
        data: Les données à remplir.
        checkbox_fields: Liste des noms de champs qui sont des cases à cocher.

    Returns:
        bytes: Le PDF rempli.
    """
    if not checkbox_fields:
        # Détection automatique
        info = inspect_pdf_fields(template_path)
        checkbox_fields = info.get("checkboxes", [])

    # Adapter les données selon le type de champ
    adapted_data = {}
    for key, value in data.items():
        if key in checkbox_fields:
            # C'est une case à cocher
            if isinstance(value, bool):
                adapted_data[key] = '/Yes' if value else '/Off'
            elif str(value).lower() in ["yes", "true", "x", "oui", "1"]:
                adapted_data[key] = '/Yes'
            else:
                adapted_data[key] = '/Off'
        else:
            # C'est un champ texte
            if value is not None and value is not False:
                adapted_data[key] = str(value)

    return fill_pdf(template_path, adapted_data)