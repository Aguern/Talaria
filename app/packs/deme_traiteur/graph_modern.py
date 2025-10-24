"""
DéMé Traiteur Pack - LangGraph Orchestration

Orchestrates the complete workflow for processing catering service requests:
1. Process and validate form data
2. Handle client (search or create in Notion)
3. Create prestation in Notion
4. Create devis lines in Notion
5. Create Google Calendar event
6. Copy and rename Google Sheet template
7. Fill Google Sheet with data
"""

import logging
from typing import Dict, Any, TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

from .integrations.notion_client import NotionClient
from .integrations.google_calendar_client import GoogleCalendarClient
from .integrations.google_sheets_client import GoogleSheetsClient
from .integrations.email_client import EmailClient

logger = logging.getLogger(__name__)


# Define the state for our graph
class DemeTraiteurState(TypedDict):
    """State for the DéMé Traiteur workflow"""
    # Inputs
    nom_complet: str
    email: str
    telephone: str
    adresse: str
    ville: str
    type_client: str
    date: str
    pax: int
    moment: str
    nom_prestation: str
    options: List[str]
    message: str

    # Processing state
    client_id: str
    prestation_id: str
    prestation_url: str
    devis_lines: List[Dict[str, Any]]
    calendar_event_id: str
    calendar_event_link: str
    devis_sheet_id: str
    devis_sheet_link: str
    devis_lines_count: int
    email_sent: bool

    # Error tracking
    errors: Annotated[List[str], operator.add]
    current_step: str


async def process_data(state: DemeTraiteurState) -> DemeTraiteurState:
    """
    Process and validate the form data
    """
    logger.info("Step 1: Processing and validating form data")

    # Set defaults
    if not state.get("moment"):
        state["moment"] = "Midi"

    # Map moment values to standardized format
    moment_mapping = {
        "Déjeuner": "Midi",
        "Dîner": "Soir",
        "Midi": "Midi",
        "Soir": "Soir"
    }
    state["moment"] = moment_mapping.get(state["moment"], "Midi")

    if not state.get("type_client"):
        state["type_client"] = "Particulier"

    # Always generate prestation name as "Nom Complet - PAX"
    state["nom_prestation"] = f"{state['nom_complet']} - {state['pax']}"

    if not state.get("options"):
        state["options"] = []

    # Initialize tracking fields
    state["errors"] = []
    state["devis_lines"] = []
    state["devis_lines_count"] = 0
    state["current_step"] = "process_data"

    # Validate required fields
    required_fields = ["nom_complet", "email", "date", "pax"]
    for field in required_fields:
        if not state.get(field):
            error_msg = f"Missing required field: {field}"
            logger.error(error_msg)
            state["errors"].append(error_msg)

    if state["errors"]:
        logger.error(f"Validation failed with {len(state['errors'])} errors")
        raise ValueError(f"Validation errors: {', '.join(state['errors'])}")

    logger.info("Data validation successful")
    return state


async def handle_client(state: DemeTraiteurState) -> DemeTraiteurState:
    """
    Search for existing client or create new one in Notion
    """
    logger.info("Step 2: Handling client in Notion")
    state["current_step"] = "handle_client"

    notion = NotionClient()

    try:
        # Search for existing client
        client_id = await notion.find_client_by_email(state["email"])

        if client_id:
            logger.info(f"Existing client found: {client_id}")
            state["client_id"] = client_id
        else:
            # Create new client
            logger.info(f"Creating new client: {state['nom_complet']}")
            client_data = {
                "nom_complet": state["nom_complet"],
                "email": state["email"],
                "telephone": state.get("telephone", ""),
                "ville": state.get("ville", ""),
                "adresse": state.get("adresse", ""),
                "type_client": state.get("type_client", "Particulier")
            }
            client_id = await notion.create_client(client_data)
            state["client_id"] = client_id
            logger.info(f"New client created: {client_id}")

        return state

    except Exception as e:
        error_msg = f"Error handling client: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        raise


async def create_prestation(state: DemeTraiteurState) -> DemeTraiteurState:
    """
    Create prestation in Notion
    """
    logger.info("Step 3: Creating prestation in Notion")
    state["current_step"] = "create_prestation"

    notion = NotionClient()

    try:
        prestation_data = {
            "nom_prestation": state["nom_prestation"],
            "date": state["date"],
            "pax": state["pax"],
            "moment": state["moment"],
            "statut": "A confirmer",
            "message": state.get("message", "")
        }

        result = await notion.create_prestation(prestation_data, state["client_id"])
        state["prestation_id"] = result["id"]
        state["prestation_url"] = result["url"]

        logger.info(f"Prestation created: {state['prestation_id']}")

        # Update client segment based on total prestations count
        prestation_count = await notion.count_client_prestations(state["client_id"])
        segment = notion.calculate_segment(prestation_count)
        await notion.update_client_segment(state["client_id"], segment)
        logger.info(f"Client segment updated to {segment} (based on {prestation_count} prestations)")

        return state

    except Exception as e:
        error_msg = f"Error creating prestation: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        raise


async def create_devis_lines(state: DemeTraiteurState) -> DemeTraiteurState:
    """
    Create devis lines in Notion based on selected options
    """
    logger.info("Step 4: Creating devis lines in Notion")
    state["current_step"] = "create_devis_lines"

    notion = NotionClient()
    lines_created = 0

    try:
        # Loop through each option selected
        for option_name in state["options"]:
            logger.info(f"Processing option: {option_name}")

            # Find catalogue item
            catalogue_item = await notion.find_catalogue_item_by_name(option_name)

            if catalogue_item:
                # Create devis line
                await notion.create_devis_line(
                    prestation_id=state["prestation_id"],
                    catalogue_item_id=catalogue_item["id"],
                    catalogue_item_name=option_name,
                    quantity=state["pax"]
                )
                lines_created += 1
                logger.info(f"Devis line created for: {option_name}")
            else:
                logger.warning(f"Catalogue item not found: {option_name}")
                state["errors"].append(f"Catalogue item not found: {option_name}")

        state["devis_lines_count"] = lines_created
        logger.info(f"Total devis lines created: {lines_created}")
        return state

    except Exception as e:
        error_msg = f"Error creating devis lines: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        raise


async def create_calendar_event(state: DemeTraiteurState) -> DemeTraiteurState:
    """
    Create Google Calendar event with enriched client and prestation information
    """
    logger.info("Step 8: Creating Google Calendar event with enriched data")
    state["current_step"] = "create_calendar_event"

    calendar = GoogleCalendarClient()

    try:
        # Prepare prestation data
        prestation_data = {
            "nom_prestation": state["nom_prestation"],
            "date": state["date"],
            "pax": state["pax"],
            "moment": state["moment"],
            "ville": state.get("ville", ""),
            "message": state.get("message", "")
        }

        # Prepare client data
        client_data = {
            "nom_complet": state["nom_complet"],
            "email": state["email"],
            "telephone": state.get("telephone", ""),
            "adresse": state.get("adresse", ""),
            "ville": state.get("ville", "")
        }

        result = await calendar.create_event_from_prestation(
            prestation_data=prestation_data,
            prestation_url=state["prestation_url"],
            client_data=client_data,
            devis_sheet_link=state["devis_sheet_link"]
        )

        state["calendar_event_id"] = result["id"]
        state["calendar_event_link"] = result["htmlLink"]

        logger.info(f"Calendar event created with enriched data: {state['calendar_event_id']}")
        return state

    except Exception as e:
        error_msg = f"Error creating calendar event: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        raise


async def copy_sheet_template(state: DemeTraiteurState) -> DemeTraiteurState:
    """
    Get a Google Sheet template (from pool or by copying master template)

    This uses a hybrid approach:
    1. Try to get a pre-created template from pool (fast)
    2. If pool is empty, copy the master template with retry logic
    """
    logger.info("Step 5: Getting Google Sheet template")
    state["current_step"] = "copy_sheet_template"

    sheets = GoogleSheetsClient()

    try:
        # Generate devis name for potential copy
        devis_name = f"Devis - {state['nom_complet']} - {state['date']}"

        # Get template (pool or copy with fallback)
        sheet_id = await sheets.get_template_with_fallback(devis_name)
        state["devis_sheet_id"] = sheet_id

        logger.info(f"Sheet template obtained: {sheet_id}")
        return state

    except Exception as e:
        error_msg = f"Error getting sheet template: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        raise


async def rename_sheet(state: DemeTraiteurState) -> DemeTraiteurState:
    """
    Rename the copied Google Sheet
    """
    logger.info("Step 6: Renaming Google Sheet")
    state["current_step"] = "rename_sheet"

    sheets = GoogleSheetsClient()

    try:
        # Generate new name
        new_name = f"Devis - {state['nom_complet']} - {state['date']}"

        result = await sheets.rename_file(state["devis_sheet_id"], new_name)
        state["devis_sheet_link"] = result["webViewLink"]

        logger.info(f"Sheet renamed to: {new_name}")
        return state

    except Exception as e:
        error_msg = f"Error renaming sheet: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        raise


async def fill_sheet(state: DemeTraiteurState) -> DemeTraiteurState:
    """
    Fill the Google Sheet with data from Notion
    """
    logger.info("Step 7: Filling Google Sheet with data")
    state["current_step"] = "fill_sheet"

    sheets = GoogleSheetsClient()
    notion = NotionClient()

    try:
        # Retrieve devis lines from Notion
        devis_lines = await notion.get_devis_lines_for_prestation(state["prestation_id"])
        state["devis_lines"] = devis_lines

        # Prepare client data
        client_data = {
            "nom_complet": state["nom_complet"],
            "email": state["email"],
            "telephone": state.get("telephone", ""),
            "adresse": state.get("adresse", ""),
            "ville": state.get("ville", "")
        }

        # Prepare prestation data
        prestation_data = {
            "nom_prestation": state["nom_prestation"],
            "date": state["date"],
            "pax": state["pax"],
            "moment": state["moment"]
        }

        # Fill the sheet
        await sheets.fill_devis_sheet(
            spreadsheet_id=state["devis_sheet_id"],
            client_data=client_data,
            prestation_data=prestation_data,
            devis_lines=devis_lines
        )

        logger.info("Google Sheet filled successfully")
        return state

    except Exception as e:
        error_msg = f"Error filling sheet: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        raise


async def send_email_notification(state: DemeTraiteurState) -> DemeTraiteurState:
    """
    Send email notification to DéMé with all prestation details
    """
    logger.info("Step 9: Sending email notification to DéMé")
    state["current_step"] = "send_email_notification"

    email_client = EmailClient()

    try:
        # Prepare client data
        client_data = {
            "nom_complet": state["nom_complet"],
            "email": state["email"],
            "telephone": state.get("telephone", ""),
            "adresse": state.get("adresse", ""),
            "ville": state.get("ville", ""),
            "type_client": state.get("type_client", "Particulier")
        }

        # Prepare prestation data
        prestation_data = {
            "date": state["date"],
            "pax": state["pax"],
            "moment": state["moment"],
            "options": state["options"],
            "message": state.get("message", "")
        }

        # Prepare links
        links = {
            "notion_url": state["prestation_url"],
            "sheet_url": state["devis_sheet_link"],
            "calendar_url": state.get("calendar_event_link", "")
        }

        # Send email
        result = await email_client.send_prestation_notification(
            client_data=client_data,
            prestation_data=prestation_data,
            links=links
        )

        state["email_sent"] = result["success"]

        if result["success"]:
            logger.info(f"Email notification sent successfully to {result.get('recipient')}")
        else:
            logger.warning(f"Email notification failed: {result.get('message')}")

        return state

    except Exception as e:
        error_msg = f"Error sending email notification: {str(e)}"
        logger.error(error_msg)
        # Don't fail the workflow if email fails - just log the error
        state["errors"].append(error_msg)
        state["email_sent"] = False
        return state


# Build the graph
def build_graph() -> StateGraph:
    """
    Build the LangGraph workflow
    """
    workflow = StateGraph(DemeTraiteurState)

    # Add nodes
    workflow.add_node("process_data", process_data)
    workflow.add_node("handle_client", handle_client)
    workflow.add_node("create_prestation", create_prestation)
    workflow.add_node("create_devis_lines", create_devis_lines)
    workflow.add_node("create_calendar_event", create_calendar_event)
    workflow.add_node("copy_sheet_template", copy_sheet_template)
    workflow.add_node("rename_sheet", rename_sheet)
    workflow.add_node("fill_sheet", fill_sheet)
    workflow.add_node("send_email_notification", send_email_notification)

    # Define the flow
    workflow.set_entry_point("process_data")
    workflow.add_edge("process_data", "handle_client")
    workflow.add_edge("handle_client", "create_prestation")
    workflow.add_edge("create_prestation", "create_devis_lines")
    workflow.add_edge("create_devis_lines", "copy_sheet_template")
    workflow.add_edge("copy_sheet_template", "rename_sheet")
    workflow.add_edge("rename_sheet", "fill_sheet")
    workflow.add_edge("fill_sheet", "create_calendar_event")
    workflow.add_edge("create_calendar_event", "send_email_notification")
    workflow.add_edge("send_email_notification", END)

    return workflow.compile()


# Main execute function (required by orchestrator)
async def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main execution function called by the orchestrator

    Args:
        inputs: Dictionary with form data matching manifest inputs

    Returns:
        Dictionary with results matching manifest outputs
    """
    logger.info("Starting DéMé Traiteur workflow execution")

    try:
        # Build the graph
        graph = build_graph()

        # Prepare initial state
        initial_state = DemeTraiteurState(
            nom_complet=inputs.get("nom_complet", ""),
            email=inputs.get("email", ""),
            telephone=inputs.get("telephone", ""),
            adresse=inputs.get("adresse", ""),
            ville=inputs.get("ville", ""),
            type_client=inputs.get("type_client", ""),
            date=inputs.get("date", ""),
            pax=inputs.get("pax", 0),
            moment=inputs.get("moment", ""),
            nom_prestation=inputs.get("nom_prestation", ""),
            options=inputs.get("options", []),
            client_id="",
            prestation_id="",
            prestation_url="",
            devis_lines=[],
            calendar_event_id="",
            calendar_event_link="",
            devis_sheet_id="",
            devis_sheet_link="",
            devis_lines_count=0,
            errors=[],
            current_step=""
        )

        # Run the graph
        final_state = await graph.ainvoke(initial_state)

        # Build result
        result = {
            "client_id": final_state["client_id"],
            "prestation_id": final_state["prestation_id"],
            "prestation_url": final_state["prestation_url"],
            "calendar_event_id": final_state["calendar_event_id"],
            "calendar_event_link": final_state["calendar_event_link"],
            "devis_sheet_id": final_state["devis_sheet_id"],
            "devis_sheet_link": final_state["devis_sheet_link"],
            "devis_lines_count": final_state["devis_lines_count"],
            "status": "completed",
            "errors": final_state.get("errors", [])
        }

        logger.info("DéMé Traiteur workflow completed successfully")
        return result

    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "current_step": inputs.get("current_step", "unknown")
        }
