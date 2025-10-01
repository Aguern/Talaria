from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid
import json
import asyncio
import httpx
import base64
from redis import Redis

from core.auth import get_current_active_user
from core.database import get_db
from core import models, schemas
from core.tasks import execute_recipe_graph
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Pydantic models
class Conversation(BaseModel):
    id: str
    title: str
    createdAt: str
    updatedAt: str
    messages: List[Dict[str, Any]] = []
    metadata: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    message: str
    conversationId: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = []
    activeRecipes: Optional[List[str]] = []
    streaming: bool = True
    workflowTaskId: Optional[str] = None  # For continuing a workflow

class MCPExecuteRequest(BaseModel):
    recipeId: str
    toolName: str
    arguments: Dict[str, Any]

# In-memory storage for conversations (should be in DB in production)
conversations_store: Dict[str, Conversation] = {}

@router.get("/conversations")
async def get_conversations(
    current_user: schemas.CurrentUser = Depends(get_current_active_user)
) -> List[Conversation]:
    """Get all conversations for the current user"""
    # Filter conversations by user (simplified for demo)
    user_conversations = [
        conv for conv in conversations_store.values()
        # In production, filter by user ID
    ]
    return user_conversations

@router.post("/conversations")
async def create_conversation(
    conversation: Conversation,
    current_user: schemas.CurrentUser = Depends(get_current_active_user)
) -> Conversation:
    """Create a new conversation"""
    conversations_store[conversation.id] = conversation
    return conversation

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: schemas.CurrentUser = Depends(get_current_active_user)
):
    """Delete a conversation"""
    if conversation_id in conversations_store:
        del conversations_store[conversation_id]
    return {"success": True}

@router.post("/chat/message")
async def send_message(
    request: ChatMessage,
    current_user: schemas.CurrentUser = Depends(get_current_active_user)
):
    """Send a message and get streaming response"""

    async def generate():
        # Helper function to format SSE
        def sse_format(data):
            return f"data: {json.dumps(data)}\n\n"

        # Simulate AI processing
        yield sse_format({'type': 'text', 'content': 'Je vais vous aider avec '})

        await asyncio.sleep(0.5)

        # Check if user is providing missing information (auto-detect)
        # This is a simpler approach that doesn't require frontend changes
        if "form3916" in request.activeRecipes and not request.attachments:
            # Check if the message contains typical missing field patterns
            message_lower = request.message.lower()
            contains_birth_info = any(x in message_lower for x in ['naissance', 'né', 'mai 1999', 'ploërmel'])
            contains_address_info = any(x in message_lower for x in ['adresse', 'impasse', 'doussard', '74210'])

            if contains_birth_info or contains_address_info:
                # User is providing missing information for an existing workflow
                yield sse_format({'type': 'text', 'content': 'Je vais compléter le formulaire avec vos informations... '})

                # Parse user input to extract missing fields
                import re
                user_data = {}
                message = request.message.lower()

                # Extract date of birth
                date_patterns = [
                    r"(?:date de naissance|né[e]? le|né[e]?)[ :]*(\d{1,2}[ /\-]?\w+[ /\-]?\d{4})",
                    r"(\d{1,2} \w+ \d{4})"
                ]
                for pattern in date_patterns:
                    match = re.search(pattern, message)
                    if match:
                        date_str = match.group(1)
                        # Convert to DD/MM/YYYY format
                        months = {
                            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
                            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
                            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
                        }
                        for month_name, month_num in months.items():
                            date_str = date_str.replace(month_name, month_num)
                        # Clean and format
                        date_str = re.sub(r'(\d+)\s+(\d+)\s+(\d+)', r'\1/\2/\3', date_str)
                        user_data['date_naissance'] = date_str
                        break

                # Extract place of birth
                lieu_patterns = [
                    r"(?:lieu de naissance|né[e]? à|à)[ :]*([A-Za-zÀ-ÿ\-\s]+?)(?:\.|,|$)",
                    r"à ([A-Za-zÀ-ÿ\-\s]+)"
                ]
                for pattern in lieu_patterns:
                    match = re.search(pattern, message)
                    if match:
                        lieu = match.group(1).strip().title()
                        if lieu and len(lieu) > 2:
                            user_data['lieu_naissance'] = lieu
                            break

                # Extract address
                adresse_patterns = [
                    r"(?:adresse|habite|domicile)[ :]*([^,\n]+(?:,\s*\d{5}\s+[^,\n]+)?)",
                    r"(\d+[^,\n]*\d{5}[^,\n]*)"
                ]
                for pattern in adresse_patterns:
                    match = re.search(pattern, message, re.IGNORECASE)
                    if match:
                        user_data['adresse_complete'] = match.group(1).strip()
                        break

                # Get last task with AWAITING_USER_INPUT status from Redis
                redis_json_client = Redis.from_url("redis://redis:6379/0", decode_responses=True)

                # Find the most recent task awaiting input
                # We'll scan recent task IDs (this is a simple approach for now)
                last_task_id = None
                last_task_data = None

                # Check last 100 keys for recent tasks
                for key in redis_json_client.scan_iter("task:*", count=100):
                    task_data = redis_json_client.get(key)
                    if task_data:
                        task_info = json.loads(task_data)
                        if task_info.get("status") == "AWAITING_USER_INPUT":
                            last_task_id = key.replace("task:", "")
                            last_task_data = task_info
                            break

                if last_task_data:
                    consolidated = last_task_data.get("result", {}).get("consolidated_data", {})

                    # Merge with new data
                    consolidated.update(user_data)

                    # Relaunch the workflow with updated data
                    new_task_id = str(uuid.uuid4())
                    redis_json_client.set(f"task:{new_task_id}", json.dumps({"status": "PENDING"}))

                    # Prepare state with all data
                    # We need to provide empty input_files to avoid error
                    # and mark that we already have classified docs to skip initial steps
                    updated_state = {
                        "input_files": [],  # Empty to avoid KeyError
                        "classified_docs": [],  # Mark as already done
                        "consolidated_data": consolidated,
                        "missing_critical": [],  # Will be recalculated by the graph
                        "user_provided_data": user_data
                    }

                    # Launch continuation task
                    execute_recipe_graph.delay(task_id=new_task_id, state=updated_state)

                    # Poll for results (same logic as before)
                    max_polls = 60
                    for poll_count in range(max_polls):
                        await asyncio.sleep(1)

                        new_task_data = redis_json_client.get(f"task:{new_task_id}")
                        if new_task_data:
                            new_task_info = json.loads(new_task_data)

                            if new_task_info.get("status") == "COMPLETED":
                                # Successfully generated PDF
                                yield sse_format({
                                    'type': 'tool_call',
                                    'tool_call': {
                                        'name': 'form3916_complete',
                                        'status': 'success',
                                        'result': new_task_info.get("result", {})
                                    }
                                })

                                if new_task_info.get("generated_pdf"):
                                    yield sse_format({'type': 'text', 'content': '✅ Le formulaire 3916 a été généré avec succès!'})
                                    yield sse_format({
                                        'type': 'pdf_generated',
                                        'pdf': new_task_info["generated_pdf"]
                                    })
                                break
                            elif new_task_info.get("status") == "ERROR":
                                yield sse_format({'type': 'text', 'content': f'❌ Erreur: {new_task_info.get("error", "Erreur inconnue")}'})
                                break

                    yield sse_format({'type': 'done'})
                    return

        # Check if Form3916 is active
        elif "form3916" in request.activeRecipes:
            yield sse_format({'type': 'text', 'content': 'le formulaire 3916. '})

            # Check for attachments
            if request.attachments:
                yield sse_format({
                    'type': 'tool_call',
                    'tool_call': {
                        'name': 'form3916_extract',
                        'displayName': 'Extraction des données',
                        'description': 'Analyse des documents fournis',
                        'status': 'running'
                    }
                })

                # Launch real extraction via Celery task
                task_id = str(uuid.uuid4())

                # Initialize Redis client
                redis_client = Redis.from_url("redis://redis:6379/0", decode_responses=False)

                # Prepare files for the pack
                input_files_data = []
                for attachment in request.attachments:
                    # Get file content from Redis using file ID
                    file_id = attachment.get('id')
                    if file_id:
                        # Retrieve actual file content from Redis
                        file_content = redis_client.get(f"file:{file_id}")
                        if file_content:
                            input_files_data.append({
                                attachment.get('name', 'document'): file_content
                            })
                        else:
                            # File not found in Redis, log warning
                            print(f"Warning: File {file_id} not found in Redis")
                    else:
                        print(f"Warning: No file ID for attachment {attachment.get('name')}")

                # Save initial state using a separate client for JSON data
                redis_json_client = Redis.from_url("redis://redis:6379/0", decode_responses=True)
                redis_json_client.set(f"task:{task_id}", json.dumps({"status": "PENDING"}))

                # Launch async task
                initial_state = {"input_files": input_files_data}
                execute_recipe_graph.delay(task_id=task_id, state=initial_state)

                # Poll for results
                max_polls = 60  # Max 60 seconds (increased for OCR processing)
                for poll_count in range(max_polls):
                    await asyncio.sleep(1)

                    # Show progress every 10 seconds
                    if poll_count > 0 and poll_count % 10 == 0:
                        yield sse_format({
                            'type': 'text',
                            'content': f'⏳ Traitement en cours... ({poll_count}s)'
                        })

                    task_data = redis_json_client.get(f"task:{task_id}")
                    if task_data:
                        task_info = json.loads(task_data)

                        if task_info.get("status") == "COMPLETED":
                            result = task_info.get("result", {})
                            consolidated_data = result.get("consolidated_data", {})

                            yield sse_format({
                                'type': 'tool_call',
                                'tool_call': {
                                    'name': 'form3916_extract',
                                    'status': 'success',
                                    'result': consolidated_data
                                }
                            })

                            # Format extracted data
                            data = consolidated_data
                            content = "J'ai extrait les informations suivantes de vos documents:\n\n"

                            # Informations du déclarant
                            if data.get("nom") or data.get("prenom"):
                                content += f"**Déclarant:**\n"
                                if data.get("nom"):
                                    content += f"- Nom: {data['nom']}\n"
                                if data.get("prenom"):
                                    content += f"- Prénom: {data['prenom']}\n"
                                if data.get("date_naissance"):
                                    content += f"- Date de naissance: {data['date_naissance']}\n"
                                if data.get("lieu_naissance"):
                                    content += f"- Lieu de naissance: {data['lieu_naissance']}\n"
                                if data.get("adresse_complete"):
                                    content += f"- Adresse: {data['adresse_complete']}\n"

                            # Informations du compte
                            if data.get("numero_compte") or data.get("designation_etablissement"):
                                content += f"\n**Compte bancaire:**\n"
                                if data.get("numero_compte"):
                                    content += f"- Numéro de compte: {data['numero_compte']}\n"
                                if data.get("designation_etablissement"):
                                    content += f"- Établissement: {data['designation_etablissement']}\n"
                                if data.get("adresse_etablissement"):
                                    content += f"- Adresse établissement: {data['adresse_etablissement']}\n"
                                if data.get("date_ouverture"):
                                    content += f"- Date d'ouverture: {data['date_ouverture']}\n"
                                if data.get("date_cloture"):
                                    content += f"- Date de clôture: {data['date_cloture']}\n"

                            missing = result.get("missing_critical", [])
                            if missing:
                                content += f"\n⚠️ Informations manquantes: {', '.join(missing)}\n"
                                content += "Pouvez-vous me fournir ces informations?"
                            else:
                                content += "\nVoulez-vous générer le formulaire 3916 avec ces données?"

                            yield sse_format({'type': 'text', 'content': content})
                            break

                        elif task_info.get("status") == "PROCESSING":
                            # Task is still processing, continue polling
                            continue

                        elif task_info.get("status") == "ERROR":
                            # Task failed with error
                            error_msg = task_info.get("error", "Une erreur est survenue lors du traitement")
                            yield sse_format({
                                'type': 'tool_call',
                                'tool_call': {
                                    'name': 'form3916_extract',
                                    'status': 'error',
                                    'result': {'error': error_msg}
                                }
                            })
                            yield sse_format({'type': 'text', 'content': f'❌ Erreur: {error_msg}'})
                            break

                        elif task_info.get("status") == "AWAITING_USER_INPUT":
                            question = task_info.get("current_question", "")
                            missing_fields = task_info.get("missing_fields", [])
                            consolidated_data = task_info.get("result", {}).get("consolidated_data", {})

                            yield sse_format({
                                'type': 'tool_call',
                                'tool_call': {
                                    'name': 'form3916_extract',
                                    'status': 'awaiting_input',
                                    'result': consolidated_data,
                                    'workflowTaskId': task_id  # Include task ID for continuation
                                }
                            })

                            content = "❓ **Information requise:**\n\n"
                            if missing_fields:
                                content += f"Il me manque les informations suivantes pour compléter le formulaire 3916:\n"
                                for field in missing_fields:
                                    content += f"- {field}\n"
                                content += "\nPouvez-vous me fournir ces informations ?"
                            else:
                                content += question

                            # Include workflow context in response
                            yield sse_format({
                                'type': 'workflow_context',
                                'workflowTaskId': task_id,
                                'missingFields': missing_fields,
                                'consolidatedData': consolidated_data
                            })

                            yield sse_format({'type': 'text', 'content': content})
                            break
                else:
                    # Timeout - fallback to simple message
                    yield sse_format({
                        'type': 'tool_call',
                        'tool_call': {
                            'name': 'form3916_extract',
                            'status': 'error',
                            'result': {'error': 'Timeout lors du traitement'}
                        }
                    })
                    yield sse_format({'type': 'text', 'content': 'Le traitement prend plus de temps que prévu. Veuillez réessayer.'})
            else:
                content = (
                    "Pour remplir le formulaire 3916, j'ai besoin des informations suivantes:\n"
                    "- Vos informations personnelles (nom, prénom, adresse, date de naissance)\n"
                    "- Les détails du compte étranger (numéro, banque, date d'ouverture)\n\n"
                    "Vous pouvez me fournir ces informations par texte ou en téléchargeant des documents."
                )
                yield sse_format({'type': 'text', 'content': content})
        else:
            # Generic response
            content = (
                f"votre demande: {request.message}\n\n"
                "Pour activer des fonctionnalités spécifiques, vous pouvez activer une recette dans la barre latérale."
            )
            yield sse_format({'type': 'text', 'content': content})

        yield sse_format({'type': 'done'})

    if request.streaming:
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        # Non-streaming response
        return {
            "answer": f"Réponse à: {request.message}",
            "toolCalls": []
        }

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: schemas.CurrentUser = Depends(get_current_active_user)
):
    """Upload files for processing"""
    uploaded = []
    for file in files:
        # Read file content for processing
        content = await file.read()
        file_id = str(uuid.uuid4())

        # Store file content in Redis temporarily (in production use S3/storage)
        redis_client = Redis.from_url("redis://redis:6379/0")
        redis_client.set(f"file:{file_id}", content, ex=3600)  # Expire after 1 hour

        uploaded.append({
            "name": file.filename,
            "type": file.content_type,
            "size": file.size,
            "url": f"/api/files/{file_id}",
            "id": file_id
        })

    return {"files": uploaded}

# MCP Endpoints
@router.get("/mcp/recipes")
async def get_mcp_recipes(
    current_user: schemas.CurrentUser = Depends(get_current_active_user)
):
    """Get available MCP recipes"""
    return [
        {
            "id": "form3916",
            "name": "Formulaire 3916",
            "description": "Déclaration de comptes bancaires étrangers",
            "category": "fiscal",
            "available": True,
            "tools": [
                {
                    "name": "form3916_extract",
                    "description": "Extraire les informations de documents",
                    "category": "extraction"
                },
                {
                    "name": "form3916_complete",
                    "description": "Compléter le formulaire avec les données",
                    "category": "transformation"
                },
                {
                    "name": "form3916_generate",
                    "description": "Générer le PDF du formulaire",
                    "category": "generation"
                }
            ],
            "status": "disconnected"
        }
    ]

@router.post("/mcp/connect")
async def connect_mcp_recipe(
    request: Dict[str, str],
    current_user: schemas.CurrentUser = Depends(get_current_active_user)
):
    """Connect to an MCP recipe server"""
    recipe_id = request.get("recipeId")

    # Simulate connection to MCP server
    if recipe_id == "form3916":
        return {"success": True, "message": f"Connected to {recipe_id}"}

    return {"success": False, "error": "Recipe not found"}

@router.post("/mcp/disconnect")
async def disconnect_mcp_recipe(
    request: Dict[str, str],
    current_user: schemas.CurrentUser = Depends(get_current_active_user)
):
    """Disconnect from an MCP recipe server"""
    recipe_id = request.get("recipeId")
    return {"success": True, "message": f"Disconnected from {recipe_id}"}

@router.post("/mcp/execute")
async def execute_mcp_tool(
    request: MCPExecuteRequest,
    current_user: schemas.CurrentUser = Depends(get_current_active_user)
):
    """Execute a tool from an MCP recipe"""

    # Simulate tool execution
    if request.recipeId == "form3916":
        if request.toolName == "form3916_extract":
            return {
                "declarant": {
                    "nom": "ANGOUGEARD",
                    "prenom": "NICOLAS MARIE",
                    "date_naissance": "29/01/1998"
                },
                "compte": {
                    "numero_compte": "CH93-0076-2011-6238-5295-7",
                    "designation_etablissement": "CREDIT SUISSE SA"
                }
            }
        elif request.toolName == "form3916_generate":
            return {
                "pdf_url": f"/api/files/form3916_{uuid.uuid4()}.pdf",
                "status": "success"
            }

    raise HTTPException(status_code=404, detail="Tool not found")