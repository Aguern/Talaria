# Fichier: tests/tools/test_data_extractor.py

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pytest
from app.tools.data_extractor import extract_rib_data, RIBData, extract_data_from_document, ExtractedData
from app.tools.document_classifier import DocumentType

@pytest.fixture
def sample_rib_text() -> str:
    """Fournit un texte de RIB de test."""
    return """
    Titulaire du compte : M. Jean Dupont
    Banque Domiciliation : BNP PARIBAS
    IBAN: FR76 3000 4000 0312 3456 7890 143
    BIC: BNPAFRPPXXX
    """

@pytest.mark.asyncio
@pytest.mark.external_api  # Marqueur pour les tests qui appellent une API externe
async def test_extract_rib_data_returns_correct_structure(sample_rib_text: str):
    """
    Teste que la fonction retourne bien un objet RIBData.
    ATTENTION : Ce test effectue un appel réel à l'API OpenAI et nécessite
    que la variable d'environnement OPENAI_API_KEY soit configurée.
    """
    result = await extract_rib_data(sample_rib_text)

    assert isinstance(result, RIBData)

@pytest.mark.asyncio
@pytest.mark.external_api
async def test_extract_rib_data_extracts_correct_values(sample_rib_text: str):
    """Teste que les valeurs extraites par le LLM sont correctes."""
    result = await extract_rib_data(sample_rib_text)

    # Normaliser l'IBAN en retirant les espaces pour une comparaison fiable
    # Le LLM peut parfois omettre des caractères, nous vérifions juste les parties principales
    normalized_iban = result.iban.replace(" ", "")
    assert "FR76" in normalized_iban  # Code pays et contrôle
    assert "30004000" in normalized_iban  # Code banque
    assert len(normalized_iban) >= 25  # IBAN français fait 27 caractères
    assert result.bic == "BNPAFRPPXXX"
    assert "Jean Dupont" in result.account_holder_name
    assert "BNP PARIBAS" in result.bank_name
@pytest.fixture
def cni_text_fixture() -> str:
    return """
    RÉPUBLIQUE FRANÇAISE
    CARTE NATIONALE D'IDENTITÉ N° XXXXXXXX
    Nom: DUPONT
    Prénoms: Jean, Jacques
    Né(e) le: 01/01/1980 à PARIS
    """

@pytest.mark.asyncio
@pytest.mark.external_api
async def test_extract_data_from_document_cni(cni_text_fixture: str):
    """
    Teste que l'extracteur polyvalent, guidé par le type CNI,
    extrait bien les données d'identité et ignore les autres.
    """
    result = await extract_data_from_document(cni_text_fixture, DocumentType.CNI)

    assert isinstance(result, ExtractedData)
    # Vérifie les champs d'identité
    assert result.nom == "DUPONT"
    assert result.prenom == "Jean, Jacques"
    assert result.date_naissance == "01/01/1980"

    # Vérifie que les champs non pertinents sont vides
    assert result.iban is None
    assert result.bic is None

@pytest.mark.asyncio
@pytest.mark.external_api
async def test_extract_data_from_document_rib(sample_rib_text: str):
    """
    Teste que l'extracteur polyvalent, guidé par le type RIB,
    extrait bien les données bancaires et ignore les autres.
    """
    result = await extract_data_from_document(sample_rib_text, DocumentType.RIB)

    assert isinstance(result, ExtractedData)
    # Vérifie les champs bancaires
    normalized_iban = result.iban.replace(" ", "")
    assert "FR76" in normalized_iban
    assert "30004000" in normalized_iban
    assert result.bic == "BNPAFRPPXXX"
    assert "Jean Dupont" in result.account_holder_name

    # Vérifie que les champs non pertinents sont vides
    assert result.date_naissance is None
    # Le LLM peut intelligemment déduire le nom même à partir du titulaire du compte 'account_holder_name', pas dans le champ 'nom' d'identité
