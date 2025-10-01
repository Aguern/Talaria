# Fichier: tests/packs/test_form_3916_graph.py

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.packs.form_3916.graph import create_form_3916_graph, Form3916State
from app.tools.document_classifier import DocumentType

@pytest.fixture
def graph_app():
    """Fournit une instance compilée du graphe."""
    return create_form_3916_graph()

@pytest.mark.asyncio
async def test_graph_happy_path(graph_app):
    """
    Teste le chemin idéal où le document contient toutes les informations.
    Le graphe doit aller jusqu'au bout et générer un PDF.
    """
    # Mock des outils pour isoler la logique du graphe
    mock_extracted_data = MagicMock()
    mock_extracted_data.iban = "FR123"
    mock_extracted_data.bank_name = "Test Bank"
    mock_extracted_data.account_holder_name = "Prénom Nom"
    # Mock du model_dump pour retourner les bonnes données avec tous les champs requis
    mock_extracted_data.model_dump.return_value = {
        "iban": "FR123",
        "bank_name": "Test Bank",
        "account_holder_name": "Prénom Nom",
        "adresse": "10 Rue de la Paix, 75001 Paris",
        "numero_compte": "FR123",
        "date_ouverture": "01/01/2020"
    }

    with patch("app.tools.document_parser.extract_text_from_file", return_value="some text") as mock_parse, \
         patch("app.tools.document_classifier.classify_document", new_callable=AsyncMock, return_value=DocumentType.RIB) as mock_classify, \
         patch("app.tools.data_extractor.extract_data_from_document", new_callable=AsyncMock, return_value=mock_extracted_data) as mock_extract, \
         patch("app.tools.pdf_filler.fill_3916_pdf", return_value=b"filled pdf content") as mock_fill:

        # Définir l'état initial (adapté pour la nouvelle API multi-documents)
        initial_state: Form3916State = {"input_files": [{"document.pdf": b"dummy content"}]}

        # Exécuter le graphe
        final_state = await graph_app.ainvoke(initial_state)

        # Assertions
        mock_parse.assert_called_once()
        mock_classify.assert_called_once()
        mock_extract.assert_called_once()
        mock_fill.assert_called_once()

        # Vérifier que l'état final contient le PDF généré
        assert final_state["generated_pdf"] == b"filled pdf content"
        # Vérifier que le graphe est bien allé jusqu'à la fin (pas en pause)
        assert final_state.get("question_to_user") is None

@pytest.mark.asyncio
async def test_graph_human_in_the_loop_path(graph_app):
    """
    Teste le chemin où une information est manquante.
    Le graphe doit s'arrêter et poser une question à l'utilisateur.
    """
    # Mock de l'extracteur qui ne trouve pas le nom
    mock_extracted_data_incomplete = MagicMock()
    mock_extracted_data_incomplete.iban = "FR123"
    mock_extracted_data_incomplete.bank_name = "Test Bank"
    mock_extracted_data_incomplete.account_holder_name = None  # NOM MANQUANT
    # Mock du model_dump pour retourner les données partielles (il manque des champs requis)
    mock_extracted_data_incomplete.model_dump.return_value = {
        "iban": "FR123",
        "bank_name": "Test Bank"
        # Il manque nom, prenom, adresse, numero_compte, date_ouverture
    }

    with patch("app.tools.document_parser.extract_text_from_file", return_value="some text"), \
         patch("app.tools.document_classifier.classify_document", new_callable=AsyncMock, return_value=DocumentType.RIB), \
         patch("app.tools.data_extractor.extract_data_from_document", new_callable=AsyncMock, return_value=mock_extracted_data_incomplete), \
         patch("app.tools.pdf_filler.fill_3916_pdf") as mock_fill:

        initial_state: Form3916State = {"input_files": [{"document.pdf": b"dummy content"}]}

        # Exécuter le graphe
        final_state = await graph_app.ainvoke(initial_state)

        # Le PDF ne doit PAS avoir été rempli
        mock_fill.assert_not_called()

        # Le graphe doit s'être mis en pause et poser une question
        assert final_state.get("generated_pdf") is None
        assert "Veuillez fournir les valeurs pour les champs suivants:" in final_state["question_to_user"]
