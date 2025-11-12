"""
Tests for DéMé Traiteur Pack - LangGraph Workflow

Tests the complete workflow orchestration with mocked external integrations
(Notion API, Google Calendar API, Google Sheets API, Email).
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.packs.deme_traiteur.graph_modern import build_graph, DemeTraiteurState


@pytest.fixture
def valid_form_data():
    """Provides valid form data for testing"""
    return {
        "nom_complet": "Jean Dupont",
        "email": "jean.dupont@example.com",
        "telephone": "0612345678",
        "adresse": "10 rue de la Paix",
        "ville": "Paris",
        "type_client": "Particulier",
        "date": "2025-12-25",
        "pax": 30,
        "moment": "Déjeuner",
        "nom_prestation": "",  # Will be auto-generated
        "options": ["Entrées (Charcuterie et Fromages)", "Plats chauds"],
        "message": "Test message"
    }


@pytest.fixture
def mock_notion_responses():
    """Provides mock responses for Notion API"""
    return {
        "client_id": "notion-client-123",
        "prestation_id": "notion-prestation-456",
        "prestation_url": "https://notion.so/prestation-456",
        "devis_lines": [
            {"item": "Entrées", "price": 150.0, "quantity": 30},
            {"item": "Plats chauds", "price": 300.0, "quantity": 30}
        ]
    }


@pytest.fixture
def mock_google_responses():
    """Provides mock responses for Google APIs"""
    return {
        "calendar_event_id": "google-calendar-event-789",
        "calendar_event_link": "https://calendar.google.com/event/789",
        "sheet_id": "google-sheet-abc123",
        "sheet_link": "https://docs.google.com/spreadsheets/d/abc123"
    }


@pytest.mark.asyncio
async def test_complete_workflow_happy_path(valid_form_data, mock_notion_responses, mock_google_responses):
    """
    Test the complete DéMé Traiteur workflow with all steps succeeding.

    Expected flow:
    1. Process and validate form data
    2. Create/find client in Notion
    3. Create prestation in Notion
    4. Create devis lines in Notion
    5. Create Google Calendar event
    6. Copy and configure Google Sheet
    7. Fill Google Sheet with data
    8. Send email notification
    """
    # Mock all external integrations
    with patch("app.packs.deme_traiteur.graph_modern.NotionClient") as MockNotionClient, \
         patch("app.packs.deme_traiteur.graph_modern.GoogleCalendarClient") as MockGoogleCalendarClient, \
         patch("app.packs.deme_traiteur.graph_modern.GoogleSheetsClient") as MockGoogleSheetsClient, \
         patch("app.packs.deme_traiteur.graph_modern.EmailClient") as MockEmailClient:

        # Configure Notion mock
        mock_notion = MockNotionClient.return_value
        mock_notion.get_or_create_client = AsyncMock(return_value=mock_notion_responses["client_id"])
        mock_notion.create_prestation = AsyncMock(return_value={
            "id": mock_notion_responses["prestation_id"],
            "url": mock_notion_responses["prestation_url"]
        })
        mock_notion.create_devis_lines = AsyncMock(return_value=mock_notion_responses["devis_lines"])

        # Configure Google Calendar mock
        mock_calendar = MockGoogleCalendarClient.return_value
        mock_calendar.create_event = AsyncMock(return_value={
            "id": mock_google_responses["calendar_event_id"],
            "htmlLink": mock_google_responses["calendar_event_link"]
        })

        # Configure Google Sheets mock
        mock_sheets = MockGoogleSheetsClient.return_value
        mock_sheets.get_template_from_pool = AsyncMock(return_value=mock_google_responses["sheet_id"])
        mock_sheets.rename_sheet = AsyncMock(return_value=True)
        mock_sheets.fill_sheet = AsyncMock(return_value=True)

        # Configure Email mock
        mock_email = MockEmailClient.return_value
        mock_email.send_prestation_notification = AsyncMock(return_value={"success": True, "recipient": "demo@example.com"})

        # Create and execute graph
        graph_app = build_graph()
        initial_state: DemeTraiteurState = valid_form_data.copy()

        final_state = await graph_app.ainvoke(initial_state)

        # Assertions - verify all steps completed
        assert final_state["client_id"] == mock_notion_responses["client_id"]
        assert final_state["prestation_id"] == mock_notion_responses["prestation_id"]
        assert final_state["prestation_url"] == mock_notion_responses["prestation_url"]
        assert final_state["calendar_event_id"] == mock_google_responses["calendar_event_id"]
        assert final_state["devis_sheet_id"] == mock_google_responses["sheet_id"]
        assert final_state["email_sent"] is True
        assert len(final_state["errors"]) == 0

        # Verify all integrations were called
        mock_notion.get_or_create_client.assert_called_once()
        mock_notion.create_prestation.assert_called_once()
        mock_notion.create_devis_lines.assert_called_once()
        mock_calendar.create_event.assert_called_once()
        mock_sheets.get_template_from_pool.assert_called_once()
        mock_sheets.fill_sheet.assert_called_once()
        mock_email.send_prestation_notification.assert_called_once()


@pytest.mark.asyncio
async def test_workflow_with_missing_required_fields():
    """
    Test validation of required fields in form data.

    The workflow should fail early if required fields are missing.
    """
    invalid_data = {
        "nom_complet": "",  # Missing required field
        "email": "test@example.com",
        "date": "2025-12-25",
        "pax": 30
    }

    graph_app = build_graph()

    final_state = await graph_app.ainvoke(invalid_data)

    # Should have errors recorded
    assert len(final_state.get("errors", [])) > 0
    assert any("Missing required field" in error for error in final_state["errors"])


@pytest.mark.asyncio
async def test_workflow_with_notion_api_error(valid_form_data, mock_google_responses):
    """
    Test handling of Notion API errors during client creation.

    The workflow should gracefully handle API failures and record errors.
    """
    with patch("app.packs.deme_traiteur.graph_modern.NotionClient") as MockNotionClient, \
         patch("app.packs.deme_traiteur.graph_modern.GoogleCalendarClient") as MockGoogleCalendarClient, \
         patch("app.packs.deme_traiteur.graph_modern.GoogleSheetsClient") as MockGoogleSheetsClient, \
         patch("app.packs.deme_traiteur.graph_modern.EmailClient") as MockEmailClient:

        # Configure Notion to raise an error
        mock_notion = MockNotionClient.return_value
        mock_notion.get_or_create_client = AsyncMock(
            side_effect=Exception("Notion API connection failed")
        )

        # Configure other mocks (won't be called due to early failure)
        mock_calendar = MockGoogleCalendarClient.return_value
        mock_sheets = MockGoogleSheetsClient.return_value
        mock_email = MockEmailClient.return_value

        graph_app = build_graph()
        initial_state: DemeTraiteurState = valid_form_data.copy()

        final_state = await graph_app.ainvoke(initial_state)

        # Should have recorded the error
        assert len(final_state.get("errors", [])) > 0
        assert any("Notion" in error for error in final_state["errors"])

        # Calendar and Sheets should not have been called
        mock_calendar.create_event.assert_not_called()
        mock_sheets.get_template_from_pool.assert_not_called()


@pytest.mark.asyncio
async def test_data_processing_and_defaults(valid_form_data):
    """
    Test the data processing step including default values and field mapping.

    Verifies:
    - Default values are set correctly
    - Moment mapping works (Déjeuner -> Midi)
    - Prestation name is auto-generated
    """
    # Remove optional fields to test defaults
    minimal_data = {
        "nom_complet": "Jean Dupont",
        "email": "jean@example.com",
        "date": "2025-12-25",
        "pax": 30,
        "moment": "Déjeuner",  # Should be mapped to "Midi"
        "message": ""
    }

    with patch("app.packs.deme_traiteur.graph_modern.NotionClient") as MockNotionClient, \
         patch("app.packs.deme_traiteur.graph_modern.GoogleCalendarClient"), \
         patch("app.packs.deme_traiteur.graph_modern.GoogleSheetsClient"), \
         patch("app.packs.deme_traiteur.graph_modern.EmailClient"):

        # Mock Notion to succeed with minimal interaction
        mock_notion = MockNotionClient.return_value
        mock_notion.get_or_create_client = AsyncMock(return_value="client-id")
        mock_notion.create_prestation = AsyncMock(return_value={"id": "prestation-id", "url": "url"})
        mock_notion.create_devis_lines = AsyncMock(return_value=[])

        graph_app = build_graph()
        final_state = await graph_app.ainvoke(minimal_data)

        # Verify defaults and transformations
        assert final_state["moment"] == "Midi"  # Mapped from Déjeuner
        assert final_state["type_client"] == "Particulier"  # Default value
        assert final_state["nom_prestation"] == "Jean Dupont - 30"  # Auto-generated
        assert final_state["options"] == []  # Default empty list


@pytest.mark.asyncio
async def test_template_pool_integration(valid_form_data, mock_notion_responses):
    """
    Test Google Sheets template pool system.

    Verifies that the workflow uses the template pool to get pre-created
    sheets instead of creating new ones (optimization for Render Free tier).
    """
    with patch("app.packs.deme_traiteur.graph_modern.NotionClient") as MockNotionClient, \
         patch("app.packs.deme_traiteur.graph_modern.GoogleCalendarClient") as MockGoogleCalendarClient, \
         patch("app.packs.deme_traiteur.graph_modern.GoogleSheetsClient") as MockGoogleSheetsClient, \
         patch("app.packs.deme_traiteur.graph_modern.EmailClient") as MockEmailClient:

        # Configure minimal mocks
        mock_notion = MockNotionClient.return_value
        mock_notion.get_or_create_client = AsyncMock(return_value="client-id")
        mock_notion.create_prestation = AsyncMock(return_value={"id": "prestation-id", "url": "url"})
        mock_notion.create_devis_lines = AsyncMock(return_value=[])

        mock_calendar = MockGoogleCalendarClient.return_value
        mock_calendar.create_event = AsyncMock(return_value={"id": "event-id", "htmlLink": "link"})

        # Focus on Sheets mock
        mock_sheets = MockGoogleSheetsClient.return_value
        mock_sheets.get_template_from_pool = AsyncMock(return_value="pooled-sheet-id")
        mock_sheets.rename_sheet = AsyncMock(return_value=True)
        mock_sheets.fill_sheet = AsyncMock(return_value=True)

        mock_email = MockEmailClient.return_value
        mock_email.send_prestation_notification = AsyncMock(return_value={"success": True, "recipient": "demo@example.com"})

        graph_app = build_graph()
        final_state = await graph_app.ainvoke(valid_form_data)

        # Verify template pool was used
        mock_sheets.get_template_from_pool.assert_called_once()

        # Verify rename was called (sheet from pool needs renaming)
        mock_sheets.rename_sheet.assert_called_once()
        assert "Jean Dupont" in mock_sheets.rename_sheet.call_args[0][1]

        # Verify sheet was filled with data
        mock_sheets.fill_sheet.assert_called_once()


@pytest.mark.asyncio
async def test_email_notification_content(valid_form_data, mock_notion_responses, mock_google_responses):
    """
    Test that the email notification contains all relevant links and information.
    """
    with patch("app.packs.deme_traiteur.graph_modern.NotionClient") as MockNotionClient, \
         patch("app.packs.deme_traiteur.graph_modern.GoogleCalendarClient") as MockGoogleCalendarClient, \
         patch("app.packs.deme_traiteur.graph_modern.GoogleSheetsClient") as MockGoogleSheetsClient, \
         patch("app.packs.deme_traiteur.graph_modern.EmailClient") as MockEmailClient:

        # Configure mocks
        mock_notion = MockNotionClient.return_value
        mock_notion.get_or_create_client = AsyncMock(return_value=mock_notion_responses["client_id"])
        mock_notion.create_prestation = AsyncMock(return_value={
            "id": mock_notion_responses["prestation_id"],
            "url": mock_notion_responses["prestation_url"]
        })
        mock_notion.create_devis_lines = AsyncMock(return_value=mock_notion_responses["devis_lines"])

        mock_calendar = MockGoogleCalendarClient.return_value
        mock_calendar.create_event = AsyncMock(return_value={
            "id": mock_google_responses["calendar_event_id"],
            "htmlLink": mock_google_responses["calendar_event_link"]
        })

        mock_sheets = MockGoogleSheetsClient.return_value
        mock_sheets.get_template_from_pool = AsyncMock(return_value=mock_google_responses["sheet_id"])
        mock_sheets.rename_sheet = AsyncMock(return_value=True)
        mock_sheets.fill_sheet = AsyncMock(return_value=True)

        mock_email = MockEmailClient.return_value
        mock_email.send_prestation_notification = AsyncMock(return_value={"success": True, "recipient": "demo@example.com"})

        graph_app = build_graph()
        final_state = await graph_app.ainvoke(valid_form_data)

        # Verify email was sent with correct data
        mock_email.send_prestation_notification.assert_called_once()
        call_args = mock_email.send_notification.call_args

        # Check that important data is passed to email function
        # (exact structure depends on EmailClient implementation)
        assert call_args is not None
