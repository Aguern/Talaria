# Fichier: tests/tools/test_document_classifier.py

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pytest
from app.tools.document_classifier import classify_document, DocumentType

@pytest.fixture
def cni_text_fixture() -> str:
    """Texte factice simulant une Carte Nationale d'Identité."""
    return """
    RÉPUBLIQUE FRANÇAISE
    CARTE NATIONALE D'IDENTITÉ N° XXXXXXXX
    Nom: DUPONT
    Prénoms: Jean, Jacques
    Né(e) le: 01/01/1980 à PARIS
    """

@pytest.fixture
def rib_text_fixture() -> str:
    """Texte factice simulant un RIB."""
    return """
    RELEVÉ D'IDENTITÉ BANCAIRE - RIB
    Titulaire: M. Jean DUPONT
    IBAN: FR76 3000 4000 0312 3456 7890 143
    BIC: BNPAFRPPXXX
    Banque: Ma Banque Populaire
    """

@pytest.fixture
def avis_imposition_text_fixture() -> str:
    """Texte factice simulant un Avis d'Imposition."""
    return """
    AVIS D'IMPÔT 2024 SUR LES REVENUS 2023
    Direction Générale des Finances Publiques
    Numéro fiscal: 1234567890123
    Adresse: 10 RUE DE LA PAIX, 75001 PARIS
    """

@pytest.mark.asyncio
@pytest.mark.external_api
async def test_classify_cni(cni_text_fixture: str):
    """Teste la classification correcte d'une CNI."""
    result = await classify_document(cni_text_fixture)
    assert result == DocumentType.CNI

@pytest.mark.asyncio
@pytest.mark.external_api
async def test_classify_rib(rib_text_fixture: str):
    """Teste la classification correcte d'un RIB."""
    result = await classify_document(rib_text_fixture)
    assert result == DocumentType.RIB

@pytest.mark.asyncio
@pytest.mark.external_api
async def test_classify_avis_imposition(avis_imposition_text_fixture: str):
    """Teste la classification correcte d'un Avis d'Imposition."""
    result = await classify_document(avis_imposition_text_fixture)
    assert result == DocumentType.AVIS_IMPOSITION

@pytest.mark.asyncio
@pytest.mark.external_api
async def test_classify_unknown():
    """Teste qu'un texte ambigu est classifié comme INCONNU."""
    unknown_text = "Ceci est une facture pour l'achat d'un croissant le 15 mars."
    result = await classify_document(unknown_text)
    assert result == DocumentType.INCONNU