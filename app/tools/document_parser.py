# Fichier: app/tools/document_parser.py

import fitz  # PyMuPDF
import io
from typing import Union

def extract_text_from_file(file_content: bytes) -> str:
    """
    Extrait le texte brut d'un fichier (PDF ou texte).

    Args:
        file_content: Le contenu du fichier sous forme de bytes.

    Returns:
        Le texte extrait du document.
    """
    text = ""

    # D'abord, essayer de décoder comme texte simple
    try:
        # Tenter de décoder comme UTF-8 (fichier texte)
        text = file_content.decode('utf-8')
        if text:  # Si on a réussi à décoder, c'est un fichier texte
            return text
    except UnicodeDecodeError:
        # Ce n'est pas un fichier texte UTF-8, continuer avec le traitement PDF
        pass

    # Si ce n'est pas un fichier texte, essayer comme PDF
    try:
        # Ouvrir le document PDF à partir du contenu en mémoire
        pdf_document = fitz.open(stream=file_content, filetype="pdf")

        # Itérer sur chaque page et extraire le texte
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()

        pdf_document.close()
    except Exception as e:
        # Gérer les erreurs si le fichier n'est pas un PDF valide ou autre problème
        print(f"Erreur lors de l'extraction du texte du PDF : {e}")
        # Essayer une dernière fois avec différents encodages
        try:
            text = file_content.decode('latin-1')
        except:
            return ""

    return text