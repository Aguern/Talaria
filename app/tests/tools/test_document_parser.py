# Fichier: tests/tools/test_document_parser.py

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.tools.document_parser import extract_text_from_file
from app.tools.pdf_filler import PDF_TEMPLATE_PATH

def test_extract_text_from_pdf():
    """
    Teste l'extraction de texte à partir d'un fichier PDF existant (le template 3916).
    """
    # On utilise notre template PDF comme fichier de test
    with open(PDF_TEMPLATE_PATH, "rb") as f:
        pdf_bytes = f.read()

    text = extract_text_from_file(pdf_bytes)

    assert isinstance(text, str)
    assert len(text) > 100  # Le PDF n'est pas vide
    # On vérifie la présence d'un texte spécifique connu du formulaire
    assert "DÉCLARATION PAR UN RÉSIDENT" in text and "COMPTE OUVERT" in text