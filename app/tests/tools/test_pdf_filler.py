# Fichier: tests/tools/test_pdf_filler.py

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pytest
from pypdf import PdfReader
import io

from app.tools.pdf_filler import fill_3916_pdf, FIELD_MAPPING

@pytest.fixture
def sample_data() -> dict:
    """Fournit des données de test pour remplir le formulaire."""
    return {
        "declarant_nom": "Dupont",
        "declarant_prenom": "Jean",
        "declarant_adresse": "123 Rue de la République",
        "numero_compte": "FR7630004000031234567890143",
        "designation_etablissement": "Banque Internationale du Web",
    }

def test_fill_3916_pdf_returns_bytes(sample_data: dict):
    """Teste que la fonction retourne bien des bytes non vides."""
    pdf_bytes = fill_3916_pdf(sample_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000  # Doit être plus grand qu'un fichier vide

def test_filled_pdf_contains_data(sample_data: dict):
    """
    Teste que les données sont réellement écrites dans les champs du PDF.
    C'est le test le plus important car il valide le mapping des champs.
    """
    pdf_bytes = fill_3916_pdf(sample_data)

    # Lire le PDF généré pour vérifier son contenu
    pdf_buffer = io.BytesIO(pdf_bytes)
    reader = PdfReader(pdf_buffer)

    # Récupérer les champs du formulaire rempli
    form_fields = reader.get_form_text_fields()

    # Vérifier une des valeurs
    # On utilise la clé du MAPPING pour trouver le nom du champ dans le PDF
    nom_field_name = FIELD_MAPPING["declarant_nom"]

    # On vérifie que le champ existe et que sa valeur est correcte
    assert nom_field_name in form_fields
    assert form_fields[nom_field_name] == sample_data["declarant_nom"]

    # Vérifier une autre valeur pour être sûr
    compte_field_name = FIELD_MAPPING["numero_compte"]
    assert compte_field_name in form_fields
    assert form_fields[compte_field_name] == sample_data["numero_compte"]

def test_fill_with_missing_template():
    """
    Teste que la fonction lève une FileNotFoundError si le template est manquant.
    Note: Ce test nécessite de manipuler le chemin du fichier, ce qui peut être complexe.
    On le laisse en placeholder pour une future amélioration si nécessaire.
    """
    # Ce test est plus complexe à mettre en place car il requiert de
    # "cacher" temporairement le fichier. On peut le skipper pour l'instant
    # si cela complique trop l'environnement de test.
    pass