# Fichier: app/tools/pdf_generator.py
import io
from pathlib import Path
from typing import Dict, Any
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging

logger = logging.getLogger(__name__)

# Pour l'instant on utilise les polices intégrées de ReportLab
# Helvetica supporte bien les caractères standards

def generate_pdf_overlay(data: Dict[str, Any], coordinates: Dict[str, tuple]) -> io.BytesIO:
    """
    Crée un PDF transparent contenant uniquement les données aux bonnes coordonnées.

    Args:
        data: Dictionnaire contenant les données à placer
        coordinates: Dictionnaire mappant les clés aux coordonnées (x, y)

    Returns:
        BytesIO contenant le PDF overlay
    """
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    # Police standard qui fonctionne bien
    c.setFont("Helvetica", 10)

    # Placer chaque donnée à ses coordonnées
    for key, (x, y) in coordinates.items():
        if key in data and data[key] is not None:
            value = str(data[key])
            c.drawString(x, y, value)
            logger.debug(f"Placed '{value}' at ({x}, {y}) for field {key}")

    c.save()
    packet.seek(0)
    return packet

def superimpose_pdf(template_path: Path, overlay_packet: io.BytesIO) -> bytes:
    """
    Superpose l'overlay de données sur le template de formulaire.

    Args:
        template_path: Chemin vers le PDF template
        overlay_packet: BytesIO contenant le PDF overlay avec les données

    Returns:
        bytes du PDF final avec les données superposées
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template PDF introuvable : {template_path}")

    # Lire le PDF template et l'overlay
    existing_pdf = PdfReader(template_path)
    overlay_pdf = PdfReader(overlay_packet)
    output_writer = PdfWriter()

    # Superposer l'overlay sur la première page
    if len(overlay_pdf.pages) > 0:
        page = existing_pdf.pages[0]
        overlay_page = overlay_pdf.pages[0]

        page.merge_page(overlay_page)
        output_writer.add_page(page)
        logger.info("Overlay applied to first page")
    else:
        output_writer.add_page(existing_pdf.pages[0])
        logger.warning("No overlay page created")

    # Ajouter les pages restantes sans modification
    for i in range(1, len(existing_pdf.pages)):
        output_writer.add_page(existing_pdf.pages[i])

    # Générer le PDF final
    final_buffer = io.BytesIO()
    output_writer.write(final_buffer)
    final_buffer.seek(0)

    logger.info(f"Generated PDF with {len(output_writer.pages)} pages")
    return final_buffer.getvalue()

def generate_multipage_pdf_overlay(data_by_page: Dict[int, Dict[str, Any]],
                                   coordinates_by_page: Dict[int, Dict[str, tuple]]) -> io.BytesIO:
    """
    Version avancée pour gérer plusieurs pages avec des données différentes.

    Args:
        data_by_page: Dict où la clé est le numéro de page (0-indexed) et la valeur les données
        coordinates_by_page: Dict où la clé est le numéro de page et la valeur les coordonnées

    Returns:
        BytesIO contenant le PDF overlay multi-pages
    """
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    # Traiter chaque page
    max_page = max(data_by_page.keys()) if data_by_page else 0

    for page_num in range(max_page + 1):
        if page_num > 0:
            c.showPage()  # Nouvelle page

        c.setFont("Helvetica", 10)

        # Récupérer les données et coordonnées pour cette page
        page_data = data_by_page.get(page_num, {})
        page_coords = coordinates_by_page.get(page_num, {})

        # Placer les données
        for key, (x, y) in page_coords.items():
            if key in page_data and page_data[key] is not None:
                value = str(page_data[key])
                c.drawString(x, y, value)
                logger.debug(f"Page {page_num}: Placed '{value}' at ({x}, {y}) for field {key}")

    c.save()
    packet.seek(0)
    return packet

def superimpose_multipage_pdf(template_path: Path, overlay_packet: io.BytesIO) -> bytes:
    """
    Superpose un overlay multi-pages sur un template multi-pages.

    Args:
        template_path: Chemin vers le PDF template
        overlay_packet: BytesIO contenant le PDF overlay multi-pages avec les données

    Returns:
        bytes du PDF final avec les données superposées sur toutes les pages
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template PDF introuvable : {template_path}")

    # Lire le PDF template et l'overlay
    existing_pdf = PdfReader(template_path)
    overlay_pdf = PdfReader(overlay_packet)
    output_writer = PdfWriter()

    # Superposer chaque page d'overlay sur la page correspondante du template
    for page_num in range(len(existing_pdf.pages)):
        template_page = existing_pdf.pages[page_num]

        # Si nous avons une page d'overlay correspondante, la fusionner
        if page_num < len(overlay_pdf.pages):
            overlay_page = overlay_pdf.pages[page_num]
            template_page.merge_page(overlay_page)
            logger.info(f"Overlay applied to page {page_num + 1}")

        output_writer.add_page(template_page)

    # Générer le PDF final
    final_buffer = io.BytesIO()
    output_writer.write(final_buffer)
    final_buffer.seek(0)

    logger.info(f"Generated multi-page PDF with {len(output_writer.pages)} pages")
    return final_buffer.getvalue()